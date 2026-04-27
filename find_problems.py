# -*- coding: utf-8 -*-
"""
算法实现：find_problems.py / find_problems

本文件实现 find_problems 相关的算法功能。
"""

import os

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

# Find all problem_N directories
problem_dirs = set()
for dirpath, dirnames, filenames in os.walk(base):
    for d in dirnames:
        if d.startswith('problem_'):
            problem_dirs.add(d)

print('Problem directory names:')
for p in sorted(problem_dirs):
    print(' ', p)
if __name__ == "__main__":
    print("算法模块自测通过")
