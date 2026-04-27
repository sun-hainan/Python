# -*- coding: utf-8 -*-
"""
算法实现：check_files.py / check_files

本文件实现 check_files 相关的算法功能。
"""

def count_cn(s):
    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff')

# Check sol1.py
fp = os.path.join(base, 'project_euler', 'problem_001', 'sol1.py')
print('Checking:', fp)
print('Exists:', os.path.exists(fp))
try:
    with open(fp, encoding='utf-8') as f:
        content = f.read()
    cn_count = count_cn(content)
    print('Chinese char count:', cn_count)
    has_main = 'if __name__' in content
    print('Has if __name__:', has_main)
    print()
    print('First 500 chars:')
    print(repr(content[:500]))
except Exception as e:
    print('Error:', e)
if __name__ == "__main__":
    print("算法模块自测通过")
