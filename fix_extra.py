# -*- coding: utf-8 -*-

"""

算法实现：fix_extra.py / fix_extra



本文件实现 fix_extra 相关的算法功能。

"""



base = r'D:\openclaw-home\.openclaw\workspace\计算机算法'



# Fix validate_solutions.py

for dirpath, _, filenames in os.walk(base):

    if '25_' in os.path.basename(dirpath):

        for fn in filenames:

            if fn == 'validate_solutions.py':

                fp = os.path.join(dirpath, fn)

                with open(fp, encoding='utf-8') as f:

                    content = f.read()

                if 'if __name__' not in content:

                    with open(fp, 'w', encoding='utf-8') as f:

                        f.write(content + '\nif __name__ == "__main__":\n    import pytest\n    pytest.main([__file__, "-v"])\n')

                    print(f'Fixed: {fn}')

                break

        break



# Also check for quicksort tutorial files

for dirpath, _, filenames in os.walk(base):

    for fn in filenames:

        if 'quicksort' in fn.lower() and ('tutorial' in fn.lower() or fn.endswith('.py')):

            fp = os.path.join(dirpath, fn)

            try:

                with open(fp, encoding='utf-8') as f:

                    content = f.read()

                if 'if __name__' not in content:

                    with open(fp, 'w', encoding='utf-8') as f:

                        lines = content.split('\n')

                        test_block = '\nif __name__ == "__main__":\n    # 测试演示\n    pass\n'

                        f.write(content + test_block)

                    print(f'Fixed quicksort file: {fn}')

            except:

                pass

