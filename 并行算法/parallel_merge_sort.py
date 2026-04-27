# -*- coding: utf-8 -*-

"""

算法实现：并行算法 / parallel_merge_sort



本文件实现 parallel_merge_sort 相关的算法功能。

"""



from concurrent.futures import ThreadPoolExecutor, as_completed





def parallel_merge_sort(arr, max_workers=None, threshold=1024):

    """

    并行归并排序主函数

    

    参数:

        arr: 输入的整数列表

        max_workers: 最大并行工作线程数

        threshold: 切换为串行排序的阈值规模

    

    返回:

        sorted_arr: 排序后的新列表（原列表不变）

    """

    if len(arr) <= 1:

        return arr.copy()

    

    # 并行归并排序

    return _parallel_merge_sort_helper(arr, max_workers, threshold)





def _parallel_merge_sort_helper(arr, max_workers, threshold):

    """

    并行归并排序的递归辅助函数

    

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

        return sorted(arr)  # 使用 Python 内置排序（高效）

    

    # 分解：从中间分割数组

    mid_idx = n // 2

    left_arr = arr[:mid_idx]

    right_arr = arr[mid_idx:]

    

    # 获取当前可用的工作线程数

    available_workers = max_workers or (ThreadPoolExecutor()._max_workers or 4)

    

    if available_workers <= 1:

        # 资源有限，递归串行执行

        sorted_left = _parallel_merge_sort_helper(left_arr, max_workers, threshold)

        sorted_right = _parallel_merge_sort_helper(right_arr, max_workers, threshold)

    else:

        # 并行执行左右两半的排序

        with ThreadPoolExecutor(max_workers=min(available_workers, 2)) as executor:

            # 提交两个子任务，每个使用一半的线程资源

            future_left = executor.submit(

                _parallel_merge_sort_helper, left_arr, available_workers // 2, threshold

            )

            future_right = executor.submit(

                _parallel_merge_sort_helper, right_arr, available_workers // 2, threshold

            )

            

            # 收集结果

            sorted_left = future_left.result()

            sorted_right = future_right.result()

    

    # 合并两个有序数组

    return merge_two_arrays(sorted_left, sorted_right)





def merge_two_arrays(left, right):

    """

    合并两个有序数组为一个有序数组

    

    参数:

        left: 左有序数组

        right: 右有序数组

    

    返回:

        merged: 合并后的有序数组

    

    复杂度: O(n) 时间, O(n) 空间

    """

    i = 0  # left 数组的遍历指针

    j = 0  # right 数组的遍历指针

    merged = []  # 合并结果

    

    # 双指针遍历，从小到大合并

    while i < len(left) and j < len(right):

        if left[i] <= right[j]:

            merged.append(left[i])

            i += 1

        else:

            merged.append(right[j])

            j += 1

    

    # 处理剩余元素

    if i < len(left):

        merged.extend(left[i:])

    if j < len(right):

        merged.extend(right[j:])

    

    return merged





# ==================== 测试代码 ====================



if __name__ == "__main__":

    import random

    import time

    

    print("=" * 60)

    print("并行归并排序 测试")

    print("=" * 60)

    

    # 测试用例1：基本排序

    test_arr = [38, 27, 43, 3, 9, 82, 10]

    print(f"\n[测试1] 输入数组: {test_arr}")

    sorted_arr = parallel_merge_sort(test_arr)

    print(f"排序结果:   {sorted_arr}")

    assert sorted_arr == sorted(test_arr), "排序结果错误！"

    print("✅ 通过\n")

    

    # 测试用例2：逆序数组

    test_arr = list(range(30, 0, -1))

    print(f"[测试2] 逆序数组: {test_arr[:10]}... (共{len(test_arr)}个)")

    sorted_arr = parallel_merge_sort(test_arr)

    print(f"排序结果 (前10个): {sorted_arr[:10]}...")

    assert sorted_arr == sorted(test_arr), "排序结果错误！"

    print("✅ 通过\n")

    

    # 测试用例3：包含重复元素

    test_arr = [5, 2, 8, 2, 1, 5, 8, 1, 9, 2]

    print(f"[测试3] 含重复元素: {test_arr}")

    sorted_arr = parallel_merge_sort(test_arr)

    print(f"排序结果:   {sorted_arr}")

    assert sorted_arr == sorted(test_arr), "排序结果错误！"

    print("✅ 通过\n")

    

    # 测试用例4：性能测试

    sizes = [1000, 5000, 10000]

    print("[测试4] 性能测试")

    for size in sizes:

        large_arr = [random.randint(0, 100000) for _ in range(size)]

        

        start_time = time.time()

        sorted_arr = parallel_merge_sort(large_arr)

        elapsed = time.time() - start_time

        

        is_correct = sorted_arr == sorted(large_arr)

        print(f"  规模 {size:>6}: {elapsed:.4f}秒, 正确性: {'✅' if is_correct else '❌'}")

    

    print()

    

    # 测试用例5：边界情况

    print("[测试5] 边界情况")

    assert parallel_merge_sort([]) == [], "空数组测试失败"

    assert parallel_merge_sort([42]) == [42], "单元素测试失败"

    assert parallel_merge_sort([2, 1]) == [1, 2], "两元素测试失败"

    print("✅ 通过")

    

    print("\n" + "=" * 60)

    print("所有测试通过！并行归并排序验证完成。")

    print("=" * 60)

