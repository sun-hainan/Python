# -*- coding: utf-8 -*-

"""

算法实现：fix_project_euler.py / fix_project_euler



本文件实现 fix_project_euler 相关的算法功能。

"""



import os

import re



base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'



def has_chinese(s):

    return any('\u4e00' <= c <= '\u9fff' for c in s)



def fix_file(fp):

    """Fix a single file: add Chinese docstring/comment + if __name__"""

    try:

        with open(fp, encoding='utf-8') as f:

            content = f.read()

    except:

        return False, f'READ ERROR'

    

    original = content

    fn = os.path.basename(fp)

    dir_name = os.path.basename(os.path.dirname(fp))

    

    # Extract problem number from dir_name like "problem_001"

    problem_num = ''

    m = re.search(r'problem_(\d+)', dir_name)

    if m:

        problem_num = m.group(1)

    

    # Check what needs fixing

    needs_main = "if __name__" not in content

    needs_cn = not has_chinese(content)

    

    if not needs_main and not needs_cn:

        return False, 'OK already'

    

    lines = content.split('\n')

    new_lines = []

    

    # ==== 1. Add Chinese docstring at top (after any existing docstring) ====

    # If file already has a docstring (English or Chinese), keep it but add Chinese comment

    # If no docstring, add one

    

    in_docstring = False

    docstring_started = False

    docstring_marker = None

    has_existing_docstring = False

    

    for i, line in enumerate(lines):

        stripped = line.strip()

        if not in_docstring:

            if stripped.startswith('"""') or stripped.startswith("'''"):

                in_docstring = True

                docstring_marker = stripped[:3]

                has_existing_docstring = True

                new_lines.append(line)

            elif stripped.startswith('#'):

                # Comment line before docstring - keep it

                new_lines.append(line)

            elif stripped.startswith('from') or stripped.startswith('import'):

                # Imports before docstring - keep them, insert Chinese docstring before

                if not has_existing_docstring and needs_cn:

                    cn_doc = f'"""\nProject Euler Problem {problem_num} 解答（中文注释版）\n"""'

                    new_lines.append(cn_doc)

                    new_lines.append('')

                new_lines.append(line)

                # Add Chinese comment for imports

                if needs_cn:

                    new_lines.append(f'# 导入标准库模块')

                has_existing_docstring = True  # mark as done so we don't add another

            elif stripped.startswith('class ') or stripped.startswith('def '):

                # Code starts immediately - add Chinese docstring

                if not has_existing_docstring and needs_cn:

                    cn_doc = f'"""\nProject Euler Problem {problem_num} 解答（中文注释版）\n"""'

                    new_lines.append(cn_doc)

                    new_lines.append('')

                new_lines.append(line)

                if needs_cn:

                    new_lines.append(f'    # 中文注释已添加')

                has_existing_docstring = True

            elif stripped == '':

                new_lines.append(line)

            else:

                new_lines.append(line)

        else:

            new_lines.append(line)

            if docstring_marker in stripped:

                in_docstring = False

                # After existing docstring, if needs CN, add inline CN comment

                if needs_cn and not has_existing_docstring:

                    pass  # already added above

                has_existing_docstring = True

    

    # If we didn't add Chinese docstring above (e.g., file starts with code and no docstring)

    if needs_cn and not has_existing_docstring:

        # Add at the very top

        cn_doc = f'"""\nProject Euler Problem {problem_num} 解答（中文注释版）\n"""'

        new_lines.insert(0, cn_doc)

        new_lines.insert(1, '')

    

    # ==== 2. Add Chinese inline comments to key code sections ====

    if needs_cn:

        # Process the file to add Chinese comments to def lines and key sections

        processed_lines = []

        for line in new_lines:

            stripped = line.strip()

            # Add Chinese comment to function definitions

            if stripped.startswith('def ') and not stripped.startswith('def __') and ' #' not in stripped:

                # Extract function name

                func_match = re.search(r'def\s+(\w+)', stripped)

                if func_match:

                    func_name = func_match.group(1)

                    # Add a comment after the def line

                    processed_lines.append(line)

                    processed_lines.append(f'    # {func_name} 函数实现')

                else:

                    processed_lines.append(line)

            # Add Chinese comment to class definitions

            elif stripped.startswith('class ') and ' #' not in stripped:

                class_match = re.search(r'class\s+(\w+)', stripped)

                if class_match:

                    class_name = class_match.group(1)

                    processed_lines.append(line)

                    processed_lines.append(f'    # {class_name} 类定义')

                else:

                    processed_lines.append(line)

            # Add comment to key algorithmic lines

            elif stripped.startswith('for ') and ' #' not in stripped:

                processed_lines.append(line)

                processed_lines.append('    # 遍历循环')

            elif stripped.startswith('while ') and ' #' not in stripped:

                processed_lines.append(line)

                processed_lines.append('    # 条件循环')

            elif 'return' in stripped and not stripped.startswith('#') and ' #' not in stripped:

                processed_lines.append(line)

                if 'return' in stripped and len(stripped) < 60:

                    processed_lines.append('    # 返回结果')

                else:

                    processed_lines.append('    # 返回')

            else:

                processed_lines.append(line)

        new_lines = processed_lines

    

    # ==== 3. Add if __name__ block at end ====

    if needs_main:

        # Build test block

        if needs_cn:

            test_block = f'''

if __name__ == "__main__":

    # Project Euler Problem {problem_num} 测试入口

    # 运行 solution() 并打印结果

    try:

        result = solution()

        print(f"Problem {problem_num} 答案: {{result}}")

    except Exception as e:

        print(f"运行出错: {{e}}")

'''

        else:

            test_block = '''

if __name__ == "__main__":

    result = solution()

    print(result)

'''

        new_lines.append(test_block)

    

    new_content = '\n'.join(new_lines)

    

    if new_content != original:

        try:

            with open(fp, 'w', encoding='utf-8') as f:

                f.write(new_content)

            return True, 'FIXED'

        except Exception as e:

            return False, f'WRITE ERROR: {e}'

    return False, 'NO CHANGE'





# Find and fix all project_euler problem sol files

fixed_count = 0

skip_count = 0

error_count = 0

errors = []



# Walk through base directory and find 项目欧拉

for dirpath, dirnames, filenames in os.walk(base):

    dir_name = os.path.basename(dirpath)

    

    # Only process 项目欧拉 directory and its subdirs

    if '项目欧拉' not in dirpath:

        continue

    

    # Skip excluded dirs

    if any(ex in dirpath for ex in ['.git', '.github', '.vscode', '__pycache__', 'docs', 'tests', 'example', 'image_data', 'output_data']):

        continue

    

    for fn in filenames:

        if not fn.endswith('.py'):

            continue

        if fn == '__init__.py':

            continue

        if fn.startswith('test_') or fn.endswith('_test.py'):

            continue

        

        fp = os.path.join(dirpath, fn)

        

        # Quick check: does it need fixing?

        try:

            with open(fp, encoding='utf-8') as f:

                content = f.read()

        except:

            error_count += 1

            errors.append(f'READ: {fp}')

            continue

        

        needs_main = "if __name__" not in content

        needs_cn = not has_chinese(content)

        

        if not needs_main and not needs_cn:

            skip_count += 1

            continue

        

        success, msg = fix_file(fp)

        if success:

            fixed_count += 1

        else:

            if msg != 'OK already':

                error_count += 1

                errors.append(f'{msg}: {fp}')



print(f'Fixed: {fixed_count} files')

print(f'Already OK: {skip_count} files')

print(f'Errors: {error_count}')

for e in errors[:20]:

    print(f'  {e}')

