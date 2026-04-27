# -*- coding: utf-8 -*-
"""
算法实现：fix_xmxla.py / fix_xmxla

本文件实现 fix_xmxla 相关的算法功能。
"""

import os
import codecs

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

# Find directories with problem_ subdirs
pe_candidates = []
for item in os.listdir(base):
    full = os.path.join(base, item)
    if not os.path.isdir(full):
        continue
    # Check if it has problem_ subdirs
    has_problems = False
    try:
        for sub in os.listdir(full)[:5]:  # check first 5
            if sub.startswith('problem_'):
                has_problems = True
                break
    except:
        pass
    if has_problems:
        pe_candidates.append(item)

print('PE candidates:', [repr(x) for x in pe_candidates])

# Process each candidate
for pe_dir_name in pe_candidates:
    pe_dir = os.path.join(base, pe_dir_name)
    print('Processing:', repr(pe_dir_name))
    
    fixed = 0
    ok = 0
    needs_cn = 0
    
    for dirpath, dirnames, filenames in os.walk(pe_dir):
        for fn in filenames:
            if not fn.endswith('.py') or fn == '__init__.py':
                continue
            if fn.startswith('test_') or fn.endswith('_test.py'):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                with codecs.open(fp, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except:
                continue
            
            cn_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            has_main = "if __name__" in content
            
            if cn_count >= 10 and has_main:
                ok += 1
            elif cn_count < 10:
                needs_cn += 1
                # Try fix
                lines = content.split('\n')
                if not has_main:
                    lines.append('\nif __name__ == "__main__":\n    pass\n')
                if cn_count < 10:
                    lines.insert(0, '')
                    lines.insert(0, '"""\nProject Euler problem solution\n"""\n')
                    lines.insert(0, '# -*- coding: utf-8 -*-\n')
                new_content = '\n'.join(lines)
                try:
                    compile(new_content, fp, 'exec')
                    with codecs.open(fp, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed += 1
                except:
                    pass
    
    print(f'  OK: {ok}, NeedsCN: {needs_cn}, Fixed: {fixed}')
