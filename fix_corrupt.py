# -*- coding: utf-8 -*-

"""

算法实现：fix_corrupt.py / fix_corrupt



本文件实现 fix_corrupt 相关的算法功能。

"""



# Fix corrupted files - remove improperly indented header lines

import os

import re

import codecs



base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'



def read_file(fp):

    try:

        with codecs.open(fp, 'r', encoding='utf-8') as f:

            return f.read()

    except:

        try:

            with open(fp, 'r', encoding='utf-8', errors='replace') as f:

                return f.read()

        except:

            return None



def write_file(fp, content):

    try:

        with codecs.open(fp, 'w', encoding='utf-8') as f:

            f.write(content)

        return True

    except:

        try:

            with open(fp, 'w', encoding='utf-8', errors='replace') as f:

                f.write(content)

            return True

        except:

            return False



def try_exec(content, fp):

    """Try to compile and exec the content. Returns True if successful."""

    try:

        exec(compile(content, fp, 'exec'), {})

        return True

    except:

        return False



CORRUPT_PATTERNS = [

    # Pattern: lines at the top that start with spaces followed by Chinese or ASCII markers

    # Lines that look like "  - comment" at module level

]



def fix_corrupt_file(fp):

    content = read_file(fp)

    if content is None:

        return False, 'READ_ERROR'

    

    lines = content.split('\n')

    

    # Check if file is syntactically valid

    if try_exec(content, fp):

        return False, 'ALREADY_VALID'

    

    # Try to find and remove corrupted header lines

    # Pattern: module-level lines starting with spaces followed by markers like "  - " or "  # "

    new_lines = []

    in_docstring = False

    docstring_marker = None

    removed_header = False

    

    for i, line in enumerate(lines):

        stripped = line.strip()

        

        # Handle docstrings

        if not in_docstring:

            if stripped.startswith('"""') or stripped.startswith("'''"):

                docstring_marker = stripped[:3]

                in_docstring = True

                new_lines.append(line)

            elif stripped == '':

                new_lines.append(line)

            elif stripped.startswith('#'):

                # Regular comment - keep it

                new_lines.append(line)

            elif not stripped.startswith('from ') and not stripped.startswith('import '):

                if not stripped.startswith('def ') and not stripped.startswith('class '):

                    # This is a suspicious line at module level - check if it starts with spaces

                    if line.startswith(' ') and stripped and not removed_header:

                        # This is a corrupted header line - skip it

                        removed_header = True

                        continue

                new_lines.append(line)

            else:

                new_lines.append(line)

        else:

            new_lines.append(line)

            if docstring_marker and docstring_marker in stripped:

                in_docstring = False

    

    new_content = '\n'.join(new_lines)

    

    if try_exec(new_content, fp):

        if write_file(fp, new_content):

            return True, 'FIXED'

        return False, 'WRITE_ERROR'

    

    # If still broken, try a more aggressive cleanup

    # Remove any remaining improperly indented lines at the top

    new_lines2 = []

    first_code_line = False

    for line in lines:

        stripped = line.strip()

        if not stripped:

            new_lines2.append(line)

            continue

        if stripped.startswith('from ') or stripped.startswith('import '):

            first_code_line = True

            new_lines2.append(line)

            continue

        if stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('@'):

            first_code_line = True

            new_lines2.append(line)

            continue

        if stripped.startswith('"""') or stripped.startswith("'''"):

            new_lines2.append(line)

            continue

        if stripped.startswith('#'):

            new_lines2.append(line)

            continue

        if not first_code_line:

            # Skip this line (corrupted header)

            continue

        new_lines2.append(line)

    

    new_content2 = '\n'.join(new_lines2)

    

    if try_exec(new_content2, fp):

        if write_file(fp, new_content2):

            return True, 'FIXED_V2'

        return False, 'WRITE_ERROR'

    

    return False, 'CANNOT_FIX'





fixed_count = 0

already_ok = 0

cannot_fix = 0

errors = []



# Files to check (the 22 corrupted category files)

corrupt_files = [

    ('05_动态规划', 'factorial.py'),

    ('05_动态规划', 'fast_fibonacci.py'),

    ('05_动态规划', 'fizz_buzz.py'),

    ('05_动态规划', 'largest_divisible_subset.py'),

    ('05_动态规划', 'max_non_adjacent_sum.py'),

    ('05_动态规划', 'minimum_cost_path.py'),

    ('05_动态规划', 'minimum_squares_to_represent_a_number.py'),

    ('05_动态规划', 'subset_generation.py'),

    ('05_动态规划', 'sum_of_subset.py'),

    ('05_动态规划', 'viterbi.py'),

    ('07_贪婪算法', 'crossword_puzzle_solver.py'),

    ('07_贪婪算法', 'fractional_knapsack_2.py'),

    ('07_贪婪算法', 'generate_parentheses_iterative.py'),

    ('07_贪婪算法', 'knight_tour.py'),

    ('07_贪婪算法', 'match_word_pattern.py'),

    ('07_贪婪算法', 'max_difference_pair.py'),

    ('07_贪婪算法', 'mergesort.py'),

    ('07_贪婪算法', 'n_queens_math.py'),

    ('07_贪婪算法', 'power.py'),

    ('07_贪婪算法', 'rat_in_maze.py'),

    ('11_几何', 'geometry.py'),

]



for subdir, fn in corrupt_files:

    fp = os.path.join(base, subdir, fn)

    success, msg = fix_corrupt_file(fp)

    if success:

        fixed_count += 1

        print('Fixed:', fn, '-', msg)

    elif msg == 'ALREADY_VALID':

        already_ok += 1

        print('Already OK:', fn)

    elif msg == 'CANNOT_FIX':

        cannot_fix += 1

        print('Cannot fix:', fn)

    else:

        errors.append(msg + ': ' + fn)



print('\nTotal fixed:', fixed_count)

print('Already OK:', already_ok)

print('Cannot fix:', cannot_fix)

print('Errors:', len(errors))





if __name__ == "__main__":

    # Test entry

    pass

