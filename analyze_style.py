# -*- coding: utf-8 -*-
"""
代码风格分析工具
==========================================

扫描指定目录下的Python文件，分析编码风格问题。

【检查项】
1. 文件头docstring是否完整
2. 是否有TODO/占位符
3. 是否有中文注释
4. 测试代码是否完整
5. 命名规范性

【用法】
python analyze_style.py [目录路径]
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict


class StyleAnalyzer:
    """代码风格分析器"""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = []

    def analyze_file(self, filepath: Path) -> Dict:
        """分析单个文件"""
        issues = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'file': str(filepath), 'issues': [f'读取失败: {e}']}

        # 检查1：文件头docstring
        if not content.startswith('"""') and not content.startswith("#"):
            issues.append("❌ 缺少文件头docstring")

        # 检查2：TODO/占位符
        todo_pattern = r'#?\s*(TODO|FIXME|XXX|HACK|NOTE).*:?\s*(请|需要|补充|待)'
        if re.search(todo_pattern, content):
            issues.append("❌ 存在TODO/占位符")

        # 检查3：空docstring
        empty_doc = r'"""\s*["""\s]*"""'
        if re.search(empty_doc, content):
            issues.append("⚠️ 存在空docstring")

        # 检查4：中文注释
        chinese_pattern = r'[\u4e00-\u9fff]'
        if not re.search(chinese_pattern, content):
            issues.append("⚠️ 无中文注释")

        # 检查5：测试代码
        if '__main__' not in content:
            issues.append("⚠️ 缺少测试代码")

        return {
            'file': str(filepath.relative_to(self.root_dir)),
            'issues': issues,
            'lines': len(content.splitlines())
        }

    def analyze(self) -> List[Dict]:
        """分析目录"""
        results = []
        py_files = list(self.root_dir.rglob("*.py"))

        # 排除特定目录
        exclude_dirs = {'__pycache__', '.git', '.github', '.vscode'}
        py_files = [f for f in py_files
                   if not any(ex in f.parts for ex in exclude_dirs)]

        for filepath in py_files:
            if filepath.name.startswith('__init__'):
                continue
            result = self.analyze_file(filepath)
            if result['issues']:
                results.append(result)

        return results

    def print_report(self):
        """打印报告"""
        results = self.analyze()

        print("=" * 70)
        print(f"代码风格分析报告: {self.root_dir}")
        print("=" * 70)

        if not results:
            print("✅ 所有文件通过检查！")
            return

        # 按问题类型分组
        issue_counts = {
            '[-] Missing header docstring': 0,
            '[-] Has TODO/placeholder': 0,
            '[!] Has empty docstring': 0,
            '[!] No Chinese comments': 0,
            '[!] No test code': 0,
        }

        for r in results:
            for issue in r['issues']:
                for key in issue_counts:
                    if key in issue:
                        issue_counts[key] += 1

        print("\n问题统计:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  {issue}: {count} files")

        print(f"\n共 {len(results)} 个文件存在问题:")
        print("-" * 70)

        for r in sorted(results, key=lambda x: -len(x['issues'])):
            print(f"\n{r['file']} ({r['lines']}行)")
            for issue in r['issues']:
                print(f"  {issue}")


def batch_fix_directory(root_dir: str, dry_run: bool = True):
    """
    批量修复目录

    【用法】
    # 预览模式（不实际修改）
    batch_fix_directory("路径", dry_run=True)

    # 执行修复
    batch_fix_directory("路径", dry_run=False)
    """
    print(f"{'[预览模式]' if dry_run else '[执行模式]'}")
    # TODO: 实现批量修复逻辑
    pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        root = "."

    analyzer = StyleAnalyzer(root)
    analyzer.print_report()
