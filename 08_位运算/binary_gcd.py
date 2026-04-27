# -*- coding: utf-8 -*-

"""

算法实现：08_位运算 / binary_gcd



本文件实现 binary_gcd 相关的算法功能。

"""



def stein_gcd(a: int, b: int) -> int:

    """

    Stein算法核心：

    1. 若a=0，返回b

    2. 若b=0，返回a

    3. 统计a和b的公共因子2的个数k（两者同时除以2^k）

    4. 轮流用减法替代除法：若a为偶数则右移，否则用gcd((a-b)//2, b)

    """

    # 处理零值

    if a == 0:

        return b

    if b == 0:

        return a



    # 计算公共的2^k因子

    k = 0

    while ((a | b) & 1) == 0:  # 当a和b都是偶数

        a >>= 1

        b >>= 1

        k += 1



    # 消除a中的偶数因子

    while (a & 1) == 0:

        a >>= 1



    while b != 0:

        # 消除b中的偶数因子

        while (b & 1) == 0:

            b >>= 1

        # 交换：确保 a <= b

        if a > b:

            a, b = b, a

        # b = b - a，保留偶数因子

        b -= a



    return a << k  # 乘回公共的2^k





def stein_gcd_steps(a: int, b: int) -> list[str]:

    """返回GCD计算过程的步骤日志"""

    steps = []

    k = 0

    steps.append(f"初始: a={a}, b={b}")

    

    if a == 0:

        steps.append(f"a=0, 返回b={b}")

        return steps

    if b == 0:

        steps.append(f"b=0, 返回a={a}")

        return steps



    # 计算公共2^k

    while ((a | b) & 1) == 0:

        a >>= 1

        b >>= 1

        k += 1

        steps.append(f"同时除以2: k={k}, a={a}, b={b}")



    # 消除a的偶数因子

    while (a & 1) == 0:

        a >>= 1

        steps.append(f"消除a的偶数: a={a}")



    while b != 0:

        while (b & 1) == 0:

            b >>= 1

            steps.append(f"消除b的偶数: b={b}")

        if a > b:

            a, b = b, a

            steps.append(f"交换: a={a}, b={b}")

        b -= a

        steps.append(f"减法: b={b}")



    steps.append(f"结果: {a << k}")

    return steps





if __name__ == "__main__":

    test_pairs = [

        (48, 18),

        (100, 35),

        (17, 19),

        (0, 42),

        (128, 96),

        (54, 24),

    ]



    for a, b in test_pairs:

        result = stein_gcd(a, b)

        import math

        expected = math.gcd(a, b)

        status = "✓" if result == expected else "✗"

        print(f"{status} gcd({a},{b}) = {result} (期望{expected})")

        steps = stein_gcd_steps(a, b)

        print(f"  步骤: {' → '.join(steps[:5])}")

        print()

