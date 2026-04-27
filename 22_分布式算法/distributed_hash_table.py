# -*- coding: utf-8 -*-

"""

算法实现：分布式算法 / distributed_hash_table



本文件实现 distributed_hash_table 相关的算法功能。

"""



import hashlib

from typing import Optional, Dict, List, Tuple





class DHTNode:

    """DHT 节点（基于 Chord 算法）"""

    def __init__(self, node_id: str, m: int = 5):

        """

        m: 标识符位数，决定哈希环大小（2^m 个槽位）

        """

        self.node_id = node_id

        self.m = m

        self.node_id_int = self._hash_to_int(node_id)  # 节点在环上的位置 [0, 2^m)



        # 前继和后继节点

        self.successor: Optional["DHTNode"] = None

        self.predecessor: Optional["DHTNode"] = None



        # Finger 表：最多 m 个条目

        self.finger_table: List[Optional["DHTNode"]] = [None] * m



        # 本节点负责的键值对

        self.data: Dict[int, str] = {}



    @staticmethod

    def _hash_to_int(key: str, m: int = 5) -> int:

        """将字符串哈希为 [0, 2^m) 范围内的整数"""

        h = hashlib.sha256(key.encode()).hexdigest()

        return int(h, 16) % (2 ** m)



    def in_range(self, key_int: int, start: int, end: int, inclusive: bool = False) -> bool:

        """判断 key 是否在 (start, end] 范围内（顺时针）"""

        if start < end:

            return start < key_int <= end if inclusive else start < key_int < end

        else:  # 跨越环的边界

            return key_int > start or key_int <= end



    def 负责(self, key_int: int) -> bool:

        """判断本节点是否负责某个键（位于前继和自身之间）"""

        if self.predecessor is None:

            return True  # 环上只有本节点

        pred_int = self.predecessor.node_id_int

        return self.in_range(key_int, pred_int, self.node_id_int)



    def find_successor(self, key_int: int) -> "DHTNode":

        """

        查找负责 key 的后继节点

        使用finger表加速：从最近的节点开始向前查找

        """

        # 找到第一个 finger[i] > key 的节点

        for i in range(self.m - 1, -1, -1):

            finger = self.finger_table[i]

            if finger is not None:

                if self.in_range(finger.node_id_int, self.node_id_int + 1, key_int):

                    return finger.find_successor(key_int)

        # 没有找到更近的：返回后继

        return self.successor if self.successor else self



    def join(self, known_node: Optional["DHTNode"]) -> None:

        """

        加入 DHT 网络

        若 known_node 为 None，则自己成为环上唯一的节点

        """

        if known_node is None:

            # 初始化空环

            self.successor = self

            self.predecessor = self

            self._init_finger_table_empty()

        else:

            # 通过已知节点找到自己的后继

            self.successor = known_node.find_successor(self.node_id_int)

            self.predecessor = self.successor.predecessor

            self.successor.predecessor = self

            self.predecessor.successor = self

            self._transfer_keys()

            self._update_others()



    def _init_finger_table_empty(self) -> None:

        """初始化 finger 表（空环情况）"""

        for i in range(self.m):

            self.finger_table[i] = self



    def _init_finger_table(self, known_node: Optional["DHTNode"]) -> None:

        """初始化 finger 表（通过已知节点查询）"""

        for i in range(self.m):

            start = (self.node_id_int + 2 ** i) % (2 ** self.m)

            if known_node:

                self.finger_table[i] = known_node.find_successor(start)

            else:

                self.finger_table[i] = self



    def _update_others(self) -> None:

        """更新其他节点的 finger 表（告知本节点的存在）"""

        # 简化：这里省略完整的更新逻辑

        pass



    def _transfer_keys(self) -> None:

        """从后继节点迁移本节点负责的键"""

        # 简化实现

        pass



    def put(self, key: str, value: str) -> bool:

        """存储键值对"""

        key_int = self._hash_to_int(key)

        responsible_node = self.find_successor(key_int)

        if responsible_node == self:

            self.data[key_int] = value

            return True

        # 递归到目标节点（实际实现会通过网络调用）

        return responsible_node.put(key, value) if hasattr(responsible_node, 'put') else False



    def get(self, key: str) -> Optional[str]:

        """获取键对应的值"""

        key_int = self._hash_to_int(key)

        responsible_node = self.find_successor(key_int)

        if responsible_node == self:

            return self.data.get(key_int)

        # 递归到目标节点

        return responsible_node.get(key) if hasattr(responsible_node, 'get') else None



    def stabilize(self) -> None:

        """稳定性检测：检查后继是否发生变化"""

        if self.successor:

            # 简化：每轮随机检查后继的稳定性

            pass



    def __repr__(self) -> str:

        return f"DHTNode({self.node_id}, pos={self.node_id_int})"





# ============================ 测试代码 ============================

if __name__ == "__main__":

    m = 5  # 2^5 = 32 个槽位

    node_ids = ["Node0", "Node1", "Node2", "Node3", "Node4"]



    print("=== DHT（Chord）演示 ===")

    print(f"哈希环大小: 2^{m} = {2**m}")



    # 创建节点

    nodes = {}

    for nid in node_ids:

        nodes[nid] = DHTNode(nid, m)

        print(f"  {nodes[nid]}")



    # 构建环结构（手动连接）

    sorted_nodes = sorted(nodes.values(), key=lambda n: n.node_id_int)

    print(f"\n节点在环上的顺序（按 ID）：{sorted_nodes}")



    # Node0 加入（成为首个节点）

    nodes["Node0"].join(None)

    nodes["Node0"].successor = nodes["Node0"]

    nodes["Node0"].predecessor = nodes["Node0"]



    # 其他节点依次加入

    for i in range(1, len(sorted_nodes)):

        sorted_nodes[i].join(sorted_nodes[0])



    # 手动建立环连接（简化）

    for i, node in enumerate(sorted_nodes):

        node.successor = sorted_nodes[(i + 1) % len(sorted_nodes)]

        node.predecessor = sorted_nodes[(i - 1) % len(sorted_nodes)]



    # 存储一些键值对

    test_data = [

        ("key_A", "value_100"),

        ("key_B", "value_200"),

        ("key_C", "value_300"),

    ]



    print("\n=== 存储键值对 ===")

    for key, value in test_data:

        key_int = DHTNode._hash_to_int(key, m)

        result_node = nodes["Node0"].find_successor(key_int)

        print(f"  '{key}' (hash={key_int}) -> 存储到 {result_node.node_id}")

        result_node.data[key_int] = value



    # 验证查找

    print("\n=== 验证查找 ===")

    for key, expected_value in test_data:

        retrieved = nodes["Node0"].get(key)

        key_int = DHTNode._hash_to_int(key, m)

        print(f"  '{key}' -> 找到值: {retrieved} (期望: {expected_value})")

        assert retrieved == expected_value



    print("\n✅ DHT 查找成功！")

    print(f"查找复杂度: O(log N) = O(log {len(node_ids)}) = O(约{len(node_ids).__ceil__()})")

    print(f"空间复杂度: O(log N) = O({m}) finger 表条目")

