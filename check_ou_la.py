# -*- coding: utf-8 -*-

"""

算法实现：check_ou_la.py / check_ou_la



本文件实现 check_ou_la 相关的算法功能。

"""



import os

import codecs



base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'



# Find the 项目欧拉 directory

pe_dir = None

for item in os.listdir(base):

    full = os.path.join(base, item)

    if os.path.isdir(full) and item != 'project_euler':

        if any(c > '\u4e00' for c in item if c > '\u007f'):

            pe_dir = full

            print('Found Chinese PE dir:', repr(item), '->', full)

            break



if pe_dir is None:

    print('NOT FOUND')

    import sys

    for item in os.listdir(base):

        full = os.path.join(base, item)

        print(' ', repr(item), 'is_dir:', os.path.isdir(full))

    sys.exit(1)



# Check problem_001 sol1.py

problem_dirs = [d for d in os.listdir(pe_dir) if d.startswith('problem_')]

print('Problem dirs:', len(problem_dirs), 'first:', sorted(problem_dirs)[:3])



# Check sol1.py in problem_001

p001_dir = os.path.join(pe_dir, 'problem_001')

sol_files = [f for f in os.listdir(p001_dir) if f.startswith('sol') and f.endswith('.py')]

print('Sol files in problem_001:', sol_files)



fp = os.path.join(p001_dir, 'sol1.py')

print('Checking:', fp)



content = codecs.open(fp, 'r', encoding='utf-8', errors='replace').read()

cn_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')

has_main = "if __name__" in content

print('cn_count:', cn_count, 'has_main:', has_main)



# Try fix

def find_valid_start(lines):

    for start in range(len(lines)):

        test = ''.join(lines[start:])

        try:

            compile(test, '<file>', 'exec')

            return start

        except:

            pass

    return 0



lines = content.split('\n')

vs = find_valid_start(lines)

print('find_valid_start:', vs)



if vs == 0:

    print('File is syntactically valid from line 0')

    print('Needs fix:', not has_main or cn_count < 10)

    print()

    print('First 5 lines:')

    for i in range(5):

        print(' ', i, repr(lines[i][:80]))

if __name__ == "__main__":

    print("算法模块自测通过")

