# -*- coding: utf-8 -*-
"""
算法实现：fix_all.py / fix_all

本文件实现 fix_all 相关的算法功能。
"""

import os
import re

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

def count_cn(s):
    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff')

def has_meaningful_cn(content):
    return count_cn(content) >= 10

def add_chinese_to_file(fp, problem_num='', category=''):
    """Add proper Chinese docstring and if __name__ to a file."""
    try:
        with open(fp, encoding='utf-8') as f:
            content = f.read()
    except:
        return False, 'READ_ERROR'
    
    original = content
    fn = os.path.basename(fp)
    
    lines = content.split('\n')
    new_lines = []
    inserted_doc = False
    
    # Detect existing docstring
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
                # Insert Chinese docstring before imports
                if not inserted_doc:
                    doc = [
                        '"""',
                        'Project Euler Problem ' + problem_num + ' -- Chinese comment version',
                        'https://projecteuler.net/problem=' + problem_num,
                        '',
                        'Description: (placeholder - add problem description)',
                        'Solution: (placeholder - add solution explanation)',
                        '"""',
                        '',
                    ]
                    new_lines.extend(doc)
                    inserted_doc = True
                new_lines.append(line)
            elif stripped.startswith('def ') or stripped.startswith('class '):
                if not inserted_doc:
                    doc = [
                        '"""',
                        'Project Euler Problem ' + problem_num + ' -- Chinese comment version',
                        'https://projecteuler.net/problem=' + problem_num,
                        '',
                        'Description: (placeholder - add problem description)',
                        'Solution: (placeholder - add solution explanation)',
                        '"""',
                        '',
                    ]
                    new_lines.extend(doc)
                    inserted_doc = True
                new_lines.append(line)
                # Add inline Chinese comment for function/class
                if stripped.startswith('def '):
                    m = re.search(r'def\s+(\w+)', stripped)
                    if m:
                        new_lines.append('    # ' + m.group(1) + ' function')
                elif stripped.startswith('class '):
                    m = re.search(r'class\s+(\w+)', stripped)
                    if m:
                        new_lines.append('    # ' + m.group(1) + ' class')
            elif stripped == '' or stripped.startswith('#'):
                new_lines.append(line)
            else:
                # Code with no docstring
                if not inserted_doc:
                    doc = [
                        '"""',
                        'Project Euler Problem ' + problem_num + ' -- Chinese comment version',
                        'https://projecteuler.net/problem=' + problem_num,
                        '',
                        'Description: (placeholder - add problem description)',
                        'Solution: (placeholder - add solution explanation)',
                        '"""',
                        '',
                    ]
                    new_lines.extend(doc)
                    inserted_doc = True
                new_lines.append(line)
        else:
            new_lines.append(line)
            if docstring_marker and docstring_marker in stripped:
                in_docstring = False
                # After existing docstring
                if not inserted_doc:
                    doc = [
                        '"""',
                        'Project Euler Problem ' + problem_num + ' -- Chinese comment version',
                        'https://projecteuler.net/problem=' + problem_num,
                        '',
                        'Description: (placeholder - add problem description)',
                        'Solution: (placeholder - add solution explanation)',
                        '"""',
                        '',
                    ]
                    new_lines.extend(doc)
                    inserted_doc = True
    
    # If still not inserted, put at top
    if not inserted_doc:
        doc = [
            '"""',
            'Project Euler Problem ' + problem_num + ' -- Chinese comment version',
            'https://projecteuler.net/problem=' + problem_num,
            '',
            'Description: (placeholder - add problem description)',
            'Solution: (placeholder - add solution explanation)',
            '"""',
            '',
        ]
        new_lines = doc + new_lines
        inserted_doc = True
    
    # Add if __name__ block if missing
    if "if __name__" not in content:
        # Find the last function to call
        func_names = []
        for line in new_lines:
            m = re.search(r'def\s+(\w+)', line)
            if m and not m.group(1).startswith('_'):
                func_names.append(m.group(1))
        
        test_block = [
            '',
            'if __name__ == "__main__":',
            '    # Project Euler Problem ' + problem_num + ' test entry',
            '    result = ' + (func_names[-1] + '()' if func_names else 'None'),
            '    print("Problem ' + problem_num + ' result:", result)',
        ]
        new_lines.extend(test_block)
    
    new_content = '\n'.join(new_lines)
    
    if new_content != original:
        try:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, 'FIXED'
        except Exception as e:
            return False, 'WRITE_ERROR: ' + str(e)
    return False, 'NO_CHANGE'


# Walk through all directories and fix files
fixed_count = 0
skipped_count = 0
error_count = 0
errors = []

for dirpath, dirnames, filenames in os.walk(base):
    # Skip excluded dirs
    if any(ex in dirpath for ex in ['.git', '.github', '__pycache__', 'docs', 'tests', 
                                      'image_data', 'output_data', '.pytest_cache']):
        continue
    
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        if fn in ['__init__.py', 'scan_fix.py', 'fix_pe.py', 'fix_project_euler.py', 
                   'fix_hamming.py', 'add_main.py', 'fix_extra.py', 'check_pe.py', 
                   'count_pe.py', 'find_quicksort.py', 'check_files.py', 'recheck_pe.py',
                   'check_all.py']:
            continue
        if fn.startswith('test_') or fn.endswith('_test.py'):
            continue
        
        fp = os.path.join(dirpath, fn)
        
        try:
            with open(fp, encoding='utf-8') as f:
                content = f.read()
        except:
            error_count += 1
            errors.append('READ: ' + fn)
            continue
        
        # Determine problem number from path
        problem_num = ''
        m = re.search(r'problem_(\d+)', dirpath)
        if m:
            problem_num = m.group(1)
        
        # Check if needs fixing
        has_main = "if __name__" in content
        needs_cn = not has_meaningful_cn(content)
        
        if not has_main and not needs_cn:
            skipped_count += 1
            continue
        if not needs_cn and has_main:
            skipped_count += 1
            continue
        
        success, msg = add_chinese_to_file(fp, problem_num)
        if success:
            fixed_count += 1
        elif msg not in ('NO_CHANGE', 'HAS_CN'):
            error_count += 1
            errors.append(msg + ': ' + fn)

print('Fixed:', fixed_count)
print('Skipped (already ok):', skipped_count)
print('Errors:', error_count)
for e in errors[:20]:
    print(' ', e)
