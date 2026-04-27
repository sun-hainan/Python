# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / baconian_cipher

本文件实现 baconian_cipher 相关的算法功能。
"""

encode_dict = {
    "a": "AAAAA",
    "b": "AAAAB",
    "c": "AAABA",
    "d": "AAABB",
    "e": "AABAA",
    "f": "AABAB",
    "g": "AABBA",
    "h": "AABBB",
    "i": "ABAAA",
    "j": "BBBAA",
    "k": "ABAAB",
    "l": "ABABA",
    "m": "ABABB",
    "n": "ABBAA",
    "o": "ABBAB",
    "p": "ABBBA",
    "q": "ABBBB",
    "r": "BAAAA",
    "s": "BAAAB",
    "t": "BAABA",
    "u": "BAABB",
    "v": "BBBAB",
    "w": "BABAA",
    "x": "BABAB",
    "y": "BABBA",
    "z": "BABBB",
    " ": " ",
}


decode_dict = {value: key for key, value in encode_dict.items()}



# encode 函数实现
def encode(word: str) -> str:
    """
    Encodes to Baconian cipher

    >>> encode("hello")
    'AABBBAABAAABABAABABAABBAB'
    >>> encode("hello world")
    'AABBBAABAAABABAABABAABBAB BABAAABBABBAAAAABABAAAABB'
    >>> encode("hello world!")
    Traceback (most recent call last):
        ...
    Exception: encode() accepts only letters of the alphabet and spaces
    """
    encoded = ""
    for letter in word.lower():
    # 遍历循环
        if letter.isalpha() or letter == " ":
    # 条件判断
            encoded += encode_dict[letter]
        else:
            raise Exception("encode() accepts only letters of the alphabet and spaces")
    return encoded
    # 返回结果



# decode 函数实现
def decode(coded: str) -> str:
    """
    Decodes from Baconian cipher

    >>> decode("AABBBAABAAABABAABABAABBAB BABAAABBABBAAAAABABAAAABB")
    'hello world'
    >>> decode("AABBBAABAAABABAABABAABBAB")
    'hello'
    >>> decode("AABBBAABAAABABAABABAABBAB BABAAABBABBAAAAABABAAAABB!")
    Traceback (most recent call last):
        ...
    Exception: decode() accepts only 'A', 'B' and spaces
    """
    if set(coded) - {"A", "B", " "} != set():
    # 条件判断
        raise Exception("decode() accepts only 'A', 'B' and spaces")
    decoded = ""
    for word in coded.split():
    # 遍历循环
        while len(word) != 0:
    # 条件循环
            decoded += decode_dict[word[:5]]
            word = word[5:]
        decoded += " "
    return decoded.strip()
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    from doctest import testmod

    testmod()
