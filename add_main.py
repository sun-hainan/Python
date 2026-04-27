# -*- coding: utf-8 -*-
"""
算法实现：add_main.py / add_main

本文件实现 add_main 相关的算法功能。
"""

import os

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

files_need_main = [
    "25_数学游戏\\validate_solutions.py",
    "Chinese Algorithms\\DP\\01_Fibonacci.py",
    "Chinese Algorithms\\DP\\02_Knapsack.py",
    "Chinese Algorithms\\DP\\03_LCS.py",
    "Chinese Algorithms\\DP\\04_LIS.py",
    "Chinese Algorithms\\Graphs\\01_BFS.py",
    "Chinese Algorithms\\Graphs\\02_DFS.py",
    "Chinese Algorithms\\Graphs\\03_Dijkstra.py",
    "Chinese Algorithms\\Graphs\\04_Prim.py",
    "Chinese Algorithms\\Graphs\\05_Kruskal.py",
    "Chinese Algorithms\\Graphs\\06_Floyd_Warshall.py",
    "Chinese Algorithms\\Graphs\\07_Topological_Sort.py",
    "Chinese Algorithms\\Sorting\\01_Bubble_Sort.py",
    "Chinese Algorithms\\Sorting\\02_Quick_Sort.py",
    "Chinese Algorithms\\Sorting\\03_Merge_Sort.py",
    "Chinese Algorithms\\Sorting\\04_Insertion_Sort.py",
    "Chinese Algorithms\\Sorting\\05_Selection_Sort.py",
    "Chinese Algorithms\\Sorting\\06_Heap_Sort.py",
    "Chinese Algorithms\\Sorting\\07_Shell_Sort.py",
    "Chinese Algorithms\\Sorting\\08_Counting_Sort.py",
    "Chinese Algorithms\\Sorting\\09_Radix_Sort.py",
    "Chinese Algorithms\\Structure\\01_Binary_Tree.py",
    "Chinese Algorithms\\Structure\\02_Linked_List.py",
    "Chinese Algorithms\\Structure\\03_Stack.py",
    "Chinese Algorithms\\Structure\\04_Queue.py",
    "Chinese Algorithms\\详细教程\\快速排序-史上最详细教程.py",
    "项目欧拉\\DP\\01_Fibonacci.py",
    "项目欧拉\\DP\\02_Knapsack.py",
    "项目欧拉\\DP\\03_LCS.py",
    "项目欧拉\\DP\\04_LIS.py",
    "项目欧拉\\Graphs\\01_BFS.py",
    "项目欧拉\\Graphs\\02_DFS.py",
    "项目欧拉\\Graphs\\03_Dijkstra.py",
    "项目欧拉\\Graphs\\04_Prim.py",
    "项目欧拉\\Graphs\\05_Kruskal.py",
    "项目欧拉\\Graphs\\06_Floyd_Warshall.py",
    "项目欧拉\\Graphs\\07_Topological_Sort.py",
    "项目欧拉\\Sorting\\01_Bubble_Sort.py",
    "项目欧拉\\Sorting\\02_Quick_Sort.py",
    "项目欧拉\\Sorting\\03_Merge_Sort.py",
    "项目欧拉\\Sorting\\04_Insertion_Sort.py",
    "项目欧拉\\Sorting\\05_Selection_Sort.py",
    "项目欧拉\\Sorting\\06_Heap_Sort.py",
    "项目欧拉\\Sorting\\07_Shell_Sort.py",
    "项目欧拉\\Sorting\\08_Counting_Sort.py",
    "项目欧拉\\Sorting\\09_Radix_Sort.py",
    "项目欧拉\\Structure\\01_Binary_Tree.py",
    "项目欧拉\\Structure\\02_Linked_List.py",
    "项目欧拉\\Structure\\03_Stack.py",
    "项目欧拉\\Structure\\04_Queue.py",
    "项目欧拉\\详细教程\\快速排序-史上最详细教程.py",
]


def get_main_block(filepath, content):
    """Determine appropriate test block based on file content"""
    fn = os.path.basename(filepath)
    
    # Read content to find function names
    lines = content.split('\n')
    func_names = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('def '):
            func_name = stripped.split('(')[0].replace('def ', '').strip()
            if not func_name.startswith('_'):
                func_names.append(func_name)
    
    # Build test block
    test_lines = ['\n', 'if __name__ == "__main__":']
    
    if func_names:
        main_func = func_names[-1]
        test_lines.append(f'    # 测试: {main_func}')
        test_lines.append(f'    result = {main_func}()')
        test_lines.append(f'    print(result)')
    else:
        test_lines.append('    pass')
    
    return '\n'.join(test_lines)


fixed = 0
failed = []

for rel_path in files_need_main:
    fp = os.path.join(base, rel_path)
    if not os.path.exists(fp):
        # Try to find it via walk
        found = False
        for dirpath, _, filenames in os.walk(base):
            for fn in filenames:
                if fn == os.path.basename(rel_path):
                    fp2 = os.path.join(dirpath, fn)
                    if os.path.basename(os.path.dirname(fp2)) == os.path.basename(os.path.dirname(fp)):
                        fp = fp2
                        found = True
                        break
            if found:
                break
        if not found:
            failed.append(f'NOT FOUND: {rel_path}')
            continue
    
    try:
        with open(fp, encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        failed.append(f'READ ERROR {rel_path}: {e}')
        continue
    
    if "if __name__" in content:
        continue  # already has it
    
    test_block = get_main_block(fp, content)
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content + test_block)
    
    fixed += 1

print(f'Fixed {fixed} files')
if failed:
    print('Failed:')
    for f in failed:
        print(f'  {f}')
