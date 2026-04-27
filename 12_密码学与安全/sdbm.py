# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / sdbm



本文件实现 sdbm 相关的算法功能。

"""



def sdbm(plain_text: str) -> int:

    """

    计算字符串的 SDBM 哈希值。

    

    Args:

        plain_text: 输入字符串

    

    Returns:

        哈希值（可能为负数）

    

    示例:

        >>> sdbm('Algorithms')

        1462174910723540325254304520539387479031000036

        >>> sdbm('scramble bits')

        730247649148944819640658295400555317318720608290373040936089

    """

    hash_value = 0

    for plain_chr in plain_text:

        # hash = ord(c) + (hash << 6) + (hash << 16) - hash

        hash_value = (

            ord(plain_chr) + (hash_value << 6) + (hash_value << 16) - hash_value

        )

    return hash_value





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    test_strings = ["Algorithms", "scramble bits", "hello", "world"]

    for s in test_strings:

        print(f"sdbm('{s}') = {sdbm(s)}")

