# -*- coding: utf-8 -*-
"""
Project Euler Problem 059

解决 Project Euler 第 059 题的 Python 实现。
https://projecteuler.net/problem=059
"""

from __future__ import annotations

"""
Project Euler Problem 059 — 中文注释版
https://projecteuler.net/problem=059

问题描述:
（请根据具体题目补充此部分）

解题思路:
（请根据具体题目补充此部分）
"""




import string
from itertools import cycle, product
from pathlib import Path

VALID_CHARS: str = (
    string.ascii_letters + string.digits + string.punctuation + string.whitespace
)
LOWERCASE_INTS: list[int] = [ord(letter) for letter in string.ascii_lowercase]
VALID_INTS: set[int] = {ord(char) for char in VALID_CHARS}

COMMON_WORDS: list[str] = ["the", "be", "to", "of", "and", "in", "that", "have"]



# =============================================================================
# Project Euler 问题 059
# =============================================================================
def try_key(ciphertext: list[int], key: tuple[int, ...]) -> str | None:
    """
    Given an encrypted message and a possible 3-character key, decrypt the message.
    If the decrypted message contains a invalid character, i.e. not an ASCII letter,
    a digit, punctuation or whitespace, then we know the key is incorrect, so return
    None.
    >>> try_key([0, 17, 20, 4, 27], (104, 116, 120))
    'hello'
    >>> try_key([68, 10, 300, 4, 27], (104, 116, 120)) is None
    True
    """
    decoded: str = ""
    keychar: int
    cipherchar: int
    decodedchar: int

    for keychar, cipherchar in zip(cycle(key), ciphertext):
    # 遍历循环
        decodedchar = cipherchar ^ keychar
        if decodedchar not in VALID_INTS:
            return None
    # 返回结果
        decoded += chr(decodedchar)

    return decoded
    # 返回结果


def filter_valid_chars(ciphertext: list[int]) -> list[str]:
    # filter_valid_chars 函数实现
    """
    Given an encrypted message, test all 3-character strings to try and find the
    key. Return a list of the possible decrypted messages.
    >>> from itertools import cycle
    >>> text = "The enemy's gate is down"
    >>> key = "end"
    >>> encoded = [ord(k) ^ ord(c) for k,c in zip(cycle(key), text)]
    >>> text in filter_valid_chars(encoded)
    True
    """
    possibles: list[str] = []
    for key in product(LOWERCASE_INTS, repeat=3):
    # 遍历循环
        encoded = try_key(ciphertext, key)
        if encoded is not None:
            possibles.append(encoded)
    return possibles
    # 返回结果


def filter_common_word(possibles: list[str], common_word: str) -> list[str]:
    # filter_common_word 函数实现
    """
    Given a list of possible decoded messages, narrow down the possibilities
    for checking for the presence of a specified common word. Only decoded messages
    # 遍历循环
    containing common_word will be returned.
    >>> filter_common_word(['asfla adf', 'I am here', '   !?! #a'], 'am')
    ['I am here']
    >>> filter_common_word(['athla amf', 'I am here', '   !?! #a'], 'am')
    ['athla amf', 'I am here']
    """
    return [possible for possible in possibles if common_word in possible.lower()]
    # 返回结果


def solution(filename: str = "p059_cipher.txt") -> int:
    # solution 函数实现
    """
    Test the ciphertext against all possible 3-character keys, then narrow down the
    possibilities by filtering using common words until there's only one possible
    decoded message.
    >>> solution("test_cipher.txt")
    3000
    """
    ciphertext: list[int]
    possibles: list[str]
    common_word: str
    decoded_text: str
    data: str = Path(__file__).parent.joinpath(filename).read_text(encoding="utf-8")

    ciphertext = [int(number) for number in data.strip().split(",")]

    possibles = filter_valid_chars(ciphertext)
    for common_word in COMMON_WORDS:
    # 遍历循环
        possibles = filter_common_word(possibles, common_word)
        if len(possibles) == 1:
            break

    decoded_text = possibles[0]
    return sum(ord(char) for char in decoded_text)
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
