# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / anagrams

本文件实现 anagrams 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""




import collections
import pprint
from pathlib import Path


def signature(word: str) -> str:
    # signature function

    # signature function
    # signature 函数实现
    """
    Return a word's frequency-based signature.

    >>> signature("test")
    'e1s1t2'
    >>> signature("this is a test")
    ' 3a1e1h1i2s3t3'
    >>> signature("finaltest")
    'a1e1f1i1l1n1s1t2'
    """
    frequencies = collections.Counter(word)
    return "".join(
        f"{char}{frequency}" for char, frequency in sorted(frequencies.items())
    )


def anagram(my_word: str) -> list[str]:
    # anagram function

    # anagram function
    # anagram 函数实现
    """
    Return every anagram of the given word from the dictionary.

    >>> anagram('test')
    ['sett', 'stet', 'test']
    >>> anagram('this is a test')
    []
    >>> anagram('final')
    ['final']
    """
    return word_by_signature[signature(my_word)]


data: str = Path(__file__).parent.joinpath("words.txt").read_text(encoding="utf-8")
word_list = sorted({word.strip().lower() for word in data.splitlines()})

word_by_signature = collections.defaultdict(list)
for word in word_list:
    word_by_signature[signature(word)].append(word)

if __name__ == "__main__":
    all_anagrams = {word: anagram(word) for word in word_list if len(anagram(word)) > 1}

    with open("anagrams.txt", "w") as file:
        file.write("all_anagrams = \n")
        file.write(pprint.pformat(all_anagrams))
