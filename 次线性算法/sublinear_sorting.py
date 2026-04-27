# -*- coding: utf-8 -*-

"""

算法实现：次线性算法 / sublinear_sorting



本文件实现 sublinear_sorting 相关的算法功能。

"""



import numpy as np

import random





def sample_sort(arr, sample_size=None):

    """

    采样排序: 先采样估计分布,再排序

    

    核心思想:

    1. 随机采样 s = O(1/ε^2) 个元素

    2. 排序采样得到分位点

    3. 将元素分配到桶中

    4. 在桶内排序

    

    时间复杂度: O(n) 对于固定 ε

    

    Parameters

    ----------

    arr : list

        输入数组

    sample_size : int

        采样大小,默认 sqrt(n)

    

    Returns

    -------

    list

        排序后的数组

    """

    n = len(arr)

    

    if n <= 1:

        return arr.copy()

    

    # 默认采样大小为 sqrt(n)

    if sample_size is None:

        sample_size = max(1, int(np.sqrt(n)))

    

    # 随机采样

    if n <= sample_size:

        sample = arr.copy()

    else:

        indices = random.sample(range(n), sample_size)

        sample = [arr[i] for i in indices]

    

    # 排序采样

    sample_sorted = sorted(sample)

    

    # 选择分位点作为桶边界

    # 使用等距分位点

    num_buckets = sample_size

    bucket_boundaries = []

    

    for i in range(1, num_buckets):

        idx = int(i * len(sample_sorted) / num_buckets)

        bucket_boundaries.append(sample_sorted[idx])

    

    # 分配元素到桶

    buckets = [[] for _ in range(num_buckets)]

    

    for x in arr:

        # 找到 x 所属的桶

        bucket_idx = 0

        for i, boundary in enumerate(bucket_boundaries):

            if x >= boundary:

                bucket_idx = i + 1

        

        buckets[bucket_idx].append(x)

    

    # 在每个桶内排序并连接

    result = []

    for bucket in buckets:

        result.extend(sorted(bucket))

    

    return result





def bucket_sort(arr, num_buckets=None):

    """

    桶排序 (Bucket Sort)

    

    适用于均匀分布的数据

    

    时间复杂度: O(n) 期望 (当数据均匀分布时)

    空间复杂度: O(n + m)

    

    Parameters

    ----------

    arr : list

        输入数组

    num_buckets : int

        桶的数量,默认 sqrt(n)

    

    Returns

    -------

    list

        排序后的数组

    """

    n = len(arr)

    

    if n <= 1:

        return arr.copy()

    

    # 确定桶数量

    if num_buckets is None:

        num_buckets = max(1, int(np.sqrt(n)))

    

    # 找到数据范围

    min_val = min(arr)

    max_val = max(arr)

    

    if min_val == max_val:

        return arr.copy()

    

    # 创建桶

    buckets = [[] for _ in range(num_buckets)]

    

    # 计算桶范围

    range_val = max_val - min_val

    

    # 分配元素到桶

    for x in arr:

        # 计算桶索引

        bucket_idx = int((x - min_val) / range_val * (num_buckets - 1))

        bucket_idx = max(0, min(num_buckets - 1, bucket_idx))

        buckets[bucket_idx].append(x)

    

    # 对每个桶排序并连接

    result = []

    for bucket in buckets:

        result.extend(sorted(bucket))

    

    return result





def radix_sort_lsd(arr, base=10):

    """

    最低位优先基数排序 (LSD Radix Sort)

    

    从最低位到最高位逐位排序

    使用计数排序作为稳定排序子程序

    

    时间复杂度: O(d * (n + base)), d = 位数

    

    Parameters

    ----------

    arr : list

        输入数组 (非负整数)

    base : int

        基数,默认 10

    

    Returns

    -------

    list

        排序后的数组

    """

    if not arr:

        return []

    

    # 找到最大数确定位数

    max_val = max(arr)

    

    if max_val == 0:

        return arr.copy()

    

    # 确定位数

    num_digits = 0

    temp = max_val

    while temp > 0:

        num_digits += 1

        temp //= base

    

    # 从最低位开始排序

    result = arr.copy()

    

    exp = 1  # 当前处理的位数

    while exp <= max_val:

        # 计数排序按当前位排序

        result = counting_sort_by_digit(result, base, exp)

        exp *= base

    

    return result





def counting_sort_by_digit(arr, base, exp):

    """

    按指定位数进行计数排序 (基数排序的子程序)

    

    Parameters

    ----------

    arr : list

        输入数组

    base : int

        基数

    exp : int

        当前位数 (1, 10, 100, ...)

    

    Returns

    -------

    list

        按当前位排序后的数组

    """

    n = len(arr)

    

    # 统计每个桶的数量

    count = [0] * base

    

    for x in arr:

        digit = (x // exp) % base

        count[digit] += 1

    

    # 累加得到位置

    output = [0] * n

    position = [0] * base

    

    # 计算起始位置

    pos = 0

    for i in range(base):

        position[i] = pos

        pos += count[i]

    

    # 放置元素

    for x in arr:

        digit = (x // exp) % base

        output[position[digit]] = x

        position[digit] += 1

    

    return output





def quicksort_inplace(arr, low=None, high=None):

    """

    原地快速排序 (作为基准比较)

    

    时间复杂度: O(n log n) 平均, O(n^2) 最坏

    空间复杂度: O(log n)

    

    Parameters

    ----------

    arr : list

        输入数组

    low : int

        起始索引

    high : int

        结束索引

    

    Returns

    -------

    list

        排序后的数组 (原地修改)

    """

    if low is None:

        low = 0

    if high is None:

        high = len(arr) - 1

    

    if low < high:

        # 分区

        pivot_idx = partition(arr, low, high)

        

        # 递归排序

        quicksort_inplace(arr, low, pivot_idx - 1)

        quicksort_inplace(arr, pivot_idx + 1, high)

    

    return arr





def partition(arr, low, high):

    """

    快速排序的分区操作

    

    Parameters

    ----------

    arr : list

        数组

    low : int

        起始索引

    high : int

        结束索引 (pivot)

    

    Returns

    -------

    int

        pivot 的最终位置

    """

    pivot = arr[high]

    i = low - 1

    

    for j in range(low, high):

        if arr[j] <= pivot:

            i += 1

            arr[i], arr[j] = arr[j], arr[i]

    

    arr[i + 1], arr[high] = arr[high], arr[i + 1]

    

    return i + 1





def merge_sort(arr):

    """

    归并排序 (作为基准比较)

    

    时间复杂度: O(n log n)

    空间复杂度: O(n)

    

    Parameters

    ----------

    arr : list

        输入数组

    

    Returns

    -------

    list

        排序后的数组

    """

    n = len(arr)

    

    if n <= 1:

        return arr.copy()

    

    mid = n // 2

    left = merge_sort(arr[:mid])

    right = merge_sort(arr[mid:])

    

    return merge(left, right)





def merge(left, right):

    """

    归并操作

    

    Parameters

    ----------

    left : list

        左半部分

    right : list

        右半部分

    

    Returns

    -------

    list

        合并后的有序数组

    """

    result = []

    i = j = 0

    

    while i < len(left) and j < len(right):

        if left[i] <= right[j]:

            result.append(left[i])

            i += 1

        else:

            result.append(right[j])

            j += 1

    

    result.extend(left[i:])

    result.extend(right[j:])

    

    return result





def approximate_sorting_error(sorted_arr, true_sorted):

    """

    计算近似排序的错误率

    

    使用 Kendall tau 距离或反转数

    

    Parameters

    ----------

    sorted_arr : list

        算法输出的排序

    true_sorted : list

        正确的排序

    

    Returns

    -------

    float

        错误率 (反转对数 / 总对数)

    """

    n = len(sorted_arr)

    

    if n <= 1:

        return 0.0

    

    # 计算反转对数

    inversions = 0

    for i in range(n):

        for j in range(i + 1, n):

            # 检查是否与真序一致

            true_i = true_sorted.index(sorted_arr[i])

            true_j = true_sorted.index(sorted_arr[j])

            

            if true_i > true_j:

                inversions += 1

    

    total_pairs = n * (n - 1) // 2

    return inversions / total_pairs





def sublinear_sorting_time(n, epsilon=0.1):

    """

    亚线性排序的时间复杂度分析

    

    对于 n 个元素,采样排序的时间:

    - 采样: O(1/ε^2)

    - 分桶: O(n)

    - 桶内排序: O(n) 期望

    

    总时间: O(n + 1/ε^2) = O(n) (当 ε 固定时)

    

    Parameters

    ----------

    n : int

        元素数量

    epsilon : float

        近似参数

    

    Returns

    -------

    dict

        各阶段时间复杂度

    """

    sample_size = int(1 / (epsilon ** 2))

    

    return {

        'sampling': min(sample_size, n),

        'bucket_assignment': n,

        'intra_bucket_sorting': n,

        'total': min(sample_size, n) + 2 * n

    }





if __name__ == "__main__":

    # 测试: 亚线性排序算法

    

    print("=" * 60)

    print("亚线性排序算法测试")

    print("=" * 60)

    

    random.seed(42)

    np.random.seed(42)

    

    # 生成测试数据

    n = 100

    test_arr = [random.randint(0, 1000) for _ in range(n)]

    true_sorted = sorted(test_arr)

    

    print(f"\n数组大小: {n}")

    print(f"测试数据前10个: {test_arr[:10]}")

    

    # 测试采样排序

    print("\n--- 采样排序 ---")

    sorted_sample = sample_sort(test_arr)

    error_sample = approximate_sorting_error(sorted_sample, true_sorted)

    print(f"排序结果前10个: {sorted_sample[:10]}")

    print(f"错误率: {error_sample:.4f}")

    

    # 测试桶排序

    print("\n--- 桶排序 ---")

    sorted_bucket = bucket_sort(test_arr)

    is_correct_bucket = sorted_bucket == true_sorted

    print(f"完全正确: {is_correct_bucket}")

    print(f"排序结果前10个: {sorted_bucket[:10]}")

    

    # 测试基数排序

    print("\n--- 基数排序 ---")

    sorted_radix = radix_sort_lsd(test_arr)

    is_correct_radix = sorted_radix == true_sorted

    print(f"完全正确: {is_correct_radix}")

    print(f"排序结果前10个: {sorted_radix[:10]}")

    

    # 比较基准排序

    print("\n--- 基准排序比较 ---")

    

    # 快速排序

    arr_quick = test_arr.copy()

    sorted_quick = quicksort_inplace(arr_quick)

    

    # 归并排序

    sorted_merge = merge_sort(test_arr)

    

    print(f"快速排序正确: {sorted_quick == true_sorted}")

    print(f"归并排序正确: {sorted_merge == true_sorted}")

    

    # 时间复杂度分析

    print("\n--- 时间复杂度分析 ---")

    for n_size in [100, 1000, 10000]:

        complexity = sublinear_sorting_time(n_size, epsilon=0.1)

        print(f"n={n_size}: 采样={complexity['sampling']}, 总时间={complexity['total']}")

    

    # 均匀分布数据测试

    print("\n--- 均匀分布数据测试 ---")

    uniform_arr = [random.uniform(0, 1) for _ in range(1000)]

    true_sorted_uniform = sorted(uniform_arr)

    

    sorted_bucket_uniform = bucket_sort(uniform_arr, num_buckets=100)

    is_correct_uniform = sorted_bucket_uniform == true_sorted_uniform

    print(f"桶排序完全正确 (均匀分布): {is_correct_uniform}")

    

    print("\n" + "=" * 60)

    print("测试完成!")

    print("=" * 60)

