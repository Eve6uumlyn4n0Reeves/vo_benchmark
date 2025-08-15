"""
完整工作流程集成测试

测试前后端集成的完整用户工作流程，确保所有新功能正常工作。
包括数据集管理、实验监控、算法对比和批量操作。

Author: VO-Benchmark Team
Version: 1.0.0
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
import requests
import json

from tests.conftest import TestClient, TestDatabase


class TestCompleteWorkflow:
    """完整工作流程测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.base_url = "http://localhost:5000/api/v1"
        self.client = TestClient()
        self.db = TestDatabase()
        
        # 清理测试数据
        self.db.clean_test_data()
        
        # 创建测试数据集
        self.test_datasets = self._create_test_datasets()
        
    def teardown_method(self):
        """测试后清理"""
        self.db.clean_test_data()
    
    def test_complete_user_workflow(self):
        """
        测试完整的用户工作流程
        
        工作流程：
        1. 浏览和选择数据集
        2. 批量创建对比实验
        3. 监控实验执行
        4. 分析和对比结果
        5. 导出报告
        """
        print("\n🚀 开始完整工作流程测试...")
        
        # 步骤1: 数据集管理
        datasets = self._test_dataset_management()
        assert len(datasets) > 0, "应该发现至少一个数据集"
        
        # 步骤2: 批量创建实验
        experiments = self._test_batch_experiment_creation(datasets[0])
        assert len(experiments) >= 2, "应该创建至少2个对比实验"
        
        # 步骤3: 实验监控
        self._test_experiment_monitoring(experiments)
        
        # 步骤4: 算法对比分析
        comparison_result = self._test_algorithm_comparison(experiments)
        assert comparison_result is not None, "应该生成对比分析结果"
        
        # 步骤5: 结果导出
        self._test_result_export(comparison_result)
        
        print("✅ 完整工作流程测试通过！")
    
    def _test_dataset_management(self) -> List[Dict[str, Any]]:
        """测试数据集管理功能"""
        print("📁 测试数据集管理...")
        
        # 获取数据集列表
        response = requests.get(f"{self.base_url}/datasets/")
        assert response.status_code == 200, f"获取数据集列表失败: {response.text}"
        
        data = response.json()
        datasets = data.get('datasets', [])
        
        print(f"   发现 {len(datasets)} 个数据集")
        
        # 验证数据集结构
        if datasets:
            dataset = datasets[0]
            required_fields = ['name', 'path', 'type', 'sequences', 'total_frames']
            for field in required_fields:
                assert field in dataset, f"数据集缺少必需字段: {field}"
            
            # 测试数据集验证
            validation_response = requests.post(
                f"{self.base_url}/datasets/validate",
                json={'path': dataset['path']}
            )
            assert validation_response.status_code == 200, "数据集验证失败"
            
            validation_result = validation_response.json()
            print(f"   数据集验证结果: {'有效' if validation_result['valid'] else '无效'}")
        
        return datasets
    
    def _test_batch_experiment_creation(self, dataset: Dict[str, Any]) -> List[str]:
        """测试批量实验创建"""
        print("🔬 测试批量实验创建...")
        
        # 准备批量创建配置
        batch_config = {
            'name_template': '算法对比_{algorithm}_{timestamp}',
            'base_config': {
                'dataset_path': dataset['path'],
                'output_dir': '/tmp/test_results',
                'max_features': 1000,
                'sequences': [dataset['sequences'][0]['name']] if dataset['sequences'] else ['test_seq']
            },
            'variations': [
                {'feature_types': ['SIFT']},
                {'feature_types': ['ORB']}
            ],
            'parallel_execution': False
        }
        
        # 执行批量创建
        response = requests.post(
            f"{self.base_url}/batch/experiments/create",
            json=batch_config
        )
        assert response.status_code == 200, f"批量创建实验失败: {response.text}"
        
        result = response.json()
        print(f"   批量创建结果: {result['success_count']}/{result['total_count']} 成功")
        
        # 提取实验ID
        experiment_ids = [
            r['target_id'] for r in result['results'] 
            if r['success']
        ]
        
        return experiment_ids
    
    def _test_experiment_monitoring(self, experiment_ids: List[str]):
        """测试实验监控功能"""
        print("📊 测试实验监控...")
        
        for exp_id in experiment_ids[:2]:  # 只测试前两个实验
            # 获取实验状态
            response = requests.get(f"{self.base_url}/monitoring/experiments/{exp_id}")
            
            if response.status_code == 200:
                status = response.json()
                print(f"   实验 {exp_id}: {status['status']} ({status['overall_progress']*100:.1f}%)")
                
                # 验证状态结构
                required_fields = ['experiment_id', 'status', 'overall_progress', 'tasks', 'system_metrics']
                for field in required_fields:
                    assert field in status, f"实验状态缺少字段: {field}"
                
                # 测试实验控制（如果实验正在运行）
                if status['status'] == 'running':
                    control_response = requests.post(
                        f"{self.base_url}/monitoring/experiments/{exp_id}/control",
                        json={'action': 'pause', 'reason': '测试暂停'}
                    )
                    if control_response.status_code == 200:
                        print(f"   成功暂停实验 {exp_id}")
            else:
                print(f"   实验 {exp_id} 状态获取失败: {response.status_code}")
        
        # 测试系统指标
        metrics_response = requests.get(f"{self.base_url}/monitoring/system")
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            print(f"   系统指标: CPU {metrics['cpu_usage']:.1f}%, 内存 {metrics['memory_usage']:.1f}%")
    
    def _test_algorithm_comparison(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """测试算法对比分析"""
        print("📈 测试算法对比分析...")
        
        # 准备对比请求
        comparison_request = {
            'experiment_ids': experiment_ids,
            'algorithm_names': ['SIFT_STANDARD', 'ORB_STANDARD'],
            'sort_by': 'trajectory_rmse',
            'sort_order': 'asc'
        }
        
        # 执行对比分析
        response = requests.post(
            f"{self.base_url}/comparison/analyze",
            json=comparison_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   对比分析完成，包含 {len(result['algorithms'])} 个算法")
            
            # 验证结果结构
            required_fields = ['algorithms', 'statistics', 'recommendations']
            for field in required_fields:
                assert field in result, f"对比结果缺少字段: {field}"
            
            # 显示最佳算法
            if result['statistics'].get('best_algorithm'):
                print(f"   最佳算法: {result['statistics']['best_algorithm']}")
            
            return result
        else:
            print(f"   对比分析失败: {response.status_code} - {response.text}")
            return None
    
    def _test_result_export(self, comparison_result: Dict[str, Any]):
        """测试结果导出功能"""
        print("📄 测试结果导出...")
        
        # 测试不同格式的导出
        export_formats = ['csv', 'json']
        
        for format_type in export_formats:
            export_request = {
                'format': format_type,
                'include_charts': False,
                'include_raw_data': True
            }
            
            response = requests.post(
                f"{self.base_url}/comparison/export",
                json=export_request
            )
            
            if response.status_code == 200:
                print(f"   {format_type.upper()} 导出成功")
                
                # 验证响应头
                content_type = response.headers.get('content-type', '')
                if format_type == 'csv':
                    assert 'text/csv' in content_type or 'application/octet-stream' in content_type
                elif format_type == 'json':
                    assert 'application/json' in content_type or 'application/octet-stream' in content_type
            else:
                print(f"   {format_type.upper()} 导出失败: {response.status_code}")
    
    def _create_test_datasets(self) -> List[Dict[str, Any]]:
        """创建测试数据集"""
        return [
            {
                'name': 'Test TUM Dataset',
                'path': '/tmp/test_tum',
                'type': 'TUM',
                'description': '测试用TUM数据集',
                'total_frames': 100,
                'sequences': [
                    {
                        'name': 'test_sequence',
                        'path': '/tmp/test_tum/test_sequence',
                        'frame_count': 100,
                        'duration': 10.0,
                        'ground_truth_available': True,
                        'format_valid': True
                    }
                ],
                'format_valid': True
            }
        ]
    
    def test_api_error_handling(self):
        """测试API错误处理"""
        print("\n🚨 测试API错误处理...")
        
        # 测试不存在的端点
        response = requests.get(f"{self.base_url}/nonexistent")
        assert response.status_code == 404
        
        # 测试无效的实验ID
        response = requests.get(f"{self.base_url}/monitoring/experiments/invalid_id")
        assert response.status_code == 404
        
        # 测试无效的请求数据
        response = requests.post(
            f"{self.base_url}/batch/experiments/create",
            json={'invalid': 'data'}
        )
        assert response.status_code == 400
        
        print("   API错误处理测试通过")
    
    def test_performance_benchmarks(self):
        """测试性能基准"""
        print("\n⚡ 测试性能基准...")
        
        # 测试API响应时间
        start_time = time.time()
        response = requests.get(f"{self.base_url}/datasets/")
        response_time = time.time() - start_time
        
        assert response_time < 2.0, f"数据集列表API响应时间过长: {response_time:.2f}s"
        print(f"   数据集列表API响应时间: {response_time:.3f}s")
        
        # 测试健康检查响应时间
        start_time = time.time()
        response = requests.get(f"{self.base_url}/health")
        health_response_time = time.time() - start_time
        
        assert health_response_time < 0.5, f"健康检查响应时间过长: {health_response_time:.2f}s"
        print(f"   健康检查响应时间: {health_response_time:.3f}s")
    
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        print("\n🔄 测试并发请求处理...")
        
        import concurrent.futures
        import threading
        
        def make_request():
            response = requests.get(f"{self.base_url}/health")
            return response.status_code == 200
        
        # 并发发送10个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        assert success_count >= 8, f"并发请求成功率过低: {success_count}/10"
        print(f"   并发请求成功率: {success_count}/10")


if __name__ == "__main__":
    # 运行集成测试
    test_workflow = TestCompleteWorkflow()
    test_workflow.setup_method()
    
    try:
        test_workflow.test_complete_user_workflow()
        test_workflow.test_api_error_handling()
        test_workflow.test_performance_benchmarks()
        test_workflow.test_concurrent_requests()
        
        print("\n🎉 所有集成测试通过！")
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        raise
    finally:
        test_workflow.teardown_method()
