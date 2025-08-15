#!/usr/bin/env python3
"""
修复相对导入问题的脚本

此脚本将所有相对导入（from .. import）转换为绝对导入，
以解决模块导入问题。

使用方法:
    python scripts/fix_imports.py --dry-run  # 预览更改
    python scripts/fix_imports.py --apply    # 应用更改
"""

import os
import re
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImportFixer:
    """导入修复器"""
    
    def __init__(self, project_root: Path, dry_run: bool = True):
        self.project_root = project_root
        self.dry_run = dry_run
        self.src_dir = project_root / "backend" / "src"
        self.fixed_files = []
        
    def fix_all_imports(self) -> List[str]:
        """修复所有相对导入"""
        logger.info(f"开始修复相对导入 (dry_run={self.dry_run})")
        
        # 查找所有Python文件
        python_files = list(self.src_dir.rglob("*.py"))
        
        for file_path in python_files:
            if self._fix_file_imports(file_path):
                self.fixed_files.append(str(file_path))
        
        return self.fixed_files
    
    def _fix_file_imports(self, file_path: Path) -> bool:
        """修复单个文件的导入"""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # 查找相对导入模式
            relative_import_pattern = r'from\s+(\.+)([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import\s+(.+)'
            
            def replace_import(match):
                dots = match.group(1)
                module_path = match.group(2)
                imports = match.group(3)
                
                # 计算绝对路径
                relative_path = file_path.relative_to(self.src_dir)
                current_dir_parts = relative_path.parent.parts
                
                # 计算向上的层级数
                up_levels = len(dots) - 1
                
                if up_levels > len(current_dir_parts):
                    # 超出了src目录，保持原样
                    return match.group(0)
                
                # 构建绝对导入路径
                if up_levels == 0:
                    # from .module import something -> from current_package.module import something
                    if len(current_dir_parts) > 0:
                        absolute_path = '.'.join(current_dir_parts) + '.' + module_path
                    else:
                        absolute_path = module_path
                else:
                    # from ..module import something
                    parent_parts = current_dir_parts[:-up_levels] if up_levels < len(current_dir_parts) else []
                    if parent_parts:
                        absolute_path = '.'.join(parent_parts) + '.' + module_path
                    else:
                        absolute_path = module_path
                
                return f'from {absolute_path} import {imports}'
            
            # 应用替换
            new_content = re.sub(relative_import_pattern, replace_import, content)
            
            if new_content != original_content:
                if not self.dry_run:
                    file_path.write_text(new_content, encoding='utf-8')
                
                logger.info(f"修复了文件: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"修复文件 {file_path} 时出错: {e}")
            return False
    
    def print_summary(self):
        """打印修复摘要"""
        print(f"\n{'='*60}")
        print(f"导入修复摘要 (dry_run={self.dry_run})")
        print(f"{'='*60}")
        print(f"修复的文件数: {len(self.fixed_files)}")
        
        for file_path in self.fixed_files:
            print(f"✅ {file_path}")
        
        print(f"{'='*60}")
        
        if self.dry_run:
            print("\n使用 --apply 参数来实际应用这些更改")

def main():
    parser = argparse.ArgumentParser(description='修复相对导入问题')
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
    
    fixer = ImportFixer(project_root, dry_run=args.dry_run)
    fixed_files = fixer.fix_all_imports()
    fixer.print_summary()

if __name__ == '__main__':
    main()
