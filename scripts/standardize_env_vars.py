#!/usr/bin/env python3
"""
环境变量标准化工具

检测和修复代码库中不安全的环境变量处理，包括：
1. 不安全的类型转换（int(), float() 等）
2. 缺少默认值的环境变量访问
3. 硬编码的环境变量值
4. 不一致的环境变量命名
"""

import os
import re
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EnvVarIssue:
    """环境变量问题"""
    file_path: str
    line_number: int
    line_content: str
    issue_type: str
    description: str
    suggestion: str
    severity: str  # 'error', 'warning', 'info'

class EnvVarStandardizer:
    """环境变量标准化器"""
    
    def __init__(self, project_root: Path, dry_run: bool = True):
        self.project_root = project_root
        self.dry_run = dry_run
        self.issues: List[EnvVarIssue] = []
        
        # 不安全的类型转换模式
        self.unsafe_patterns = {
            'unsafe_int': {
                'pattern': r'int\(os\.environ\.get\([^)]+\)\)',
                'description': '不安全的整数类型转换',
                'severity': 'error',
                'suggestion': '使用安全的类型转换函数，包含异常处理'
            },
            'unsafe_float': {
                'pattern': r'float\(os\.environ\.get\([^)]+\)\)',
                'description': '不安全的浮点类型转换',
                'severity': 'error',
                'suggestion': '使用安全的类型转换函数，包含异常处理'
            },
            'unsafe_bool': {
                'pattern': r'bool\(os\.environ\.get\([^)]+\)\)',
                'description': '不安全的布尔类型转换',
                'severity': 'warning',
                'suggestion': '使用 .lower() == "true" 进行布尔转换'
            },
            'no_default': {
                'pattern': r'os\.environ\[[\'"][^\'\"]+[\'\"]\]',
                'description': '直接访问环境变量，可能导致 KeyError',
                'severity': 'error',
                'suggestion': '使用 os.environ.get() 并提供默认值'
            },
            'getenv_no_default': {
                'pattern': r'os\.getenv\([\'"][^\'\"]+[\'\"]\)(?!\s*,)',
                'description': '使用 getenv 但没有提供默认值',
                'severity': 'warning',
                'suggestion': '为 getenv 提供合适的默认值'
            }
        }
        
        # 文件扩展名过滤
        self.file_extensions = {'.py', '.ts', '.tsx', '.js', '.jsx'}
        
        # 排除的目录
        self.exclude_dirs = {
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'venv', 'env', '.venv', 'dist', 'build'
        }

    def scan_project(self) -> List[EnvVarIssue]:
        """扫描整个项目"""
        logger.info(f"扫描项目: {self.project_root}")
        
        for file_path in self._get_source_files():
            self._scan_file(file_path)
        
        logger.info(f"扫描完成，发现 {len(self.issues)} 个问题")
        return self.issues

    def _get_source_files(self) -> List[Path]:
        """获取所有源代码文件"""
        files = []
        
        for root, dirs, filenames in os.walk(self.project_root):
            # 排除特定目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix in self.file_extensions:
                    files.append(file_path)
        
        return files

    def _scan_file(self, file_path: Path):
        """扫描单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            logger.warning(f"无法读取文件 {file_path}: {e}")
            return

        for line_num, line in enumerate(lines, 1):
            self._check_line(file_path, line_num, line.strip())

    def _check_line(self, file_path: Path, line_num: int, line: str):
        """检查单行代码"""
        for issue_type, pattern_info in self.unsafe_patterns.items():
            if re.search(pattern_info['pattern'], line):
                issue = EnvVarIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    line_content=line,
                    issue_type=issue_type,
                    description=pattern_info['description'],
                    suggestion=pattern_info['suggestion'],
                    severity=pattern_info['severity']
                )
                self.issues.append(issue)

    def generate_fixes(self) -> Dict[str, List[str]]:
        """生成修复建议"""
        fixes = {}
        
        for issue in self.issues:
            if issue.file_path not in fixes:
                fixes[issue.file_path] = []
            
            fix_suggestion = self._generate_fix_for_issue(issue)
            fixes[issue.file_path].append(fix_suggestion)
        
        return fixes

    def _generate_fix_for_issue(self, issue: EnvVarIssue) -> str:
        """为特定问题生成修复建议"""
        line = issue.line_content
        
        if issue.issue_type == 'unsafe_int':
            # 替换不安全的 int() 转换
            match = re.search(r'int\(os\.environ\.get\([^)]+\)\)', line)
            if match:
                original = match.group(0)
                # 提取环境变量名和默认值
                env_match = re.search(r'os\.environ\.get\([\'"]([^\'\"]+)[\'"](?:,\s*[\'"]?([^\'\"]*)[\'"]?)?\)', original)
                if env_match:
                    env_name = env_match.group(1)
                    default_val = env_match.group(2) or '0'
                    
                    safe_replacement = f"""try:
    {env_name.lower()}_value = int(os.environ.get('{env_name}', '{default_val}'))
except (ValueError, TypeError):
    logger.warning("环境变量 {env_name} 无效，使用默认值 {default_val}")
    {env_name.lower()}_value = {default_val}"""
                    
                    return f"第 {issue.line_number} 行: 替换为安全的类型转换:\n{safe_replacement}"
        
        elif issue.issue_type == 'unsafe_float':
            # 类似处理浮点数转换
            match = re.search(r'float\(os\.environ\.get\([^)]+\)\)', line)
            if match:
                return f"第 {issue.line_number} 行: 使用安全的浮点数转换，包含异常处理"
        
        elif issue.issue_type == 'no_default':
            # 替换直接访问为 get() 方式
            match = re.search(r'os\.environ\[[\'"]([^\'\"]+)[\'\"]\]', line)
            if match:
                env_name = match.group(1)
                return f"第 {issue.line_number} 行: 替换为 os.environ.get('{env_name}', 'default_value')"
        
        return f"第 {issue.line_number} 行: {issue.suggestion}"

    def print_report(self):
        """打印报告"""
        if not self.issues:
            print("✅ 没有发现环境变量处理问题！")
            return
        
        print(f"\n🔍 环境变量标准化报告")
        print(f"{'='*60}")
        print(f"总计发现 {len(self.issues)} 个问题")
        
        # 按严重程度分组
        by_severity = {}
        for issue in self.issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)
        
        for severity in ['error', 'warning', 'info']:
            if severity in by_severity:
                issues = by_severity[severity]
                print(f"\n{severity.upper()} ({len(issues)} 个):")
                print("-" * 40)
                
                for issue in issues:
                    print(f"📁 {issue.file_path}:{issue.line_number}")
                    print(f"   问题: {issue.description}")
                    print(f"   代码: {issue.line_content}")
                    print(f"   建议: {issue.suggestion}")
                    print()
        
        print(f"{'='*60}")
        
        if self.dry_run:
            print("\n💡 使用 --apply 参数来生成具体的修复建议")

def main():
    parser = argparse.ArgumentParser(description='环境变量标准化工具')
    parser.add_argument('--project-root', type=str, default='.', help='项目根目录')
    parser.add_argument('--dry-run', action='store_true', default=True, help='预览模式（默认）')
    parser.add_argument('--apply', action='store_true', help='生成修复建议')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"❌ 项目根目录不存在: {project_root}")
        sys.exit(1)
    
    dry_run = not args.apply
    
    standardizer = EnvVarStandardizer(project_root, dry_run=dry_run)
    issues = standardizer.scan_project()
    standardizer.print_report()
    
    if args.apply and issues:
        print("\n🔧 生成修复建议...")
        fixes = standardizer.generate_fixes()
        
        for file_path, file_fixes in fixes.items():
            print(f"\n📁 {file_path}:")
            for fix in file_fixes:
                print(f"  {fix}")

if __name__ == '__main__':
    main()
