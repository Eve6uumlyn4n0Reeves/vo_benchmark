#!/usr/bin/env python3
"""
后端设计问题修复脚本

此脚本自动修复已识别的后端设计问题，包括：
1. 移除硬编码值
2. 修复配置管理
3. 统一API路径
4. 清理假实现

使用方法:
    python scripts/fix_backend_issues.py --dry-run  # 预览更改
    python scripts/fix_backend_issues.py --apply    # 应用更改
"""

import os
import re
import sys
import json
import yaml
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FixResult:
    """修复结果"""
    file_path: str
    changes_made: List[str]
    success: bool
    error_message: str = ""

class BackendIssueFixer:
    """后端问题修复器"""
    
    def __init__(self, project_root: Path, dry_run: bool = True):
        self.project_root = project_root
        self.dry_run = dry_run
        self.results: List[FixResult] = []
        
        # 硬编码替换映射
        self.hardcode_replacements = {
            # Python文件中的硬编码
            r"'5000'": "os.environ.get('FLASK_PORT', '5000')",
            r'"5000"': "os.environ.get('FLASK_PORT', '5000')",
            r"'3000'": "os.environ.get('FRONTEND_PORT', '3000')",
            r'"3000"': "os.environ.get('FRONTEND_PORT', '3000')",
            r"'http://localhost:3000'": "os.environ.get('FRONTEND_URL', 'http://localhost:3000')",
            r'"http://localhost:3000"': "os.environ.get('FRONTEND_URL', 'http://localhost:3000')",
            r"'redis://localhost:6379/0'": "os.environ.get('REDIS_URL', 'redis://localhost:6379/0')",
            r'"redis://localhost:6379/0"': "os.environ.get('REDIS_URL', 'redis://localhost:6379/0')",
            r"'sqlite:///vo_benchmark.db'": "os.environ.get('DATABASE_URL', 'sqlite:///vo_benchmark.db')",
            r'"sqlite:///vo_benchmark.db"': "os.environ.get('DATABASE_URL', 'sqlite:///vo_benchmark.db')",
        }
        
        # TypeScript/JavaScript文件中的硬编码
        self.js_hardcode_replacements = {
            r"'5000'": "import.meta.env.VITE_BACKEND_PORT || '5000'",
            r'"5000"': "import.meta.env.VITE_BACKEND_PORT || '5000'",
            r"'3000'": "import.meta.env.VITE_FRONTEND_PORT || '3000'",
            r'"3000"': "import.meta.env.VITE_FRONTEND_PORT || '3000'",
        }
    
    def fix_all_issues(self) -> List[FixResult]:
        """修复所有已识别的问题"""
        logger.info(f"开始修复后端设计问题 (dry_run={self.dry_run})")
        
        # 1. 修复服务器启动问题
        self._fix_server_startup()
        
        # 2. 修复硬编码问题
        self._fix_hardcoded_values()
        
        # 3. 修复CORS配置
        self._fix_cors_configuration()
        
        # 4. 统一API路径
        self._fix_api_paths()
        
        # 5. 创建配置文件
        self._create_config_files()
        
        # 6. 移除假实现
        self._remove_fake_implementations()
        
        return self.results
    
    def _fix_server_startup(self):
        """修复服务器启动问题"""
        logger.info("修复服务器启动问题...")
        
        start_server_path = self.project_root / "backend" / "start_server.py"
        if not start_server_path.exists():
            return
        
        try:
            content = start_server_path.read_text(encoding='utf-8')
            
            # 移除工作目录切换代码
            old_pattern = r'# 关键修复：切换到src目录.*?os\.chdir\(src_dir\)\s*logger\.info\(f"工作目录已切换到: \{os\.getcwd\(\)\}"\)'
            new_code = '# 直接导入，无需切换工作目录'
            
            if re.search(old_pattern, content, re.DOTALL):
                content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)
                
                # 移除环境变量硬编码设置
                env_pattern = r"os\.environ\.setdefault\('FLASK_PORT', '5000'\)"
                content = re.sub(env_pattern, "os.environ.setdefault('FLASK_PORT', os.environ.get('FLASK_PORT', '5000'))", content)
                
                if not self.dry_run:
                    start_server_path.write_text(content, encoding='utf-8')
                
                self.results.append(FixResult(
                    file_path=str(start_server_path),
                    changes_made=["移除工作目录切换", "修复环境变量硬编码"],
                    success=True
                ))
            
        except Exception as e:
            self.results.append(FixResult(
                file_path=str(start_server_path),
                changes_made=[],
                success=False,
                error_message=str(e)
            ))
    
    def _fix_hardcoded_values(self):
        """修复硬编码值"""
        logger.info("修复硬编码值...")
        
        # Python文件
        python_files = [
            "backend/src/api/app.py",
            "backend/src/api/config.py",
            "backend/src/main.py",
            "backend/start_server.py"
        ]
        
        for file_path in python_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self._fix_hardcoded_in_file(full_path, self.hardcode_replacements, "Python")
        
        # TypeScript/JavaScript文件
        js_files = [
            "frontend/src/utils/constants.ts",
            "frontend/src/api/client.ts",
            "frontend/vite.config.ts"
        ]
        
        for file_path in js_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self._fix_hardcoded_in_file(full_path, self.js_hardcode_replacements, "TypeScript")
    
    def _fix_hardcoded_in_file(self, file_path: Path, replacements: Dict[str, str], file_type: str):
        """在单个文件中修复硬编码值"""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            changes_made = []
            
            for pattern, replacement in replacements.items():
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    changes_made.append(f"替换 {pattern} -> {replacement}")
            
            if changes_made and not self.dry_run:
                file_path.write_text(content, encoding='utf-8')
            
            if changes_made:
                self.results.append(FixResult(
                    file_path=str(file_path),
                    changes_made=changes_made,
                    success=True
                ))
                
        except Exception as e:
            self.results.append(FixResult(
                file_path=str(file_path),
                changes_made=[],
                success=False,
                error_message=str(e)
            ))
    
    def _fix_cors_configuration(self):
        """修复CORS配置"""
        logger.info("修复CORS配置...")
        
        app_py_path = self.project_root / "backend" / "src" / "api" / "app.py"
        if not app_py_path.exists():
            return
        
        try:
            content = app_py_path.read_text(encoding='utf-8')
            
            # 替换硬编码的CORS配置
            old_cors = r"'origins': app\.config\.get\('CORS_ORIGINS', \['http://localhost:3000'\]\)"
            new_cors = """'origins': self._get_cors_origins(app)"""
            
            if re.search(old_cors, content):
                content = re.sub(old_cors, new_cors, content)
                
                # 添加动态CORS配置方法
                cors_method = '''
    def _get_cors_origins(self, app: Flask) -> List[str]:
        """获取CORS允许的源"""
        origins = app.config.get('CORS_ORIGINS', [])
        
        # 开发环境自动添加本地地址
        if app.config.get('FLASK_ENV') == 'development':
            dev_origins = [
                'http://localhost:3000',
                'http://127.0.0.1:3000',
                'http://localhost:5173'
            ]
            origins.extend([origin for origin in dev_origins if origin not in origins])
        
        return origins
'''
                
                # 在setup_cors函数前添加方法
                setup_cors_pattern = r'(def setup_cors\(app: Flask\) -> None:)'
                content = re.sub(setup_cors_pattern, cors_method + r'\n\1', content)
                
                if not self.dry_run:
                    app_py_path.write_text(content, encoding='utf-8')
                
                self.results.append(FixResult(
                    file_path=str(app_py_path),
                    changes_made=["修复CORS配置", "添加动态CORS源配置"],
                    success=True
                ))
                
        except Exception as e:
            self.results.append(FixResult(
                file_path=str(app_py_path),
                changes_made=[],
                success=False,
                error_message=str(e)
            ))
    
    def _fix_api_paths(self):
        """统一API路径"""
        logger.info("统一API路径...")
        
        app_py_path = self.project_root / "backend" / "src" / "api" / "app.py"
        if not app_py_path.exists():
            return
        
        try:
            content = app_py_path.read_text(encoding='utf-8')
            
            # 注释掉legacy API注册
            legacy_pattern = r'(# Register legacy blueprints.*?app\.logger\.info\("Legacy API blueprints registered at /api/v1/legacy/"\))'
            replacement = '# Legacy API blueprints disabled - use documented API only\n    # ' + r'\1'
            
            if re.search(legacy_pattern, content, re.DOTALL):
                content = re.sub(legacy_pattern, replacement, content, flags=re.DOTALL)
                
                if not self.dry_run:
                    app_py_path.write_text(content, encoding='utf-8')
                
                self.results.append(FixResult(
                    file_path=str(app_py_path),
                    changes_made=["禁用legacy API路径", "统一使用documented API"],
                    success=True
                ))
                
        except Exception as e:
            self.results.append(FixResult(
                file_path=str(app_py_path),
                changes_made=[],
                success=False,
                error_message=str(e)
            ))
    
    def _create_config_files(self):
        """创建配置文件"""
        logger.info("创建配置文件...")
        
        config_dir = self.project_root / "backend" / "config"
        config_dir.mkdir(exist_ok=True)
        
        # 开发环境配置
        dev_config = {
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': True
            },
            'database': {
                'url': 'sqlite:///vo_benchmark_dev.db'
            },
            'redis': {
                'url': 'redis://localhost:6379/0'
            },
            'cors': {
                'origins': [
                    'http://localhost:3000',
                    'http://127.0.0.1:3000',
                    'http://localhost:5173'
                ]
            },
            'logging': {
                'level': 'DEBUG',
                'requests': True
            }
        }
        
        # 生产环境配置
        prod_config = {
            'server': {
                'host': '0.0.0.0',
                'port': '${FLASK_PORT}',
                'debug': False
            },
            'database': {
                'url': '${DATABASE_URL}'
            },
            'redis': {
                'url': '${REDIS_URL}'
            },
            'cors': {
                'origins': '${CORS_ORIGINS}'.split(',')
            },
            'logging': {
                'level': 'INFO',
                'requests': False
            }
        }
        
        configs = [
            ('development.yaml', dev_config),
            ('production.yaml', prod_config)
        ]
        
        for filename, config in configs:
            config_path = config_dir / filename
            if not self.dry_run:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            self.results.append(FixResult(
                file_path=str(config_path),
                changes_made=[f"创建{filename}配置文件"],
                success=True
            ))
    
    def _remove_fake_implementations(self):
        """移除假实现"""
        logger.info("移除假实现...")
        
        factory_path = self.project_root / "backend" / "src" / "algorithms" / "factory.py"
        if not factory_path.exists():
            return
        
        try:
            content = factory_path.read_text(encoding='utf-8')
            
            # 移除合成数据生成代码
            fake_pattern = r'# If no test data provided, generate synthetic benchmark results.*?inlier_ratios = \[i/m if m > 0 else 0 for i, m in zip\(inlier_counts, match_counts\)\]'
            replacement = '''# If no test data provided, raise an error instead of generating fake data
                raise ValueError(f"No test data provided for {algorithm_name}. Please provide valid test data.")'''
            
            if re.search(fake_pattern, content, re.DOTALL):
                content = re.sub(fake_pattern, replacement, content, flags=re.DOTALL)
                
                if not self.dry_run:
                    factory_path.write_text(content, encoding='utf-8')
                
                self.results.append(FixResult(
                    file_path=str(factory_path),
                    changes_made=["移除合成数据生成", "添加数据验证"],
                    success=True
                ))
                
        except Exception as e:
            self.results.append(FixResult(
                file_path=str(factory_path),
                changes_made=[],
                success=False,
                error_message=str(e)
            ))
    
    def print_summary(self):
        """打印修复摘要"""
        total_files = len(self.results)
        successful_fixes = len([r for r in self.results if r.success])
        failed_fixes = total_files - successful_fixes
        
        print(f"\n{'='*60}")
        print(f"修复摘要 (dry_run={self.dry_run})")
        print(f"{'='*60}")
        print(f"总文件数: {total_files}")
        print(f"成功修复: {successful_fixes}")
        print(f"修复失败: {failed_fixes}")
        print(f"{'='*60}")
        
        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.file_path}")
            for change in result.changes_made:
                print(f"   - {change}")
            if not result.success:
                print(f"   错误: {result.error_message}")
        
        print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(description='修复后端设计问题')
    parser.add_argument('--dry-run', action='store_true', help='预览更改，不实际修改文件')
    parser.add_argument('--apply', action='store_true', help='应用更改')
    parser.add_argument('--project-root', type=str, default='.', help='项目根目录')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("请指定 --dry-run 或 --apply 参数")
        sys.exit(1)
    
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"项目根目录不存在: {project_root}")
        sys.exit(1)
    
    fixer = BackendIssueFixer(project_root, dry_run=args.dry_run)
    results = fixer.fix_all_issues()
    fixer.print_summary()
    
    if args.dry_run:
        print("\n使用 --apply 参数来实际应用这些更改")

if __name__ == '__main__':
    main()
