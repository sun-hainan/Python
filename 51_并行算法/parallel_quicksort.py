# -*- coding: utf-8 -*-

"""

算法实现：并行算法 / parallel_quicksort



本文件实现 parallel_quicksort 相关的算法功能。

"""



from concurrent.futures import ThreadPoolExecutor





def parallel_quicksort(arr, max_workers=None, threshold=512):

    """

    并行快速排序主函数

    

    参数:

        arr: 输入的整数列表

        max_workers: 最大并行工作线程数

        threshold: 切换为串行排序的阈值规模

    

    返回:

        sorted_arr: 排序后的新列表（原列表不变）

    """

    if len(arr) <= 1:

        return arr.copy()

    

    return _parallel_quicksort_helper(arr, max_workers, threshold)





def _parallel_quicksort_helper(arr, max_workers, threshold):

    """

    并行快速排序的递归辅助函数

    

    参数:

        arr: 输入数组

        max_workers: 最大并行工作线程数

        threshold: 串行切换阈值

    

    返回:

        有序数组

    """

    n = len(arr)

    

    # 递归终止条件：规模足够小时使用串行排序

    if n <= threshold:

        return sorted(arr)

    

    # pivot 选择：使用中间位置

    pivot_idx = n // 2

    pivot_val = arr[pivot_idx]

    

    # 分区操作：将数组分为 left(< pivot), middle(= pivot), right(> pivot)

    left_part = []

    middle_part = []

    right_part = []

    

    for elem in arr:

        if elem < pivot_val:

            left_part.append(elem)

        elif elem > pivot_val:

            right_part.append(elem)

        else:

            middle_part.append(elem)

    

    # 递归终止：若某部分为空，直接返回

    if len(arr) == len(middle_part):

        return middle_part.copy()

    

    # 获取可用工作线程数

    available_workers = max_workers or 4

    

    if available_workers <= 1:

        # 串行执行

        sorted_left = _parallel_quicksort_helper(left_part, 1, threshold)

        sorted_right = _parallel_quicksort_helper(right_part, 1, threshold)

    else:

        # 并行执行左右子数组的排序

        with ThreadPoolExecutor(max_workers=2) as executor:

            future_left = executor.submit(

                _parallel_quicksort_helper, left_part, available_workers // 2, threshold

            )

            future_right = executor.submit(

                _parallel_quicksort_helper, right_part, available_workers // 2, threshold

            )

            

            sorted_left = future_left.result()

            sorted_right = future_right.result()

    

    # 合并结果：sorted_left + middle_part + sorted_right

    result = sorted_left + middle_part + sorted_right

    return result





# ==================== 测试代码 ====================



if __name__ == "__main__":

    import random

    import time

    

    print("=" * 60)

    print("并行快速排序 测试")

    print("=" * 60)

    

    # 测试用例1：基本排序

    test_arr = [33, 10, 59, 87, 23, 45, 12, 66]

    print(f"\n[测试1] 输入数组: {test_arr}")

    sorted_arr = parallel_quicksort(test_arr)

    print(f"排序结果:   {sorted_arr}")

    assert sorted_arr == sorted(test_arr), "排序结果错误！"

    print("✅ 通过\n")

    

    # 测试用例2：逆序数组

    test_arr = list(range(25, 0, -1))

    print(f"[测试2] 逆序数组: {test_arr}")

    sorted_arr = parallel_quicksort(test_arr)

    assert sorted_arr == sorted(test_arr), "排序结果错误！"

    print("✅ 通过\n")

    

    # 测试用例3：包含大量重复元素

    test_arr = [7, 1, 3, 7, 5, 7, 9, 1, 3, 7, 5, 9]

    print(f"[测试3] 含重复元素: {test_arr}")

    sorted_arr = parallel_quicksort(test_arr)

    print(f"排序结果:   {sorted_arr}")

    assert sorted_arr == sorted(test_arr), "排序结果错误！"

    print("✅ 通过\n")

    

    # 测试用例4：性能测试

    sizes = [2000, 5000, 10000]

    print("[测试4] 性能测试")

    for size in sizes:

        large_arr = [random.randint(0, 100000) for _ in range(size)]

        

        start_time = time.time()

        sorted_arr = parallel_quicksort(large_arr)

        elapsed = time.time() - start_time

        

        is_correct = sorted_arr == sorted(large_arr)

        print(f"  规模 {size:>6}: {elapsed:.4f}秒, 正确性: {'✅' if is_correct else '❌'}")

    print()

    

    # 测试用例5：边界情况

    print("[测试5] 边界情况")

    assert parallel_quicksort([]) == [], "空数组测试失败"

    assert parallel_quicksort([99]) == [99], "单元素测试失败"

    assert parallel_quicksort([3, 1]) == [1, 3], "两元素测试失败"

    assert parallel_quicksort([1, 2, 3]) == [1, 2, 3], "已排序数组测试失败"

    print("✅ 通过")

    

    print("\n" + "=" * 60)

    print("所有测试通过！并行快速排序验证完成。")

    print("=" * 60)

