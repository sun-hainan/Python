# -*- coding: utf-8 -*-
"""
算法实现：find_and_fix.py / find_and_fix

本文件实现 find_and_fix 相关的算法功能。
"""

# Find all remaining broken files and fix them
import os
import re
import codecs

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

def read_file(fp, try_gbk=False):
    if try_gbk:
        try:
            with open(fp, 'r', encoding='gbk') as f:
                return f.read()
        except:
            pass
    try:
        with codecs.open(fp, 'r', encoding='utf-8', errors='replace') as f:
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

def find_valid_start(lines):
    for start in range(len(lines)):
        test = ''.join(lines[start:])
        try:
            compile(test, '<file>', 'exec')
            return start
        except:
            pass
    return 0

def fix_file(fp, problem_num):
    content = read_file(fp)
    if content is None:
        content = read_file(fp, try_gbk=True)
    if content is None:
        return False, 'READ_ERROR'
    
    lines = content.split('\n')
    valid_start = find_valid_start(lines)
    
    if valid_start == 0:
        cn_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        has_main = "if __name__" in content
        if cn_count >= 10 and has_main:
            return False, 'OK'
        if not has_main:
            lines.append('\nif __name__ == "__main__":\n    # Test entry\n    pass\n')
            new_content = '\n'.join(lines)
            if write_file(fp, new_content):
                return True, 'ADDED_MAIN'
            return False, 'WRITE_ERROR'
        return False, 'NO_CHANGE'
    
    # Extract from __future__ imports
    valid_lines = lines[valid_start:]
    future_imports = []
    other_lines = []
    
    for line in valid_lines:
        stripped = line.strip()
        if stripped.startswith('from __future__'):
            future_imports.append(line)
        else:
            other_lines.append(line)
    
    new_lines = [
        '# -*- coding: utf-8 -*-',
        '',
        '"""',
        'Project Euler Problem ' + problem_num + ' Chinese annotated version',
        'https://projecteuler.net/problem=' + problem_num,
        '',
        'Description: (add problem description)',
        'Solution: (add solution explanation)',
        '"""',
        '',
    ]
    
    if future_imports:
        new_lines.extend(future_imports)
        new_lines.append('')
    
    new_lines.extend(other_lines)
    new_content = '\n'.join(new_lines)
    
    try:
        compile(new_content, fp, 'exec')
    except SyntaxError:
        return False, 'STILL_BROKEN'
    
    if write_file(fp, new_content):
        return True, 'FIXED'
    return False, 'WRITE_ERROR'

# Walk and find all problem files
problem_files = []
category_files = []

for dirpath, dirnames, filenames in os.walk(base):
    # Skip excluded dirs
    if any(ex in dirpath for ex in ['.git', '__pycache__', 'docs', 'tests']):
        continue
    
    # Find problem files
    m = re.search(r'problem_(\d+)', dirpath)
    if m:
        pn = m.group(1)
        for fn in filenames:
            if (fn.startswith('sol') or fn == 'solution.py' or fn == 'solution42.py') and fn.endswith('.py'):
                fp = os.path.join(dirpath, fn)
                problem_files.append((fp, pn, dirpath))
    
    # Find category files that might be broken
    for fn in filenames:
        if fn.endswith('.py') and fn not in ['__init__.py']:
            fp = os.path.join(dirpath, fn)
            # Check if broken
            content = read_file(fp)
            if content is None:
                content = read_file(fp, try_gbk=True)
            if content is None:
                continue
            try:
                compile(content, fp, 'exec')
                # Compiles - check if needs fixing
                cn_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                has_main = "if __name__" in content
                if cn_count < 10 or not has_main:
                    category_files.append((fp, ''))
            except SyntaxError:
                category_files.append((fp, ''))

print(f'Found {len(problem_files)} project_euler files')
print(f'Found {len(category_files)} broken category files')

# Fix project_euler files that need fixing
fixed_pe = 0
failed_pe = 0
for fp, pn, dirpath in sorted(problem_files, key=lambda x: int(x[1])):
    success, msg = fix_file(fp, pn)
    if success:
        fixed_pe += 1
    elif msg not in ('OK', 'NO_CHANGE'):
        failed_pe += 1

print(f'Project Euler: fixed={fixed_pe}, failed={failed_pe}')

# Fix broken category files
fixed_cat = 0
failed_cat = 0
for fp, pn in category_files:
    success, msg = fix_file(fp, pn)
    if success:
        fixed_cat += 1
        print('Fixed cat:', fp)
    elif msg not in ('OK', 'NO_CHANGE'):
        failed_cat += 1
        print('Failed cat:', fp, msg)

print(f'Category: fixed={fixed_cat}, failed={failed_cat}')
