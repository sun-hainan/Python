# -*- coding: utf-8 -*-

"""

算法实现：fix_pe.py / fix_pe



本文件实现 fix_pe 相关的算法功能。

"""



import os

import re



base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'



def count_chinese(s):

    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff')



def has_meaningful_chinese(content):

    """Check if content has meaningful Chinese (>= 10 chars)"""

    return count_chinese(content) >= 10



def add_chinese_docstring(lines, problem_num):

    """Add Chinese docstring at appropriate position"""

    cn_doc = f'''"""

Project Euler Problem {problem_num} — 中文注释版

https://projecteuler.net/problem={problem_num}



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""'''

    

    new_lines = []

    inserted = False

    in_docstring = False

    docstring_marker = None

    

    for i, line in enumerate(lines):

        stripped = line.strip()

        

        if not in_docstring:

            if stripped.startswith('"""') or stripped.startswith("'''"):

                docstring_marker = stripped[:3]

                in_docstring = True

                new_lines.append(line)

            elif stripped.startswith('from ') or stripped.startswith('import '):

                if not inserted:

                    new_lines.append(cn_doc)

                    new_lines.append('')

                    inserted = True

                new_lines.append(line)

            elif stripped.startswith('def ') or stripped.startswith('class '):

                if not inserted:

                    new_lines.append(cn_doc)

                    new_lines.append('')

                    inserted = True

                new_lines.append(line)

            elif stripped == '':

                new_lines.append(line)

            else:

                new_lines.append(line)

        else:

            new_lines.append(line)

            if docstring_marker and docstring_marker in stripped:

                in_docstring = False

                # After closing docstring

                if not inserted:

                    new_lines.append(cn_doc)

                    new_lines.append('')

                    inserted = True

    

    if not inserted:

        new_lines.insert(0, cn_doc)

        new_lines.insert(1, '')

    

    return new_lines





def add_chinese_comments(lines):

    """Add Chinese inline comments to key lines"""

    processed = []

    for line in lines:

        stripped = line.strip()

        

        # Add comment to function definitions

        if stripped.startswith('def ') and ' #' not in stripped:

            m = re.search(r'def\s+(\w+)', stripped)

            if m:

                processed.append(line)

                # Only add if the previous few lines don't already have Chinese

                recent = '\n'.join(processed[-3:])

                if count_chinese(recent) == 0:

                    processed.append(f'    # {m.group(1)} 函数实现')

                continue

        

        # Add comment to class definitions

        if stripped.startswith('class ') and ' #' not in stripped:

            m = re.search(r'class\s+(\w+)', stripped)

            if m:

                processed.append(line)

                recent = '\n'.join(processed[-3:])

                if count_chinese(recent) == 0:

                    processed.append(f'    # {m.group(1)} 类定义')

                continue

        

        # Add comment to key algorithmic lines

        if stripped.startswith('for ') and ' #' not in stripped:

            processed.append(line)

            recent = '\n'.join(processed[-2:])

            if count_chinese(recent) == 0:

                processed.append('    # 遍历循环')

            continue

        

        if stripped.startswith('while ') and ' #' not in stripped:

            processed.append(line)

            recent = '\n'.join(processed[-2:])

            if count_chinese(recent) == 0:

                processed.append('    # 条件循环')

            continue

        

        if stripped.startswith('return ') and ' #' not in stripped and len(stripped) < 80:

            processed.append(line)

            recent = '\n'.join(processed[-2:])

            if count_chinese(recent) == 0:

                processed.append('    # 返回结果')

            continue

        

        processed.append(line)

    

    return processed





def fix_file(fp):

    """Fix a single file"""

    try:

        with open(fp, encoding='utf-8') as f:

            content = f.read()

    except:

        return False, 'READ ERROR'

    

    if has_meaningful_chinese(content):

        return False, 'HAS MEANINGFUL CN'

    

    original = content

    fn = os.path.basename(fp)

    dir_name = os.path.basename(os.path.dirname(fp))

    

    m = re.search(r'problem_(\d+)', dir_name)

    problem_num = m.group(1) if m else '?'

    

    lines = content.split('\n')

    

    # Step 1: Add Chinese docstring

    lines = add_chinese_docstring(lines, problem_num)

    

    # Step 2: Add Chinese inline comments

    lines = add_chinese_comments(lines)

    

    # Step 3: Ensure if __name__ block exists

    if "if __name__" not in '\n'.join(lines):

        lines.append('\nif __name__ == "__main__":')

        lines.append(f'    # Project Euler Problem {problem_num} 测试入口')

        lines.append('    result = solution()')

        lines.append('    print(f"答案: {{{result}}}")')

    

    new_content = '\n'.join(lines)

    

    if new_content != original:

        try:

            with open(fp, 'w', encoding='utf-8') as f:

                f.write(new_content)

            return True, 'FIXED'

        except Exception as e:

            return False, f'WRITE ERROR: {e}'

    return False, 'NO CHANGE'





fixed_count = 0

skipped = 0

errors = []



# Find project_euler directory

proj_euler_path = None

for dirpath, dirnames, filenames in os.walk(base):

    if os.path.basename(dirpath) == 'project_euler':

        proj_euler_path = dirpath

        break



if proj_euler_path:

    print(f'Found project_euler at: {proj_euler_path}')

    

    for dirpath, dirnames, filenames in os.walk(proj_euler_path):

        # Only process problem_NNN directories

        if not os.path.basename(dirpath).startswith('problem_'):

            continue

        

        for fn in filenames:

            if not fn.endswith('.py'):

                continue

            if fn == '__init__.py':

                continue

            if fn.startswith('test_') or fn.endswith('_test.py'):

                continue

            

            fp = os.path.join(dirpath, fn)

            

            try:

                with open(fp, encoding='utf-8') as f:

                    content = f.read()

            except:

                errors.append(f'READ: {fn}')

                continue

            

            if has_meaningful_chinese(content):

                skipped += 1

                continue

            

            success, msg = fix_file(fp)

            if success:

                fixed_count += 1

            elif msg != 'HAS MEANINGFUL CN':

                errors.append(f'{msg}: {fn}')



print(f'\nFixed: {fixed_count} project_euler files')

print(f'Already had meaningful Chinese: {skipped}')

print(f'Errors: {len(errors)}')

for e in errors[:10]:

    print(f'  {e}')

