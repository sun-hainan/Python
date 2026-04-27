# -*- coding: utf-8 -*-

"""

算法实现：13_数学基础 / test_prime_check



本文件实现 test_prime_check 相关的算法功能。

"""



import math

import random





def is_prime_basic(n: int) -> bool:

    """

    基础试除法



    参数：

        n: 待检测的整数



    返回：是否为素数



    复杂度：时间O(√n)，空间O(1)

    """

    if n < 2:

        return False

    if n == 2:

        return True

    if n % 2 == 0:

        return False



    # 只需检测到√n

    for i in range(3, int(math.sqrt(n)) + 1, 2):

        if n % i == 0:

            return False



    return True





def is_prime_sieve(n: int, limit: int = 1000000) -> bool:

    """

    埃拉托斯特尼筛法



    先生成素数表，再查表判断



    参数：

        n: 待检测的数

        limit: 筛选上限



    返回：是否为素数



    复杂度：O(limit log log limit)预处理，O(1)查询

    """

    if n < 2:

        return False

    if n <= 3:

        return True

    if n % 2 == 0 or n % 3 == 0:

        return False



    sieve = [True] * (limit + 1)

    sieve[0] = sieve[1] = False



    for i in range(2, int(math.sqrt(limit)) + 1):

        if sieve[i]:

            for j in range(i * i, limit + 1, i):

                sieve[j] = False



    return sieve[n]





def is_prime_miller_rabin(n: int, k: int = 10) -> bool:

    """

    Miller-Rabin素性测试（概率算法）



    参数：

        n: 待检测的整数

        k: 测试轮数（轮数越多越准确）



    返回：是否为素数（高概率正确）



    复杂度：时间O(k log³n)



    注意：

        - 当n < 2^64时，只需测试特定的a即可保证正确

        - k=10对于实际应用足够安全

    """

    if n < 2:

        return False

    if n == 2 or n == 3:

        return True

    if n % 2 == 0:

        return False



    # 将 n-1 写成 d * 2^s 的形式

    d = n - 1

    s = 0

    while d % 2 == 0:

        d //= 2

        s += 1



    # 测试k轮

    for _ in range(k):

        # 选择随机底数

        a = random.randrange(2, n - 2)



        # 计算 x = a^d mod n

        x = pow(a, d, n)



        if x == 1 or x == n - 1:

            continue



        # 继续平方

        for _ in range(s - 1):

            x = (x * x) % n

            if x == n - 1:

                break

        else:

            # n是合数

            return False



    return True





def is_prime_deterministic(n: int) -> bool:

    """

    确定性Miller-Rabin（对64位整数有效）



    参数：

        n: 待检测的整数（n < 2^64）



    返回：是否为素数（确定）



    使用已知的确定性底数集合

    """

    if n < 2:

        return False

    if n == 2 or n == 3:

        return True

    if n % 2 == 0:

        return False



    # 对于 n < 2^64，以下底数足够

    test_bases = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]



    # 将 n-1 写成 d * 2^s

    d = n - 1

    s = 0

    while d % 2 == 0:

        d //= 2

        s += 1



    for a in test_bases:

        if a % n == 0:

            continue



        x = pow(a, d, n)



        if x == 1 or x == n - 1:

            continue



        for _ in range(s - 1):

            x = (x * x) % n

            if x == n - 1:

                break

        else:

            return False



    return True





def generate_primes(limit: int) -> list:

    """

    生成指定范围内的所有素数



    参数：

        limit: 上限



    返回：素数列表



    复杂度：时间O(limit log log limit)

    """

    sieve = [True] * (limit + 1)

    sieve[0] = sieve[1] = False



    for i in range(2, int(math.sqrt(limit)) + 1):

        if sieve[i]:

            for j in range(i * i, limit + 1, i):

                sieve[j] = False



    return [i for i in range(limit + 1) if sieve[i]]





def next_prime(n: int) -> int:

    """

    找到大于n的下一个素数



    参数：

        n: 起始数



    返回：下一个素数

    """

    candidate = n + 1

    if candidate % 2 == 0:

        candidate += 1



    while not is_prime_deterministic(candidate):

        candidate += 2



    return candidate





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 素数判定算法测试 ===\n")



    test_numbers = [1, 2, 17, 100, 561, 991, 1000, 104729, 15485863]



    print("素数判定结果:")

    for n in test_numbers:

        basic = is_prime_basic(n)

        miller = is_prime_miller_rabin(n)

        det = is_prime_deterministic(n)

        print(f"  {n:>10}: 试除法={'是' if basic else '否'}, Miller-Rabin={'是' if miller else '否'}, 确定性={'是' if det else '否'}")



    print()



    # 性能测试

    import time



    large_prime = 104729  # 10000附近的素数

    large_composite = 104730



    print("性能测试:")

    for n in [large_prime, large_composite]:

        start = time.time()

        for _ in range(1000):

            is_prime_basic(n)

        elapsed = time.time() - start

        print(f"  {n}: 1000次基础判定耗时 {elapsed*1000:.2f}ms")



    print()



    # 生成素数

    primes = generate_primes(100)

    print(f"100以内的素数（共{len(primes)}个）:")

    print(f"  {primes}")



    print()

    print("算法对比：")

    print("  试除法：简单直接，适合小数字")

    print("  埃氏筛法：批量生成，需要O(n)空间")

    print("  Miller-Rabin：适合大数，概率正确")

    print("  确定性Miller-Rabin：64位内保证正确")

    print()

    print("实际应用：")

    print("  - RSA: 需要512-4096位素数，必须用Miller-Rabin")

    print("  - 哈希表: 用素数做容量（如Python dict）")

