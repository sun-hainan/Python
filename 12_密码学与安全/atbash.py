# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / atbash

本文件实现 atbash 相关的算法功能。
"""

import string



# atbash_slow 函数实现
def atbash_slow(sequence: str) -> str:
    """
    >>> atbash_slow("ABCDEFG")
    'ZYXWVUT'

    >>> atbash_slow("aW;;123BX")
    'zD;;123YC'
    """
    output = ""
    for i in sequence:
    # 遍历循环
        extract = ord(i)
        if 65 <= extract <= 90:
    # 条件判断
            output += chr(155 - extract)
        elif 97 <= extract <= 122:
            output += chr(219 - extract)
        else:
            output += i
    return output
    # 返回结果



# atbash 函数实现
def atbash(sequence: str) -> str:
    """
    >>> atbash("ABCDEFG")
    'ZYXWVUT'

    >>> atbash("aW;;123BX")
    'zD;;123YC'
    """
    letters = string.ascii_letters
    letters_reversed = string.ascii_lowercase[::-1] + string.ascii_uppercase[::-1]
    return "".join(
    # 返回结果
        letters_reversed[letters.index(c)] if c in letters else c for c in sequence
    )



# benchmark 函数实现
def benchmark() -> None:
    """Let's benchmark our functions side-by-side..."""
    from timeit import timeit

    print("Running performance benchmarks...")
    setup = "from string import printable ; from __main__ import atbash, atbash_slow"
    print(f"> atbash_slow(): {timeit('atbash_slow(printable)', setup=setup)} seconds")
    print(f">      atbash(): {timeit('atbash(printable)', setup=setup)} seconds")


if __name__ == "__main__":
    # 条件判断
    for example in ("ABCDEFGH", "123GGjj", "testStringtest", "with space"):
    # 遍历循环
        print(f"{example} encrypted in atbash: {atbash(example)}")
    benchmark()
