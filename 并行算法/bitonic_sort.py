# -*- coding: utf-8 -*-

"""

算法实现：并行算法 / bitonic_sort



本文件实现 bitonic_sort 相关的算法功能。

"""



from typing import List, Callable, Any

import math





def compare_and_swap(data: List[Any], i: int, j: int, 

                     ascending: bool = True) -> None:

    """

    比较并交换两个元素

    

    参数:

        data: 数据列表

        i: 第一个索引

        j: 第二个索引

        ascending: True升序，False降序

    """

    if i >= len(data) or j >= len(data):

        return

    

    # 根据升序/降序决定是否交换

    if ascending:

        if data[i] > data[j]:

            data[i], data[j] = data[j], data[i]

    else:

        if data[i] < data[j]:

            data[i], data[j] = data[j], data[i]





def bitonic_split(data: List[Any], ascending: bool) -> None:

    """

    双调分割：将序列分成两半，一半升序，一半降序

    

    参数:

        data: 数据列表

        ascending: True表示第一半升序，第二半降序

    """

    n = len(data)

    if n <= 1:

        return

    

    half = n // 2

    

    # 对每一对元素执行比较交换

    for i in range(half):

        compare_and_swap(data, i, i + half, ascending)





def bitonic_merge(data: List[Any], ascending: bool) -> None:

    """

    双调合并：将两个有序序列合并为一个有序序列

    

    参数:

        data: 数据列表

        ascending: True升序，False降序

    """

    n = len(data)

    if n <= 1:

        return

    

    # 首先分割

    bitonic_split(data, ascending)

    

    # 递归合并前半部分

    half = n // 2

    if half > 1:

        bitonic_merge(data[:half], ascending)

        bitonic_merge(data[half:], ascending)





def bitonic_sort_recursive(data: List[Any], ascending: bool = True) -> None:

    """

    递归版双调排序

    

    参数:

        data: 数据列表（原地排序）

        ascending: True升序，False降序

    """

    n = len(data)

    if n <= 1:

        return

    

    if n == 2:

        compare_and_swap(data, 0, 1, ascending)

        return

    

    # 分成两半

    half = n // 2

    

    # 前一半升序

    bitonic_sort_recursive(data[:half], True)

    # 后一半降序

    bitonic_sort_recursive(data[half:], False)

    

    # 合并整个序列

    bitonic_merge(data, ascending)





def is_power_of_2(n: int) -> bool:

    """

    检查n是否是2的幂次

    

    参数:

        n: 输入整数

    

    返回:

        True如果是2的幂次

    """

    return n > 0 and (n & (n - 1)) == 0





def pad_to_power_of_2(data: List[Any], pad_value: Any = None) -> tuple:

    """

    将数据填充到2的幂次长度

    

    参数:

        data: 输入数据

        pad_value: 填充值

    

    返回:

        (填充后的数据, 原始长度)

    """

    n = len(data)

    if n == 0:

        return [], 0

    

    # 计算下一个2的幂次

    size = 1

    while size < n:

        size *= 2

    

    # 填充

    if size > n:

        padded = list(data) + [pad_value] * (size - n)

    else:

        padded = list(data)

    

    return padded, n





def bitonic_sort(data: List[Any], ascending: bool = True) -> List[Any]:

    """

    双调排序入口函数（自动处理非2的幂次长度）

    

    参数:

        data: 输入数据列表

        ascending: True升序，False降序

    

    返回:

        排序后的新列表

    """

    if len(data) == 0:

        return []

    

    # 填充到2的幂次

    padded, original_len = pad_to_power_of_2(data)

    

    # 排序

    bitonic_sort_recursive(padded, ascending)

    

    # 截断回原始长度

    return padded[:original_len]





def bitonic_sort_iterative(data: List[Any], ascending: bool = True) -> None:

    """

    迭代版双调排序（更清晰地展示算法结构）

    

    参数:

        data: 数据列表（原地排序）

        ascending: True升序

    """

    n = len(data)

    if n <= 1:

        return

    

    # 确保是2的幂次

    size = 1

    while size < n:

        size *= 2

    

    # 扩展数据

    original_len = n

    if size > n:

        data.extend([float('inf')] * (size - n))

    

    # 外层循环：序列长度

    k = 2

    while k <= size:

        # 中层循环：升序/降序

        j = k // 2

        while j > 0:

            # 内层循环：比较位置

            for i in range(size):

                # 计算比较的两个位置

                ixj = i ^ j

                if ixj > i:

                    if (i & k) == 0:

                        # 升序比较

                        compare_and_swap(data, i, ixj, True)

                    else:

                        # 降序比较

                        compare_and_swap(data, i, ixj, False)

            j //= 2

        k *= 2

    

    # 截断回原始长度

    del data[original_len:]





class BitonicSortNetwork:

    """

    双调排序网络可视化类

    """

    

    def __init__(self, data: List[Any]):

        """

        初始化排序网络

        

        参数:

            data: 输入数据

        """

        self.original_data = list(data)

        self.data = list(data)

        self.steps = []

        self.record_step("初始数据", list(self.data))

    

    def record_step(self, description: str, data_state: List[Any]):

        """

        记录一步执行状态

        

        参数:

            description: 步骤描述

            data_state: 数据状态

        """

        self.steps.append({

            'description': description,

            'data': list(data_state)

        })

    

    def run(self, ascending: bool = True) -> List[Any]:

        """

        执行双调排序

        

        参数:

            ascending: True升序

        

        返回:

            排序结果

        """

        n = len(self.data)

        if n <= 1:

            return self.data

        

        # 确保是2的幂次

        size = 1

        while size < n:

            size *= 2

        

        original_len = n

        if size > n:

            self.data.extend([float('inf')] * (size - n))

        

        # 排序

        bitonic_sort_recursive(self.data, ascending)

        

        # 截断

        result = self.data[:original_len]

        

        self.record_step("排序完成", result)

        

        return result

    

    def get_steps(self) -> List[dict]:

        """

        获取所有步骤

        

        返回:

            步骤列表

        """

        return self.steps

    

    def print_steps(self):

        """

        打印排序过程

        """

        for i, step in enumerate(self.steps):

            print(f"步骤 {i}: {step['description']}")

            print(f"  数据: {step['data']}")





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：基本双调排序

    print("=" * 50)

    print("测试1: 基本双调排序")

    print("=" * 50)

    

    data = [3, 7, 2, 8, 1, 5, 4, 6]

    

    print(f"输入: {data}")

    result = bitonic_sort(data)

    print(f"输出: {result}")

    print(f"正确: {result == sorted(data)}")

    

    # 测试用例2：非2的幂次长度

    print("\n" + "=" * 50)

    print("测试2: 非2的幂次长度")

    print("=" * 50)

    

    data = [5, 2, 8, 1, 9, 3]

    print(f"输入: {data}")

    result = bitonic_sort(data)

    print(f"输出: {result}")

    print(f"正确: {result == sorted(data)}")

    

    # 测试用例3：迭代版

    print("\n" + "=" * 50)

    print("测试3: 迭代版排序")

    print("=" * 50)

    

    data = [3, 7, 2, 8, 1, 5, 4, 6]

    print(f"输入: {data}")

    bitonic_sort_iterative(data)

    print(f"输出: {data}")

    

    # 测试用例4：排序网络可视化

    print("\n" + "=" * 50)

    print("测试4: 排序过程")

    print("=" * 50)

    

    data = [8, 3, 7, 1, 5, 9, 2, 4]

    network = BitonicSortNetwork(data)

    result = network.run()

    

    print(f"输入: {data}")

    print(f"输出: {result}")

    

    # 打印部分步骤

    steps = network.get_steps()

    print(f"\n共 {len(steps)} 个步骤")

    for i, step in enumerate(steps[:5]):

        print(f"  {step['description']}: {step['data']}")

    if len(steps) > 5:

        print(f"  ... (省略 {len(steps) - 5} 步)")

    

    # 测试用例5：降序排序

    print("\n" + "=" * 50)

    print("测试5: 降序排序")

    print("=" * 50)

    

    data = [3, 7, 2, 8, 1, 5, 4, 6]

    print(f"输入: {data}")

    result = bitonic_sort(data, ascending=False)

    print(f"降序输出: {result}")

    print(f"正确: {result == sorted(data, reverse=True)}")

    

    # 测试用例6：大规模数据测试

    print("\n" + "=" * 50)

    print("测试6: 性能测试")

    print("=" * 50)

    

    import random

    

    for size in [8, 16, 32, 64]:

        data = [random.randint(1, 100) for _ in range(size)]

        original = list(data)

        

        result = bitonic_sort(data)

        is_sorted = all(result[i] <= result[i+1] for i in range(len(result)-1))

        

        print(f"大小={size:3d}: 排序正确={is_sorted}")

