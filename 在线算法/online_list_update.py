# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / online_list_update

本文件实现 online_list_update 相关的算法功能。
"""

import random
import math


class ListElement:
    """列表元素"""

    def __init__(self, key, data=None):
        self.key = key
        self.data = data
        self.prev = None
        self.next = None


class LinkedList:
    """链表实现"""

    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, element):
        """在末尾添加"""
        if self.head is None:
            self.head = element
            self.tail = element
        else:
            element.prev = self.tail
            self.tail.next = element
            self.tail = element
        self.size += 1

    def remove(self, element):
        """移除元素"""
        if element.prev:
            element.prev.next = element.next
        else:
            self.head = element.next
        
        if element.next:
            element.next.prev = element.prev
        else:
            self.tail = element.prev
        
        element.prev = None
        element.next = None
        self.size -= 1

    def insert_after(self, element, new_element):
        """在元素后插入"""
        new_element.prev = element
        new_element.next = element.next
        
        if element.next:
            element.next.prev = new_element
        else:
            self.tail = new_element
        
        element.next = new_element
        self.size += 1

    def get_position(self, element):
        """获取元素位置（1-indexed）"""
        pos = 1
        current = self.head
        while current and current != element:
            current = current.next
            pos += 1
        return pos if current == element else -1

    def find(self, key):
        """查找元素"""
        current = self.head
        while current:
            if current.key == key:
                return current
            current = current.next
        return None

    def __len__(self):
        return self.size


class OnlineListUpdate:
    """在线列表更新算法基类"""

    def __init__(self, items):
        """
        初始化
        
        参数:
            items: 初始元素列表
        """
        self.list = LinkedList()
        self.access_cost = 0
        self.move_cost = 0
        self.accesses = 0
        
        # 创建元素并添加到列表
        self.elements = {}
        for item in items:
            elem = ListElement(item)
            self.elements[item] = elem
            self.list.append(elem)

    def access(self, key):
        """
        访问元素
        
        参数:
            key: 要访问的键
        返回:
            cost: 访问代价
        """
        elem = self.list.find(key)
        if elem is None:
            return -1
        
        # 计算位置（访问代价）
        pos = self.list.get_position(elem)
        self.access_cost += pos
        self.accesses += 1
        
        # 根据算法执行移动
        self.on_access(elem)
        
        return pos

    def on_access(self, element):
        """
        访问后的处理（子类实现）
        
        参数:
            element: 被访问的元素
        """
        raise NotImplementedError

    def get_total_cost(self):
        """获取总代价"""
        return self.access_cost + self.move_cost

    def get_stats(self):
        """获取统计"""
        return {
            'access_cost': self.access_cost,
            'move_cost': self.move_cost,
            'total_cost': self.get_total_cost(),
            'accesses': self.accesses
        }


class MoveToFront(OnlineListUpdate):
    """
    Move-To-Front (MTF) 算法
    
    每次访问后将元素移动到列表前端
    """

    def on_access(self, element):
        """移动到前端"""
        if element != self.list.head:
            self.list.remove(element)
            element.next = self.list.head
            if self.list.head:
                self.list.head.prev = element
            self.list.head = element
            if element.next is None:
                self.list.tail = element
            self.move_cost += 1


class Transpose(OnlineListUpdate):
    """
    Transpose 算法
    
    每次访问后将元素与其前一个元素交换
    """

    def on_access(self, element):
        """与前一个元素交换"""
        if element.prev:
            prev = element.prev
            # 移除 element
            self.list.remove(element)
            # 在 prev 前面插入
            if prev.prev:
                prev.prev.next = element
                element.prev = prev.prev
            else:
                self.list.head = element
                element.prev = None
            element.next = prev
            prev.prev = element
            self.move_cost += 1


class FrequencyCount(OnlineListUpdate):
    """
    Frequency Count 算法
    
    维护每个元素的访问计数，按频率排序
    """

    def __init__(self, items):
        super().__init__(items)
        self.count = {item: 0 for item in items}

    def on_access(self, element):
        """增加计数并可能重新排序"""
        key = element.key
        self.count[key] += 1
        
        # 如果前一个元素计数更少，交换
        if element.prev and self.count[element.prev.key] < self.count[key]:
            # 找到正确的位置（按频率递减）
            current = element.prev
            while current.prev and self.count[current.prev.key] < self.count[key]:
                current = current.prev
            
            if current != element.prev:
                # 移动 element 到 current 之后
                self.list.remove(element)
                self.list.insert_after(current, element)
                self.move_cost += 1


class TimestampUpdate(OnlineListUpdate):
    """
    Timestamp 算法
    
    记录每个元素上次访问时间，按最近访问排序
    """

    def __init__(self, items):
        super().__init__(items)
        self.timestamp = {item: 0 for item in items}
        self.current_time = 0

    def on_access(self, element):
        """更新 timestamp 并可能移动"""
        key = element.key
        self.current_time += 1
        self.timestamp[key] = self.current_time
        
        # 如果前一个元素的 timestamp 更小（更旧），交换
        if element.prev and self.timestamp[element.prev.key] < self.timestamp[key]:
            # 移动到正确位置（timestamp 递减）
            current = element.prev
            while current.prev and self.timestamp[current.prev.key] < self.timestamp[key]:
                current = current.prev
            
            if current != element.prev:
                self.list.remove(element)
                self.list.insert_after(current, element)
                self.move_cost += 1


class RandomizedListUpdate(OnlineListUpdate):
    """
    随机化算法
    
    以一定概率执行 MTF
    """

    def __init__(self, items, probability=0.5):
        super().__init__(items)
        self.probability = probability

    def on_access(self, element):
        """以概率 p 执行 MTF"""
        if random.random() < self.probability:
            if element != self.list.head:
                self.list.remove(element)
                element.next = self.list.head
                if self.list.head:
                    self.list.head.prev = element
                self.list.head = element
                if element.next is None:
                    self.list.tail = element
                self.move_cost += 1


class Bit(OnlineListUpdate):
    """
    BIT (Best Integer) 算法
    
    使用两列表方法
    """

    def __init__(self, items):
        super().__init__(items)
        # 辅助列表
        self辅助列表 = LinkedList()
        self.辅助元素 = {}
        
        for item in items:
            elem = ListElement(item)
            self.辅助元素[item] = elem
            self.辅助列表.append(elem)
        
        self.bit_level = {item: 0 for item in items}

    def on_access(self, element):
        """BIT 规则"""
        key = element.key
        level = self.bit_level[key]
        
        # 提升到更高层级
        self.bit_level[key] = min(level + 1, len(self.elements) - 1)
        
        # 以概率 2^{-level} 执行 MTF
        if random.random() < 2 ** (-level):
            if element != self.list.head:
                self.list.remove(element)
                element.next = self.list.head
                if self.list.head:
                    self.list.head.prev = element
                self.list.head = element
                self.move_cost += 1


class Timestamp:
    """
    时间戳算法（另一个版本）
    
    简化实现
    """

    def __init__(self, items):
        self.items = list(items)
        self.timestamps = {item: 0 for item in items}
        self.time = 0

    def access(self, key):
        """访问并返回代价"""
        self.time += 1
        self.timestamps[key] = self.time
        
        # 找到位置
        try:
            pos = self.items.index(key) + 1
            # 移动到开头
            self.items.remove(key)
            self.items.insert(0, key)
            return pos
        except ValueError:
            return -1


def optimal_offline(items, requests):
    """
    离线最优算法（用于比较）
    
    使用逆序生成最优排列
    """
    # 统计频率
    freq = {}
    for key in requests:
        freq[key] = freq.get(key, 0) + 1
    
    # 按频率排序
    sorted_items = sorted(items, key=lambda x: -freq.get(x, 0))
    
    # 计算代价
    item_pos = {item: i + 1 for i, item in enumerate(sorted_items)}
    total_cost = sum(item_pos.get(key, len(items)) for key in requests)
    
    return total_cost


if __name__ == "__main__":
    print("=== 在线列表更新测试 ===\n")

    # 初始化元素
    items = ['a', 'b', 'c', 'd', 'e']

    # 测试序列
    requests = ['a', 'b', 'c', 'a', 'd', 'a', 'e', 'a']

    print("--- 测试序列 ---")
    print(f"元素: {items}")
    print(f"请求: {requests}\n")

    # 测试各算法
    algorithms = [
        ('MTF', MoveToFront),
        ('Transpose', Transpose),
        ('Frequency', FrequencyCount),
        ('Timestamp', TimestampUpdate),
        ('Random', lambda x: RandomizedListUpdate(x, 0.5)),
    ]

    print("--- 各算法结果 ---")
    for name, algo_class in algorithms:
        algo = algo_class(items[:])
        for req in requests:
            algo.access(req)
        
        stats = algo.get_stats()
        print(f"{name}: 访问代价={stats['access_cost']}, "
              f"移动代价={stats['move_cost']}, 总代价={stats['total_cost']}")

    # 离线最优
    opt_cost = optimal_offline(items, requests)
    print(f"\n离线最优: {opt_cost}")

    # 竞争比
    print("\n--- 竞争比 ---")
    for name, algo_class in algorithms:
        algo = algo_class(items[:])
        for req in requests:
            algo.access(req)
        ratio = algo.get_total_cost() / opt_cost if opt_cost > 0 else 0
        print(f"{name}: {ratio:.2f}")

    # 模拟 Zipf 访问模式
    print("\n--- Zipf 访问模拟 ---")
    import random
    
    def zipf_access(n, alpha=1.0):
        """生成 Zipf 分布的访问序列"""
        # 简化的 Zipf 生成
        weights = [1.0 / (i + 1) ** alpha for i in range(n)]
        total = sum(weights)
        probs = [w / total for w in weights]
        
        r = random.random()
        cumsum = 0
        for i, p in enumerate(probs):
            cumsum += p
            if r <= cumsum:
                return i
        return n - 1

    # 生成 Zipf 请求
    n_items = 20
    items = list(range(n_items))
    zipf_requests = [zipf_access(n_items) for _ in range(1000)]

    print(f"元素数: {n_items}, 请求数: {len(zipf_requests)}")

    # 各算法性能
    algorithms = [
        ('MTF', MoveToFront),
        ('Transpose', Transpose),
        ('Frequency', FrequencyCount),
        ('Timestamp', TimestampUpdate),
    ]

    results = {}
    for name, algo_class in algorithms:
        algo = algo_class(items[:])
        for req in zipf_requests:
            algo.access(req)
        results[name] = algo.get_total_cost()
        print(f"{name}: 总代价 = {results[name]}")

    # 离线最优
    opt_cost = optimal_offline(items, zipf_requests)
    print(f"离线最优: {opt_cost}")

    print("\n--- 竞争比 ---")
    for name, cost in results.items():
        ratio = cost / opt_cost if opt_cost > 0 else 0
        print(f"{name}: {ratio:.2f}")

    # 时间戳算法单独测试
    print("\n--- Timestamp 算法单独测试 ---")
    ts = Timestamp(items)
    for req in requests:
        cost = ts.access(req)
    
    # 手动计算代价
    ts_cost = sum(i + 1 for i in range(len(requests)))
    print(f"Timestamp 代价: {ts_cost}")

    # 性能测试
    print("\n--- 性能测试 ---")
    import time
    
    n = 10000
    large_items = list(range(100))
    large_requests = [random.randint(0, 99) for _ in range(n)]
    
    for name, algo_class in [('MTF', MoveToFront), ('Frequency', FrequencyCount)]:
        algo = algo_class(large_items[:])
        
        start = time.time()
        for req in large_requests:
            algo.access(req)
        elapsed = time.time() - start
        
        print(f"{name}: {n} 次访问, {elapsed:.2f}s ({n/elapsed:.0f} ops/s)")
