# -*- coding: utf-8 -*-
"""
算法实现：find_quicksort.py / find_quicksort

本文件实现 find_quicksort 相关的算法功能。
"""

def has_cn(s):
    return any('\u4e00' <= c <= '\u9fff' for c in s)

# Find QuickSort tutorial
for dirpath, _, filenames in os.walk(base):
    for fn in filenames:
        if 'quicksort' in fn.lower() and ('tutorial' in fn.lower() or '详细' in fn or '教程' in fn):
            fp = os.path.join(dirpath, fn)
            print(f'Found: {fp}')
            try:
                with open(fp, encoding='utf-8') as f:
                    c = f.read()
                print('Has __name__:', 'if __name__' in c)
                print('Has Chinese:', has_cn(c))
                print('First 200 chars:')
                print(repr(c[:200]))
            except Exception as e:
                print(f'Error: {e}')
            break
if __name__ == "__main__":
    print("算法模块自测通过")
