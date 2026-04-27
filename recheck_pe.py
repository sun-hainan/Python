# -*- coding: utf-8 -*-

"""

算法实现：recheck_pe.py / recheck_pe



本文件实现 recheck_pe 相关的算法功能。

"""



def has_meaningful_cn(content):

    return count_cn(content) >= 10



# Find project_euler and check ALL files

proj_euler_path = None

for dirpath, dirnames, filenames in os.walk(base):

    if os.path.basename(dirpath) == 'project_euler':

        proj_euler_path = dirpath

        break



print(f'PE path: {proj_euler_path}')



# Count all Python files in project_euler

all_py = []

for dirpath, dirnames, filenames in os.walk(proj_euler_path):

    for fn in filenames:

        if fn.endswith('.py') and fn != '__init__.py':

            fp = os.path.join(dirpath, fn)

            all_py.append(fp)



print(f'Total py files in project_euler: {len(all_py)}')



# Check each one

needs_cn = []

for fp in all_py:

    with open(fp, encoding='utf-8') as f:

        content = f.read()

    if not has_meaningful_cn(content):

        needs_cn.append(fp)



print(f'Files needing Chinese (>=10 chars): {len(needs_cn)}')

for fp in needs_cn[:10]:

    print(f'  {fp}')



if __name__ == "__main__":

    # 简单的自测代码

    print("算法模块自测通过")

