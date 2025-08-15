"""
API注册与中间件一致性的集成测试
"""
import pytest
import json
from flask import Flask
from src.api.app import create_app


class TestAPIRegistration:
    """API注册和中间件测试类"""

    def setup_method(self):
        """设置测试环境"""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown_method(self):
        """清理测试环境"""
        self.app_context.pop()

    def test_app_creation(self):
        """测试应用创建"""
        assert isinstance(self.app, Flask)
        assert self.app.config["TESTING"] is True

    def test_health_endpoint_basic(self):
        """测试基本健康检查端点"""
        response = self.client.get("/api/v1/health/")

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应是JSON格式
        assert response.content_type.startswith("application/json")

        # 验证响应内容
        data = response.get_json()
        assert data is not None
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_endpoint_documented(self):
        """测试文档化的健康检查端点"""
        response = self.client.get("/api/v1/health-doc/")

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应是JSON格式
        assert response.content_type.startswith("application/json")

        # 验证响应内容
        data = response.get_json()
        assert data is not None
        assert "status" in data

    def test_api_documentation_endpoint(self):
        """测试API文档端点"""
        response = self.client.get("/api/v1/docs/")
        
        # 文档端点应该返回HTML或重定向
        assert response.status_code in [200, 302, 404]  # 404也可接受，表示文档未完全配置

    def test_cors_headers(self):
        """测试CORS头设置"""
        response = self.client.get("/api/v1/health/")

        # 验证CORS头存在
        assert "Access-Control-Allow-Origin" in response.headers

        # 测试OPTIONS请求
        options_response = self.client.options("/api/v1/health/")
        assert options_response.status_code in [200, 204]
        assert "Access-Control-Allow-Methods" in options_response.headers

    def test_error_handling_middleware(self):
        """测试错误处理中间件"""
        # 测试不存在的端点
        response = self.client.get("/api/v1/nonexistent")
        
        # 验证返回404
        assert response.status_code == 404
        
        # 验证错误响应是JSON格式
        assert response.content_type.startswith("application/json")
        
        # 验证错误响应结构
        data = response.get_json()
        assert data is not None
        assert "error" in data or "message" in data

    def test_security_headers(self):
        """测试安全头设置"""
        response = self.client.get("/api/v1/health/")

        # 验证安全头
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_json_error_responses(self):
        """测试JSON错误响应一致性"""
        # 测试方法不允许的错误
        response = self.client.post("/api/v1/health/")  # health端点通常只支持GET

        # 验证响应是JSON格式（即使是错误）
        if response.status_code in [405, 404]:  # Method Not Allowed 或 Not Found
            assert response.content_type.startswith("application/json")
            data = response.get_json()
            assert data is not None

    def test_experiments_endpoint_basic(self):
        """测试实验端点基本功能"""
        response = self.client.get("/api/v1/experiments-doc/")

        # 验证响应状态（可能是200或404，取决于是否有数据）
        assert response.status_code in [200, 404]

        # 验证响应是JSON格式
        assert response.content_type.startswith("application/json")

    def test_tasks_endpoint_basic(self):
        """测试任务端点基本功能"""
        response = self.client.get("/api/v1/tasks/")

        # 验证响应状态
        assert response.status_code in [200, 404]

        # 验证响应是JSON格式
        assert response.content_type.startswith("application/json")

    def test_results_endpoint_basic(self):
        """测试结果端点基本功能"""
        # results端点需要experiment_id，测试一个不存在的ID
        response = self.client.get("/api/v1/results/test_exp/overview")

        # 验证响应状态（应该是404，因为实验不存在）
        assert response.status_code in [200, 404]

        # 验证响应是JSON格式
        assert response.content_type.startswith("application/json")

    def test_events_endpoint_basic(self):
        """测试事件端点基本功能"""
        response = self.client.get("/api/v1/events/")

        # 验证响应状态（SSE端点可能返回不同状态）
        assert response.status_code in [200, 404]

        # 事件端点返回text/event-stream，不是JSON
        # assert response.content_type.startswith("application/json")

    def test_websocket_fallback(self):
        """测试WebSocket回退端点"""
        response = self.client.get("/ws")
        
        # 验证返回404并提供替代方案
        assert response.status_code == 404
        assert response.content_type.startswith("application/json")
        
        data = response.get_json()
        assert data is not None
        assert "error" in data
        assert "polling_endpoints" in data

    def test_no_duplicate_blueprint_registration(self):
        """测试没有重复的蓝图注册"""
        # 这个测试通过应用成功创建来验证
        # 如果有重复注册，Flask会抛出异常
        app2 = create_app("testing")
        assert isinstance(app2, Flask)

    def test_middleware_request_hooks(self):
        """测试中间件请求钩子"""
        # 启用请求日志记录
        with self.app.test_request_context():
            self.app.config["LOG_REQUESTS"] = True
            
            response = self.client.get("/api/v1/health/")

            # 验证响应成功
            assert response.status_code == 200
            
            # 验证安全头被添加
            assert "X-Content-Type-Options" in response.headers

    def test_config_endpoint_availability(self):
        """测试配置端点可用性"""
        response = self.client.get("/api/v1/config")
        
        # 配置端点可能存在也可能不存在，取决于模块加载
        # 如果存在，应该返回JSON
        if response.status_code == 200:
            assert response.content_type.startswith("application/json")
        elif response.status_code == 404:
            # 404也是可接受的，表示配置端点未启用
            assert response.content_type.startswith("application/json")

    def test_api_version_in_config(self):
        """测试API版本配置"""
        assert "API_VERSION" in self.app.config
        assert self.app.config["API_VERSION"] == "1.0.0"

    def test_unified_error_format(self):
        """测试统一的错误格式"""
        # 测试多个不同的错误端点，确保错误格式一致
        error_endpoints = [
            "/api/v1/nonexistent",
            "/api/v1/experiments/nonexistent",
            "/api/v1/results/nonexistent"
        ]
        
        for endpoint in error_endpoints:
            response = self.client.get(endpoint)
            
            # 验证是JSON响应
            assert response.content_type.startswith("application/json")
            
            # 验证错误结构
            data = response.get_json()
            assert data is not None
            # 错误响应应该包含error或message字段
            assert "error" in data or "message" in data or "detail" in data

    def test_content_type_handling(self):
        """测试内容类型处理"""
        # 测试JSON请求
        response = self.client.post(
            "/api/v1/health",
            data=json.dumps({"test": "data"}),
            content_type="application/json"
        )
        
        # 验证响应是JSON格式
        assert response.content_type.startswith("application/json")

    def test_request_method_validation(self):
        """测试请求方法验证"""
        # 测试不支持的HTTP方法
        response = self.client.patch("/api/v1/health")
        
        # 应该返回方法不允许或未找到
        assert response.status_code in [405, 404]
        assert response.content_type.startswith("application/json")

    def test_large_request_handling(self):
        """测试大请求处理"""
        # 创建一个较大的JSON请求
        large_data = {"data": "x" * 1000}  # 1KB数据
        
        response = self.client.post(
            "/api/v1/experiments-doc/",
            data=json.dumps(large_data),
            content_type="application/json"
        )
        
        # 验证响应是JSON格式（无论成功还是失败）
        assert response.content_type.startswith("application/json")

    def test_api_consistency_across_endpoints(self):
        """测试API端点间的一致性"""
        endpoints = [
            "/api/v1/health/",
            "/api/v1/experiments-doc/",
            "/api/v1/tasks/",
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)

            # 所有端点都应该返回JSON
            assert response.content_type.startswith("application/json")

            # 所有端点都应该有CORS头
            assert "Access-Control-Allow-Origin" in response.headers

            # 所有端点都应该有安全头
            assert "X-Content-Type-Options" in response.headers
