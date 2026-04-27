# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / simple_substitution_cipher



本文件实现 simple_substitution_cipher 相关的算法功能。

"""



import random

import sys



LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"







# main 函数实现

def main() -> None:

    message = input("Enter message: ")

    key = "LFWOAYUISVKMNXPBDCRJTQEGHZ"

    resp = input("Encrypt/Decrypt [e/d]: ")



    check_valid_key(key)



    if resp.lower().startswith("e"):

    # 条件判断

        mode = "encrypt"

        translated = encrypt_message(key, message)

    elif resp.lower().startswith("d"):

        mode = "decrypt"

        translated = decrypt_message(key, message)



    print(f"\n{mode.title()}ion: \n{translated}")







# check_valid_key 函数实现

def check_valid_key(key: str) -> None:

    key_list = list(key)

    letters_list = list(LETTERS)

    key_list.sort()

    letters_list.sort()



    if key_list != letters_list:

    # 条件判断

        sys.exit("Error in the key or symbol set.")







# encrypt_message 函数实现

def encrypt_message(key: str, message: str) -> str:

    """

    >>> encrypt_message('LFWOAYUISVKMNXPBDCRJTQEGHZ', 'Harshil Darji')

    'Ilcrism Olcvs'

    """

    return translate_message(key, message, "encrypt")

    # 返回结果







# decrypt_message 函数实现

def decrypt_message(key: str, message: str) -> str:

    """

    >>> decrypt_message('LFWOAYUISVKMNXPBDCRJTQEGHZ', 'Ilcrism Olcvs')

    'Harshil Darji'

    """

    return translate_message(key, message, "decrypt")

    # 返回结果







# translate_message 函数实现

def translate_message(key: str, message: str, mode: str) -> str:

    translated = ""

    chars_a = LETTERS

    chars_b = key



    if mode == "decrypt":

    # 条件判断

        chars_a, chars_b = chars_b, chars_a



    for symbol in message:

    # 遍历循环

        if symbol.upper() in chars_a:

    # 条件判断

            sym_index = chars_a.find(symbol.upper())

            if symbol.isupper():

    # 条件判断

                translated += chars_b[sym_index].upper()

            else:

                translated += chars_b[sym_index].lower()

        else:

            translated += symbol



    return translated

    # 返回结果







# get_random_key 函数实现

def get_random_key() -> str:

    key = list(LETTERS)

    random.shuffle(key)

    return "".join(key)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    main()

