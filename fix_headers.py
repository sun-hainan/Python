# -*- coding: utf-8 -*-

"""

算法实现：fix_headers.py / fix_headers



本文件实现 fix_headers 相关的算法功能。

"""



# Fix corrupted files - remove broken header with improper indentation

import os

import re

import codecs



base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'



def read_file(fp):

    try:

        with codecs.open(fp, 'r', encoding='utf-8') as f:

            return f.read()

    except:

        return None



def write_file(fp, content):

    try:

        with codecs.open(fp, 'w', encoding='utf-8') as f:

            f.write(content)

        return True

    except:

        return False



def try_import(fp, mod_name):

    import importlib.util

    spec = importlib.util.spec_from_file_location(mod_name, fp)

    if spec and spec.loader:

        mod = importlib.util.module_from_spec(spec)

        try:

            spec.loader.exec_module(mod)

            return mod

        except Exception as e:

            return None

    return None



def fix_file_v2(fp):

    content = read_file(fp)

    if content is None:

        return False

    

    lines = content.split('\n')

    

    # Strategy: find the FIRST valid Python code line (import/def/class/@)

    # Then find any orphaned docstring before it

    # Remove everything before the FIRST import or the actual code

    

    first_code_idx = None

    for i, line in enumerate(lines):

        stripped = line.strip()

        if stripped.startswith(('from ', 'import ', 'def ', 'class ', '@')):

            first_code_idx = i

            break

    

    if first_code_idx is None:

        return False

    

    # Check if there's a broken docstring header

    # Look for lines before first_code_idx that start with spaces

    new_lines = []

    skip_until = -1

    

    for i, line in enumerate(lines):

        if i < skip_until:

            continue

        

        stripped = line.strip()

        

        # If this is before first code, check if it's part of broken header

        if i < first_code_idx:

            # Check if line starts with spaces (indented at module level = broken)

            if line.startswith(' ') and stripped:

                # Find the extent of the broken header

                j = i

                while j < first_code_idx and (lines[j].startswith(' ') or not lines[j].strip()):

                    j += 1

                skip_until = j

                continue

            else:

                new_lines.append(line)

        else:

            new_lines.append(line)

    

    new_content = '\n'.join(new_lines)

    

    # Try compiling

    try:

        compile(new_content, fp, 'exec')

    except SyntaxError as e:

        # Try even more aggressive cleanup

        new_lines2 = []

        for i, line in enumerate(lines):

            stripped = line.strip()

            if stripped.startswith(('from ', 'import ', 'def ', 'class ', '@')):

                # Start from here

                new_lines2 = lines[i:]

                break

        new_content2 = '\n'.join(new_lines2)

        try:

            compile(new_content2, fp, 'exec')

            new_content = new_content2

        except:

            return False

    

    # Try importing

    mod = try_import(fp, 'temp_mod')

    if mod is None:

        return False

    

    if write_file(fp, new_content):

        return True

    return False





# Test with factorial.py

fp = os.path.join(base, '05_动态规划', 'factorial.py')

print('Testing factorial.py...')

print('Before fix:')

try:

    compile(read_file(fp), fp, 'exec')

    print('  Compiles OK')

except SyntaxError as e:

    print('  SyntaxError:', e)



success = fix_file_v2(fp)

print('Fix result:', success)



if success:

    print('After fix:')

    try:

        compile(read_file(fp), fp, 'exec')

        print('  Compiles OK')

    except SyntaxError as e:

        print('  SyntaxError:', e)

    

    # Try importing

    mod = try_import(fp, 'factorial')

    if mod:

        print('  Import OK, factorial(5)=', mod.factorial(5))

    else:

        print('  Import FAILED')





if __name__ == "__main__":

    # Test entry

    pass

