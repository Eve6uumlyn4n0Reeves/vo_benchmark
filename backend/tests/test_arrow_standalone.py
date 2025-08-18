"""
独立的 Arrow 功能测试
"""
import pytest
import tempfile
import shutil
from pathlib import Path

# 测试 PyArrow 是否可用
try:
    import pyarrow as pa
    import pyarrow.ipc as ipc
    ARROW_AVAILABLE = True
except ImportError:
    ARROW_AVAILABLE = False


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Windows上可能存在句柄占用，使用忽略错误方式清理
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.mark.skipif(not ARROW_AVAILABLE, reason="PyArrow not available")
class TestArrowBasicFunctionality:
    """测试 Arrow 基本功能"""

    def test_arrow_installation(self):
        """测试 PyArrow 安装正确"""
        assert pa is not None
        assert ipc is not None

    def test_create_simple_table(self, temp_dir):
        """测试创建简单的 Arrow 表"""
        # 创建测试数据
        data = {
            'x': [1.0, 2.0, 3.0],
            'y': [4.0, 5.0, 6.0],
            'z': [7.0, 8.0, 9.0]
        }
        
        # 创建 Arrow 表
        arrays = {k: pa.array(v, type=pa.float32()) for k, v in data.items()}
        table = pa.Table.from_pydict(arrays)
        
        assert table.num_rows == 3
        assert table.num_columns == 3
        assert 'x' in table.column_names
        assert 'y' in table.column_names
        assert 'z' in table.column_names

    def test_write_read_arrow_file(self, temp_dir):
        """测试 Arrow 文件写入和读取"""
        # 创建测试数据
        data = {
            'precisions': [0.9, 0.8, 0.7, 0.6],
            'recalls': [0.1, 0.3, 0.6, 0.9],
            'thresholds': [0.9, 0.7, 0.4, 0.1]
        }
        
        # 创建 Arrow 表
        arrays = {k: pa.array(v, type=pa.float32()) for k, v in data.items()}
        table = pa.Table.from_pydict(arrays)
        
        # 写入文件
        output_path = temp_dir / "test.arrow"
        with ipc.new_file(output_path, table.schema) as sink:
            sink.write(table)
        
        # 验证文件存在
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # 读取文件
        with ipc.open_file(output_path) as source:
            read_table = source.read_all()
        
        # 验证数据
        assert read_table.num_rows == 4
        assert read_table.num_columns == 3
        
        # 验证数据内容
        precisions = read_table.column('precisions').to_pylist()
        recalls = read_table.column('recalls').to_pylist()
        thresholds = read_table.column('thresholds').to_pylist()
        
        # 浮点比较采用近似断言，避免 float32 读回与 Python float 的微小差异
        for a, b in zip(precisions, data['precisions']):
            assert abs(a - b) < 1e-6
        for a, b in zip(recalls, data['recalls']):
            assert abs(a - b) < 1e-6
        for a, b in zip(thresholds, data['thresholds']):
            assert abs(a - b) < 1e-6

    def test_arrow_with_metadata(self, temp_dir):
        """测试带元数据的 Arrow 文件"""
        # 创建测试数据
        data = {
            'x': [1.0, 2.0, 3.0],
            'y': [4.0, 5.0, 6.0]
        }
        
        # 创建 Arrow 表
        arrays = {k: pa.array(v, type=pa.float32()) for k, v in data.items()}
        table = pa.Table.from_pydict(arrays)
        
        # 添加元数据
        metadata = {
            'version': 'test',
            'algorithm': 'test_algorithm',
            'points': '3'
        }
        table = table.replace_schema_metadata(metadata)
        
        # 写入文件
        output_path = temp_dir / "test_metadata.arrow"
        with ipc.new_file(output_path, table.schema) as sink:
            sink.write(table)
        
        # 读取文件
        with ipc.open_file(output_path) as source:
            read_table = source.read_all()
        
        # 验证元数据
        assert read_table.schema.metadata is not None
        read_metadata = dict(read_table.schema.metadata)
        
        assert read_metadata[b'version'] == b'test'
        assert read_metadata[b'algorithm'] == b'test_algorithm'
        assert read_metadata[b'points'] == b'3'

    def test_arrow_compression(self, temp_dir):
        """测试 Arrow 文件压缩（如果支持）"""
        # 创建较大的测试数据
        size = 1000
        data = {
            'x': [float(i) for i in range(size)],
            'y': [float(i * 2) for i in range(size)],
            'z': [float(i * 3) for i in range(size)]
        }
        
        # 创建 Arrow 表
        arrays = {k: pa.array(v, type=pa.float32()) for k, v in data.items()}
        table = pa.Table.from_pydict(arrays)
        
        # 写入未压缩文件
        uncompressed_path = temp_dir / "uncompressed.arrow"
        with ipc.new_file(uncompressed_path, table.schema) as sink:
            sink.write(table)
        
        uncompressed_size = uncompressed_path.stat().st_size
        
        # 验证文件大小合理
        assert uncompressed_size > 1000  # 至少1KB
        
        # 读取验证
        with ipc.open_file(uncompressed_path) as source:
            read_table = source.read_all()
        
        assert read_table.num_rows == size
        assert read_table.column('x').to_pylist()[:5] == [0.0, 1.0, 2.0, 3.0, 4.0]


@pytest.mark.skipif(ARROW_AVAILABLE, reason="Test for when PyArrow is not available")
class TestArrowUnavailable:
    """测试 PyArrow 不可用时的行为"""

    def test_arrow_import_fails(self):
        """测试 PyArrow 导入失败"""
        with pytest.raises(ImportError):
            import pyarrow as pa


class TestArrowDataTypes:
    """测试 Arrow 数据类型"""

    @pytest.mark.skipif(not ARROW_AVAILABLE, reason="PyArrow not available")
    def test_different_data_types(self, temp_dir):
        """测试不同数据类型"""
        # 创建混合类型数据
        data = {
            'float_col': pa.array([1.1, 2.2, 3.3], type=pa.float32()),
            'double_col': pa.array([1.11, 2.22, 3.33], type=pa.float64()),
            'int_col': pa.array([1, 2, 3], type=pa.uint32()),
            'string_col': pa.array(['a', 'b', 'c'], type=pa.string())
        }
        
        table = pa.Table.from_pydict(data)
        
        # 写入文件
        output_path = temp_dir / "mixed_types.arrow"
        with ipc.new_file(output_path, table.schema) as sink:
            sink.write(table)
        
        # 读取文件
        with ipc.open_file(output_path) as source:
            read_table = source.read_all()
        
        # 验证数据类型
        assert read_table.column('float_col').type == pa.float32()
        assert read_table.column('double_col').type == pa.float64()
        assert read_table.column('int_col').type == pa.uint32()
        assert read_table.column('string_col').type == pa.string()
        
        # 验证数据内容
        vals = read_table.column('float_col').to_pylist()
        for a, b in zip(vals, [1.1, 2.2, 3.3]):
            assert abs(a - b) < 1e-6
        assert read_table.column('string_col').to_pylist() == ['a', 'b', 'c']


if __name__ == "__main__":
    # 简单的手动测试
    if ARROW_AVAILABLE:
        print("✅ PyArrow is available")
        
        # 测试基本功能
        data = {'x': [1, 2, 3], 'y': [4, 5, 6]}
        arrays = {k: pa.array(v) for k, v in data.items()}
        table = pa.Table.from_pydict(arrays)
        print(f"✅ Created table with {table.num_rows} rows and {table.num_columns} columns")
        
        # 测试文件操作
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.arrow', delete=False) as f:
            with ipc.new_file(f.name, table.schema) as sink:
                sink.write(table)
            print(f"✅ Wrote Arrow file: {f.name}")
            
            with ipc.open_file(f.name) as source:
                read_table = source.read_all()
            print(f"✅ Read Arrow file: {read_table.num_rows} rows")
        
        print("🎉 All basic Arrow tests passed!")
    else:
        print("❌ PyArrow is not available")
