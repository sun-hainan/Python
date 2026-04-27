# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / skiplist



本文件实现 skiplist 相关的算法功能。

"""



import random





class SkipListNode:

    """跳表节点"""



    def __init__(self, key, value, max_level=16):

        """

        初始化跳表节点

        

        参数:

            key: 键

            value: 值

            max_level: 最大层数

        """

        self.key = key

        self.value = value

        # 前进指针数组：forward[i] 指向第 i 层的下一个节点

        self.forward = [None] * (max_level + 1)



    def __str__(self):

        return f"({self.key}: {self.value})"





class SkipList:

    """跳表"""



    # 默认最大层数

    MAX_LEVEL = 16

    # 晋升概率

    P = 0.5



    def __init__(self, max_level=None):

        """

        初始化跳表

        

        参数:

            max_level: 最大层数，默认 16

        """

        self.max_level = max_level or self.MAX_LEVEL

        # 头节点（哨兵）

        self.header = SkipListNode(None, None, self.max_level)

        # 当前最大层数

        self.level = 0

        # 元素计数

        self.count = 0



    def _random_level(self):

        """

        随机生成节点高度

        

        返回:

            level: 节点高度（1 到 max_level）

        """

        level = 1

        while random.random() < self.P and level < self.max_level:

            level += 1

        return level



    def search(self, key):

        """

        搜索键对应的值

        

        参数:

            key: 要搜索的键

        返回:

            value: 找到的值，未找到返回 None

        """

        # 从最高层开始

        current = self.header

        for i in range(self.level, -1, -1):

            # 在第 i 层向前搜索，直到下一个节点键大于目标键

            while current.forward[i] and current.forward[i].key < key:

                current = current.forward[i]

        

        # 移动到最底层

        current = current.forward[0]

        

        # 检查是否找到

        if current and current.key == key:

            return current.value

        return None



    def insert(self, key, value):

        """

        插入键值对

        

        参数:

            key: 键

            value: 值

        """

        # 存储每层的前驱节点

        update = [None] * (self.max_level + 1)

        current = self.header

        

        # 从最高层向下搜索

        for i in range(self.level, -1, -1):

            while current.forward[i] and current.forward[i].key < key:

                current = current.forward[i]

            update[i] = current

        

        # 移动到最底层

        current = current.forward[0]

        

        # 如果键已存在，更新值

        if current and current.key == key:

            current.value = value

        else:

            # 生成随机高度

            new_level = self._random_level()

            

            # 如果新节点高度大于当前最大层

            if new_level > self.level:

                for i in range(self.level + 1, new_level + 1):

                    update[i] = self.header

                self.level = new_level

            

            # 创建新节点并插入

            new_node = SkipListNode(key, value, self.max_level)

            for i in range(new_level + 1):

                new_node.forward[i] = update[i].forward[i]

                update[i].forward[i] = new_node

            

            self.count += 1



    def delete(self, key):

        """

        删除键对应的节点

        

        参数:

            key: 要删除的键

        返回:

            success: 是否成功删除

        """

        update = [None] * (self.max_level + 1)

        current = self.header

        

        # 搜索要删除的节点

        for i in range(self.level, -1, -1):

            while current.forward[i] and current.forward[i].key < key:

                current = current.forward[i]

            update[i] = current

        

        current = current.forward[0]

        

        # 检查键是否存在

        if not current or current.key != key:

            return False

        

        # 删除节点

        for i in range(self.level + 1):

            if update[i].forward[i] == current:

                update[i].forward[i] = current.forward[i]

        

        # 更新层数

        while self.level > 0 and self.header.forward[self.level] is None:

            self.level -= 1

        

        self.count -= 1

        return True



    def contains(self, key):

        """检查键是否存在"""

        return self.search(key) is not None



    def get_min(self):

        """获取最小键值对"""

        if self.count == 0:

            return None, None

        node = self.header.forward[0]

        return node.key, node.value



    def get_max(self):

        """获取最大键值对"""

        if self.count == 0:

            return None, None

        

        current = self.header

        for i in range(self.level, -1, -1):

            while current.forward[i]:

                current = current.forward[i]

        return current.key, current.value



    def range_query(self, lo, hi):

        """

        范围查询

        

        参数:

            lo: 下界

            hi: 上界

        返回:

            results: [(key, value), ...] 列表

        """

        results = []

        current = self.header.forward[0]

        

        while current and current.key < lo:

            current = current.forward[0]

        

        while current and current.key <= hi:

            results.append((current.key, current.value))

            current = current.forward[0]

        

        return results



    def __len__(self):

        """返回元素数量"""

        return self.count



    def __str__(self):

        """返回跳表的字符串表示"""

        if self.count == 0:

            return "SkipList: []"

        

        items = []

        current = self.header.forward[0]

        for _ in range(min(self.count, 20)):

            if current:

                items.append(str(current))

                current = current.forward[0]

            else:

                break

        

        suffix = " ..." if self.count > 20 else ""

        return f"SkipList: [{', '.join(items)}{suffix}]"



    def print_levels(self):

        """打印每层结构（用于调试）"""

        print(f"跳表 (层数={self.level}, 元素={self.count})")

        for i in range(self.level, -1, -1):

            row = []

            current = self.header

            while current.forward[i]:

                row.append(f"[{current.forward[i].key}]")

                current = current.forward[i]

            print(f"  Level {i}: {' -> '.join(row)}")





if __name__ == "__main__":

    # 测试跳表

    print("=== 跳表测试 ===\n")



    # 创建跳表

    skip_list = SkipList()



    # 插入测试

    print("--- 插入测试 ---")

    test_data = [(3, "three"), (1, "one"), (7, "seven"), (5, "five"), (9, "nine"), (2, "two")]

    for key, value in test_data:

        skip_list.insert(key, value)

        print(f"插入 ({key}, {value}): 长度={len(skip_list)}")



    print(f"\n跳表内容: {skip_list}")

    skip_list.print_levels()



    # 搜索测试

    print("\n--- 搜索测试 ---")

    search_keys = [5, 8, 1]

    for key in search_keys:

        result = skip_list.search(key)

        print(f"  搜索 {key}: {'找到 ' + str(result) if result else '未找到'}")



    # 范围查询

    print("\n--- 范围查询 ---")

    results = skip_list.range_query(2, 7)

    print(f"  范围 [2, 7]: {results}")



    # 删除测试

    print("\n--- 删除测试 ---")

    delete_keys = [5, 10]

    for key in delete_keys:

        success = skip_list.delete(key)

        print(f"  删除 {key}: {'成功' if success else '失败'}")

        print(f"  跳表: {skip_list}")



    # 最小/最大

    print("\n--- 最小/最大 ---")

    min_k, min_v = skip_list.get_min()

    max_k, max_v = skip_list.get_max()

    print(f"  最小: ({min_k}, {min_v})")

    print(f"  最大: ({max_k}, {max_v})")



    # 性能测试

    print("\n--- 性能测试 ---")

    import time

    

    large_skip_list = SkipList()

    n = 10000

    start = time.time()

    for i in range(n):

        large_skip_list.insert(i, f"value_{i}")

    insert_time = time.time() - start

    

    start = time.time()

    for i in range(n):

        large_skip_list.search(random.randint(0, n))

    search_time = time.time() - start

    

    print(f"  插入 {n} 个元素: {insert_time:.3f}s")

    print(f"  搜索 {n} 次: {search_time:.3f}s")

    print(f"  跳表长度: {len(large_skip_list)}")

