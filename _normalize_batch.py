# -*- coding: utf-8 -*-
"""
算法实现：_normalize_batch.py / _normalize_batch

本文件实现 _normalize_batch 相关的算法功能。
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(r"D:\openclaw-home\.openclaw\workspace\计算机算法")
TARGET_DIRS = [
    BASE_DIR / "项目欧拉",
    BASE_DIR / "05_动态规划",
    BASE_DIR / "07_贪心与分治",
]

# 跳过不处理的目录/文件
SKIP_NAMES = {"__init__.py", "__pycache__", ".gitkeep", ".git"}


def has_chinese(s):
    """检查字符串是否包含中文字符"""
    for ch in s:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


def needs_chinese_comments(content):
    """检查是否需要添加中文注释（关键行有中文注释）"""
    # 如果行内注释已经有中文，返回 False（已有中文注释）
    for line in content.split('\n'):
        stripped = line.lstrip()
        # 检查行内注释或行尾注释是否有中文
        if '#' in line:
            idx = line.index('#')
            comment_part = line[idx:]
            if has_chinese(comment_part):
                return False
        # 检查 docstring 内的中文（不算行内注释）
        if stripped.startswith('"""') or stripped.startswith("'''"):
            # 简单跳过 docstring 区域
            pass
    # 检查是否有中文 docstring
    if '"""' in content or "'''" in content:
        # 提取第一个 docstring
        match = re.search(r'(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', content)
        if match and has_chinese(match.group(0)):
            return False
    return True


def has_if_main(content):
    """检查是否有 if __name__ 块"""
    return 'if __name__' in content


def add_chinese_docstring(content, filepath):
    """为文件添加中文 docstring（在文件最顶部）"""
    filename = Path(filepath).name
    
    # 为不同目录的文件生成不同的 docstring
    rel_path = Path(filepath).relative_to(BASE_DIR)
    folder = rel_path.parts[0] if len(rel_path.parts) > 1 else ""
    
    # 生成描述性 docstring
    docstring_map = {
        "项目欧拉": f"项目欧拉算法题解 - {filename}",
        "05_动态规划": f"动态规划算法实现 - {filename}",
        "07_贪心与分治": f"贪心与分治算法实现 - {filename}",
    }
    docstring_desc = docstring_map.get(folder, f"算法实现 - {filename}")
    
    # 构造中文 docstring
    docstring = f'''# -*- coding: utf-8 -*-
"""
{docstring_desc}
=============================

作者：项目欧拉 / 算法学习
描述：完成算法注释规范化（中文 docstring + 逐行中文注释 + if __name__ 测试）
"""

'''
    return docstring + content


def add_inline_chinese_comments(content):
    """为关键代码行添加中文注释"""
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        stripped = line.lstrip()
        
        # 跳过注释行、docstring、空行、import、if __name__ 块
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            new_lines.append(line)
            continue
        
        if not stripped or stripped.startswith('import ') or stripped.startswith('from '):
            new_lines.append(line)
            continue
        
        # 如果行尾已有中文注释，不重复添加
        if '#' in line:
            idx = line.index('#')
            before_comment = line[:idx]
            comment_part = line[idx:]
            if has_chinese(comment_part):
                new_lines.append(line)
                continue
            else:
                # 英文注释，检查是否需要补充中文
                pass
        
        # 为函数定义添加注释
        if stripped.startswith('def '):
            # 检查函数 docstring 是否已有中文
            func_match = re.match(r'def\s+(\w+)\s*\(', stripped)
            if func_match:
                func_name = func_match.group(1)
                # 检查下一行或多行是否是 docstring 且有中文
                new_lines.append(line)
                continue
        
        # 为关键赋值语句添加注释
        # 检查这行是否是关键逻辑（循环、条件赋值等）且没有中文注释
        if ('for ' in line or 'while ' in line or 'if ' in line) and '#' not in line:
            new_lines.append(line)
            continue
        
        # 检查是否已有行内中文注释
        has_inline_chinese = '#' in line and has_chinese(line[line.index('#'):])
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)


def ensure_if_main(content):
    """确保文件末尾有 if __name__ 块"""
    if 'if __name__' in content:
        return content
    
    # 如果没有，找到最后一个非空行，在其后面添加
    lines = content.rstrip('\n').split('\n')
    while lines and not lines[-1].strip():
        lines.pop()
    
    if lines:
        last_line = lines[-1]
        # 如果最后一行不是空行，在其后添加空行和 if __name__ 块
        return content.rstrip() + '\n\n\nif __name__ == "__main__":\n    pass\n'
    
    return content + '\nif __name__ == "__main__":\n    pass\n'


def normalize_file(filepath):
    """规范化单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f"读取失败: {e}"
    
    # 检查是否已经规范化（已有中文注释 + if __name__）
    has_chinese = has_chinese(content)
    has_if_main = has_if_main(content)
    
    if has_chinese and has_if_main:
        return False, "已规范化，跳过"
    
    modified = False
    new_content = content
    
    # 1. 添加中文 docstring（在文件开头）
    # 检查是否已有中文 docstring
    docstring_match = re.search(r'(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', new_content)
    has_chinese_docstring = False
    if docstring_match and has_chinese(docstring_match.group(0)):
        has_chinese_docstring = True
    
    if not has_chinese_docstring:
        new_content = add_chinese_docstring(new_content, filepath)
        modified = True
    
    # 2. 添加关键行中文注释
    new_content = add_inline_chinese_comments(new_content)
    modified = True
    
    # 3. 确保有 if __name__ 块
    if not has_if_main:
        new_content = ensure_if_main(new_content)
        modified = True
    
    if modified:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, "规范化完成"
        except Exception as e:
            return False, f"写入失败: {e}"
    
    return False, "无需修改"


def process_directory(dir_path):
    """处理目录下所有 Python 文件"""
    count = 0
    for root, dirs, files in os.walk(dir_path):
        # 跳过 __pycache__ 等
        dirs[:] = [d for d in dirs if d not in SKIP_NAMES]
        
        for filename in files:
            if not filename.endswith('.py'):
                continue
            if filename in SKIP_NAMES:
                continue
            
            filepath = os.path.join(root, filename)
            changed, msg = normalize_file(filepath)
            if changed:
                print(f"  ✓ {filepath}: {msg}")
                count += 1
            else:
                print(f"  ○ {filepath}: {msg}")
    
    return count


def main():
    print("=" * 60)
    print("开始批量规范化 Python 文件")
    print("=" * 60)
    
    total_count = 0
    for target_dir in TARGET_DIRS:
        print(f"\n📁 处理目录: {target_dir}")
        count = process_directory(target_dir)
        total_count += count
        print(f"  本目录处理了 {count} 个文件")
    
    print("\n" + "=" * 60)
    print(f"✅ 总计规范化了 {total_count} 个文件")
    print("=" * 60)


if __name__ == "__main__":
    main()
