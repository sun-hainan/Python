# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / external_scan



本文件实现 external_scan 相关的算法功能。

"""



import random





def sequential_scan_cost(n, b):

    """

    顺序扫描 n 个元素的 I/O 成本。



    参数:

        n: 元素数量

        b: 每块可容纳的元素数



    返回:

        I/O 次数

    """

    return (n + b - 1) // b





def random_access_cost(n, b, m):

    """

    随机访问的 I/O 成本。



    假设内存可以容纳 m 个块。



    参数:

        n: 元素数量

        b: 块大小

        m: 内存中块的数量



    返回:

        平均 I/O 次数

    """

    # 每次访问平均需要加载一个新块

    return 1





def optimize_scan_order(data, block_size):

    """

    优化扫描顺序：按块对齐访问以减少 I/O。



    参数:

        data: 数据数组

        block_size: 块大小



    返回:

        处理所需的 I/O 次数

    """

    n = len(data)

    io_count = 0

    current_block = -1



    for i in range(n):

        expected_block = i // block_size

        if expected_block != current_block:

            io_count += 1

            current_block = expected_block



    return io_count





def prefetch_scan(data, block_size, prefetch_distance=2):

    """

    预取优化：提前加载下一个块。



    参数:

        data: 数据数组

        block_size: 块大小

        prefetch_distance: 预取距离（提前多少块）



    返回:

        实际 I/O 次数（考虑预取）

    """

    n = len(data)

    num_blocks = (n + block_size - 1) // block_size

    io_count = 0

    prefetched = set()



    for i in range(n):

        block_id = i // block_size



        if block_id not in prefetched:

            # 需要加载这个块

            io_count += 1

            # 预取后续块

            for d in range(1, prefetch_distance + 1):

                next_block = block_id + d

                if next_block < num_blocks:

                    prefetched.add(next_block)



    return io_count





def amortized_scan_analysis(n, b, k):

    """

    分摊分析：连续 k 次扫描的 I/O 成本。



    参数:

        n: 元素数

        b: 块大小

        k: 扫描次数



    返回:

        总 I/O 和平均 I/O

    """

    # 第一次扫描需要加载所有块

    first_io = sequential_scan_cost(n, b)



    # 后续扫描如果数据没变，可以缓存命中

    subsequent_io = 0



    return first_io, subsequent_io





def simulate_disk_access(data, block_size, access_pattern):

    """

    模拟磁盘访问并计算 I/O。



    参数:

        data: 数据数组

        block_size: 块大小

        access_pattern: 访问模式列表（索引序列）

    """

    loaded_blocks = set()

    io_count = 0



    for idx in access_pattern:

        block_id = idx // block_size

        if block_id not in loaded_blocks:

            io_count += 1

            loaded_blocks.add(block_id)

            # 简化：只保留最近加载的几个块

            if len(loaded_blocks) > 4:

                loaded_blocks = {block_id}



    return io_count





if __name__ == "__main__":

    print("=== 外部记忆扫描分析 ===")



    # 参数设置

    n = 10**6       # 1M 元素

    b = 4000        # 块大小

    m = 1000        # 内存块数



    print(f"参数: N={n:,}, B={b}, M={m}")



    # 顺序扫描

    scan_io = sequential_scan_cost(n, b)

    print(f"\n顺序扫描 I/O: {scan_io:,}")



    # 优化顺序

    test_data = list(range(n))

    opt_io = optimize_scan_order(test_data, b)

    print(f"优化顺序扫描 I/O: {opt_io}")



    # 预取优化

    for dist in [1, 2, 4]:

        prefetch_io = prefetch_scan(test_data[:10000], 100, prefetch_distance=dist)

        print(f"预取距离={dist} 的 I/O: {prefetch_io}")



    # 随机访问模式

    print("\n=== 随机访问模拟 ===")

    random.seed(42)

    access_pattern = [random.randint(0, 9999) for _ in range(100)]

    block_size = 100



    sequential_pattern = list(range(100))

    io_seq = simulate_disk_access(test_data, block_size, sequential_pattern)

    io_rand = simulate_disk_access(test_data, block_size, access_pattern)



    print(f"顺序访问 100 次: {io_seq} I/O")

    print(f"随机访问 100 次: {io_rand} I/O")



    # 分摊分析

    print("\n=== 分摊分析 ===")

    for k in [1, 10, 100]:

        first, subsequent = amortized_scan_analysis(n, b, k)

        total = first + subsequent * (k - 1)

        avg = total / k

        print(f"k={k}: 总 I/O={total}, 平均={avg:.2f}")



    print("\n扫描优化策略:")

    print("  块对齐访问：减少不必要的块加载")

    print("  预取：重叠 I/O 和计算")

    print("  缓存复用：同一块在短时间内多次访问")

    print("  批量处理：减少随机访问次数")

