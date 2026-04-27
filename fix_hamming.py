# -*- coding: utf-8 -*-

"""

算法实现：fix_hamming.py / fix_hamming



本文件实现 fix_hamming 相关的算法功能。

"""



import os



root = r'D:\openclaw-home\.openclaw\workspace\计算机算法'

cn_header = '''# 汉明码（Hamming Code）实现——差错检测与纠错

# 参考文献: https://en.wikipedia.org/wiki/Hamming_code

# 功能：对消息进行汉明编码，支持引入错误并检测/纠正



'''



for dirpath, _, filenames in os.walk(root):

    bn = os.path.basename(dirpath)

    if bn.startswith('12_'):

        for fn in filenames:

            if fn == 'hamming_code.py':

                full = os.path.join(dirpath, fn)

                with open(full, encoding='utf-8') as f:

                    content = f.read()

                lines = content.split('\n')

                

                # Find end of module docstring

                new_lines = []

                in_docstring = False

                docstring_marker = None

                inserted = False

                

                for i, line in enumerate(lines):

                    if not in_docstring:

                        stripped = line.strip()

                        if stripped.startswith('"""') or stripped.startswith("'''"):

                            docstring_marker = stripped[:3]

                            in_docstring = True

                            new_lines.append(line)

                        else:

                            new_lines.append(line)

                    else:

                        new_lines.append(line)

                        if docstring_marker in line:

                            in_docstring = False

                            new_lines.append(cn_header)

                            inserted = True

                

                if not inserted:

                    # insert after imports

                    for i, line in enumerate(lines):

                        if line.startswith('import') or line.startswith('from'):

                            pass

                        elif not line.strip() and i > 3:

                            new_lines.insert(i+1, cn_header)

                            inserted = True

                            break

                    if not inserted:

                        new_lines.insert(0, cn_header)

                

                # Add if __name__ block at the end

                test_block = '''

if __name__ == "__main__":

    # 示例：对 "Message01" 进行汉明编码

    text = "Message01"

    size_par = 4  # 奇偶校验位数



    # 将文本转为二进制

    binary_text = text_to_bits(text)

    print(f"原文二进制: {binary_text}")



    # 编码

    encoded = emitter_converter(size_par, binary_text)

    print(f"编码后: {''.join(encoded)}")



    # 译码（无错误）

    decoded, ack = receptor_converter(size_par, encoded)

    print(f"译码结果: {''.join(decoded)} | 完整性: {ack}")



    # 模拟传输错误（翻转最后一位）

    encoded[2] = "1" if encoded[2] == "0" else "0"

    print(f"引入错误后: {''.join(encoded)}")



    # 再次译码

    decoded, ack = receptor_converter(size_par, encoded)

    print(f"译码结果: {''.join(decoded)} | 完整性: {ack}")

'''

                new_lines.append(test_block)

                

                with open(full, 'w', encoding='utf-8') as f:

                    f.write('\n'.join(new_lines))

                print(f'Done: {full}')

                break

        break

