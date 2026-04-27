# -*- coding: utf-8 -*-

"""

算法实现：并行算法 / parallel_filter



本文件实现 parallel_filter 相关的算法功能。

"""



from concurrent.futures import ThreadPoolExecutor

from typing import Callable, List, TypeVar, Any



T = TypeVar('T')  # 输入类型

R = TypeVar('R')  # 输出类型





def parallel_map(func: Callable[[T], R], arr: List[T], num_workers: int = None) -> List[R]:

    """

    并行映射：将函数应用于数组的每个元素

    

    参数:

        func: 转换函数，接收一个元素，返回转换后的元素

        arr: 输入数组

        num_workers: 并行工作线程数

    

    返回:

        result: 转换后的新数组

    

    示例:

        >>> parallel_map(lambda x: x * 2, [1, 2, 3])

        [2, 4, 6]

    

    复杂度: O(n/p) 并行部分 + O(n) 合并

    """

    n = len(arr)

    

    if n == 0:

        return []

    

    if n <= 512:

        # 小规模数据直接串行处理

        return [func(elem) for elem in arr]

    

    # 计算分块大小

    num_workers = num_workers or 4

    chunk_size = max(1, n // num_workers)

    

    # 将数组分块

    chunks = []

    for i in range(0, n, chunk_size):

        chunks.append((arr[i:i + chunk_size], func))

    

    # 并行处理各块

    results = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:

        futures = [executor.submit(process_map_chunk, chunk) for chunk in chunks]

        for future in futures:

            results.append(future.result())

    

    # 合并结果

    merged = []

    for chunk_result in results:

        merged.extend(chunk_result)

    

    return merged





def process_map_chunk(chunk):

    """处理映射块：应用函数到块内每个元素"""

    arr, func = chunk

    return [func(elem) for elem in arr]





def parallel_filter(predicate: Callable[[T], bool], arr: List[T], num_workers: int = None) -> List[T]:

    """

    并行筛选：保留满足条件的元素

    

    参数:

        predicate: 谓词函数，接收一个元素，返回 bool

        arr: 输入数组

        num_workers: 并行工作线程数

    

    返回:

        result: 满足条件的元素列表

    

    示例:

        >>> parallel_filter(lambda x: x > 2, [1, 2, 3, 4, 5])

        [3, 4, 5]

    

    复杂度: O(n/p) 并行部分 + O(n) 合并

    """

    n = len(arr)

    

    if n == 0:

        return []

    

    if n <= 512:

        # 小规模数据直接串行处理

        return [elem for elem in arr if predicate(elem)]

    

    # 计算分块大小

    num_workers = num_workers or 4

    chunk_size = max(1, n // num_workers)

    

    # 将数组分块

    chunks = []

    for i in range(0, n, chunk_size):

        chunks.append((arr[i:i + chunk_size], predicate))

    

    # 并行处理各块

    results = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:

        futures = [executor.submit(process_filter_chunk, chunk) for chunk in chunks]

        for future in futures:

            results.append(future.result())

    

    # 合并结果

    merged = []

    for chunk_result in results:

        merged.extend(chunk_result)

    

    return merged





def process_filter_chunk(chunk):

    """处理筛选块：保留满足条件的元素"""

    arr, predicate = chunk

    return [elem for elem in arr if predicate(elem)]





def parallel_map_filter(

    predicate: Callable[[T], bool],

    transform: Callable[[T], R],

    arr: List[T],

    num_workers: int = None

) -> List[R]:

    """

    并行筛选-映射组合：先筛选再转换

    

    参数:

        predicate: 筛选条件函数

        transform: 转换函数

        arr: 输入数组

        num_workers: 并行工作线程数

    

    返回:

        result: 满足条件且经过转换的元素列表

    

    注意：先筛选可以减少需要转换的元素数量

    """

    filtered = parallel_filter(predicate, arr, num_workers)

    return parallel_map(transform, filtered, num_workers)





# ==================== 测试代码 ====================



if __name__ == "__main__":

    import random

    import time

    

    print("=" * 60)

    print("并行筛选与映射 测试")

    print("=" * 60)

    

    # ===== Map 测试 =====

    print("\n--- Map 测试 ---")

    

    # 测试用例1：基本映射

    test_arr = [1, 2, 3, 4, 5]

    print(f"\n[测试1] 基本映射: {test_arr}")

    result = parallel_map(lambda x: x * 2, test_arr)

    expected = [x * 2 for x in test_arr]

    print(f"结果: {result}")

    assert result == expected, "映射结果错误"

    print("✅ 通过\n")

    

    # 测试用例2：字符串操作

    test_arr = ["hello", "world", "python"]

    print(f"[测试2] 字符串映射: {test_arr}")

    result = parallel_map(str.upper, test_arr)

    expected = [s.upper() for s in test_arr]

    print(f"结果: {result}")

    assert result == expected, "字符串映射结果错误"

    print("✅ 通过\n")

    

    # 测试用例3：性能测试

    large_arr = list(range(10000))

    print(f"[测试3] 大数组映射 (规模 {len(large_arr)})")

    

    start = time.time()

    result = parallel_map(lambda x: x ** 2, large_arr)

    elapsed = time.time() - start

    

    expected = [x ** 2 for x in large_arr]

    is_correct = result == expected

    print(f"耗时: {elapsed:.4f}秒, 正确性: {'✅' if is_correct else '❌'}\n")

    

    # ===== Filter 测试 =====

    print("--- Filter 测试 ---")

    

    # 测试用例4：基本筛选

    test_arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    print(f"\n[测试4] 基本筛选 (偶数): {test_arr}")

    result = parallel_filter(lambda x: x % 2 == 0, test_arr)

    expected = [x for x in test_arr if x % 2 == 0]

    print(f"结果: {result}")

    assert result == expected, "筛选结果错误"

    print("✅ 通过\n")

    

    # 测试用例5：字符串筛选

    test_arr = ["apple", "banana", "cherry", "date", "elderberry"]

    print(f"[测试5] 字符串筛选 (长度>5): {test_arr}")

    result = parallel_filter(lambda s: len(s) > 5, test_arr)

    expected = [s for s in test_arr if len(s) > 5]

    print(f"结果: {result}")

    assert result == expected, "字符串筛选结果错误"

    print("✅ 通过\n")

    

    # 测试用例6：浮点数筛选

    test_arr = [random.uniform(-10, 10) for _ in range(5000)]

    positive = [x for x in test_arr if x > 0]

    print(f"[测试6] 大规模正数筛选 (规模 {len(test_arr)})")

    result = parallel_filter(lambda x: x > 0, test_arr)

    result.sort()

    positive.sort()

    is_correct = result == positive

    print(f"筛选出 {len(result)} 个正数, 正确性: {'✅' if is_correct else '❌'}\n")

    

    # ===== 组合测试 =====

    print("--- 组合测试 ---")

    

    # 测试用例7：筛选后映射

    test_arr = list(range(1, 21))

    print(f"\n[测试7] 筛选后映射: {test_arr[:10]}...")

    

    # 筛选偶数，然后平方

    result = parallel_map_filter(

        lambda x: x % 2 == 0,

        lambda x: x ** 2,

        test_arr

    )

    expected = [x ** 2 for x in test_arr if x % 2 == 0]

    print(f"偶数平方: {result}")

    assert result == expected, "组合操作结果错误"

    print("✅ 通过\n")

    

    # 测试用例8：嵌套数据结构

    print("[测试8] 嵌套数据结构映射")

    data = [{"name": "Alice", "score": 85}, {"name": "Bob", "score": 92}]

    result = parallel_map(lambda d: d["score"], data)

    expected = [85, 92]

    print(f"提取分数: {result}")

    assert result == expected, "嵌套数据映射错误"

    print("✅ 通过\n")

    

    # ===== 边界测试 =====

    print("--- 边界测试 ---")

    

    print("\n[边界测试]")

    assert parallel_map(lambda x: x, []) == [], "空数组映射失败"

    assert parallel_filter(lambda x: True, []) == [], "空数组筛选失败"

    assert parallel_map(lambda x: x * 2, [5]) == [10], "单元素映射失败"

    assert parallel_filter(lambda x: x > 3, [5]) == [5], "单元素筛选失败"

    print("✅ 通过")

    

    print("\n" + "=" * 60)

    print("所有测试通过！并行筛选与映射验证完成。")

    print("=" * 60)

