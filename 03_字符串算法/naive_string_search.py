# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / naive_string_search

本文件实现 naive_string_search 相关的算法功能。
"""

def naive_pattern_search(s: str, pattern: str) -> list:
    # naive_pattern_search function

    # naive_pattern_search function
    # naive_pattern_search 函数实现
    """
    >>> naive_pattern_search("ABAAABCDBBABCDDEBCABC", "ABC")
    [4, 10, 18]
    >>> naive_pattern_search("ABC", "ABAAABCDBBABCDDEBCABC")
    []
    >>> naive_pattern_search("", "ABC")
    []
    >>> naive_pattern_search("TEST", "TEST")
    [0]
    >>> naive_pattern_search("ABCDEGFTEST", "TEST")
    [7]
    """
    pat_len = len(pattern)
    position = []
    for i in range(len(s) - pat_len + 1):
        match_found = True
        for j in range(pat_len):
            if s[i + j] != pattern[j]:
                match_found = False
                break
        if match_found:
            position.append(i)
    return position


if __name__ == "__main__":
    assert naive_pattern_search("ABCDEFG", "DE") == [3]
    print(naive_pattern_search("ABAAABCDBBABCDDEBCABC", "ABC"))
