# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / blelloch_scan

本文件实现 blelloch_scan 相关的算法功能。
"""

from typing import List, Callable, Any, Union
import math


def hillis_steele_scan(data: List[Any], operator: Callable[[Any, Any], Any], 
                       inclusive: bool = False) -> List[Any]:
    """
    Hillis-Steele并行扫描算法
    
    时间复杂度: O(n log n)
    工作量: O(n log n)
    
    参数:
        data: 输入数据列表
        operator: 二元运算符（如 add, max）
        inclusive: True返回包含扫描，False返回排除扫描
    
    返回:
        扫描结果列表
    """
    n = len(data)
    if n == 0:
        return []
    
    # 初始化工作数组
    result = [data[0]] + [None] * (n - 1)
    width = 1
    
    # 第0层复制原始数据
    level_data = list(data)
    
    # 逐层扩大窗口
    while width < n:
        for i in range(n):
            if i >= width:
                result[i] = operator(level_data[i - width], level_data[i])
            else:
                result[i] = level_data[i]
        
        level_data = list(result)
        width *= 2
    
    # 处理inclusive/exclusive
    if inclusive:
        return result
    else:
        # exclusive: 将每个位置的值替换为之前所有值的归约
        exclusive_result = [None] + result[:-1]
        exclusive_result[0] = operator.__self__ if hasattr(operator, '__self__') else None
        return exclusive_result


def blelloch_prefix_sum(numbers: List[Union[int, float]], 
                         inclusive: bool = False) -> List[Union[int, float]]:
    """
    Blelloch并行前缀和算法
    
    参数:
        numbers: 输入数字列表
        inclusive: True返回包含扫描，False返回排除扫描
    
    返回:
        前缀和数组
    """
    n = len(numbers)
    if n == 0:
        return []
    
    # 复制输入数据
    data = list(numbers)
    
    # 计算需要的工作组大小（2的幂次）
    size = 1
    while size < n:
        size *= 2
    
    # 扩展到2的幂次
    data.extend([0] * (size - n))
    
    # 上扫（Up-Sweep）阶段：构建归约树
    # 从叶子开始，逐步归约到根
    offset = 1
    for d in range(int(math.log2(size)), -1, -1):
        for i in range(0, size, 2 * offset):
            data[i + 2 * offset - 1] = data[i + offset - 1] + data[i + 2 * offset - 1]
        offset *= 2
    
    # 移位：根节点设为0
    data[size - 1] = 0
    
    # 下扫（Down-Sweep）阶段：从根开始传播
    offset = size // 2
    for d in range(int(math.log2(size)) + 1):
        for i in range(0, size, 2 * offset):
            t = data[i + offset - 1]
            data[i + offset - 1] = data[i + 2 * offset - 1]
            data[i + 2 * offset - 1] = t + data[i + 2 * offset - 1]
        offset //= 2
    
    # 截断到原始长度
    result = data[:n]
    
    if inclusive:
        # inclusive: 每个位置i包含data[i]和之前的和
        return [result[i] + numbers[i] for i in range(n)]
    else:
        return result


def blelloch_scan(data: List[Any], operator: Callable[[Any, Any], Any],
                   identity: Any = 0, inclusive: bool = False) -> List[Any]:
    """
    通用Blelloch扫描算法
    
    参数:
        data: 输入数据列表
        operator: 二元运算符
        identity: 单位元
        inclusive: True返回包含扫描
    
    返回:
        扫描结果
    """
    n = len(data)
    if n == 0:
        return []
    
    # 复制输入
    work_data = list(data)
    
    # 计算大小
    size = 1
    while size < n:
        size *= 2
    
    # 扩展
    work_data.extend([identity] * (size - n))
    
    # 上扫阶段
    offset = 1
    for d in range(int(math.log2(size)), -1, -1):
        for i in range(0, size, 2 * offset):
            left_idx = i + offset - 1
            right_idx = i + 2 * offset - 1
            if right_idx < size:
                work_data[right_idx] = operator(work_data[left_idx], work_data[right_idx])
        offset *= 2
    
    # 移位
    work_data[size - 1] = identity
    
    # 下扫阶段
    offset = size // 2
    for d in range(int(math.log2(size)) + 1):
        for i in range(0, size, 2 * offset):
            left_idx = i + offset - 1
            right_idx = i + 2 * offset - 1
            if right_idx < size:
                t = work_data[left_idx]
                work_data[left_idx] = work_data[right_idx]
                work_data[right_idx] = operator(t, work_data[right_idx])
        offset //= 2
    
    result = work_data[:n]
    
    if inclusive:
        return [operator(result[i], data[i]) for i in range(n)]
    return result


def parallel_prefix_max(values: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    并行前缀最大值
    
    参数:
        values: 输入值列表
    
    返回:
        每个位置的前缀最大值
    """
    return blelloch_scan(values, max, float('-inf'))


def parallel_prefix_min(values: List[Union[int, float]]) -> List[Union[int, float]]:
    """
    并行前缀最小值
    
    参数:
        values: 输入值列表
    
    返回:
        每个位置的前缀最小值
    """
    return blelloch_scan(values, min, float('inf'))


class ScanVisualizer:
    """
    扫描过程可视化类
    """
    
    def __init__(self, data: List[Any], operator: Callable[[Any, Any], Any]):
        self.data = list(data)
        self.operator = operator
        self.up_sweep_levels = []
        self.down_sweep_levels = []
        self.tree_structure = []
    
    def run(self) -> List[Any]:
        """
        执行扫描并记录过程
        
        返回:
            扫描结果
        """
        n = len(self.data)
        if n == 0:
            return []
        
        # 复制数据
        work = list(self.data)
        size = 1
        while size < n:
            size *= 2
        
        work.extend([0] * (size - n))
        
        # 上扫阶段
        offset = 1
        self.up_sweep_levels.append(list(work))
        
        for d in range(int(math.log2(size)), -1, -1):
            for i in range(0, size, 2 * offset):
                if i + 2 * offset - 1 < size:
                    work[i + 2 * offset - 1] = self.operator(
                        work[i + offset - 1], 
                        work[i + 2 * offset - 1]
                    )
            self.up_sweep_levels.append(list(work))
            offset *= 2
        
        # 下扫阶段
        work[size - 1] = 0
        
        offset = size // 2
        self.down_sweep_levels.append(list(work))
        
        for d in range(int(math.log2(size)) + 1):
            for i in range(0, size, 2 * offset):
                left = i + offset - 1
                right = i + 2 * offset - 1
                if right < size:
                    t = work[left]
                    work[left] = work[right]
                    work[right] = self.operator(t, work[right])
            self.down_sweep_levels.append(list(work))
            offset //= 2
        
        return work[:n]
    
    def print_algorithm_steps(self):
        """
        打印算法执行步骤
        """
        print("=" * 60)
        print("上扫（Up-Sweep）阶段 - 构建归约树")
        print("=" * 60)
        for i, level in enumerate(self.up_sweep_levels):
            print(f"步骤 {i}: {level[:len(self.data)]}")
        
        print("\n" + "=" * 60)
        print("下扫（Down-Sweep）阶段 - 传播值")
        print("=" * 60)
        for i, level in enumerate(self.down_sweep_levels):
            print(f"步骤 {len(self.up_sweep_levels) - 1 + i}: {level[:len(self.data)]}")


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本前缀和
    print("=" * 50)
    print("测试1: Blelloch前缀和")
    print("=" * 50)
    
    numbers = [3, 1, 7, 0, 4, 1, 6, 3]
    
    exclusive_sum = blelloch_prefix_sum(numbers, inclusive=False)
    inclusive_sum = blelloch_prefix_sum(numbers, inclusive=True)
    
    print(f"输入:    {numbers}")
    print(f"前缀和:  {exclusive_sum}")
    print(f"包含当前: {inclusive_sum}")
    
    # 验证
    expected = []
    running = 0
    for x in numbers:
        expected.append(running)
        running += x
    print(f"预期:    {expected}")
    
    # 测试用例2：前缀最大值
    print("\n" + "=" * 50)
    print("测试2: 前缀最大值")
    print("=" * 50)
    
    values = [5, 2, 9, 1, 7, 3, 8, 4]
    
    prefix_max = parallel_prefix_max(values)
    
    print(f"输入:        {values}")
    print(f"前缀最大值: {prefix_max}")
    
    # 测试用例3：可视化
    print("\n" + "=" * 50)
    print("测试3: 扫描过程可视化")
    print("=" * 50)
    
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    visualizer = ScanVisualizer(data, lambda a, b: a + b)
    result = visualizer.run()
    
    visualizer.print_algorithm_steps()
    
    print(f"\n最终结果: {result}")
    
    # 测试用例4：通用扫描
    print("\n" + "=" * 50)
    print("测试4: 通用Blelloch扫描")
    print("=" * 50)
    
    values = [1, 2, 3, 4, 5, 6, 7, 8]
    
    # 自定义运算符：乘积
    product_scan = blelloch_scan(values, lambda a, b: a * b, identity=1)
    
    print(f"输入: {values}")
    print(f"前缀乘积: {product_scan}")
    
    # 测试用例5：与Hillis-Steele比较
    print("\n" + "=" * 50)
    print("测试5: Hillis-Steele vs Blelloch")
    print("=" * 50)
    
    numbers = [1, 2, 3, 4, 5, 6, 7, 8]
    
    blelloch_result = blelloch_prefix_sum(numbers)
    
    # Hillis-Steele (简化版)
    def simple_hillis_steele(data):
        n = len(data)
        result = [data[0]]
        for width in range(1, n):
            for i in range(n):
                if i >= width:
                    result[i] = result[i - width] + data[i]
                else:
                    result[i] = data[i]
        return result
    
    hillis_result = simple_hillis_steele(numbers)
    
    print(f"输入: {numbers}")
    print(f"Blelloch:  {blelloch_result}")
    print(f"Hillis:    {hillis_result}")
