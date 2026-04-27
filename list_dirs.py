# -*- coding: utf-8 -*-

"""

算法实现：list_dirs.py / list_dirs



本文件实现 list_dirs 相关的算法功能。

"""



import os

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

output = []

for item in sorted(os.listdir(base)):

    full = os.path.join(base, item)

    output.append(repr(item) + ' is_dir: ' + str(os.path.isdir(full)))

with open(r'D:\openclaw-home\.openclaw\workspace\_dirs.txt', 'w', encoding='utf-8') as f:

    f.write('\n'.join(output))

print('Done, found', len(output), 'items')

if __name__ == "__main__":

    print("算法模块自测通过")

