# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / transposition_cipher



本文件实现 transposition_cipher 相关的算法功能。

"""



import math



"""

In cryptography, the TRANSPOSITION cipher is a method of encryption where the

positions of plaintext are shifted a certain number(determined by the key) that

follows a regular system that results in the permuted text, known as the encrypted

text. The type of transposition cipher demonstrated under is the ROUTE cipher.

"""







# main 函数实现

def main() -> None:

    message = input("Enter message: ")

    key = int(input(f"Enter key [2-{len(message) - 1}]: "))

    mode = input("Encryption/Decryption [e/d]: ")



    if mode.lower().startswith("e"):

    # 条件判断

        text = encrypt_message(key, message)

    elif mode.lower().startswith("d"):

        text = decrypt_message(key, message)



    # Append pipe symbol (vertical bar) to identify spaces at the end.

    print(f"Output:\n{text + '|'}")







# encrypt_message 函数实现

def encrypt_message(key: int, message: str) -> str:

    """

    >>> encrypt_message(6, 'Harshil Darji')

    'Hlia rDsahrij'

    """

    cipher_text = [""] * key

    for col in range(key):

    # 遍历循环

        pointer = col

        while pointer < len(message):

    # 条件循环

            cipher_text[col] += message[pointer]

            pointer += key

    return "".join(cipher_text)

    # 返回结果







# decrypt_message 函数实现

def decrypt_message(key: int, message: str) -> str:

    """

    >>> decrypt_message(6, 'Hlia rDsahrij')

    'Harshil Darji'

    """

    num_cols = math.ceil(len(message) / key)

    num_rows = key

    num_shaded_boxes = (num_cols * num_rows) - len(message)

    plain_text = [""] * num_cols

    col = 0

    row = 0



    for symbol in message:

    # 遍历循环

        plain_text[col] += symbol

        col += 1



        if (col == num_cols) or (

            (col == num_cols - 1) and (row >= num_rows - num_shaded_boxes)

        ):

            col = 0

            row += 1



    return "".join(plain_text)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

    main()

