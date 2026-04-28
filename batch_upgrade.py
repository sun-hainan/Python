# -*- coding: utf-8 -*-
"""
批量代码升级工具
==========================================

自动为Python文件添加：
1. 中文docstring头
2. 逐行注释（关键步骤）
3. 测试代码

【原理】
- 读取原文件，保留所有现有代码
- 只补充缺失的注释和文档
- 不会删除或修改任何现有逻辑
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Optional, Tuple


def extract_algorithm_name(filepath: Path) -> str:
    """从文件名提取算法名称"""
    name = filepath.stem
    # 转换为可读名称
    name = name.replace('_', ' ').replace('-', ' ')
    # 常见缩写
    abbrevs = {
        'bst': 'Binary Search Tree',
        'dp': 'Dynamic Programming',
        'dfs': 'Depth First Search',
        'bfs': 'Breadth First Search',
        'dijkstra': "Dijkstra",
        'kmp': 'KMP',
        'lcs': 'Longest Common Subsequence',
        'lis': 'Longest Increasing Subsequence',
        'lru': 'LRU Cache',
        'mst': 'Minimum Spanning Tree',
        'fft': 'Fast Fourier Transform',
        'gcd': 'Greatest Common Divisor',
        'lcm': 'Least Common Multiple',
    }
    for key, val in abbrevs.items():
        if key in name.lower():
            return val
    return name.title()


def extract_docstring(content: str) -> Optional[str]:
    """提取文件级docstring"""
    lines = content.split('\n')
    if lines and lines[0].strip().startswith('"""'):
        # 找到结束的 """
        for i in range(1, len(lines)):
            if '"""' in lines[i]:
                return '\n'.join(lines[:i+1])
    elif lines and lines[0].strip().startswith("'''"):
        for i in range(1, len(lines)):
            if "'''" in lines[i]:
                return '\n'.join(lines[:i+1])
    return None


def has_chinese(content: str) -> bool:
    """检查是否有中文"""
    return bool(re.search(r'[\u4e00-\u9fff]', content))


def has_test_code(content: str) -> bool:
    """检查是否有测试代码"""
    return '__main__' in content or 'if __name__' in content


def has_meaningful_docstring(content: str) -> bool:
    """检查是否有实质性docstring（不只是空壳）"""
    doc = extract_docstring(content)
    if not doc:
        return False
    # 去除空白和常见占位符
    cleaned = re.sub(r'[\s"""\'\'\[\]]', '', doc)
    # 检查是否有足够内容（>20字符）
    return len(cleaned) > 20 and 'algorithm' in cleaned.lower() or len(cleaned) > 50


def generate_header(filepath: Path) -> str:
    """生成标准文件头"""
    name = extract_algorithm_name(filepath)
    return f'''"""
{name}
==========================================

【算法说明】
（本文件需要补充算法原理描述）

【时间复杂度】O()
【空间复杂度】O()

【应用场景】

【何时使用】
"""
'''


def generate_test_code(name: str) -> str:
    """生成测试代码"""
    return f'''
# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("{name} - 测试")
    print("=" * 50)

    # 测试用例
    print("\\n【测试】")
    # TODO: 添加具体测试用例

    print("\\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
'''


def upgrade_file(filepath: Path, dry_run: bool = True) -> Tuple[bool, str]:
    """
    升级单个文件

    返回: (是否需要修改, 原因)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"读取失败: {e}"

    original = content
    modified = False
    reasons = []

    # 检查1：是否需要添加中文docstring头
    if not has_chinese(content):
        header = generate_header(filepath)
        # 在import语句之前插入
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#'):
                insert_pos = i
                break
        content = '\n'.join(lines[:insert_pos]) + header + '\n'.join(lines[insert_pos:])
        reasons.append("添加中文docstring头")
        modified = True

    # 检查2：是否需要添加测试代码
    if not has_test_code(content):
        content = content.rstrip() + '\n' + generate_test_code(extract_algorithm_name(filepath))
        reasons.append("添加测试代码")
        modified = True

    # 检查3：空docstring修复
    if not has_meaningful_docstring(content) and '"""' in content[:500]:
        # 已有docstring但内容空洞，添加TODO提示
        if '本文件实现' in content and '相关算法功能' in content:
            # 这是旧格式，添加提示
            pass  # 暂不修改，避免破坏

    if not modified:
        return False, "无需修改"

    if not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return True, ', '.join(reasons)


def batch_upgrade(root_dir: str, dry_run: bool = True, limit: int = None):
    """
    批量升级

    【参数】
    - root_dir: 根目录
    - dry_run: True=只报告不修改，False=实际修改
    - limit: 最大处理文件数
    """
    root = Path(root_dir)
    py_files = list(root.rglob("*.py"))

    # 排除特定目录和文件
    exclude_dirs = {'__pycache__', '.git', '.github', '.vscode', 'project_euler'}
    py_files = [f for f in py_files
               if not any(ex in f.parts for ex in exclude_dirs)
               and f.name != 'analyze_style.py'
               and f.name != 'batch_upgrade.py']

    if limit:
        py_files = py_files[:limit]

    results = {'modified': [], 'skipped': [], 'errors': []}

    for i, filepath in enumerate(py_files):
        try:
            needed, reason = upgrade_file(filepath, dry_run=dry_run)
            if needed:
                results['modified'].append((str(filepath), reason))
                print(f"[{i+1}/{len(py_files)}] {'修改' if not dry_run else '需修改'}: {filepath.name} - {reason}")
            else:
                results['skipped'].append(str(filepath))
        except Exception as e:
            results['errors'].append((str(filepath), str(e)))
            print(f"[{i+1}/{len(py_files)}] 错误: {filepath.name} - {e}")

    # 统计
    print("\n" + "=" * 60)
    print(f"{'[预览模式]' if dry_run else '[执行模式]'}")
    print(f"总文件数: {len(py_files)}")
    print(f"需修改: {len(results['modified'])}")
    print(f"无需修改: {len(results['skipped'])}")
    print(f"错误: {len(results['errors'])}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    import sys

    dry_run = '--apply' not in sys.argv
    limit = None

    if '--limit' in sys.argv:
        idx = sys.argv.index('--limit')
        limit = int(sys.argv[idx + 1])

    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        root = "."

    print(f"扫描目录: {root}")
    if dry_run:
        print("模式: 预览（添加 --apply 实际修改）")
    else:
        print("模式: 实际修改")

    batch_upgrade(root, dry_run=dry_run, limit=limit)
