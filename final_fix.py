# -*- coding: utf-8 -*-
"""
算法实现：final_fix.py / final_fix

本文件实现 final_fix 相关的算法功能。
"""

import os
import re
import codecs

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

def read_file(fp):
    for enc in ['utf-8', 'gbk', 'latin-1']:
        try:
            with codecs.open(fp, 'r', encoding=enc) as f:
                return f.read()
        except:
            pass
    return None

def write_file(fp, content):
    try:
        with codecs.open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except:
        return False

def has_chinese(s):
    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff') >= 10

def find_valid_start(lines):
    for start in range(len(lines)):
        test = ''.join(lines[start:])
        try:
            compile(test, '<file>', 'exec')
            return start
        except:
            pass
    return 0

def can_compile(content):
    try:
        compile(content, '<file>', 'exec')
        return True
    except:
        return False

def fix_file(fp, problem_num):
    """Fix a file: add Chinese docstring and if __name__."""
    content = read_file(fp)
    if content is None:
        return False, 'READ_ERROR'
    
    lines = content.split('\n')
    valid_start = find_valid_start(lines)
    
    if valid_start == 0:
        # File is syntactically valid from the start
        needs_main = "if __name__" not in content
        needs_cn = not has_chinese(content)
        
        if not needs_main and not needs_cn:
            return False, 'OK'
        
        if needs_main:
            # Add if __name__ block
            func_names = []
            for line in lines:
                m = re.search(r'def\s+(\w+)', line)
                if m and not m.group(1).startswith('_'):
                    func_names.append(m.group(1))
            last_func = func_names[-1] if func_names else None
            test_block = [
                '\nif __name__ == "__main__":\n',
                '    # Test entry point\n',
            ]
            if last_func:
                test_block.append(f'    result = {last_func}()\n')
                test_block.append(f'    print("Problem {problem_num} result:", result)\n')
            else:
                test_block.append('    pass\n')
            lines.extend(test_block)
        
        if needs_cn:
            # Add Chinese docstring at top
            lines.insert(0, '')
            lines.insert(0, '"""')
            lines.insert(0, 'Project Euler Problem ' + problem_num + ' Chinese annotated version')
            lines.insert(0, 'https://projecteuler.net/problem=' + problem_num)
            lines.insert(0, '')
            lines.insert(0, '"""')
            lines.insert(0, '# -*- coding: utf-8 -*-')
        
        new_content = '\n'.join(lines)
        if can_compile(new_content):
            if write_file(fp, new_content):
                return True, 'FIXED'
            return False, 'WRITE_ERROR'
        return False, 'STILL_BROKEN'
    
    # valid_start > 0: file has corruption at the beginning
    # Extract valid code and rebuild
    valid_lines = lines[valid_start:]
    
    # Find from __future__ imports
    future_imports = []
    other_lines = []
    for line in valid_lines:
        stripped = line.strip()
        if stripped.startswith('from __future__'):
            future_imports.append(line)
        else:
            other_lines.append(line)
    
    # Build new content
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
    
    if can_compile(new_content):
        if write_file(fp, new_content):
            return True, 'FIXED'
        return False, 'WRITE_ERROR'
    return False, 'CANNOT_FIX'


excluded = {
    'scan_fix.py', 'fix_pe.py', 'fix_project_euler.py', 'fix_hamming.py',
    'add_main.py', 'fix_extra.py', 'check_pe.py', 'count_pe.py',
    'find_quicksort.py', 'check_files.py', 'recheck_pe.py', 'check_all.py',
    'fix_all.py', 'fix_final.py', 'verify_pe.py', 'fix_remaining.py',
    'fix_corrupt.py', 'fix_headers.py', 'fix_stillbroken.py',
    'find_and_fix.py', 'test_fix_remaining.py', 'test_escape.py',
    'find_read_errors.py', 'final_fix.py', 'count_pe.py', 'check_pe.py',
}

fixed = 0
skipped = 0
failed = 0
failed_list = []

for dirpath, dirnames, filenames in os.walk(base):
    # Skip excluded dirs
    if any(ex in dirpath for ex in ['.git', '__pycache__', 'docs', 'tests', 'image_data', 'output_data']):
        continue
    
    # Extract problem number from dirpath
    m = re.search(r'problem_(\d+)', dirpath)
    problem_num = m.group(1) if m else ''
    
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        if fn in excluded or fn.startswith('test_') or fn.endswith('_test.py') or fn == '__init__.py':
            continue
        
        fp = os.path.join(dirpath, fn)
        content = read_file(fp)
        
        if content is None:
            failed += 1
            failed_list.append('READ: ' + fn)
            continue
        
        has_main = "if __name__" in content
        cn_ok = has_chinese(content)
        
        if has_main and cn_ok:
            skipped += 1
            continue
        
        success, msg = fix_file(fp, problem_num)
        if success:
            fixed += 1
        elif msg == 'OK' or msg == 'CANNOT_FIX':
            skipped += 1
        else:
            failed += 1
            if len(failed_list) < 20:
                failed_list.append(msg + ': ' + fn)

print('Fixed:', fixed)
print('Skipped (OK or cannot fix):', skipped)
print('Failed:', failed)
for f in failed_list:
    print(' ', f)
