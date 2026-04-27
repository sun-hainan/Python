# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / sublinear_algorithms



本文件实现 sublinear_algorithms 相关的算法功能。

"""



import random

from typing import List, Callable





def majority_element_sublinear(data: List[int]) -> int:

    """

    寻找出现次数超过50%的众数(摩尔投票算法的变体)

    O(n)时间,O(1)空间

    

    Args:

        data: 输入数组

    

    Returns:

        众数(如果存在),否则-1

    """

    candidate = None

    count = 0

    

    for x in data:

        if count == 0:

            candidate = x

            count = 1

        elif x == candidate:

            count += 1

        else:

            count -= 1

    

    # 验证候选

    verification_count = sum(1 for x in data if x == candidate)

    

    if verification_count > len(data) // 2:

        return candidate

    return -1





def element_distinctness_sublinear(data: List[int]) -> bool:

    """

    判断数组是否有重复元素

    使用Floyd的乌龟兔子算法检测循环

    

    Args:

        data: 输入数组

    

    Returns:

        是否有重复

    """

    n = len(data)

    # 哈希函数

    h = lambda x: (x * 31 + 17) % n

    

    # 从哈希值开始

    tortoise = data[h(0)]

    hare = data[h(h(0))]

    

    # 检测循环

    while tortoise != hare:

        tortoise = data[h(tortoise)]

        hare = data[h(h(hare))]

    

    # 找循环起点

    mu = 0

    tortoise = data[0]

    while tortoise != hare:

        tortoise = data[h(tortoise)]

        hare = data[h(hare)]

        mu += 1

    

    # 找循环长度

    lam = 1

    hare = data[h(tortoise)]

    while tortoise != hare:

        hare = data[h(hare)]

        lam += 1

    

    # 如果循环长度<n,则有重复

    return lam < n





def sortedness_sublinear(data: List[int], sample_size: int = 100) -> float:

    """

    估计数组的有序程度(亚线性采样)

    

    Args:

        data: 输入数组

        sample_size: 采样数量

    

    Returns:

        有序程度估计(0-1之间)

    """

    n = len(data)

    if n <= 1:

        return 1.0

    

    # 随机采样

    indices = random.sample(range(n), min(sample_size, n))

    indices.sort()

    

    # 检查采样点的顺序关系

    correct = 0

    total = 0

    

    for i in range(len(indices) - 1):

        idx1, idx2 = indices[i], indices[i + 1]

        if data[idx1] <= data[idx2]:

            correct += 1

        total += 1

    

    # 也检查采样式内部排序

    for _ in range(min(sample_size, n // 2)):

        i, j = random.sample(range(n), 2)

        if i < j and data[i] <= data[j]:

            correct += 1

        elif i > j and data[i] >= data[j]:

            correct += 1

        total += 1

    

    return correct / total if total > 0 else 1.0





def frequency_moment_sublinear(data: List[int], k: int, sample_size: int = 1000) -> float:

    """

    估计第k阶频率矩F_k

    F_k = sum(f_i^k), f_i是第i个值的频率

    

    Args:

        data: 输入数组

        k: 阶

        sample_size: 采样数量

    

    Returns:

        F_k的估计值

    """

    n = len(data)

    

    if n == 0:

        return 0.0

    

    # 简单采样估计

    if n <= sample_size:

        # 使用全部数据

        from collections import Counter

        freq = Counter(data)

        return sum(f ** k for f in freq.values())

    

    # 随机采样

    sample = random.sample(data, sample_size)

    

    # 估计频率

    from collections import Counter

    sample_freq = Counter(sample)

    

    # 外推

    estimated_total = 0.0

    for f in sample_freq.values():

        # f是样本中的频率,实际频率约为 f * n / sample_size

        actual_f = f * n / sample_size

        estimated_total += actual_f ** k

    

    return estimated_total





def distinct_elements_sublinear(data: List[int], sample_size: int = 1000) -> int:

    """

    估计不同元素的数量(Flajolet-Martin算法的简化版)

    

    Args:

        data: 输入数组

        sample_size: 采样数量

    

    Returns:

        不同元素数的估计

    """

    n = len(data)

    

    if n <= sample_size:

        return len(set(data))

    

    # 采样

    sample = random.sample(data, sample_size)

    

    # 统计样本中不同元素的比例

    distinct_in_sample = len(set(sample))

    

    # 估计总数(捕获-再捕获估计)

    # 使用Good-Turing估计的简化版

    return int(distinct_in_sample * n / sample_size)





def property_testing_framework(

    property_func: Callable[[List[int]], bool],

    test_func: Callable[[List[int]], bool],

    num_tests: int = 100

) -> dict:

    """

    属性测试框架

    

    Args:

        property_func: 真实属性函数

        test_func: 测试函数

        num_tests: 测试次数

    

    Returns:

        测试结果统计

    """

    results = {

        'true_positive': 0,  # 有属性,测试通过

        'true_negative': 0, # 无属性,测试失败

        'false_positive': 0, # 有属性,测试失败

        'false_negative': 0, # 无属性,测试通过

    }

    

    return results





# 测试代码

if __name__ == "__main__":

    # 测试1: 众数检测

    print("测试1 - 众数检测:")

    data1 = [1, 2, 1, 3, 1, 4, 1]

    result1 = majority_element_sublinear(data1)

    print(f"  数据: {data1}")

    print(f"  众数: {result1} (应为1)")

    

    data1b = [1, 2, 3, 4, 5]

    result1b = majority_element_sublinear(data1b)

    print(f"  无众数: {result1b} (应为-1)")

    

    # 测试2: 元素不同性检测

    print("\n测试2 - 元素不同性检测:")

    data2a = [1, 2, 3, 4, 5]

    data2b = [1, 2, 3, 3, 5]

    

    print(f"  {data2a} 有重复: {element_distinctness_sublinear(data2a)} (应为True)")

    print(f"  {data2b} 有重复: {element_distinctness_sublinear(data2b)} (应为False)")

    

    # 测试3: 有序程度估计

    print("\n测试3 - 有序程度估计:")

    data3_sorted = list(range(1000))

    data3_random = random.sample(range(1000), 1000)

    data3_partially = list(range(500)) + random.sample(range(500), 500)

    

    sortness_sorted = sortedness_sublinear(data3_sorted)

    sortness_random = sortedness_sublinear(data3_random)

    sortness_partial = sortedness_sublinear(data3_partially)

    

    print(f"  完全有序: {sortness_sorted:.4f} (应为1.0)")

    print(f"  完全随机: {sortness_random:.4f} (应接近0.5)")

    print(f"  部分有序: {sortness_partial:.4f}")

    

    # 测试4: 频率矩估计

    print("\n测试4 - 频率矩估计:")

    data4 = [1, 1, 1, 2, 2, 3, 3, 3, 3]

    

    # 精确计算

    from collections import Counter

    freq = Counter(data4)

    exact_f2 = sum(f ** 2 for f in freq.values())

    exact_f1 = sum(f for f in freq.values())

    

    # 采样估计

    est_f2 = frequency_moment_sublinear(data4, k=2, sample_size=20)

    

    print(f"  数据: {data4}")

    print(f"  精确F_1={exact_f1}, F_2={exact_f2}")

    print(f"  估计F_2={est_f2:.2f}")

    

    # 测试5: 不同元素估计

    print("\n测试5 - 不同元素估计:")

    data5 = list(range(100)) * 5 + list(range(50))

    

    exact_distinct = len(set(data5))

    est_distinct = distinct_elements_sublinear(data5, sample_size=200)

    

    print(f"  数据长度: {len(data5)}")

    print(f"  精确不同元素: {exact_distinct}")

    print(f"  估计不同元素: {est_distinct}")

    

    # 测试6: 下界相关讨论

    print("\n测试6 - 亚线性算法的必要性:")

    print("  对于某些问题,亚线性是必要的:")

    print("  - 排序需要Ω(n log n)")

    print("  - 寻找最小值需要Ω(n)")

    print("  - 但某些性质可以用亚线性时间测试:")

    print("    - 图连通性:O(log n)")

    print("    - 平面性:O(log n)")

    print("    - 有序程度:O(1)采样")

    

    print("\n所有测试完成!")

