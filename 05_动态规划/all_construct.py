# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / all_construct

本文件实现 all_construct 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""


"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""




def all_construct(target: str, word_bank: list[str] | None = None) -> list[list[str]]:
    # all_construct function

    # all_construct function
    # all_construct 函数实现
    """
    returns the list containing all the possible
    combinations a string(`target`) can be constructed from
    the given list of substrings(`word_bank`)

    >>> all_construct("hello", ["he", "l", "o"])
    [['he', 'l', 'l', 'o']]
    >>> all_construct("purple",["purp","p","ur","le","purpl"])
    [['purp', 'le'], ['p', 'ur', 'p', 'le']]
    """

    word_bank = word_bank or []
    # create a table
    table_size: int = len(target) + 1

    table: list[list[list[str]]] = []
    for _ in range(table_size):
        table.append([])
    # seed value
    table[0] = [[]]  # because empty string has empty combination

    # iterate through the indices
    for i in range(table_size):
        # condition
        if table[i] != []:
            for word in word_bank:
                # slice condition
                if target[i : i + len(word)] == word:
                    new_combinations: list[list[str]] = [
                        [word, *way] for way in table[i]
                    ]
                    # adds the word to every combination the current position holds
                    # now,push that combination to the table[i+len(word)]
                    table[i + len(word)] += new_combinations

    # combinations are in reverse order so reverse for better output
    for combination in table[len(target)]:
        combination.reverse()

    return table[len(target)]


if __name__ == "__main__":
    print(all_construct("jwajalapa", ["jwa", "j", "w", "a", "la", "lapa"]))
    print(all_construct("rajamati", ["s", "raj", "amat", "raja", "ma", "i", "t"]))
    print(
        all_construct(
            "hexagonosaurus",
            ["h", "ex", "hex", "ag", "ago", "ru", "auru", "rus", "go", "no", "o", "s"],
        )
    )
