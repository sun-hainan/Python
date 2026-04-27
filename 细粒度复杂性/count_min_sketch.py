# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / count_min_sketch

本文件实现 count_min_sketch 相关的算法功能。
"""

import hashlib
from typing import List, Dict


class CountMinSketch:
    """
    Count-Min Sketch算法
    使用多个哈希表来估计元素出现频率
    """
    
    def __init__(self, width: int, depth: int = None):
        """
        初始化
        
        Args:
            width: 每行的宽度(列数)
            depth: 行数(哈希函数数)
        """
        self.width = width
        if depth is None:
            # depth = log(1/epsilon) 其中epsilon是误差界
            self.depth = int(2 / 0.1)  # 假设epsilon=0.1, delta=0.1
        else:
            self.depth = depth
        
        # 哈希表
        self.table = [[0] * width for _ in range(self.depth)]
        
        # 生成哈希函数参数
        self._generate_hash_funcs()
    
    def _generate_hash_funcs(self):
        """生成哈希函数参数"""
        import random
        random.seed(42)
        
        self.hash_params = []
        for _ in range(self.depth):
            a = random.randint(1, self.width * 2)
            b = random.randint(0, self.width * 2)
            self.hash_params.append((a, b))
    
    def _get_positions(self, item: str) -> List[int]:
        """获取元素在每行中的位置"""
        positions = []
        for a, b in self.hash_params:
            h = hashlib.md5(f"{a}{item}{b}".encode()).hexdigest()
            pos = int(h, 16) % self.width
            positions.append(pos)
        return positions
    
    def add(self, item: str, count: int = 1):
        """
        增加元素的计数
        
        Args:
            item: 元素
            count: 增加的数量
        """
        for row, pos in enumerate(self._get_positions(item)):
            self.table[row][pos] += count
    
    def estimate(self, item: str) -> int:
        """
        估计元素的频率
        
        Args:
            item: 元素
        
        Returns:
            估计的频率(上界)
        """
        positions = self._get_positions(item)
        return min(self.table[row][pos] for row, pos in enumerate(positions))
    
    def clear(self):
        """清空"""
        self.table = [[0] * self.width for _ in range(self.depth)]


def create_count_min_sketch(epsilon: float = 0.01, delta: float = 0.01) -> CountMinSketch:
    """
    根据误差参数创建Count-Min Sketch
    
    Args:
        epsilon: 误差上界
        delta: 失败概率
    
    Returns:
        CountMinSketch实例
    """
    import math
    
    width = int(2 / epsilon)
    depth = int(-math.log(delta) / math.log(2))
    
    return CountMinSketch(width, depth)


# 测试代码
if __name__ == "__main__":
    # 测试1: 基本功能
    print("测试1 - 基本功能:")
    cms = CountMinSketch(100, 5)
    
    items = ["a", "b", "a", "c", "a", "b", "a"]
    
    for item in items:
        cms.add(item)
    
    print(f"  添加: {items}")
    print(f"  频率估计:")
    for item in ["a", "b", "c", "d"]:
        est = cms.estimate(item)
        actual = items.count(item)
        print(f"    {item}: 估计={est}, 实际={actual}")
    
    # 测试2: 较大规模
    print("\n测试2 - 大规模测试:")
    import random
    
    random.seed(42)
    
    cms_large = CountMinSketch(1000, 10)
    
    # 生成频率分布(zipfian)
    n = 1000
    frequencies = {}
    for i in range(n):
        freq = n // (i + 1)  # zipfian分布
        frequencies[f"item_{i}"] = freq
    
    # 添加到sketch
    for item, freq in frequencies.items():
        cms_large.add(item, freq)
    
    # 验证
    print("  频率估计 vs 实际(前10个):")
    for i in range(10):
        item = f"item_{i}"
        est = cms_large.estimate(item)
        actual = frequencies[item]
        error = est - actual
        print(f"    {item}: 估计={est}, 实际={actual}, 误差={error}")
    
    # 测试3: 便捷函数
    print("\n测试3 - 便捷函数:")
    cms_auto = create_count_min_sketch(0.01, 0.01)
    print(f"  创建CMS: width={cms_auto.width}, depth={cms_auto.depth}")
    
    # 测试4: 错误边界验证
    print("\n测试4 - 错误边界验证:")
    cms_bound = CountMinSketch(200, 5)  # epsilon=0.01
    
    # 添加10000次a
    for _ in range(10000):
        cms_bound.add("a")
    
    est_a = cms_bound.estimate("a")
    print(f"  添加10000次'a'")
    print(f"  估计: {est_a}")
    print(f"  真实: 10000")
    print(f"  误差上界(epsilon*N): {0.01 * 10000}")
    
    # 测试5: 多元素
    print("\n测试5 - 多元素干扰:")
    cms_multi = CountMinSketch(50, 5)
    
    # 添加各种元素
    for _ in range(5000):
        cms_multi.add("a")
    for _ in range(1000):
        cms_multi.add("b")
    for _ in range(500):
        cms_multi.add("c")
    
    est_a = cms_multi.estimate("a")
    est_b = cms_multi.estimate("b")
    est_c = cms_multi.estimate("c")
    
    print(f"  a真实=5000, 估计={est_a}")
    print(f"  b真实=1000, 估计={est_b}")
    print(f"  c真实=500, 估计={est_c}")
    
    print("\n所有测试完成!")
