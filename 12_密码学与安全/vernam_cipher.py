# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / vernam_cipher



本文件实现 vernam_cipher 相关的算法功能。

"""



# vernam_encrypt 函数实现

def vernam_encrypt(plaintext: str, key: str) -> str:

    """

    >>> vernam_encrypt("HELLO","KEY")

    'RIJVS'

    """

    ciphertext = ""

    for i in range(len(plaintext)):

    # 遍历循环

        ct = ord(key[i % len(key)]) - 65 + ord(plaintext[i]) - 65

        while ct > 25:

    # 条件循环

            ct = ct - 26

        ciphertext += chr(65 + ct)

    return ciphertext

    # 返回结果







# vernam_decrypt 函数实现

def vernam_decrypt(ciphertext: str, key: str) -> str:

    """

    >>> vernam_decrypt("RIJVS","KEY")

    'HELLO'

    """

    decrypted_text = ""

    for i in range(len(ciphertext)):

    # 遍历循环

        ct = ord(ciphertext[i]) - ord(key[i % len(key)])

        while ct < 0:

    # 条件循环

            ct = 26 + ct

        decrypted_text += chr(65 + ct)

    return decrypted_text

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    from doctest import testmod



    testmod()



    # Example usage

    plaintext = "HELLO"

    key = "KEY"

    encrypted_text = vernam_encrypt(plaintext, key)

    decrypted_text = vernam_decrypt(encrypted_text, key)

    print("\n\n")

    print("Plaintext:", plaintext)

    print("Encrypted:", encrypted_text)

    print("Decrypted:", decrypted_text)

