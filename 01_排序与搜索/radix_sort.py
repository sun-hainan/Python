# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / radix_sort



本文件实现 radix_sort 相关的算法功能。

"""



from typing import List





def counting_sort_for_radix(arr: List[int], exp: int, base: int = 10) -> List[int]:

    """

    按指定位数进行计数排序（基数排序的稳定子步骤）



    参数：

        arr: 输入数组

        exp: 10的幂次（1, 10, 100, ...）

        base: 进制基数

    """

    n = len(arr)

    output = [0] * n

    count = [0] * base



    # 统计每个桶的数量

    for num in arr:

        digit = (num // exp) % base

        count[digit] += 1



    # 累加count（确定位置）

    for i in range(1, base):

        count[i] += count[i - 1]



    # 从后往前遍历，保证稳定性

    for i in range(n - 1, -1, -1):

        digit = (arr[i] // exp) % base

        output[count[digit] - 1] = arr[i]

        count[digit] -= 1



    return output





def radix_sort_lsd(arr: List[int]) -> List[int]:

    """

    基数排序（LSD，最低有效位优先）



    参数：

        arr: 非负整数数组



    返回：排序后的数组

    """

    if not arr:

        return []



    # 找到最大数以确定位数

    max_val = max(arr)

    if max_val == 0:

        return arr.copy()



    # 从低位到高位逐位排序

    exp = 1

    while max_val // exp > 0:

        arr = counting_sort_for_radix(arr, exp)

        exp *= 10



    return arr





def radix_sort_msd(arr: List[int], base: int = 10) -> List[int]:

    """

    基数排序（MSD，最高有效位优先）



    递归版本

    """

    if not arr or len(arr) <= 1:

        return arr.copy()



    max_val = max(arr) if arr else 0



    # 找到最大位数

    max_digits = len(str(max_val)) if max_val > 0 else 1



    def sort_recursive(arr: List[int], digit: int) -> List[int]:

        if not arr or digit < 0:

            return arr



        # 按当前位分组

        buckets = [[] for _ in range(base)]

        for num in arr:

            d = (num // (base ** digit)) % base

            buckets[d].append(num)



        # 递归处理下一位

        result = []

        for bucket in buckets:

            if len(bucket) > 1 and digit > 0:

                result.extend(sort_recursive(bucket, digit - 1))

            else:

                result.extend(bucket)



        return result



    return sort_recursive(arr, max_digits - 1)





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 基数排序测试 ===\n")



    import random



    test_cases = [

        [170, 45, 75, 90, 802, 24, 2, 66],

        list(range(20, 0, -1)),

        [random.randint(1, 10000) for _ in range(30)],

        [999, 123, 456, 789, 321, 654, 987, 111],

        [1],

        [5, 5, 5, 5],

    ]



    for arr in test_cases:

        original = arr.copy()

        result = radix_sort_lsd(arr)

        expected = sorted(original)

        print(f"原始: {original[:10]}{'...' if len(original) > 10 else ''}")

        print(f"结果: {result[:10]}{'...' if len(result) > 10 else ''}")

        print(f"正确: {'✅' if result == expected else '❌'}")

        print()



    # 性能测试

    import time



    sizes = [1000, 10000]

    print("性能测试（n=位数）：")



    for size in sizes:

        arr = [random.randint(1, size * 10) for _ in range(size)]



        start = time.time()

        radix_sort_lsd(arr.copy())

        time_lsd = time.time() - start



        print(f"  n={size:5d}: LSD耗时 {time_lsd*1000:.2f}ms")



    print("\n说明：")

    print("  - LSD：从低位到高位，稳定排序")

    print("  - MSD：从高位到低位，可递归优化")

    print("  - 适用于整数或字符串排序")

