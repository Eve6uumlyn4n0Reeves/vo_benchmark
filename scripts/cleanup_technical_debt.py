#!/usr/bin/env python3
"""
技术债务清理脚本

扫描代码库中的技术债务，包括：
- TODO注释
- FIXME注释
- HACK注释
- 注释掉的代码
- 临时解决方案
- console.log调试代码
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TechnicalDebt:
    file_path: str
    line_number: int
    line_content: str
    debt_type: str
    severity: str
    description: str

class TechnicalDebtScanner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.debts: List[TechnicalDebt] = []
        
        # 定义扫描模式
        self.patterns = {
            'TODO': {
                'pattern': r'(//|#|/\*|\*|<!--)\s*(TODO|todo)\s*:?\s*(.+)',
                'severity': 'medium',
                'description': 'TODO注释'
            },
            'FIXME': {
                'pattern': r'(//|#|/\*|\*|<!--)\s*(FIXME|fixme)\s*:?\s*(.+)',
                'severity': 'high',
                'description': 'FIXME注释'
            },
            'HACK': {
                'pattern': r'(//|#|/\*|\*|<!--)\s*(HACK|hack)\s*:?\s*(.+)',
                'severity': 'high',
                'description': 'HACK注释'
            },
            'XXX': {
                'pattern': r'(//|#|/\*|\*|<!--)\s*(XXX|xxx)\s*:?\s*(.+)',
                'severity': 'high',
                'description': 'XXX注释'
            },
            'TEMPORARY': {
                'pattern': r'(//|#|/\*|\*|<!--)\s*(临时|temp|temporary|暂时)\s*(.+)',
                'severity': 'medium',
                'description': '临时解决方案'
            },
            'COMMENTED_CODE': {
                'pattern': r'^\s*(//|#)\s*[a-zA-Z_$][a-zA-Z0-9_$]*\s*[=\(\{]',
                'severity': 'low',
                'description': '注释掉的代码'
            },
            'CONSOLE_LOG': {
                'pattern': r'console\.(log|debug|info|warn|error)\s*\(',
                'severity': 'low',
                'description': '调试日志'
            },
            'DEBUGGER': {
                'pattern': r'\bdebugger\b',
                'severity': 'high',
                'description': '调试断点'
            }
        }
        
        # 需要扫描的文件扩展名
        self.file_extensions = {'.ts', '.tsx', '.js', '.jsx', '.py', '.vue', '.html', '.css', '.scss'}
        
        # 忽略的目录
        self.ignore_dirs = {'node_modules', '.git', 'dist', 'build', '__pycache__', '.pytest_cache'}

    def scan_file(self, file_path: Path) -> None:
        """扫描单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                    
                for debt_type, config in self.patterns.items():
                    pattern = config['pattern']
                    if re.search(pattern, line, re.IGNORECASE):
                        debt = TechnicalDebt(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            line_content=line_stripped,
                            debt_type=debt_type,
                            severity=config['severity'],
                            description=config['description']
                        )
                        self.debts.append(debt)
                        
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

    def scan_directory(self, directory: Path) -> None:
        """递归扫描目录"""
        for item in directory.iterdir():
            if item.is_dir():
                if item.name not in self.ignore_dirs:
                    self.scan_directory(item)
            elif item.is_file():
                if item.suffix in self.file_extensions:
                    self.scan_file(item)

    def scan(self) -> List[TechnicalDebt]:
        """扫描整个项目"""
        print(f"Scanning project at: {self.project_root}")
        self.debts = []
        self.scan_directory(self.project_root)
        return self.debts

    def generate_report(self) -> Dict[str, Any]:
        """生成报告"""
        # 按严重程度分组
        by_severity = {'high': [], 'medium': [], 'low': []}
        for debt in self.debts:
            by_severity[debt.severity].append(debt)
        
        # 按类型分组
        by_type = {}
        for debt in self.debts:
            if debt.debt_type not in by_type:
                by_type[debt.debt_type] = []
            by_type[debt.debt_type].append(debt)
        
        # 按文件分组
        by_file = {}
        for debt in self.debts:
            if debt.file_path not in by_file:
                by_file[debt.file_path] = []
            by_file[debt.file_path].append(debt)
        
        return {
            'total_debts': len(self.debts),
            'by_severity': {k: len(v) for k, v in by_severity.items()},
            'by_type': {k: len(v) for k, v in by_type.items()},
            'by_file': {k: len(v) for k, v in by_file.items()},
            'details': {
                'by_severity': by_severity,
                'by_type': by_type,
                'by_file': by_file
            }
        }

    def save_report(self, output_file: str) -> None:
        """保存报告到文件"""
        report = self.generate_report()
        
        # 转换为可序列化的格式
        serializable_report = {
            'total_debts': report['total_debts'],
            'by_severity': report['by_severity'],
            'by_type': report['by_type'],
            'by_file': report['by_file'],
            'debts': [
                {
                    'file_path': debt.file_path,
                    'line_number': debt.line_number,
                    'line_content': debt.line_content,
                    'debt_type': debt.debt_type,
                    'severity': debt.severity,
                    'description': debt.description
                }
                for debt in self.debts
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_report, f, indent=2, ensure_ascii=False)
        
        print(f"Report saved to: {output_file}")

    def print_summary(self) -> None:
        """打印摘要"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("技术债务扫描报告")
        print("="*60)
        print(f"总计发现技术债务: {report['total_debts']} 项")
        print()
        
        print("按严重程度分布:")
        for severity, count in report['by_severity'].items():
            print(f"  {severity.upper()}: {count} 项")
        print()
        
        print("按类型分布:")
        for debt_type, count in report['by_type'].items():
            print(f"  {debt_type}: {count} 项")
        print()
        
        print("问题最多的文件:")
        sorted_files = sorted(report['by_file'].items(), key=lambda x: x[1], reverse=True)
        for file_path, count in sorted_files[:10]:
            print(f"  {file_path}: {count} 项")
        print()
        
        # 显示高优先级问题
        high_priority = report['details']['by_severity']['high']
        if high_priority:
            print("高优先级问题 (需要立即处理):")
            for debt in high_priority[:10]:  # 只显示前10个
                print(f"  {debt.file_path}:{debt.line_number} - {debt.description}")
                print(f"    {debt.line_content}")
            if len(high_priority) > 10:
                print(f"    ... 还有 {len(high_priority) - 10} 个高优先级问题")
        print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='扫描技术债务')
    parser.add_argument('--project-root', default='.', help='项目根目录')
    parser.add_argument('--output', default='technical_debt_report.json', help='输出文件')
    parser.add_argument('--summary-only', action='store_true', help='只显示摘要')
    
    args = parser.parse_args()
    
    scanner = TechnicalDebtScanner(args.project_root)
    debts = scanner.scan()
    
    if not args.summary_only:
        scanner.save_report(args.output)
    
    scanner.print_summary()
    
    # 提供清理建议
    print("清理建议:")
    print("1. 优先处理 FIXME、HACK、XXX 类型的问题")
    print("2. 移除调试代码 (console.log)")
    print("3. 清理注释掉的代码")
    print("4. 将 TODO 转换为正式的任务或实现")
    print("5. 重构临时解决方案")

if __name__ == '__main__':
    main()
