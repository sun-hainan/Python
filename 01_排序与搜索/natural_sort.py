# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / natural_sort

本文件实现 natural_sort 相关的算法功能。
"""

from __future__ import annotations

import re



# natural_sort 函数实现
def natural_sort(input_list: list[str]) -> list[str]:
    """
    Sort the given list of strings in the way that humans expect.

    The normal Python sort algorithm sorts lexicographically,
    so you might not get the results that you expect...

    >>> example1 = ['2 ft 7 in', '1 ft 5 in', '10 ft 2 in', '2 ft 11 in', '7 ft 6 in']
    >>> sorted(example1)
    ['1 ft 5 in', '10 ft 2 in', '2 ft 11 in', '2 ft 7 in', '7 ft 6 in']
    >>> # The natural sort algorithm sort based on meaning and not computer code point.
    >>> natural_sort(example1)
    ['1 ft 5 in', '2 ft 7 in', '2 ft 11 in', '7 ft 6 in', '10 ft 2 in']

    >>> example2 = ['Elm11', 'Elm12', 'Elm2', 'elm0', 'elm1', 'elm10', 'elm13', 'elm9']
    >>> sorted(example2)
    ['Elm11', 'Elm12', 'Elm2', 'elm0', 'elm1', 'elm10', 'elm13', 'elm9']
    >>> natural_sort(example2)
    ['elm0', 'elm1', 'Elm2', 'elm9', 'elm10', 'Elm11', 'Elm12', 'elm13']
    """


# alphanum_key 函数实现
    def alphanum_key(key):
        return [int(s) if s.isdigit() else s.lower() for s in re.split("([0-9]+)", key)]
    # 返回结果

    return sorted(input_list, key=alphanum_key)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
