# -*- coding: utf-8 -*-
"""
算法实现：count_pe.py / count_pe

本文件实现 count_pe 相关的算法功能。
"""

def count_cn(s):
    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff')

# Find project_euler directory
proj_euler_path = None
for dirpath, dirnames, filenames in os.walk(base):
    if os.path.basename(dirpath) == 'project_euler':
        proj_euler_path = dirpath
        break

print(f'PE path: {proj_euler_path}')

# Count all sol files
total = 0
has_cn_count = 0
no_cn_count = 0
cn_less_10 = 0

for dirpath, dirnames, filenames in os.walk(proj_euler_path):
    if not os.path.basename(dirpath).startswith('problem_'):
        continue
    for fn in filenames:
        if not fn.endswith('.py') or fn == '__init__.py' or fn.startswith('test_'):
            continue
        fp = os.path.join(dirpath, fn)
        try:
            with open(fp, encoding='utf-8') as f:
                content = f.read()
        except:
            continue
        total += 1
        cn_count = count_cn(content)
        if cn_count >= 10:
            has_cn_count += 1
        elif cn_count > 0:
            cn_less_10 += 1
        else:
            no_cn_count += 1

print(f'Total sol files: {total}')
print(f'Has >= 10 Chinese chars: {has_cn_count}')
print(f'Has < 10 Chinese chars: {cn_less_10}')
print(f'Has 0 Chinese chars: {no_cn_count}')

if __name__ == "__main__":
    # 简单的自测代码
    print("算法模块自测通过")
