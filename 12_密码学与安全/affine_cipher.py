# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / affine_cipher



本文件实现 affine_cipher 相关的算法功能。

"""



import random

import sys



from maths.greatest_common_divisor import gcd_by_iterative



from . import cryptomath_module as cryptomath



SYMBOLS = (

    r""" !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`"""

    r"""abcdefghijklmnopqrstuvwxyz{|}~"""

)







# check_keys 函数实现

def check_keys(key_a: int, key_b: int, mode: str) -> None:

    if mode == "encrypt":

    # 条件判断

        if key_a == 1:

    # 条件判断

            sys.exit(

                "The affine cipher becomes weak when key "

                "A is set to 1. Choose different key"

            )

        if key_b == 0:

    # 条件判断

            sys.exit(

                "The affine cipher becomes weak when key "

                "B is set to 0. Choose different key"

            )

    if key_a < 0 or key_b < 0 or key_b > len(SYMBOLS) - 1:

    # 条件判断

        sys.exit(

            "Key A must be greater than 0 and key B must "

            f"be between 0 and {len(SYMBOLS) - 1}."

        )

    if gcd_by_iterative(key_a, len(SYMBOLS)) != 1:

    # 条件判断

        sys.exit(

            f"Key A {key_a} and the symbol set size {len(SYMBOLS)} "

            "are not relatively prime. Choose a different key."

        )







# encrypt_message 函数实现

def encrypt_message(key: int, message: str) -> str:

    """

    >>> encrypt_message(4545, 'The affine cipher is a type of monoalphabetic '

    ...                       'substitution cipher.')

    'VL}p MM{I}p~{HL}Gp{vp pFsH}pxMpyxIx JHL O}F{~pvuOvF{FuF{xIp~{HL}Gi'

    """

    key_a, key_b = divmod(key, len(SYMBOLS))

    check_keys(key_a, key_b, "encrypt")

    cipher_text = ""

    for symbol in message:

    # 遍历循环

        if symbol in SYMBOLS:

    # 条件判断

            sym_index = SYMBOLS.find(symbol)

            cipher_text += SYMBOLS[(sym_index * key_a + key_b) % len(SYMBOLS)]

        else:

            cipher_text += symbol

    return cipher_text

    # 返回结果







# decrypt_message 函数实现

def decrypt_message(key: int, message: str) -> str:

    """

    >>> decrypt_message(4545, 'VL}p MM{I}p~{HL}Gp{vp pFsH}pxMpyxIx JHL O}F{~pvuOvF{FuF'

    ...                       '{xIp~{HL}Gi')

    'The affine cipher is a type of monoalphabetic substitution cipher.'

    """

    key_a, key_b = divmod(key, len(SYMBOLS))

    check_keys(key_a, key_b, "decrypt")

    plain_text = ""

    mod_inverse_of_key_a = cryptomath.find_mod_inverse(key_a, len(SYMBOLS))

    for symbol in message:

    # 遍历循环

        if symbol in SYMBOLS:

    # 条件判断

            sym_index = SYMBOLS.find(symbol)

            plain_text += SYMBOLS[

                (sym_index - key_b) * mod_inverse_of_key_a % len(SYMBOLS)

            ]

        else:

            plain_text += symbol

    return plain_text

    # 返回结果







# get_random_key 函数实现

def get_random_key() -> int:

    while True:

    # 条件循环

        key_b = random.randint(2, len(SYMBOLS))

        key_b = random.randint(2, len(SYMBOLS))

        if gcd_by_iterative(key_b, len(SYMBOLS)) == 1 and key_b % len(SYMBOLS) != 0:

    # 条件判断

            return key_b * len(SYMBOLS) + key_b

    # 返回结果







# main 函数实现

def main() -> None:

    """

    >>> key = get_random_key()

    >>> msg = "This is a test!"

    >>> decrypt_message(key, encrypt_message(key, msg)) == msg

    True

    """

    message = input("Enter message: ").strip()

    key = int(input("Enter key [2000 - 9000]: ").strip())

    mode = input("Encrypt/Decrypt [E/D]: ").strip().lower()



    if mode.startswith("e"):

    # 条件判断

        mode = "encrypt"

        translated = encrypt_message(key, message)

    elif mode.startswith("d"):

        mode = "decrypt"

        translated = decrypt_message(key, message)

    print(f"\n{mode.title()}ed text: \n{translated}")





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

    # main()

