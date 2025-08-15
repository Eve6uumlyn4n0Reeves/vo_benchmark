#!/usr/bin/env python3
"""
配置验证脚本

验证后端配置的完整性和一致性，包括：
1. 环境变量配置
2. 配置文件格式
3. 前后端配置一致性
4. 生产环境安全检查

使用方法:
    python scripts/validate_configuration.py --env development
    python scripts/validate_configuration.py --env production --strict
"""

import os
import sys
import yaml
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """验证结果"""
    category: str
    item: str
    status: str  # 'pass', 'warning', 'error'
    message: str
    suggestion: Optional[str] = None

class ConfigurationValidator:
    """配置验证器"""
    
    def __init__(self, project_root: Path, environment: str = 'development', strict: bool = False):
        self.project_root = project_root
        self.environment = environment
        self.strict = strict
        self.results: List[ValidationResult] = []
        
        # 必需的环境变量
        self.required_env_vars = {
            'development': [
                'FLASK_ENV',
                'SECRET_KEY'
            ],
            'production': [
                'FLASK_ENV',
                'SECRET_KEY',
                'DATABASE_URL',
                'CORS_ORIGINS',
                'REDIS_URL'
            ]
        }
        
        # 推荐的环境变量
        self.recommended_env_vars = [
            'FLASK_HOST',
            'FLASK_PORT',
            'LOG_LEVEL',
            'MAX_CONCURRENT_TASKS'
        ]
        
        # 安全敏感的配置项
        self.sensitive_configs = [
            'SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL',
            'JWT_SECRET_KEY'
        ]
    
    def validate_all(self) -> List[ValidationResult]:
        """执行所有验证"""
        logger.info(f"开始验证 {self.environment} 环境配置...")
        
        # 1. 验证环境变量
        self._validate_environment_variables()
        
        # 2. 验证配置文件
        self._validate_config_files()
        
        # 3. 验证前后端配置一致性
        self._validate_frontend_backend_consistency()
        
        # 4. 验证安全配置
        self._validate_security_configuration()
        
        # 5. 验证网络配置
        self._validate_network_configuration()
        
        # 6. 验证数据库配置
        self._validate_database_configuration()
        
        return self.results
    
    def _validate_environment_variables(self):
        """验证环境变量"""
        logger.info("验证环境变量...")
        
        required_vars = self.required_env_vars.get(self.environment, [])
        
        # 检查必需的环境变量
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                self.results.append(ValidationResult(
                    category="环境变量",
                    item=var,
                    status="error",
                    message=f"缺少必需的环境变量: {var}",
                    suggestion=f"请在 .env 文件中设置 {var}=<value>"
                ))
            elif var in self.sensitive_configs and value in ['your-secret-key-change-in-production', 'change-me']:
                self.results.append(ValidationResult(
                    category="环境变量",
                    item=var,
                    status="error",
                    message=f"使用了默认的不安全值: {var}",
                    suggestion=f"请为 {var} 设置安全的随机值"
                ))
            else:
                self.results.append(ValidationResult(
                    category="环境变量",
                    item=var,
                    status="pass",
                    message=f"环境变量 {var} 已正确设置"
                ))
        
        # 检查推荐的环境变量
        for var in self.recommended_env_vars:
            value = os.environ.get(var)
            if not value:
                self.results.append(ValidationResult(
                    category="环境变量",
                    item=var,
                    status="warning",
                    message=f"推荐设置环境变量: {var}",
                    suggestion=f"考虑在 .env 文件中设置 {var} 以获得更好的配置控制"
                ))
    
    def _validate_config_files(self):
        """验证配置文件"""
        logger.info("验证配置文件...")
        
        config_dir = self.project_root / "backend" / "config"
        config_file = config_dir / f"{self.environment}.yaml"
        
        if not config_file.exists():
            self.results.append(ValidationResult(
                category="配置文件",
                item=str(config_file),
                status="warning",
                message=f"配置文件不存在: {config_file}",
                suggestion="运行 python scripts/fix_backend_issues.py --apply 创建配置文件"
            ))
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                self.results.append(ValidationResult(
                    category="配置文件",
                    item=str(config_file),
                    status="error",
                    message="配置文件为空",
                    suggestion="请添加必要的配置项"
                ))
                return
            
            # 验证配置结构
            required_sections = ['server', 'database', 'cors']
            for section in required_sections:
                if section not in config:
                    self.results.append(ValidationResult(
                        category="配置文件",
                        item=f"{config_file}:{section}",
                        status="error",
                        message=f"缺少配置节: {section}",
                        suggestion=f"请在配置文件中添加 {section} 节"
                    ))
                else:
                    self.results.append(ValidationResult(
                        category="配置文件",
                        item=f"{config_file}:{section}",
                        status="pass",
                        message=f"配置节 {section} 存在"
                    ))
            
            # 验证服务器配置
            if 'server' in config:
                server_config = config['server']
                if 'port' in server_config:
                    port = server_config['port']
                    if not isinstance(port, int) or port < 1024 or port > 65535:
                        self.results.append(ValidationResult(
                            category="配置文件",
                            item="server.port",
                            status="error",
                            message=f"无效的端口号: {port}",
                            suggestion="端口号应该是 1024-65535 之间的整数"
                        ))
            
        except yaml.YAMLError as e:
            self.results.append(ValidationResult(
                category="配置文件",
                item=str(config_file),
                status="error",
                message=f"YAML 格式错误: {e}",
                suggestion="请检查 YAML 文件格式"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                category="配置文件",
                item=str(config_file),
                status="error",
                message=f"读取配置文件失败: {e}",
                suggestion="请检查文件权限和格式"
            ))
    
    def _validate_frontend_backend_consistency(self):
        """验证前后端配置一致性"""
        logger.info("验证前后端配置一致性...")
        
        # 检查端口配置
        backend_port = os.environ.get('FLASK_PORT', '5000')
        frontend_env_file = self.project_root / "frontend" / ".env.example"
        
        if frontend_env_file.exists():
            try:
                with open(frontend_env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找前端配置的后端端口
                import re
                port_match = re.search(r'VITE_BACKEND_PORT=(\d+)', content)
                if port_match:
                    frontend_backend_port = port_match.group(1)
                    if backend_port != frontend_backend_port:
                        self.results.append(ValidationResult(
                            category="前后端一致性",
                            item="端口配置",
                            status="warning",
                            message=f"前后端端口配置不一致: 后端={backend_port}, 前端配置={frontend_backend_port}",
                            suggestion="请确保前后端使用相同的端口配置"
                        ))
                    else:
                        self.results.append(ValidationResult(
                            category="前后端一致性",
                            item="端口配置",
                            status="pass",
                            message="前后端端口配置一致"
                        ))
                
            except Exception as e:
                self.results.append(ValidationResult(
                    category="前后端一致性",
                    item="前端配置文件",
                    status="warning",
                    message=f"无法读取前端配置文件: {e}",
                    suggestion="请检查前端 .env.example 文件"
                ))
    
    def _validate_security_configuration(self):
        """验证安全配置"""
        logger.info("验证安全配置...")
        
        # 检查 SECRET_KEY
        secret_key = os.environ.get('SECRET_KEY')
        if secret_key:
            if len(secret_key) < 32:
                self.results.append(ValidationResult(
                    category="安全配置",
                    item="SECRET_KEY",
                    status="warning",
                    message="SECRET_KEY 长度过短",
                    suggestion="建议使用至少32字符的随机字符串"
                ))
            elif secret_key in ['your-secret-key-change-in-production', 'change-me', 'test-secret']:
                self.results.append(ValidationResult(
                    category="安全配置",
                    item="SECRET_KEY",
                    status="error",
                    message="使用了不安全的默认 SECRET_KEY",
                    suggestion="请生成安全的随机密钥: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                ))
            else:
                self.results.append(ValidationResult(
                    category="安全配置",
                    item="SECRET_KEY",
                    status="pass",
                    message="SECRET_KEY 配置正确"
                ))
        
        # 检查生产环境安全设置
        if self.environment == 'production':
            debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower()
            if debug_mode == 'true':
                self.results.append(ValidationResult(
                    category="安全配置",
                    item="FLASK_DEBUG",
                    status="error",
                    message="生产环境不应启用调试模式",
                    suggestion="请设置 FLASK_DEBUG=false"
                ))
    
    def _validate_network_configuration(self):
        """验证网络配置"""
        logger.info("验证网络配置...")
        
        # 检查 CORS 配置
        cors_origins = os.environ.get('CORS_ORIGINS', '')
        if cors_origins:
            origins = [origin.strip() for origin in cors_origins.split(',')]
            for origin in origins:
                if origin:
                    try:
                        parsed = urlparse(origin)
                        if not parsed.scheme or not parsed.netloc:
                            self.results.append(ValidationResult(
                                category="网络配置",
                                item="CORS_ORIGINS",
                                status="error",
                                message=f"无效的 CORS 源: {origin}",
                                suggestion="请使用完整的 URL 格式，如 http://localhost:3000"
                            ))
                    except Exception:
                        self.results.append(ValidationResult(
                            category="网络配置",
                            item="CORS_ORIGINS",
                            status="error",
                            message=f"无法解析 CORS 源: {origin}",
                            suggestion="请检查 URL 格式"
                        ))
        
        # 检查生产环境 CORS 配置
        if self.environment == 'production' and not cors_origins:
            self.results.append(ValidationResult(
                category="网络配置",
                item="CORS_ORIGINS",
                status="error",
                message="生产环境必须设置 CORS_ORIGINS",
                suggestion="请设置允许的前端域名"
            ))
    
    def _validate_database_configuration(self):
        """验证数据库配置"""
        logger.info("验证数据库配置...")
        
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            try:
                parsed = urlparse(database_url)
                
                # 检查数据库类型
                if parsed.scheme not in ['sqlite', 'postgresql', 'mysql']:
                    self.results.append(ValidationResult(
                        category="数据库配置",
                        item="DATABASE_URL",
                        status="warning",
                        message=f"不支持的数据库类型: {parsed.scheme}",
                        suggestion="建议使用 sqlite、postgresql 或 mysql"
                    ))
                
                # 生产环境不应使用 SQLite
                if self.environment == 'production' and parsed.scheme == 'sqlite':
                    self.results.append(ValidationResult(
                        category="数据库配置",
                        item="DATABASE_URL",
                        status="warning",
                        message="生产环境不建议使用 SQLite",
                        suggestion="考虑使用 PostgreSQL 或 MySQL"
                    ))
                
                self.results.append(ValidationResult(
                    category="数据库配置",
                    item="DATABASE_URL",
                    status="pass",
                    message="数据库 URL 格式正确"
                ))
                
            except Exception as e:
                self.results.append(ValidationResult(
                    category="数据库配置",
                    item="DATABASE_URL",
                    status="error",
                    message=f"无效的数据库 URL: {e}",
                    suggestion="请检查数据库 URL 格式"
                ))
    
    def print_summary(self):
        """打印验证摘要"""
        total_checks = len(self.results)
        passed = len([r for r in self.results if r.status == 'pass'])
        warnings = len([r for r in self.results if r.status == 'warning'])
        errors = len([r for r in self.results if r.status == 'error'])
        
        print(f"\n{'='*80}")
        print(f"配置验证报告 - {self.environment.upper()} 环境")
        print(f"{'='*80}")
        print(f"总检查项: {total_checks}")
        print(f"✅ 通过: {passed}")
        print(f"⚠️  警告: {warnings}")
        print(f"❌ 错误: {errors}")
        print(f"{'='*80}")
        
        # 按类别分组显示结果
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        for category, results in categories.items():
            print(f"\n📋 {category}")
            print("-" * 40)
            for result in results:
                status_icon = {"pass": "✅", "warning": "⚠️", "error": "❌"}[result.status]
                print(f"{status_icon} {result.item}: {result.message}")
                if result.suggestion:
                    print(f"   💡 建议: {result.suggestion}")
        
        print(f"\n{'='*80}")
        
        # 返回退出码
        return 0 if errors == 0 else 1

def main():
    parser = argparse.ArgumentParser(description='验证后端配置')
    parser.add_argument('--env', choices=['development', 'production', 'testing'], 
                       default='development', help='环境名称')
    parser.add_argument('--strict', action='store_true', help='严格模式，警告也视为错误')
    parser.add_argument('--project-root', type=str, default='.', help='项目根目录')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"项目根目录不存在: {project_root}")
        sys.exit(1)
    
    validator = ConfigurationValidator(project_root, args.env, args.strict)
    results = validator.validate_all()
    exit_code = validator.print_summary()
    
    # 严格模式下，警告也导致失败
    if args.strict:
        warnings = len([r for r in results if r.status == 'warning'])
        if warnings > 0:
            exit_code = 1
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
