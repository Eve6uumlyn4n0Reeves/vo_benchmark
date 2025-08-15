#!/usr/bin/env python3
"""
优化验证脚本：验证轨迹加载优化是否正常工作
"""

import argparse
import asyncio
import time
import sys
from pathlib import Path
import json
import aiohttp
import logging

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.experiment import ExperimentStorage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OptimizationValidator:
    """优化验证器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        
        # 测试结果
        self.results = {
            'manifest_tests': [],
            'trajectory_tests': [],
            'pr_curve_tests': [],
            'performance_tests': [],
            'errors': []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_manifest_endpoint(self, experiment_id: str, algorithm_key: str) -> dict:
        """测试清单端点"""
        test_result = {
            'test': 'manifest',
            'experiment_id': experiment_id,
            'algorithm_key': algorithm_key,
            'success': False,
            'response_time': 0,
            'payload_size': 0,
            'has_trajectory': False,
            'has_pr_curve': False,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            url = f"{self.base_url}/api/v1/results/{experiment_id}/{algorithm_key}/manifest"
            async with self.session.get(url) as response:
                test_result['response_time'] = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    test_result['success'] = True
                    test_result['payload_size'] = len(await response.text())
                    
                    # 检查清单内容
                    test_result['has_trajectory'] = bool(data.get('trajectory'))
                    test_result['has_pr_curve'] = bool(data.get('pr_curve'))
                    
                    logger.info(f"✅ Manifest测试通过: {experiment_id}/{algorithm_key} ({test_result['response_time']:.3f}s)")
                else:
                    test_result['error'] = f"HTTP {response.status}"
                    logger.warning(f"❌ Manifest测试失败: {experiment_id}/{algorithm_key} - {test_result['error']}")
                    
        except Exception as e:
            test_result['error'] = str(e)
            test_result['response_time'] = time.time() - start_time
            logger.error(f"❌ Manifest测试异常: {experiment_id}/{algorithm_key} - {e}")
        
        self.results['manifest_tests'].append(test_result)
        return test_result
    
    async def test_trajectory_endpoint(self, experiment_id: str, algorithm_key: str, max_points: str = "1500") -> dict:
        """测试轨迹端点"""
        test_result = {
            'test': 'trajectory',
            'experiment_id': experiment_id,
            'algorithm_key': algorithm_key,
            'max_points': max_points,
            'success': False,
            'response_time': 0,
            'payload_size': 0,
            'point_count': 0,
            'compressed': False,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            url = f"{self.base_url}/api/v1/results/{experiment_id}/{algorithm_key}/trajectory"
            params = {'max_points': max_points} if max_points != "1500" else {}
            
            async with self.session.get(url, params=params) as response:
                test_result['response_time'] = time.time() - start_time
                
                # 检查响应头
                test_result['compressed'] = 'gzip' in response.headers.get('Content-Encoding', '')
                
                if response.status == 200:
                    data = await response.json()
                    test_result['success'] = True
                    test_result['payload_size'] = len(await response.text())
                    
                    # 计算点数
                    estimated = data.get('estimated_trajectory', data.get('poses', []))
                    test_result['point_count'] = len(estimated)
                    
                    logger.info(f"✅ 轨迹测试通过: {experiment_id}/{algorithm_key} ({test_result['point_count']} 点, {test_result['response_time']:.3f}s)")
                else:
                    test_result['error'] = f"HTTP {response.status}"
                    logger.warning(f"❌ 轨迹测试失败: {experiment_id}/{algorithm_key} - {test_result['error']}")
                    
        except Exception as e:
            test_result['error'] = str(e)
            test_result['response_time'] = time.time() - start_time
            logger.error(f"❌ 轨迹测试异常: {experiment_id}/{algorithm_key} - {e}")
        
        self.results['trajectory_tests'].append(test_result)
        return test_result
    
    async def test_pr_curve_endpoint(self, experiment_id: str, algorithm_key: str) -> dict:
        """测试PR曲线端点"""
        test_result = {
            'test': 'pr_curve',
            'experiment_id': experiment_id,
            'algorithm_key': algorithm_key,
            'success': False,
            'response_time': 0,
            'payload_size': 0,
            'point_count': 0,
            'has_raw_data': False,
            'compressed': False,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            url = f"{self.base_url}/api/v1/results/{experiment_id}/{algorithm_key}/pr-curve"
            async with self.session.get(url) as response:
                test_result['response_time'] = time.time() - start_time
                
                # 检查响应头
                test_result['compressed'] = 'gzip' in response.headers.get('Content-Encoding', '')
                
                if response.status == 200:
                    data = await response.json()
                    test_result['success'] = True
                    test_result['payload_size'] = len(await response.text())
                    
                    # 检查数据
                    test_result['point_count'] = len(data.get('precisions', []))
                    test_result['has_raw_data'] = 'raw_precisions' in data
                    
                    logger.info(f"✅ PR曲线测试通过: {experiment_id}/{algorithm_key} ({test_result['point_count']} 点, raw: {test_result['has_raw_data']})")
                else:
                    test_result['error'] = f"HTTP {response.status}"
                    logger.warning(f"❌ PR曲线测试失败: {experiment_id}/{algorithm_key} - {test_result['error']}")
                    
        except Exception as e:
            test_result['error'] = str(e)
            test_result['response_time'] = time.time() - start_time
            logger.error(f"❌ PR曲线测试异常: {experiment_id}/{algorithm_key} - {e}")
        
        self.results['pr_curve_tests'].append(test_result)
        return test_result
    
    async def test_performance_comparison(self, experiment_id: str, algorithm_key: str) -> dict:
        """测试性能对比（UI vs Full）"""
        test_result = {
            'test': 'performance',
            'experiment_id': experiment_id,
            'algorithm_key': algorithm_key,
            'ui_time': 0,
            'full_time': 0,
            'ui_size': 0,
            'full_size': 0,
            'ui_points': 0,
            'full_points': 0,
            'improvement_ratio': 0,
            'error': None
        }
        
        try:
            # 测试UI版本
            ui_result = await self.test_trajectory_endpoint(experiment_id, algorithm_key, "1500")
            if ui_result['success']:
                test_result['ui_time'] = ui_result['response_time']
                test_result['ui_size'] = ui_result['payload_size']
                test_result['ui_points'] = ui_result['point_count']
            
            # 测试Full版本
            full_result = await self.test_trajectory_endpoint(experiment_id, algorithm_key, "full")
            if full_result['success']:
                test_result['full_time'] = full_result['response_time']
                test_result['full_size'] = full_result['payload_size']
                test_result['full_points'] = full_result['point_count']
            
            # 计算改进比例
            if test_result['full_time'] > 0:
                test_result['improvement_ratio'] = test_result['full_time'] / test_result['ui_time']
            
            logger.info(f"📊 性能对比: UI({test_result['ui_points']}点, {test_result['ui_time']:.3f}s) vs Full({test_result['full_points']}点, {test_result['full_time']:.3f}s)")
            
        except Exception as e:
            test_result['error'] = str(e)
            logger.error(f"❌ 性能测试异常: {experiment_id}/{algorithm_key} - {e}")
        
        self.results['performance_tests'].append(test_result)
        return test_result
    
    def discover_test_cases(self, storage_root: str) -> list:
        """发现测试用例"""
        storage = ExperimentStorage(storage_root)
        test_cases = []
        
        experiments_dir = Path(storage_root) / "experiments"
        if not experiments_dir.exists():
            logger.warning(f"实验目录不存在: {experiments_dir}")
            return test_cases
        
        for exp_dir in experiments_dir.iterdir():
            if not exp_dir.is_dir():
                continue
            
            experiment_id = exp_dir.name
            
            # 查找算法
            algorithms = set()
            
            # 从轨迹目录发现
            traj_dir = exp_dir / "trajectories"
            if traj_dir.exists():
                for file in traj_dir.glob("*.json.gz"):
                    algorithms.add(file.stem)
                for file in traj_dir.glob("*.arrow"):
                    if not file.name.endswith('.ui.arrow'):
                        algorithms.add(file.stem)
            
            # 从PR曲线目录发现
            pr_dir = exp_dir / "pr_curves"
            if pr_dir.exists():
                for file in pr_dir.glob("*.json.gz"):
                    algorithms.add(file.stem)
                for file in pr_dir.glob("*.arrow"):
                    if not file.name.endswith('.ui.arrow'):
                        algorithms.add(file.stem)
            
            for algorithm_key in algorithms:
                test_cases.append((experiment_id, algorithm_key))
        
        logger.info(f"发现 {len(test_cases)} 个测试用例")
        return test_cases
    
    async def run_all_tests(self, storage_root: str, max_cases: int = 5) -> None:
        """运行所有测试"""
        test_cases = self.discover_test_cases(storage_root)
        
        if not test_cases:
            logger.warning("没有发现测试用例")
            return
        
        # 限制测试用例数量
        test_cases = test_cases[:max_cases]
        logger.info(f"将测试 {len(test_cases)} 个用例")
        
        for i, (experiment_id, algorithm_key) in enumerate(test_cases, 1):
            logger.info(f"\n[{i}/{len(test_cases)}] 测试: {experiment_id}/{algorithm_key}")
            
            # 测试清单
            await self.test_manifest_endpoint(experiment_id, algorithm_key)
            
            # 测试轨迹
            await self.test_trajectory_endpoint(experiment_id, algorithm_key)
            
            # 测试PR曲线
            await self.test_pr_curve_endpoint(experiment_id, algorithm_key)
            
            # 性能对比
            await self.test_performance_comparison(experiment_id, algorithm_key)
            
            # 短暂延迟避免过载
            await asyncio.sleep(0.1)
    
    def print_summary(self) -> None:
        """打印测试摘要"""
        print("\n" + "="*60)
        print("优化验证摘要")
        print("="*60)
        
        # 清单测试
        manifest_success = sum(1 for t in self.results['manifest_tests'] if t['success'])
        print(f"清单测试: {manifest_success}/{len(self.results['manifest_tests'])} 通过")
        
        # 轨迹测试
        trajectory_success = sum(1 for t in self.results['trajectory_tests'] if t['success'])
        print(f"轨迹测试: {trajectory_success}/{len(self.results['trajectory_tests'])} 通过")
        
        # PR曲线测试
        pr_success = sum(1 for t in self.results['pr_curve_tests'] if t['success'])
        print(f"PR曲线测试: {pr_success}/{len(self.results['pr_curve_tests'])} 通过")
        
        # 性能统计
        if self.results['performance_tests']:
            avg_ui_time = sum(t['ui_time'] for t in self.results['performance_tests']) / len(self.results['performance_tests'])
            avg_full_time = sum(t['full_time'] for t in self.results['performance_tests'] if t['full_time'] > 0)
            if avg_full_time:
                avg_full_time /= len([t for t in self.results['performance_tests'] if t['full_time'] > 0])
                improvement = avg_full_time / avg_ui_time if avg_ui_time > 0 else 1
                print(f"平均响应时间: UI {avg_ui_time:.3f}s, Full {avg_full_time:.3f}s (提升 {improvement:.1f}x)")
        
        # 压缩统计
        compressed_count = sum(1 for t in self.results['trajectory_tests'] + self.results['pr_curve_tests'] if t.get('compressed'))
        total_requests = len(self.results['trajectory_tests']) + len(self.results['pr_curve_tests'])
        if total_requests > 0:
            print(f"HTTP压缩: {compressed_count}/{total_requests} 请求启用压缩")
        
        print("="*60)


async def main():
    parser = argparse.ArgumentParser(description="验证轨迹加载优化")
    parser.add_argument("--storage-root", required=True, help="存储根目录路径")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="API基础URL")
    parser.add_argument("--max-cases", type=int, default=5, help="最大测试用例数")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    storage_root = Path(args.storage_root)
    if not storage_root.exists():
        print(f"错误: 存储根目录不存在: {storage_root}")
        sys.exit(1)
    
    print(f"开始优化验证...")
    print(f"存储根目录: {storage_root}")
    print(f"API地址: {args.base_url}")
    print(f"最大测试用例: {args.max_cases}")
    
    try:
        async with OptimizationValidator(args.base_url) as validator:
            await validator.run_all_tests(str(storage_root), args.max_cases)
            validator.print_summary()
            
        print("\n验证完成！")
        
    except KeyboardInterrupt:
        print("\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
