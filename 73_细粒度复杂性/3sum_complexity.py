# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / 3sum_complexity



本文件实现 3sum_complexity 相关的算法功能。

"""



import random

from typing import List





def brute_force_3sum(arr: List[int]) -> bool:

    """

    暴力3SUM



    复杂度：O(n^3)

    """

    n = len(arr)

    for i in range(n):

        for j in range(i + 1, n):

            for k in range(j + 1, n):

                if arr[i] + arr[j] + arr[k] == 0:

                    return True

    return False





def quadratic_3sum(arr: List[int]) -> bool:

    """

    O(n^2) 3SUM算法



    步骤：

    1. 排序数组

    2. 对每个对使用二分搜索找第三个数

    """

    n = len(arr)

    arr.sort()



    for i in range(n):

        for j in range(i + 1, n - 1):

            # 找 arr[i] + arr[j] + arr[k] = 0

            # 即 arr[k] = -(arr[i] + arr[j])

            target = -(arr[i] + arr[j])



            # 二分搜索

            left, right = j + 1, n - 1

            while left <= right:

                mid = (left + right) // 2

                if arr[mid] == target:

                    return True

                elif arr[mid] < target:

                    left = mid + 1

                else:

                    right = mid - 1



    return False





def three_sum_hash(arr: List[int]) -> bool:

    """

    基于哈希的O(n^2)方法



    将所有数放入哈希表，然后对每对查找

    """

    seen = set(arr)

    n = len(arr)



    for i in range(n):

        for j in range(i + 1, n):

            target = -(arr[i] + arr[j])

            if target in seen and arr.index(target) > j:

                return True



    return False





def get_all_triples(arr: List[int]) -> List[tuple]:

    """

    找出所有和为0的三元组

    """

    n = len(arr)

    arr.sort()

    triples = []



    for i in range(n):

        for j in range(i + 1, n - 1):

            target = -(arr[i] + arr[j])

            # 二分搜索

            left, right = j + 1, n - 1

            while left <= right:

                mid = (left + right) // 2

                if arr[mid] == target:

                    triples.append((arr[i], arr[j], target))

                    break

                elif arr[mid] < target:

                    left = mid + 1

                else:

                    right = mid - 1



    return triples





def seth_hardness():

    """3SUM的SETH硬度"""

    print("=== 3SUM 细粒度下界 ===")

    print()

    print("假设（3SUM conjecture）：")

    print("  3SUM无法在 O(n^2 / (log n)^c) 时间内解决")

    print("  其中c是任意正常数")

    print()

    print("推论：")

    print("  - 许多几何、图、字符串问题有类似下界")

    print("  - 包括：三角数检测、子字符串相等性等")





def hardness_applications():

    """3SUM硬度应用"""

    print()

    print("=== 3SUM-hardness 应用 ===")

    print()

    print("问题被归约为3SUM：")

    print("  1. 点的共线性检测")

    print("  2. 凸多边形顶点检测")

    print("  3. 线段交点检测")

    print("  4. 字符串匹配变体")

    print()

    print("这意味着：")

    print("  如果能更快解决3SUM，就能解决很多难题")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 3SUM问题测试 ===\n")



    # 测试用例

    test_cases = [

        [-1, 0, 1, 2, -1, -4],

        [0, 0, 0],

        [1, 2, 3, 4, 5],

        [-2, -1, 0, 1, 2, 3],

    ]



    for arr in test_cases:

        result = quadratic_3sum(arr)

        triples = get_all_triples(arr)

        print(f"数组: {arr}")

        print(f"  有解: {result}")

        print(f"  解: {triples}")

        print()



    print("复杂度对比：")

    print("  暴力：O(n^3)")

    print("  排序+二分：O(n^2 log n)")

    print("  哈希：O(n^2)")

    print()

    print("最优下界：Ω(n^2)（假设3SUM conjecture）")



    seth_hardness()

    hardness_applications()

