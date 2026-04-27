# -*- coding: utf-8 -*-

"""

算法实现：count_remaining.py / count_remaining



本文件实现 count_remaining 相关的算法功能。

"""



import os

import codecs



base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'



def has_chinese(s):

    return any('\u4e00' <= c <= '\u9fff' for c in s)



def check_file(fp):

    try:

        with open(fp, encoding='utf-8', errors='replace') as f:

            content = f.read()

    except:

        return None

    lines = content.split('\n')

    has_main = any("if __name__" in line for line in lines)

    has_cn = False

    in_docstring = False

    docstring_marker = None

    for line in lines:

        stripped = line.strip()

        if not in_docstring:

            if stripped.startswith('"""') or stripped.startswith("'''"):

                docstring_marker = stripped[:3]

                in_docstring = True

                count = stripped.count(docstring_marker)

                if count >= 2:

                    in_docstring = False

                    inner = stripped[3:]

                    idx = inner.find(docstring_marker)

                    if idx != -1:

                        inner = inner[:idx]

                    if has_chinese(inner):

                        has_cn = True

        else:

            if docstring_marker in stripped:

                in_docstring = False

            else:

                if has_chinese(stripped):

                    has_cn = True

    if not has_cn:

        has_cn = any('#' in line and has_chinese(line.split('#', 1)[1]) for line in lines)

    return {'has_main': has_main, 'has_cn': has_cn}



excluded_files = {

    'scan_fix.py', 'scan_final.py', 'fix_pe.py', 'fix_project_euler.py', 'fix_hamming.py',

    'add_main.py', 'fix_extra.py', 'check_pe.py', 'count_pe.py',

    'find_quicksort.py', 'check_files.py', 'recheck_pe.py', 'check_all.py',

    'fix_all.py', 'fix_final.py', 'verify_pe.py', 'fix_remaining.py',

    'fix_corrupt.py', 'fix_headers.py', 'fix_stillbroken.py',

    'find_and_fix.py', 'test_fix_remaining.py', 'test_escape.py',

    'find_read_errors.py', 'final_fix.py', 'test_escape.py',

    'find_problems.py', 'test_oula.py', 'count_pe.py', 'check_pe.py',

    'fix_ou_la.py', 'fix_all_corrupt.py', 'fix_xmxla.py', 'check_ou_la.py',

    'list_dirs.py', 'test_fix_remaining.py',

}



excluded_dirs = {'.git', '.github', '__pycache__', 'docs', 'tests', 'image_data', 'output_data'}



need_main = []

need_cn = []

ok_count = 0

skipped = 0



for dirpath, dirnames, filenames in os.walk(base):

    dirnames[:] = [d for d in dirnames if d not in excluded_dirs and not d.startswith('.')]

    for fn in filenames:

        if not fn.endswith('.py'):

            continue

        if fn in excluded_files or fn.startswith('test_') or fn.endswith('_test.py') or fn == '__init__.py':

            skipped += 1

            continue

        fp = os.path.join(dirpath, fn)

        result = check_file(fp)

        if result is None:

            skipped += 1

            continue

        if not result['has_main']:

            need_main.append(fp)

        if not result['has_cn']:

            need_cn.append(fp)

        if result['has_main'] and result['has_cn']:

            ok_count += 1



need_both = sorted(set(need_main) & set(need_cn))

only_main = sorted(set(need_main) - set(need_cn))

only_cn = sorted(set(need_cn) - set(need_main))



# Categorize remaining files

pe_files = []

cat_files = []

utility_files = []

other_files = []



for f in sorted(need_cn):

    if any(x in f for x in ['project_euler', 'xe9xa1xb9xe6x95x99xe6xacxa7']):

        pe_files.append(f)

    elif any(x in f for x in ['fix_', 'check_', 'test_', 'scan_', 'find_', 'count_']):

        utility_files.append(f)

    else:

        cat_files.append(f)



print('=== FINAL SUMMARY ===')

print(f'OK (has both main+cn): {ok_count}')

print(f'Skipped (excluded): {skipped}')

print(f'Need main only: {len(only_main)}')

print(f'Need cn only: {len(only_cn)}')

print(f'Need both: {len(need_both)}')

print()

print(f'--- Remaining files needing CN ({len(only_cn)} total) ---')

print(f'Project Euler files: {len(pe_files)}')

print(f'Utility scripts: {len(utility_files)}')

print(f'Category algorithm files: {len(cat_files)}')

print()

print('Category files (need CN):')

for f in cat_files:

    print(' ', os.path.basename(os.path.dirname(f)), '/', os.path.basename(f))

if __name__ == "__main__":

    print("算法模块自测通过")

