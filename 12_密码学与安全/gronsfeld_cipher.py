# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / gronsfeld_cipher

本文件实现 gronsfeld_cipher 相关的算法功能。
"""

from string import ascii_uppercase



# gronsfeld 函数实现
def gronsfeld(text: str, key: str) -> str:
    """
    Encrypt plaintext with the Gronsfeld cipher

    >>> gronsfeld('hello', '412')
    'LFNPP'
    >>> gronsfeld('hello', '123')
    'IGOMQ'
    >>> gronsfeld('', '123')
    ''
    >>> gronsfeld('yes, ¥€$ - _!@#%?', '0')
    'YES, ¥€$ - _!@#%?'
    >>> gronsfeld('yes, ¥€$ - _!@#%?', '01')
    'YFS, ¥€$ - _!@#%?'
    >>> gronsfeld('yes, ¥€$ - _!@#%?', '012')
    'YFU, ¥€$ - _!@#%?'
    >>> gronsfeld('yes, ¥€$ - _!@#%?', '')
    Traceback (most recent call last):
      ...
    ZeroDivisionError: division by zero
    """
    ascii_len = len(ascii_uppercase)
    key_len = len(key)
    encrypted_text = ""
    keys = [int(char) for char in key]
    upper_case_text = text.upper()

    for i, char in enumerate(upper_case_text):
    # 遍历循环
        if char in ascii_uppercase:
    # 条件判断
            new_position = (ascii_uppercase.index(char) + keys[i % key_len]) % ascii_len
            shifted_letter = ascii_uppercase[new_position]
            encrypted_text += shifted_letter
        else:
            encrypted_text += char

    return encrypted_text
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    from doctest import testmod

    testmod()
