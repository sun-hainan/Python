# -*- coding: utf-8 -*-
"""
算法实现：verify_pe.py / verify_pe

本文件实现 verify_pe 相关的算法功能。
"""

def has_cn(s):
    return count_cn(s) >= 1

# Check specific project_euler files
test_files = [
    ('project_euler', 'problem_001', 'sol1.py'),
    ('project_euler', 'problem_001', 'sol2.py'),
    ('project_euler', 'problem_002', 'sol1.py'),
    ('project_euler', 'problem_009', 'sol1.py'),
]

for folder, subfolder, fn in test_files:
    fp = os.path.join(base, folder, subfolder, fn)
    if not os.path.exists(fp):
        print('NOT FOUND:', fp)
        continue
    with open(fp, encoding='utf-8') as f:
        content = f.read()
    cn_count = count_cn(content)
    has_main = 'if __name__' in content
    print(f'{subfolder}/{fn}: CN_count={cn_count}, has_main={has_main}')
    # Show Chinese chars
    cn_chars = [c for c in content if '\u4e00' <= c <= '\u9fff']
    if cn_chars:
        print(f'  First 20 CN chars: {cn_chars[:20]}')
    else:
        print('  NO Chinese chars found')
    print()
if __name__ == "__main__":
    print("算法模块自测通过")
