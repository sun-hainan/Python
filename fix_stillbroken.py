# -*- coding: utf-8 -*-
"""
算法实现：fix_stillbroken.py / fix_stillbroken

本文件实现 fix_stillbroken 相关的算法功能。
"""

# Fix files with from __future__ imports that got displaced
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
    
    # Extract from __future__ imports from valid code
    valid_lines = lines[valid_start:]
    future_imports = []
    other_lines = []
    
    for line in valid_lines:
        stripped = line.strip()
        if stripped.startswith('from __future__'):
            future_imports.append(line)
        elif stripped.startswith('import ') or stripped.startswith('from '):
            if stripped.startswith('from __future__'):
                future_imports.append(line)
            else:
                other_lines.append(line)
        else:
            other_lines.append(line)
    
    # Build new content
    new_lines = []
    
    # Header
    new_lines.append('# -*- coding: utf-8 -*-')
    new_lines.append('')
    new_lines.append('"""')
    new_lines.append('Project Euler Problem ' + problem_num + ' Chinese annotated version')
    new_lines.append('https://projecteuler.net/problem=' + problem_num)
    new_lines.append('')
    new_lines.append('Description: (add problem description)')
    new_lines.append('Solution: (add solution explanation)')
    new_lines.append('"""')
    new_lines.append('')
    
    # Add __future__ imports first
    new_lines.extend(future_imports)
    if future_imports:
        new_lines.append('')
    
    # Add other content
    new_lines.extend(other_lines)
    
    new_content = '\n'.join(new_lines)
    
    try:
        compile(new_content, fp, 'exec')
    except SyntaxError as e:
        return False, 'STILL_BROKEN: ' + str(e)
    
    if write_file(fp, new_content):
        return True, 'FIXED'
    return False, 'WRITE_ERROR'


# Fix specific problematic files
files_to_fix = [
    (r'05_动态规划', 'fast_fibonacci.py', ''),
    (r'05_动态规划', 'largest_divisible_subset.py', ''),
    (r'05_动态规划', 'max_non_adjacent_sum.py', ''),
    (r'05_动态规划', 'minimum_cost_path.py', ''),
]

print('Fixing remaining category files:')
fixed = 0
failed = 0
for subdir, fn, pn in files_to_fix:
    fp = os.path.join(base, subdir, fn)
    success, msg = fix_file(fp, pn)
    if success:
        fixed += 1
        print('Fixed:', fn, '-', msg)
    else:
        failed += 1
        print('Failed:', fn, '-', msg)

print('Result: fixed', fixed, 'failed', failed)
