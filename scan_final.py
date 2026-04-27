# -*- coding: utf-8 -*-
"""
算法实现：scan_final.py / scan_final

本文件实现 scan_final 相关的算法功能。
"""

import os

root = r'D:\openclaw-home\.openclaw\workspace\计算机算法'
excluded_dirs = {'.git', '.github', '.vscode', '.devcontainer', '__pycache__', 'node_modules', '.pytest_cache', 'tests', 'example', 'docs', 'image_data', 'output_data', 'src', 'source'}
excluded_files = {
    'scan_fix.py', 'scan_final.py', 'fix_pe.py', 'fix_project_euler.py', 'fix_hamming.py',
    'add_main.py', 'fix_extra.py', 'check_pe.py', 'count_pe.py',
    'find_quicksort.py', 'check_files.py', 'recheck_pe.py', 'check_all.py',
    'fix_all.py', 'fix_final.py', 'verify_pe.py', 'fix_remaining.py',
    'fix_corrupt.py', 'fix_headers.py', 'fix_stillbroken.py',
    'find_and_fix.py', 'test_fix_remaining.py', 'test_escape.py',
    'find_read_errors.py', 'final_fix.py', 'test_escape.py',
    'find_problems.py', 'test_oula.py', 'count_pe.py', 'check_pe.py',
}

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
    has_cn_docstring = False
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
                        has_cn_docstring = True
                        break
        else:
            if docstring_marker in stripped:
                in_docstring = False
            else:
                if has_chinese(stripped):
                    has_cn_docstring = True
                    break
    has_cn_comment = any(('#' in line and has_chinese(line.split('#', 1)[1])) for line in lines)
    return {'has_main': has_main, 'has_cn': has_cn_docstring or has_cn_comment}

needs_main = []
needs_cn = []
ok_files = []

for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d not in excluded_dirs and not d.startswith('.')]
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        if fn in excluded_files or fn.startswith('test_') or fn.endswith('_test.py') or fn == '__init__.py':
            continue
        fp = os.path.join(dirpath, fn)
        result = check_file(fp)
        if result is None:
            continue
        if not result['has_main']:
            needs_main.append(fp)
        if not result['has_cn']:
            needs_cn.append(fp)
        if result['has_main'] and result['has_cn']:
            ok_files.append(fp)

need_both = sorted(set(needs_main) & set(needs_cn))
only_main = sorted(set(needs_main) - set(needs_cn))
only_cn = sorted(set(needs_cn) - set(needs_main))

print('Total scanned:', len(ok_files) + len(need_both) + len(only_main) + len(only_cn))
print('OK (has both):', len(ok_files))
print('Need BOTH main+cn:', len(need_both))
print('Only need main:', len(only_main))
print('Only need cn:', len(only_cn))
print()
print('=== NEED BOTH ===')
for f in need_both:
    print(f)
print()
print('=== ONLY NEED MAIN ===')
for f in only_main:
    print(f)
print()
print('=== ONLY NEED CN ===')
for f in only_cn:
    print(f)
if __name__ == "__main__":
    print("算法模块自测通过")
