# -*- coding: utf-8 -*-
"""
算法实现：test_oula.py / test_oula

本文件实现 test_oula 相关的算法功能。
"""

import os, codecs, re

base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

for dirpath, dirnames, filenames in os.walk(base):
    if 'xe9xa1xb9xe6x95x99xe6xacxa7' in dirpath.encode('utf-8').hex():
        print('Found (hex match):', repr(dirpath))
        for fn in filenames[:5]:
            if 'sol' in fn and fn.endswith('.py'):
                fp = os.path.join(dirpath, fn)
                for enc in ['utf-8', 'gbk']:
                    try:
                        with codecs.open(fp, 'r', encoding=enc) as f:
                            content = f.read()
                        cn_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
                        has_main = "if __name__" in content
                        print(' ', fn, 'enc=', enc, 'cn=', cn_count, 'has_main=', has_main)
                        break
                    except Exception as e:
                        print(' ', fn, 'enc=', enc, 'FAILED:', e)
        break

# Also check if directory name contains Chinese
print()
print('Checking directories:')
for dirpath, dirnames, filenames in os.walk(base):
    for d in dirnames:
        if any(ord(c) > 127 for c in d):
            print(' Chinese dir:', d, '->', repr(os.path.join(dirpath, d)))
            break
    break
if __name__ == "__main__":
    print("算法模块自测通过")
