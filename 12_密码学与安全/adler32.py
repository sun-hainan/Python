# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / adler32



本文件实现 adler32 相关的算法功能。

"""



# MOD_ADLER: 模数，取 65521（小于 2^16 的最大素数）

MOD_ADLER = 65521





def adler32(plain_text: str) -> int:

    """

    计算字符串的 Adler-32 校验和。

    

    Args:

        plain_text: 输入字符串

    

    Returns:

        32位校验和（整数）

    

    示例:

        >>> adler32('Algorithms')

        363791387

        >>> adler32('go adler em all')

        708642122

    """

    a = 1  # 初始值 A = 1

    b = 0  # 初始值 B = 0

    

    # 遍历每个字符，更新 A 和 B

    for plain_chr in plain_text:

        # A = (A + ord(c)) mod 65521

        a = (a + ord(plain_chr)) % MOD_ADLER

        # B = (B + A) mod 65521

        b = (b + a) % MOD_ADLER

    

    # 合并 A 和 B 得到 32 位结果

    return (b << 16) | a





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    # 测试用例

    test_strings = ["Algorithms", "hello", "world", ""]

    for s in test_strings:

        print(f"Adler-32('{s}') = {adler32(s)}")

