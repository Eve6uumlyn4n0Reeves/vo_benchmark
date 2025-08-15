#!/usr/bin/env python3
"""
清理调试代码脚本

移除前端代码中的console.log调试语句和注释掉的代码
"""

import re
import sys
from pathlib import Path
import argparse

def clean_file(file_path: Path, dry_run: bool = True) -> tuple[int, list[str]]:
    """清理单个文件中的调试代码"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return 0, []
    
    original_lines = len(lines)
    cleaned_lines = []
    removed_lines = []
    
    for i, line in enumerate(lines, 1):
        # 检查是否是需要移除的调试代码
        should_remove = False
        
        # 1. console.log 调试语句（但保留错误处理中的console.error）
        if re.match(r'^\s*console\.(log|debug|info)\s*\(', line):
            should_remove = True
            removed_lines.append(f"Line {i}: {line.strip()}")
        
        # 2. 注释掉的代码行（简单的变量赋值、函数调用等）
        elif re.match(r'^\s*//\s*[a-zA-Z_$][a-zA-Z0-9_$]*\s*[=\(\{]', line):
            should_remove = True
            removed_lines.append(f"Line {i}: {line.strip()}")
        
        # 3. 注释掉的import语句
        elif re.match(r'^\s*//\s*(import|from)\s+', line):
            should_remove = True
            removed_lines.append(f"Line {i}: {line.strip()}")
        
        # 4. 临时调试注释
        elif re.match(r'^\s*//\s*(调试|测试|临时|debug|test|temp)\b', line, re.IGNORECASE):
            should_remove = True
            removed_lines.append(f"Line {i}: {line.strip()}")
        
        if not should_remove:
            cleaned_lines.append(line)
    
    # 如果不是dry run，写回文件
    if not dry_run and removed_lines:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            print(f"✅ 已清理文件: {file_path} (移除了 {len(removed_lines)} 行)")
        except Exception as e:
            print(f"❌ 写入文件失败 {file_path}: {e}")
            return 0, []
    
    return len(removed_lines), removed_lines

def main():
    parser = argparse.ArgumentParser(description='清理调试代码')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改文件')
    parser.add_argument('--apply', action='store_true', help='应用清理')
    parser.add_argument('--project-root', type=str, default='.', help='项目根目录')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        print("请指定 --dry-run 或 --apply 参数")
        sys.exit(1)
    
    project_root = Path(args.project_root).resolve()
    frontend_src = project_root / "frontend" / "src"
    
    if not frontend_src.exists():
        print(f"前端源码目录不存在: {frontend_src}")
        sys.exit(1)
    
    # 获取所有TypeScript/JavaScript文件
    file_extensions = {'.ts', '.tsx', '.js', '.jsx'}
    exclude_dirs = {'node_modules', '.git', 'dist', 'build'}
    
    files_to_clean = []
    for file_path in frontend_src.rglob('*'):
        if (file_path.is_file() and 
            file_path.suffix in file_extensions and
            not any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs)):
            files_to_clean.append(file_path)
    
    print(f"🔍 找到 {len(files_to_clean)} 个文件需要检查")
    print(f"📋 模式: {'预览模式' if args.dry_run else '清理模式'}")
    print()
    
    total_removed = 0
    files_modified = 0
    
    for file_path in files_to_clean:
        removed_count, removed_lines = clean_file(file_path, dry_run=args.dry_run)
        
        if removed_count > 0:
            files_modified += 1
            total_removed += removed_count
            
            relative_path = file_path.relative_to(project_root)
            print(f"📁 {relative_path}")
            
            if args.dry_run:
                print(f"   将移除 {removed_count} 行调试代码:")
                for line in removed_lines[:5]:  # 只显示前5行
                    print(f"   - {line}")
                if len(removed_lines) > 5:
                    print(f"   ... 还有 {len(removed_lines) - 5} 行")
            else:
                print(f"   已移除 {removed_count} 行调试代码")
            print()
    
    print("=" * 60)
    print(f"📊 清理统计:")
    print(f"   - 检查文件数: {len(files_to_clean)}")
    print(f"   - 需要修改的文件数: {files_modified}")
    print(f"   - 总共移除行数: {total_removed}")
    
    if args.dry_run:
        print()
        print("💡 使用 --apply 参数来实际应用这些清理")
    else:
        print()
        print("✅ 清理完成！")

if __name__ == '__main__':
    main()
