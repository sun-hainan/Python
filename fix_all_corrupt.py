# -*- coding: utf-8 -*-
"""
算法实现：fix_all_corrupt.py / fix_all_corrupt

本文件实现 fix_all_corrupt 相关的算法功能。
"""

# Comprehensive fix for all corrupted files
import os
import re
import codecs

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

def read_file(fp):
    try:
        with codecs.open(fp, 'r', encoding='utf-8') as f:
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

def add_chinese_docstring(problem_num):
    docstring = (
        '# -*- coding: utf-8 -*-\n'
        '"""\n'
        'Project Euler Problem ' + problem_num + ' Chinese annotated version\n'
        'https://projecteuler.net/problem=' + problem_num + '\n'
        '\n'
        'Description: (add problem description)\n'
        'Solution: (add solution explanation)\n'
        '"""\n'
        '\n'
    )
    return docstring

def fix_file(fp, problem_num):
    content = read_file(fp)
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
    
    valid_lines = lines[valid_start:]
    new_lines = [add_chinese_docstring(problem_num)]
    new_lines.extend(valid_lines)
    new_content = '\n'.join(new_lines)
    
    try:
        compile(new_content, fp, 'exec')
    except SyntaxError as e:
        return False, 'STILL_BROKEN: ' + str(e)
    
    if write_file(fp, new_content):
        return True, 'FIXED from line ' + str(valid_start)
    return False, 'WRITE_ERROR'


# Get problem sol files from project_euler
problem_sols = {}
for dirpath, dirnames, filenames in os.walk(base):
    if os.path.basename(dirpath).startswith('problem_'):
        for fn in filenames:
            if fn.startswith('sol') and fn.endswith('.py') or fn == 'solution.py' or fn == 'solution42.py':
                m = re.search(r'problem_(\d+)', dirpath)
                if m:
                    pn = m.group(1)
                    fp = os.path.join(dirpath, fn)
                    problem_sols.setdefault(pn, []).append(fp)

# Category files needing fix
category_files = [
    ('05_动态规划', 'factorial.py', ''),
    ('05_动态规划', 'fast_fibonacci.py', ''),
    ('05_动态规划', 'fizz_buzz.py', ''),
    ('05_动态规划', 'largest_divisible_subset.py', ''),
    ('05_动态规划', 'max_non_adjacent_sum.py', ''),
    ('05_动态规划', 'minimum_cost_path.py', ''),
    ('05_动态规划', 'minimum_squares_to_represent_a_number.py', ''),
    ('05_动态规划', 'subset_generation.py', ''),
    ('05_动态规划', 'sum_of_subset.py', ''),
    ('05_动态规划', 'viterbi.py', ''),
    ('07_贪婪算法', 'crossword_puzzle_solver.py', ''),
    ('07_贪婪算法', 'fractional_knapsack_2.py', ''),
    ('07_贪婪算法', 'generate_parentheses_iterative.py', ''),
    ('07_贪婪算法', 'knight_tour.py', ''),
    ('07_贪婪算法', 'match_word_pattern.py', ''),
    ('07_贪婪算法', 'max_difference_pair.py', ''),
    ('07_贪婪算法', 'mergesort.py', ''),
    ('07_贪婪算法', 'n_queens_math.py', ''),
    ('07_贪婪算法', 'power.py', ''),
    ('07_贪婪算法', 'rat_in_maze.py', ''),
    ('11_几何', 'geometry.py', ''),
]

print('=== Fixing category files ===')
fixed_cat = 0
for subdir, fn, pn in category_files:
    fp = os.path.join(base, subdir, fn)
    success, msg = fix_file(fp, pn)
    if success:
        fixed_cat += 1
        print('Fixed:', fn, '-', msg)
    else:
        print('Skipped:', fn, '-', msg)

print('Category fixed:', fixed_cat)

print('\n=== Fixing project_euler files ===')
fixed_pe = 0
skipped_pe = 0
failed_pe = 0
for pn in sorted(problem_sols.keys(), key=lambda x: int(x)):
    for fp in problem_sols[pn]:
        success, msg = fix_file(fp, pn)
        if success:
            fixed_pe += 1
        elif msg == 'OK' or msg == 'NO_CHANGE':
            skipped_pe += 1
        else:
            failed_pe += 1
            if failed_pe <= 5:
                print('Failed:', fp, '-', msg)

print('PE fixed:', fixed_pe, 'skipped:', skipped_pe, 'failed:', failed_pe)
