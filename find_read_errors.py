# -*- coding: utf-8 -*-

"""

算法实现：find_read_errors.py / find_read_errors



本文件实现 find_read_errors 相关的算法功能。

"""



# Find and fix READ_ERROR category files

import os

import codecs



base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'



read_error_files = [

    (r'07_贪婪算法', 'crossword_puzzle_solver.py'),

    (r'07_贪婪算法', 'fractional_knapsack_2.py'),

    (r'07_贪婪算法', 'generate_parentheses_iterative.py'),

    (r'07_贪婪算法', 'knight_tour.py'),

    (r'07_贪婪算法', 'match_word_pattern.py'),

    (r'07_贪婪算法', 'max_difference_pair.py'),

    (r'07_贪婪算法', 'mergesort.py'),

    (r'07_贪婪算法', 'n_queens_math.py'),

    (r'07_贪婪算法', 'power.py'),

    (r'07_贪婪算法', 'rat_in_maze.py'),

    (r'11_几何', 'geometry.py'),

]



for subdir, fn in read_error_files:

    fp = os.path.join(base, subdir, fn)

    print(f'Testing {subdir}/{fn}:')

    print(f'  Exists: {os.path.exists(fp)}')

    

    # Try different encodings

    for enc in ['utf-8', 'gbk', 'latin-1', 'cp1252']:

        try:

            with codecs.open(fp, 'r', encoding=enc) as f:

                content = f.read()

            print(f'  Read OK with {enc}, length={len(content)}')

            # Check if valid Python

            try:

                compile(content, fp, 'exec')

                print(f'  Compiles OK')

            except SyntaxError as e:

                print(f'  SyntaxError: {e}')

            break

        except Exception as e:

            print(f'  {enc} failed: {type(e).__name__}: {e}')





if __name__ == "__main__":

    # Test entry

    pass

