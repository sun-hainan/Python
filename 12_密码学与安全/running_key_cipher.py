# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / running_key_cipher

本文件实现 running_key_cipher 相关的算法功能。
"""

# running_key_encrypt 函数实现
def running_key_encrypt(key: str, plaintext: str) -> str:
    """
    Encrypts the plaintext using the Running Key Cipher.

    :param key: The running key (long piece of text).
    :param plaintext: The plaintext to be encrypted.
    :return: The ciphertext.
    """
    plaintext = plaintext.replace(" ", "").upper()
    key = key.replace(" ", "").upper()
    key_length = len(key)
    ciphertext = []
    ord_a = ord("A")

    for i, char in enumerate(plaintext):
    # 遍历循环
        p = ord(char) - ord_a
        k = ord(key[i % key_length]) - ord_a
        c = (p + k) % 26
        ciphertext.append(chr(c + ord_a))

    return "".join(ciphertext)
    # 返回结果



# running_key_decrypt 函数实现
def running_key_decrypt(key: str, ciphertext: str) -> str:
    """
    Decrypts the ciphertext using the Running Key Cipher.

    :param key: The running key (long piece of text).
    :param ciphertext: The ciphertext to be decrypted.
    :return: The plaintext.
    """
    ciphertext = ciphertext.replace(" ", "").upper()
    key = key.replace(" ", "").upper()
    key_length = len(key)
    plaintext = []
    ord_a = ord("A")

    for i, char in enumerate(ciphertext):
    # 遍历循环
        c = ord(char) - ord_a
        k = ord(key[i % key_length]) - ord_a
        p = (c - k) % 26
        plaintext.append(chr(p + ord_a))

    return "".join(plaintext)
    # 返回结果



# test_running_key_encrypt 函数实现
def test_running_key_encrypt() -> None:
    """
    >>> key = "How does the duck know that? said Victor"
    >>> ciphertext = running_key_encrypt(key, "DEFEND THIS")
    >>> running_key_decrypt(key, ciphertext) == "DEFENDTHIS"
    True
    """


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
    test_running_key_encrypt()

    plaintext = input("Enter the plaintext: ").upper()
    print(f"\n{plaintext = }")

    key = "How does the duck know that? said Victor"
    encrypted_text = running_key_encrypt(key, plaintext)
    print(f"{encrypted_text = }")

    decrypted_text = running_key_decrypt(key, encrypted_text)
    print(f"{decrypted_text = }")
