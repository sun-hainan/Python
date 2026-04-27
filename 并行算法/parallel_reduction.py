# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / parallel_reduction

本文件实现 parallel_reduction 相关的算法功能。
"""

import math
from typing import Callable, List, Any, Union


def parallel_reduce(data: List[Any], operator: Callable[[Any, Any], Any], 
                    identity: Any) -> Any:
    """
    并行归约（模拟单进程版本，实际需要多进程/多线程环境）
    
    参数:
        data: 要归约的数据列表
        operator: 二元运算符（如 sum, max, min）
        identity: 单位元（如 sum 的 0，max 的 -inf）
    
    返回:
        归约结果
    """
    if len(data) == 0:
        return identity
    
    # 模拟树形归约的过程
    result = list(data)
    
    # 树形合并
    while len(result) > 1:
        # 计算这一轮需要合并的对数
        new_len = (len(result) + 1) // 2
        new_result = []
        
        for i in range(new_len):
            if 2 * i + 1 < len(result):
                new_result.append(operator(result[2 * i], result[2 * i + 1]))
            else:
                # 奇数情况，最后一个元素直接传递
                new_result.append(result[2 * i])
        
        result = new_result
    
    return result[0]


def parallel_sum(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    并行求和
    
    参数:
        numbers: 数字列表
    
    返回:
        所有数字的和
    """
    return parallel_reduce(numbers, lambda a, b: a + b, 0)


def parallel_max(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    并行求最大值
    
    参数:
        numbers: 数字列表
    
    返回:
        最大值
    """
    if not numbers:
        return float('-inf')
    return parallel_reduce(numbers, max, float('-inf'))


def parallel_min(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    并行求最小值
    
    参数:
        numbers: 数字列表
    
    返回:
        最小值
    """
    if not numbers:
        return float('inf')
    return parallel_reduce(numbers, min, float('inf'))


def parallel_product(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    并行求积
    
    参数:
        numbers: 数字列表
    
    返回:
        所有数字的乘积
    """
    if not numbers:
        return 1
    return parallel_reduce(numbers, lambda a, b: a * b, 1)


def parallel_and(values: List[bool]) -> bool:
    """
    并行逻辑与
    
    参数:
        values: 布尔值列表
    
    返回:
        所有值的逻辑与结果
    """
    return parallel_reduce(values, lambda a, b: a and b, True)


def parallel_or(values: List[bool]) -> bool:
    """
    并行逻辑或
    
    参数:
        values: 布尔值列表
    
    返回:
        所有值的逻辑或结果
    """
    return parallel_reduce(values, lambda a, b: a or b, False)


class TreeReduction:
    """
    树形归约可视化类
    
    展示归约过程的树形结构
    """
    
    def __init__(self, data: List[Any], operator: Callable[[Any, Any], Any]):
        """
        初始化
        
        参数:
            data: 初始数据列表
            operator: 二元运算符
        """
        self.data = data
        self.operator = operator
        self.levels = [list(data)]  # 保存每层的状态
    
    def run(self) -> Any:
        """
        执行归约并记录过程
        
        返回:
            最终结果
        """
        current = list(self.data)
        
        while len(current) > 1:
            new_level = []
            for i in range(0, len(current), 2):
                if i + 1 < len(current):
                    new_level.append(self.operator(current[i], current[i + 1]))
                else:
                    new_level.append(current[i])
            
            self.levels.append(new_level)
            current = new_level
        
        return current[0]
    
    def get_tree_structure(self) -> List[List[Any]]:
        """
        获取归约树的完整结构
        
        返回:
            每层归约结果的列表
        """
        return self.levels
    
    def print_tree(self):
        """
        打印归约树
        """
        print("归约过程：")
        for i, level in enumerate(self.levels):
            indent = "  " * i
            print(f"{indent}层{i}: {level}")


def simulate_parallel_reduction(data: List[Any], num_processors: int,
                                 operator: Callable[[Any, Any], Any],
                                 identity: Any) -> dict:
    """
    模拟并行归约的执行过程
    
    参数:
        data: 输入数据
        num_processors: 处理器数量
        operator: 运算符
        identity: 单位元
    
    返回:
        包含执行统计的字典
    """
    stats = {
        'num_processors': num_processors,
        'input_size': len(data),
        'num_rounds': 0,
        'work_per_round': [],
        'total_work': 0
    }
    
    current = list(data)
    chunk_size = math.ceil(len(data) / num_processors)
    
    # 模拟本地归约阶段
    local_results = []
    for i in range(num_processors):
        start = i * chunk_size
        end = min(start + chunk_size, len(data))
        chunk = data[start:end]
        if chunk:
            local_result = parallel_reduce(chunk, operator, identity)
            local_results.append(local_result)
    
    stats['work_per_round'].append(len(local_results))
    stats['num_rounds'] = 1
    
    # 模拟树形合并阶段
    while len(local_results) > 1:
        num_active = math.ceil(len(local_results) / num_processors)
        new_results = []
        
        for i in range(num_active):
            start = i * num_processors
            end = min(start + num_processors, len(local_results))
            chunk = local_results[start:end]
            if len(chunk) > 1:
                new_results.append(parallel_reduce(chunk, operator, identity))
            elif chunk:
                new_results.append(chunk[0])
        
        local_results = new_results
        stats['work_per_round'].append(len(local_results))
        stats['num_rounds'] += 1
    
    stats['total_work'] = stats['input_size'] + sum(stats['work_per_round'])
    
    return stats


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本并行归约
    print("=" * 50)
    print("测试1: 基本并行归约")
    print("=" * 50)
    
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    print(f"输入数据: {numbers}")
    print(f"并行求和: {parallel_sum(numbers)}")
    print(f"并行最大值: {parallel_max(numbers)}")
    print(f"并行最小值: {parallel_min(numbers)}")
    print(f"并行求积: {parallel_product(numbers)}")
    
    # 测试用例2：树形归约过程
    print("\n" + "=" * 50)
    print("测试2: 树形归约可视化")
    print("=" * 50)
    
    data = [3, 7, 2, 9, 1, 5, 8, 4]
    reducer = TreeReduction(data, max)
    result = reducer.run()
    
    reducer.print_tree()
    print(f"\n最终结果: {result}")
    
    # 测试用例3：布尔归约
    print("\n" + "=" * 50)
    print("测试3: 布尔值归约")
    print("=" * 50)
    
    bool_values = [True, False, True, True, False]
    print(f"输入: {bool_values}")
    print(f"AND结果: {parallel_and(bool_values)}")
    print(f"OR结果: {parallel_or(bool_values)}")
    
    # 测试用例4：并行度模拟
    print("\n" + "=" * 50)
    print("测试4: 并行度对性能的影响")
    print("=" * 50)
    
    large_data = list(range(1, 65))
    
    for num_procs in [1, 2, 4, 8, 16]:
        stats = simulate_parallel_reduction(
            large_data, 
            num_procs, 
            lambda a, b: a + b, 
            0
        )
        print(f"处理器数={num_procs:2d}: "
              f"轮数={stats['num_rounds']}, "
              f"总工作量={stats['total_work']}")
    
    # 测试用例5：自定义运算符
    print("\n" + "=" * 50)
    print("测试5: 自定义运算符")
    print("=" * 50)
    
    # 自定义字符串连接运算符
    strings = ["Hello", " ", "World", "!"]
    concat = parallel_reduce(strings, lambda a, b: a + b, "")
    print(f"字符串拼接: '{concat}'")
    
    # 自定义取模加法
    modular_add = parallel_reduce([2, 3, 4, 5], lambda a, b: (a + b) % 10, 0)
    print(f"模10加法: {modular_add}")
