# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / mono_alphabetic_ciphers



本文件实现 mono_alphabetic_ciphers 相关的算法功能。

"""



from typing import Literal



LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"







# translate_message 函数实现

def translate_message(

    key: str, message: str, mode: Literal["encrypt", "decrypt"]

) -> str:

    """

    >>> translate_message("QWERTYUIOPASDFGHJKLZXCVBNM","Hello World","encrypt")

    'Pcssi Bidsm'

    """

    chars_a = LETTERS if mode == "decrypt" else key

    chars_b = key if mode == "decrypt" else LETTERS

    translated = ""

    # loop through each symbol in the message

    for symbol in message:

    # 遍历循环

        if symbol.upper() in chars_a:

    # 条件判断

            # encrypt/decrypt the symbol

            sym_index = chars_a.find(symbol.upper())

            if symbol.isupper():

    # 条件判断

                translated += chars_b[sym_index].upper()

            else:

                translated += chars_b[sym_index].lower()

        else:

            # symbol is not in LETTERS, just add it

            translated += symbol

    return translated

    # 返回结果







# encrypt_message 函数实现

def encrypt_message(key: str, message: str) -> str:

    """

    >>> encrypt_message("QWERTYUIOPASDFGHJKLZXCVBNM", "Hello World")

    'Pcssi Bidsm'

    """

    return translate_message(key, message, "encrypt")

    # 返回结果







# decrypt_message 函数实现

def decrypt_message(key: str, message: str) -> str:

    """

    >>> decrypt_message("QWERTYUIOPASDFGHJKLZXCVBNM", "Hello World")

    'Itssg Vgksr'

    """

    return translate_message(key, message, "decrypt")

    # 返回结果







# main 函数实现

def main() -> None:

    message = "Hello World"

    key = "QWERTYUIOPASDFGHJKLZXCVBNM"

    mode = "decrypt"  # set to 'encrypt' or 'decrypt'



    if mode == "encrypt":

    # 条件判断

        translated = encrypt_message(key, message)

    elif mode == "decrypt":

        translated = decrypt_message(key, message)

    print(f"Using the key {key}, the {mode}ed message is: {translated}")





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

    main()

