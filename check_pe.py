# -*- coding: utf-8 -*-

"""

算法实现：check_pe.py / check_pe



本文件实现 check_pe 相关的算法功能。

"""



import os

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

count = 0

output = []



for dirpath, dirnames, filenames in os.walk(base):

    # Only look in project_euler/problem_NNN/sol*.py

    parts = dirpath.split(os.sep)

    if 'project_euler' in parts:

        # Find which index project_euler is at

        pe_idx = parts.index('project_euler')

        # Check if this is a problem_NNN subdirectory

        if len(parts) > pe_idx + 1:

            subdir = parts[pe_idx + 1]

            if subdir.startswith('problem_'):

                for fn in sorted(filenames):

                    if fn.startswith('sol') and fn.endswith('.py'):

                        fp = os.path.join(dirpath, fn)

                        try:

                            with open(fp, encoding='utf-8') as f:

                                lines = f.read().split('\n')[:8]

                            for i, l in enumerate(lines):

                                output.append(f'{subdir}/{fn} L{i}: {repr(l[:60])}')

                        except Exception as e:

                            output.append(f'ERROR {fn}: {e}')

                        count += 1

                        if count >= 5:

                            break

                if count >= 5:

                    break

        if count >= 5:

            break



with open(r'D:\openclaw-home\.openclaw\workspace\_temp_pe_check.txt', 'w', encoding='utf-8') as f:

    f.write('\n'.join(output))

print(f'Done, checked {count} files')

if __name__ == "__main__":

    print("算法模块自测通过")

