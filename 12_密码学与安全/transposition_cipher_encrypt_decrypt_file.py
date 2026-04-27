# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / transposition_cipher_encrypt_decrypt_file

本文件实现 transposition_cipher_encrypt_decrypt_file 相关的算法功能。
"""

import os
import sys
import time

from . import transposition_cipher as trans_cipher



# main 函数实现
def main() -> None:
    input_file = "./prehistoric_men.txt"
    output_file = "./Output.txt"
    key = int(input("Enter key: "))
    mode = input("Encrypt/Decrypt [e/d]: ")

    if not os.path.exists(input_file):
    # 条件判断
        print(f"File {input_file} does not exist. Quitting...")
        sys.exit()
    if os.path.exists(output_file):
    # 条件判断
        print(f"Overwrite {output_file}? [y/n]")
        response = input("> ")
        if not response.lower().startswith("y"):
    # 条件判断
            sys.exit()

    start_time = time.time()
    if mode.lower().startswith("e"):
    # 条件判断
        with open(input_file) as f:
            content = f.read()
        translated = trans_cipher.encrypt_message(key, content)
    elif mode.lower().startswith("d"):
        with open(output_file) as f:
            content = f.read()
        translated = trans_cipher.decrypt_message(key, content)

    with open(output_file, "w") as output_obj:
        output_obj.write(translated)

    total_time = round(time.time() - start_time, 2)
    print(("Done (", total_time, "seconds )"))


if __name__ == "__main__":
    # 条件判断
    main()
