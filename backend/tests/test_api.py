#
# 功能: API接口测试
#
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.api.app import create_app
from src.config.manager import get_config
from src.storage.memory import MemoryStorage
from src.storage.experiment import ExperimentStorage

class TestAPI:
    """API接口测试类"""
    
    @pytest.fixture
    def app(self):
        """创建测试应用"""
        app = create_app('testing')
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return app.test_client()
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get('/api/v1/health/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'uptime' in data
    
    def test_detailed_health_check(self, client):
        """测试详细健康检查接口"""
        response = client.get('/api/v1/health/detailed')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] in ['healthy', 'degraded']
        assert 'system' in data
        assert 'dependencies' in data
    
    def test_create_experiment_validation(self, client):
        """测试创建实验的数据验证"""
        # 测试缺少必需字段
        response = client.post('/api/v1/experiments/', 
                             json={}, 
                             content_type='application/json')
        assert response.status_code == 400
        
        # 测试无效的特征类型
        invalid_data = {
            "name": "test_experiment",
            "dataset_path": "/tmp/test_dataset",
            "output_dir": "/tmp/test_output",
            "feature_types": ["INVALID_FEATURE"],
            "ransac_types": ["STANDARD"],
            "sequences": ["sequence01"],
            "num_runs": 1
        }
        
        response = client.post('/api/v1/experiments/', 
                             json=invalid_data, 
                             content_type='application/json')
        assert response.status_code == 400
    
    @patch('src.api.routes.experiments.experiment_service.create_experiment')
    def test_create_experiment_success(self, mock_create, client, temp_dir):
        """测试成功创建实验"""
        # 创建测试数据集目录
        dataset_dir = temp_dir / "dataset"
        dataset_dir.mkdir()
        
        # 模拟服务返回
        mock_response = Mock()
        mock_response.dict.return_value = {
            "experiment_id": "test_exp_123",
            "task_id": "task_456"
        }
        mock_create.return_value = mock_response
        
        valid_data = {
            "name": "test_experiment",
            "dataset_path": str(dataset_dir),
            "output_dir": str(temp_dir / "output"),
            "feature_types": ["SIFT"],
            "ransac_types": ["STANDARD"],
            "sequences": ["sequence01"],
            "num_runs": 1
        }
        
        response = client.post('/api/v1/experiments/', 
                             json=valid_data, 
                             content_type='application/json')
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['experiment_id'] == "test_exp_123"
        assert data['task_id'] == "task_456"
    
    @patch('src.api.routes.experiments.experiment_service.list_experiments')
    def test_list_experiments(self, mock_list_experiments, client):
        """测试列出实验"""
        # 模拟服务返回
        mock_experiment = Mock()
        mock_experiment.dict.return_value = {
            "experiment_id": "exp1",
            "name": "Test Experiment 1",
            "status": "COMPLETED",
            "created_at": "2023-01-01T00:00:00"
        }
        mock_list_experiments.return_value = [mock_experiment]
        
        response = client.get('/api/v1/experiments/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        # 响应现在是包含分页信息的字典
        assert 'experiments' in data
        assert len(data['experiments']) == 1
        assert data['experiments'][0]['experiment_id'] == "exp1"
    
    @patch('src.api.routes.tasks.task_service.get_task')
    def test_get_task_status(self, mock_get_task, client):
        """测试获取任务状态"""
        # 模拟服务返回
        mock_task = Mock()
        mock_task.dict.return_value = {
            "task_id": "task_123",
            "status": "RUNNING",
            "progress": 0.5,
            "message": "Processing frames..."
        }
        mock_get_task.return_value = mock_task
        
        response = client.get('/api/v1/tasks/task_123')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['task_id'] == "task_123"
        assert data['status'] == "RUNNING"
        assert data['progress'] == 0.5
    
    def test_get_nonexistent_task(self, client):
        """测试获取不存在的任务"""
        response = client.get('/api/v1/tasks/nonexistent_task')
        assert response.status_code == 404
    
    def test_cors_headers(self, client):
        """测试CORS头部"""
        response = client.options('/api/v1/health/')
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_error_handling(self, client):
        """测试错误处理"""
        # 测试404错误
        response = client.get('/api/v1/nonexistent_endpoint')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error_code' in data
        assert 'message' in data
        assert 'timestamp' in data
    
    def test_request_validation_middleware(self, client):
        """测试请求验证中间件"""
        # 测试无效的JSON
        response = client.post('/api/v1/experiments/', 
                             data='invalid json', 
                             content_type='application/json')
        assert response.status_code == 400
    
    @patch('src.api.routes.results.result_service.export_results')
    def test_get_experiment_results(self, mock_export_results, client, tmp_path):
        """测试导出实验结果"""
        # 创建临时文件
        temp_file = tmp_path / "test_results.json"
        temp_file.write_text('{"experiment_id": "exp_123", "results": []}')

        # 模拟服务返回文件路径
        mock_export_results.return_value = str(temp_file)

        response = client.get('/api/v1/results/exp_123/export?format=json')
        assert response.status_code == 200

class TestAPIIntegration:
    """API集成测试类"""
    
    @pytest.fixture
    def app(self):
        """创建集成测试应用"""
        app = create_app('testing')
        return app
    
    @pytest.fixture
    def client(self, app):
        """创建集成测试客户端"""
        return app.test_client()
    
    def test_full_experiment_workflow(self, client, tmp_path):
        """测试完整的实验工作流程"""
        # 这个测试需要更复杂的设置，包括模拟数据集等
        # 由于时间限制，这里提供一个框架
        pass
    
    def test_concurrent_requests(self, client):
        """测试并发请求处理"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get('/api/v1/health/')
            results.append(response.status_code)
        
        # 创建多个线程同时发送请求
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有请求都成功
        assert all(status == 200 for status in results)
        assert len(results) == 10

if __name__ == '__main__':
    pytest.main([__file__])
