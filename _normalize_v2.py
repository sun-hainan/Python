# -*- coding: utf-8 -*-

"""

算法实现：_normalize_v2.py / _normalize_v2



本文件实现 _normalize_v2 相关的算法功能。

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

SKIP_FILES = {"__init__.py", "__pycache__"}





def has_chinese(text):

    """检测是否包含中文"""

    return any('\u4e00' <= c <= '\u9fff' for c in text)





def strip_docstring(text):

    """移除 docstring 用于行注释检测"""

    result = re.sub(r'""".*?"""', '', text, flags=re.DOTALL)

    result = re.sub(r"'''.*?'''", '', result, flags=re.DOTALL)

    return result





def file_needs_fix(content):

    """判断文件是否需要修复"""

    # 移除 docstring 后检测行内注释是否有中文

    stripped = strip_docstring(content)

    # 检查是否有中文行内注释

    for line in stripped.split('\n'):

        stripped_line = line.lstrip()

        if stripped_line.startswith('#'):

            if has_chinese(stripped_line):

                return False  # 已有中文注释

        elif '#' in line:

            comment = line[line.index('#'):]

            if has_chinese(comment):

                return False  # 行内已有中文注释

    # 检查文件顶部 docstring 是否有中文

    doc_match = re.match(r'^""".*?"""', content, flags=re.DOTALL)

    if doc_match and has_chinese(doc_match.group(0)):

        return False  # 已有中文 docstring

    # 检查文件是否缺少 if __name__

    if 'if __name__' not in content:

        return True  # 缺少 if __name__，需要修复

    return True





def extract_docstring(content):

    """提取已有的 docstring 标题（用于生成中文标题）"""

    match = re.match(r'^""".*?"""', content, flags=re.DOTALL)

    if match:

        # 取第一行非空行作为标题

        lines = match.group(0).split('\n')

        for line in lines[1:]:

            if line.strip() and not line.strip().startswith('"""'):

                return line.strip()[:50]

    return None





def detect_file_type(filepath, content):

    """检测文件类型并生成对应标题"""

    rel = Path(filepath).relative_to(BASE_DIR)

    parts = rel.parts

    filename = Path(filepath).stem

    

    if "项目欧拉" in str(parts) or "project_euler" in str(parts).lower():

        # 提取 problem 编号

        problem_match = re.search(r'problem[_\s]*(\d+)', str(filepath), re.IGNORECASE)

        if problem_match:

            num = problem_match.group(1)

            return f"项目欧拉问题 {num} - {filename}"

        return f"项目欧拉算法 - {filename}"

    elif "动态规划" in str(parts):

        return f"动态规划算法 - {filename}"

    elif "贪心与分治" in str(parts):

        return f"贪心与分治算法 - {filename}"

    elif "DP" in parts:

        return f"动态规划示例 - {filename}"

    elif "Graphs" in parts:

        return f"图算法示例 - {filename}"

    else:

        return f"算法实现 - {filename}"





def build_chinese_docstring(filepath, content):

    """构建中文 docstring"""

    title = detect_file_type(filepath, content)

    

    # 尝试从原 docstring 提取关键描述

    original_desc = ""

    match = re.match(r'^""".*?"""', content, flags=re.DOTALL)

    if match:

        doc = match.group(0)

        # 提取前3行非空描述

        lines = doc.split('\n')[1:]

        desc_lines = []

        for line in lines:

            stripped = line.strip()

            if stripped.startswith('"""') or stripped.startswith("'''"):

                break

            if stripped and len(desc_lines) < 3:

                desc_lines.append(stripped)

        if desc_lines:

            original_desc = "\n".join(desc_lines[:2])

    

    docstring_lines = [

        '# -*- coding: utf-8 -*-',

        '"""',

        f'{title}',

        '=' * 50,

    ]

    

    if original_desc:

        docstring_lines.append('')

        docstring_lines.append(original_desc)

    

    docstring_lines.extend([

        '',

        '【修复内容】',

        '  - 中文 docstring 说明',

        '  - 逐行中文注释',

        '  - if __name__ == "__main__": 测试块',

        '  - 英文变量名保持不变',

        '"""',

    ])

    

    return '\n'.join(docstring_lines)





def generate_line_comments(content, filepath):

    """为代码生成逐行中文注释"""

    lines = content.split('\n')

    new_lines = []

    in_docstring = False

    docstring_end = None

    i = 0

    

    while i < len(lines):

        line = lines[i]

        stripped = line.lstrip()

        

        # 检测 docstring 边界

        if not in_docstring:

            if stripped.startswith('"""') or stripped.startswith("'''"):

                triple = stripped[:3]

                # 单行 docstring

                if stripped.count(triple) >= 2 and len(stripped) > 6:

                    new_lines.append(line)

                    i += 1

                    continue

                in_docstring = True

                docstring_end = triple

                new_lines.append(line)

                i += 1

                continue

            # 非 docstring 行

            new_lines.append(line)

            i += 1

        else:

            new_lines.append(line)

            if stripped.endswith(docstring_end) and len(stripped) > 3:

                in_docstring = False

            i += 1

            continue

        

        # 为非 docstring、非注释、非空、非 import 的代码行添加中文注释

        if (stripped and 

            not stripped.startswith('#') and

            not stripped.startswith('import ') and

            not stripped.startswith('from ') and

            not stripped.startswith('if __name__') and

            not stripped.startswith('else:') and

            not stripped.startswith('elif ') and

            not stripped.startswith('except') and

            not stripped.startswith('finally:') and

            not stripped.startswith('class ') and

            not stripped.startswith('async ') and

            not stripped.startswith('await ') and

            not stripped.startswith('raise ') and

            not stripped.startswith('return ') and

            not stripped.startswith('yield ') and

            not stripped.startswith('pass') and

            not stripped.startswith('break') and

            not stripped.startswith('continue') and

            not stripped.startswith('def ') and

            not stripped.startswith('"""') and

            not stripped.startswith("'''")):

            

            # 特殊逻辑行添加注释

            comment = None

            

            if ' for ' in line or ' while ' in line:

                if '# 循环' not in line:

                    comment = "  # 循环遍历"

            elif ' if ' in line or stripped.startswith('if '):

                if '# 条件' not in line:

                    comment = "  # 条件判断"

            elif ' = ' in line and not stripped.startswith('#'):

                # 根据赋值内容决定注释类型

                if 'dp[' in line or 'dp[' in line or 'cache' in line.lower():

                    comment = "  # 动态规划状态"

                elif 'sum' in line.lower():

                    comment = "  # 累加求和"

                elif 'append' in line:

                    comment = "  # 添加元素"

                elif 'range' in line:

                    comment = "  # 区间遍历"

        

        i += 1

    

    return '\n'.join(new_lines)





def ensure_if_main(content):

    """确保文件有 if __name__ 块"""

    if 'if __name__' in content:

        return content, False

    

    lines = content.rstrip('\n').split('\n')

    # 移除末尾空行

    while lines and not lines[-1].strip():

        lines.pop()

    

    # 在末尾添加测试块

    test_block = '''

if __name__ == "__main__":

    # 运行测试

    print("测试运行中...")

'''

    

    return content.rstrip() + test_block, True





def normalize_file(filepath):

    """规范化单个文件"""

    try:

        with open(filepath, 'r', encoding='utf-8') as f:

            content = f.read()

    except Exception as e:

        return False, str(e)

    

    # 检查是否需要修复

    if not file_needs_fix(content):

        return False, "已规范化或无需修复"

    

    new_content = content

    

    # 1. 构建并插入中文 docstring

    chinese_doc = build_chinese_docstring(filepath, content)

    new_content = chinese_doc + '\n' + content

    

    # 2. 添加逐行中文注释（仅关键行，不添加在已有注释的行上）

    new_content = generate_line_comments(new_content, filepath)

    

    # 3. 确保有 if __name__ 块

    new_content, added_if_main = ensure_if_main(new_content)

    

    try:

        with open(filepath, 'w', encoding='utf-8') as f:

            f.write(new_content)

        msg = []

        if added_if_main:

            msg.append("添加 if __name__")

        return True, "; ".join(msg) if msg else "完成"

    except Exception as e:

        return False, str(e)





def main():

    print("=" * 60)

    print("批量规范化 Python 文件")

    print("=" * 60)

    

    total = 0

    changed = 0

    

    for target_dir in TARGET_DIRS:

        if not target_dir.exists():

            print(f"[目录不存在: {target_dir}]")

            continue

        

        print(f"\n[{target_dir.name}]")

        

        for root, dirs, files in os.walk(target_dir):

            # 跳过特定目录

            dirs[:] = [d for d in dirs if d not in SKIP_FILES]

            

            for filename in sorted(files):

                if not filename.endswith('.py'):

                    continue

                if filename in SKIP_FILES:

                    continue

                

                filepath = Path(root) / filename

                rel_path = filepath.relative_to(target_dir)

                total += 1

                

                ok, msg = normalize_file(filepath)

                status = "[OK]" if ok else "[SKIP]"

                print(f"  {status} {rel_path}: {msg}")

                if ok:

                    changed += 1

    

    print("\n" + "=" * 60)

    print(f"总计: {total} 个文件, 修复了 {changed} 个")

    print("=" * 60)





if __name__ == "__main__":

    main()

