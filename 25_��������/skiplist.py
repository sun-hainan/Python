# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / skiplist

本文件实现 skiplist 相关的算法功能。
"""

import random
from dataclasses import Node
from typing import Optional, Any, List


class SkipListNode:
    """跳表节点"""
    
    def __init__(self, key: Any, value: Any, level: int):
        self.key = key
        self.value = value
        self.forward: List[SkipListNode] = [None] * (level + 1)


class SkipList:
    """
    跳表实现
    
    层级概率：每层包含下一层约1/p的元素
    p=1/2时，平均每元素有2个指针
    """
    
    MAX_LEVEL = 16  # 最大层级
    P = 0.5  # 晋升概率
    
    def __init__(self):
        self.header = SkipListNode(None, None, self.MAX_LEVEL)
        self.level = 0
        self.size = 0
    
    def _random_level(self) -> int:
        """
        随机生成层级
        
        使用几何分布，层级k的概率 = P^k * (1-P)
        """
        level = 0
        while random.random() < self.P and level < self.MAX_LEVEL - 1:
            level += 1
        return level
    
    def search(self, key: Any) -> Optional[Any]:
        """
        查找键
        
        Args:
            key: 要查找的键
        
        Returns:
            对应的值或None
        """
        current = self.header
        
        # 从最高层开始，从左向右查找
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        
        current = current.forward[0]
        
        if current and current.key == key:
            return current.value
        return None
    
    def insert(self, key: Any, value: Any):
        """
        插入键值对
        
        Args:
            key: 键
            value: 值
        """
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.header
        
        # 记录每层需要更新的位置
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        
        # 检查是否已存在
        current = current.forward[0]
        
        if current and current.key == key:
            current.value = value
        else:
            # 插入新节点
            new_level = self._random_level()
            
            if new_level > self.level:
                for i in range(self.level + 1, new_level + 1):
                    update[i] = self.header
                self.level = new_level
            
            # 创建新节点
            new_node = SkipListNode(key, value, new_level)
            
            # 更新指针
            for i in range(new_level + 1):
                new_node.forward[i] = update[i].forward[i]
                update[i].forward[i] = new_node
            
            self.size += 1
    
    def delete(self, key: Any) -> bool:
        """
        删除键
        
        Args:
            key: 要删除的键
        
        Returns:
            是否成功删除
        """
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.header
        
        # 查找要删除的节点
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if current and current.key == key:
            # 删除节点
            for i in range(self.level + 1):
                if update[i].forward[i] == current:
                    update[i].forward[i] = current.forward[i]
            
            # 降低层级
            while self.level > 0 and self.header.forward[self.level] is None:
                self.level -= 1
            
            self.size -= 1
            return True
        
        return False
    
    def range_query(self, low: Any, high: Any) -> List[tuple]:
        """
        范围查询
        
        Args:
            low: 下界
            high: 上界
        
        Returns:
            [key, value] 列表
        """
        result = []
        current = self.header.forward[0]
        
        while current and current.key <= high:
            if current.key >= low:
                result.append((current.key, current.value))
            current = current.forward[0]
        
        return result
    
    def __len__(self) -> int:
        return self.size
    
    def __str__(self) -> str:
        result = []
        for i in range(self.level, -1, -1):
            level_str = f"L{i}: "
            current = self.header.forward[i]
            while current:
                level_str += f"({current.key}, {current.value}) -> "
                current = current.forward[i]
            level_str += "NIL"
            result.append(level_str)
        return "\n".join(result)


def demo_basic_operations():
    """演示基本操作"""
    print("=== 跳表基本操作演示 ===\n")
    
    skip_list = SkipList()
    
    # 插入
    print("插入元素:")
    for i in [3, 6, 7, 9, 12, 19, 25]:
        skip_list.insert(i, f"value-{i}")
        print(f"  插入 {i}")
    
    print(f"\n跳表大小: {len(skip_list)}")
    print(f"当前层级: {skip_list.level}")
    
    # 打印跳表结构
    print("\n跳表结构:")
    print(skip_list)
    
    # 查找
    print("\n查找测试:")
    for key in [6, 15, 25]:
        result = skip_list.search(key)
        print(f"  查找 {key}: {result if result else '未找到'}")
    
    # 范围查询
    print("\n范围查询 [5, 20]:")
    result = skip_list.range_query(5, 20)
    for key, value in result:
        print(f"  {key}: {value}")


def demo_random_levels():
    """演示随机层级分布"""
    print("\n=== 随机层级分布 ===\n")
    
    levels_count = [0] * 17
    
    # 模拟10000次随机层级生成
    skip_list = SkipList()
    for _ in range(10000):
        level = skip_list._random_level()
        levels_count[level] += 1
    
    print("随机层级分布 (10000次):")
    for i, count in enumerate(levels_count):
        if count > 0:
            pct = count / 100
            bar = '█' * int(count / 100)
            print(f"  Level {i}: {count:5d} ({pct:5.2f}%) {bar}")
    
    # 理论值
    print("\n理论分布 (P=0.5):")
    for i in range(8):
        theoretical = 10000 * (0.5 ** i) * 0.5
        print(f"  Level {i}: {theoretical:.0f} (期望)")


def demo_probability_analysis():
    """概率分析"""
    print("\n=== 跳表概率分析 ===\n")
    
    print("跳表高度分析:")
    print("  第k层元素数量的期望: n * P^k")
    print("  P = 0.5 时:")
    print()
    
    n = 1000000  # 100万元素
    print(f"  元素总数 n = {n:,}")
    print("  | 层级 | 期望数量 | 剩余元素 |")
    print("  |------|---------|---------|")
    
    remaining = n
    for k in range(8):
        expected = n * (0.5 ** k) * 0.5
        remaining = n * (0.5 ** k)
        print(f"  | {k:4d} | {expected:8.0f} | {remaining:7.0f} |")
    
    print()
    print("查找复杂度:")
    print("  期望比较次数: O(log n)")
    print("  具体: 从最高层开始，每层最多遍历几个节点")
    print("  高度期望: O(log n)")
    
    # 计算期望高度
    import math
    expected_height = math.log(n, 1/0.5)
    print(f"\n  n={n} 的期望高度: {expected_height:.1f} 层")


def demo_vs_balanced_tree():
    """对比平衡树"""
    print("\n=== 跳表 vs 平衡树 ===\n")
    
    print("| 特性        | 跳表      | 平衡树(AVL) |")
    print("|-------------|-----------|-------------|")
    print("| 查找复杂度   | O(log n)  | O(log n)    |")
    print("| 插入复杂度   | O(log n)  | O(log n)    |")
    print("| 删除复杂度   | O(log n)  | O(log n)    |")
    print("| 空间复杂度   | O(n log n)| O(n)        |")
    print("| 实现复杂度   | 简单      | 复杂        |")
    print("| 并发友好     | 是        | 否          |")
    print("| 顺序遍历     | 简单      | 简单        |")
    print("| 稳定性       | 概率保证  | 确定保证    |")
    
    print("\n跳表优势:")
    print("  1. 实现比AVL/红黑树简单得多")
    print("  2. 更容易实现并发版本")
    print("  3. 插入/删除不需要旋转")
    print("  4. 顺序遍历简单高效")
    
    print("\n平衡树优势:")
    print("  1. 确定性性能保证")
    print("  2. 空间效率更高")
    print("  3. 更广泛的使用经验")


def benchmark():
    """性能基准测试"""
    import time
    
    print("\n=== 性能基准测试 ===\n")
    
    skip_list = SkipList()
    
    n = 100000
    print(f"测试规模: {n:,} 元素")
    
    # 插入
    start = time.time()
    for i in range(n):
        skip_list.insert(i, f"value-{i}")
    insert_time = time.time() - start
    print(f"插入: {insert_time:.3f}s ({n/insert_time:,.0f} ops/s)")
    
    # 查找
    keys_to_find = [random.randint(0, n-1) for _ in range(10000)]
    
    start = time.time()
    for key in keys_to_find:
        skip_list.search(key)
    search_time = time.time() - start
    print(f"查找: {search_time:.3f}s ({10000/search_time:,.0f} ops/s)")
    
    # 范围查询
    start = time.time()
    for _ in range(1000):
        skip_list.range_query(n//4, n//4*3)
    range_time = time.time() - start
    print(f"范围查询: {range_time:.3f}s ({1000/range_time:,.0f} ops/s)")


if __name__ == "__main__":
    print("=" * 60)
    print("跳表 (Skip List) 完整实现")
    print("=" * 60)
    
    # 基本操作
    demo_basic_operations()
    
    # 随机层级
    demo_random_levels()
    
    # 概率分析
    demo_probability_analysis()
    
    # 与平衡树对比
    demo_vs_balanced_tree()
    
    # 性能测试
    benchmark()
    
    print("\n" + "=" * 60)
    print("跳表核心原理:")
    print("=" * 60)
    print("""
1. 层级结构:
   - 底层是普通有序链表
   - 每层是下层的快速通道
   - 元素以概率P晋升到上一层

2. 查找过程:
   - 从最高层开始
   - 找到小于目标的最大元素
   - 下降到下一层继续
   - O(log n) 平均时间

3. 插入过程:
   - 先查找插入位置
   - 随机决定新节点层数
   - 更新各层的前向指针

4. Redis Sorted Set:
   - 底层使用跳表
   - 结合哈希表实现O(1)查找
   - 元素按分数排序
""")
