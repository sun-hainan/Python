# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / word_occurrence

本文件实现 word_occurrence 相关的算法功能。
"""

# Created by sarathkaul on 17/11/19
# Modified by Arkadip Bhattacharya(@darkmatter18) on 20/04/2020
"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""

from collections import defaultdict


def word_occurrence(sentence: str) -> dict:
    # word_occurrence function

    # word_occurrence function
    # word_occurrence 函数实现
    """
    >>> from collections import Counter
    >>> SENTENCE = "a b A b c b d b d e f e g e h e i e j e 0"
    >>> occurence_dict = word_occurrence(SENTENCE)
    >>> all(occurence_dict[word] == count for word, count
    ...     in Counter(SENTENCE.split()).items())
    True
    >>> dict(word_occurrence("Two  spaces"))
    {'Two': 1, 'spaces': 1}
    """
    occurrence: defaultdict[str, int] = defaultdict(int)
    # Creating a dictionary containing count of each word
    for word in sentence.split():
        occurrence[word] += 1
    return occurrence


if __name__ == "__main__":
    for word, count in word_occurrence("INPUT STRING").items():
        print(f"{word}: {count}")
