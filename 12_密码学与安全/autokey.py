# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / autokey

本文件实现 autokey 相关的算法功能。
"""

# encrypt 函数实现
def encrypt(plaintext: str, key: str) -> str:
    """
    Encrypt a given `plaintext` (string) and `key` (string), returning the
    encrypted ciphertext.

    >>> encrypt("hello world", "coffee")
    'jsqqs avvwo'
    >>> encrypt("coffee is good as python", "TheAlgorithms")
    'vvjfpk wj ohvp su ddylsv'
    >>> encrypt("coffee is good as python", 2)
    Traceback (most recent call last):
        ...
    TypeError: key must be a string
    >>> encrypt("", "TheAlgorithms")
    Traceback (most recent call last):
        ...
    ValueError: plaintext is empty
    >>> encrypt("coffee is good as python", "")
    Traceback (most recent call last):
        ...
    ValueError: key is empty
    >>> encrypt(527.26, "TheAlgorithms")
    Traceback (most recent call last):
        ...
    TypeError: plaintext must be a string
    """
    if not isinstance(plaintext, str):
    # 条件判断
        raise TypeError("plaintext must be a string")
    if not isinstance(key, str):
    # 条件判断
        raise TypeError("key must be a string")

    if not plaintext:
    # 条件判断
        raise ValueError("plaintext is empty")
    if not key:
    # 条件判断
        raise ValueError("key is empty")

    key += plaintext
    plaintext = plaintext.lower()
    key = key.lower()
    plaintext_iterator = 0
    key_iterator = 0
    ciphertext = ""
    while plaintext_iterator < len(plaintext):
    # 条件循环
        if (
            ord(plaintext[plaintext_iterator]) < 97
            or ord(plaintext[plaintext_iterator]) > 122
        ):
            ciphertext += plaintext[plaintext_iterator]
            plaintext_iterator += 1
        elif ord(key[key_iterator]) < 97 or ord(key[key_iterator]) > 122:
            key_iterator += 1
        else:
            ciphertext += chr(
                (
                    (ord(plaintext[plaintext_iterator]) - 97 + ord(key[key_iterator]))
                    - 97
                )
                % 26
                + 97
            )
            key_iterator += 1
            plaintext_iterator += 1
    return ciphertext
    # 返回结果



# decrypt 函数实现
def decrypt(ciphertext: str, key: str) -> str:
    """
    Decrypt a given `ciphertext` (string) and `key` (string), returning the decrypted
    ciphertext.

    >>> decrypt("jsqqs avvwo", "coffee")
    'hello world'
    >>> decrypt("vvjfpk wj ohvp su ddylsv", "TheAlgorithms")
    'coffee is good as python'
    >>> decrypt("vvjfpk wj ohvp su ddylsv", "")
    Traceback (most recent call last):
        ...
    ValueError: key is empty
    >>> decrypt(527.26, "TheAlgorithms")
    Traceback (most recent call last):
        ...
    TypeError: ciphertext must be a string
    >>> decrypt("", "TheAlgorithms")
    Traceback (most recent call last):
        ...
    ValueError: ciphertext is empty
    >>> decrypt("vvjfpk wj ohvp su ddylsv", 2)
    Traceback (most recent call last):
        ...
    TypeError: key must be a string
    """
    if not isinstance(ciphertext, str):
    # 条件判断
        raise TypeError("ciphertext must be a string")
    if not isinstance(key, str):
    # 条件判断
        raise TypeError("key must be a string")

    if not ciphertext:
    # 条件判断
        raise ValueError("ciphertext is empty")
    if not key:
    # 条件判断
        raise ValueError("key is empty")

    key = key.lower()
    ciphertext_iterator = 0
    key_iterator = 0
    plaintext = ""
    while ciphertext_iterator < len(ciphertext):
    # 条件循环
        if (
            ord(ciphertext[ciphertext_iterator]) < 97
            or ord(ciphertext[ciphertext_iterator]) > 122
        ):
            plaintext += ciphertext[ciphertext_iterator]
        else:
            plaintext += chr(
                (ord(ciphertext[ciphertext_iterator]) - ord(key[key_iterator])) % 26
                + 97
            )
            key += chr(
                (ord(ciphertext[ciphertext_iterator]) - ord(key[key_iterator])) % 26
                + 97
            )
            key_iterator += 1
        ciphertext_iterator += 1
    return plaintext
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
    operation = int(input("Type 1 to encrypt or 2 to decrypt:"))
    if operation == 1:
    # 条件判断
        plaintext = input("Typeplaintext to be encrypted:\n")
        key = input("Type the key:\n")
        print(encrypt(plaintext, key))
    elif operation == 2:
        ciphertext = input("Type the ciphertext to be decrypted:\n")
        key = input("Type the key:\n")
        print(decrypt(ciphertext, key))
    decrypt("jsqqs avvwo", "coffee")
