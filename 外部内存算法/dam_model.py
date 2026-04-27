# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / dam_model



本文件实现 dam_model 相关的算法功能。

"""



import math





def dam_scan_cost(n, b):

    """

    扫描操作的 DAM 成本：读取所有 n 个元素。



    参数:

        n: 元素数量

        b: 每块可容纳的元素数



    返回:

        I/O 次数

    """

    return (n + b - 1) // b





def dam_search_cost(n, b, compare_cost=1):

    """

    二分搜索的 DAM 成本。



    每次比较需要一次 I/O（读取块），最多 log(n) 次比较。



    参数:

        n: 元素数量

        b: 每块大小

        compare_cost: 每次比较的 I/O 成本



    返回:

        总 I/O 次数

    """

    depth = math.ceil(math.log2(n))

    # 每一层深度可能需要一次 I/O

    return depth * compare_cost





def dam_range_search_cost(n, r, b):

    """

    范围查询的 DAM 成本。



    找到第一个元素：O(log_b n) 次 I/O

    读取结果：O(r/b) 次 I/O（r 个结果分散在 r/b 块中）



    参数:

        n: 总元素数

        r: 查询结果数

        b: 块大小



    返回:

        总 I/O 次数

    """

    # 搜索成本 + 结果读取成本

    search_io = math.ceil(math.log2(n))

    result_io = (r + b - 1) // b

    return search_io + result_io





def dam_sorting_lower_bound(n, b):

    """

    排序的 DAM 下界。



    定理：排序 n 个元素至少需要 Ω((n/b) * log_{b}(n/b)) 次 I/O。



    参数:

        n: 元素数

        b: 块大小



    返回:

        下界（近似）

    """

    runs = n // b

    return math.ceil((n / b) * math.log2(runs))





def external_merge_sort(data, b, m):

    """

    外部归并排序。



    阶段1：每次读取 M 个元素到内存，排序后写出（生成 n/M 个有序段）

    阶段2：每次读取 M 个有序段，归并排序



    参数:

        data: 数据列表

        b: 块大小

        m: 内存可容纳的块数



    返回:

        排序后的数据

    """

    n = len(data)

    elements_per_run = m * b



    # 阶段1：生成初始有序段

    runs = []

    for i in range(0, n, elements_per_run):

        run = sorted(data[i:i + elements_per_run])

        runs.append(run)



    # 阶段2：K 路归并

    while len(runs) > 1:

        # 每次归并最多 m 个有序段

        new_runs = []

        for i in range(0, len(runs), m):

            group = runs[i:i + m]

            merged = _k_way_merge(group)

            new_runs.append(merged)

        runs = new_runs



    return runs[0] if runs else []





def _k_way_merge(sorted_lists):

    """K路归并（简化）。"""

    import heapq

    heap = []

    result = []



    for idx, lst in enumerate(sorted_lists):

        if lst:

            heapq.heappush(heap, (lst[0], idx, 0))



    lists = [list(lst) for lst in sorted_lists]



    while heap:

        val, list_idx, elem_idx = heapq.heappop(heap)

        result.append(val)

        next_idx = elem_idx + 1

        if next_idx < len(lists[list_idx]):

            heapq.heappush(heap, (lists[list_idx][next_idx], list_idx, next_idx))



    return result





def dam_io_analysis(n, b, m, operation):

    """

    统一分析各类操作的 DAM I/O 复杂度。



    参数:

        n: 元素数

        b: 块大小

        m: 内存块数

        operation: 操作类型



    返回:

        I/O 次数和分析

    """

    analysis = {

        'scan': dam_scan_cost(n, b),

        'binary_search': dam_search_cost(n, b),

        'sorting_lower_bound': dam_sorting_lower_bound(n, b),

    }



    if operation == 'sort':

        return analysis['sorting_lower_bound']

    elif operation == 'scan':

        return analysis['scan']

    elif operation == 'search':

        return analysis['binary_search']



    return analysis





if __name__ == "__main__":

    print("=== DAM 模型 I/O 分析 ===")



    # 参数设置

    n = 10**6        # 1M 元素

    b = 4000         # 每块 4000 个整数（约 16KB）

    m = 1000         # 内存可容纳 1000 块（约 16MB）



    print(f"参数: N={n:,}, B={b}, M={m} blocks")

    print(f"估计内存大小: {m * b * 4 / 1024 / 1024:.1f} MB")

    print(f"磁盘块数: {n // b:,}")



    # 扫描

    scan_io = dam_scan_cost(n, b)

    print(f"\n扫描: {scan_io:,} 次 I/O")



    # 二分搜索

    search_io = dam_search_cost(n, b)

    print(f"二分搜索: {search_io} 次 I/O")



    # 排序下界

    sort_lower = dam_sorting_lower_bound(n, b)

    print(f"排序 I/O 下界: ~{sort_lower:,}")



    # 范围查询

    for r in [10, 100, 1000]:

        range_io = dam_range_search_cost(n, r, b)

        print(f"\n范围查询 (r={r}): {range_io} 次 I/O")



    # 外部归并排序 I/O 计数

    print("\n=== 外部归并排序模拟 ===")

    test_data = list(range(100, 0, -1))

    b_test = 5

    m_test = 3  # 每次可容纳 3 块

    sorted_result = external_merge_sort(test_data, b_test, m_test)

    print(f"测试数据: {test_data}")

    print(f"排序结果: {sorted_result}")

    print(f"是否有序: {sorted_result == sorted(test_data)}")



    print("\nDAM 模型要点:")

    print("  扫描: Θ(n/b)")

    print("  搜索: Θ(log_b n)")

    print("  排序: Θ((n/b) * log_m/b (n/m))")

