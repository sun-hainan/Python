# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / merkle_tree

本文件实现 merkle_tree 相关的算法功能。
"""

import hashlib


class MerkleTree:
    """Merkle树"""

    def __init__(self, data_blocks: List[str]):
        """
        参数：
            data_blocks: 数据块列表
        """
        self.data_blocks = data_blocks
        self.leaves = [self._hash(data.encode()) for data in data_blocks]
        self.root = self._build_tree()

    def _hash(self, data: bytes) -> str:
        """双SHA256哈希（比特币风格）"""
        return hashlib.sha256(hashlib.sha256(data).digest()).hexdigest()

    def _build_tree(self) -> str:
        """构建Merkle树"""
        current_level = self.leaves.copy()
        level = 0

        while len(current_level) > 1:
            next_level = []

            # 如果奇数个，复制最后一个
            if len(current_level) % 2 == 1:
                current_level.append(current_level[-1])

            # 两两配对
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i+1]
                next_level.append(self._hash(combined.encode()))

            current_level = next_level
            level += 1

        return current_level[0] if current_level else None

    def get_proof(self, index: int) -> List[Tuple[str, str]]:
        """
        获取验证路径

        返回：[(邻居哈希, 方向), ...]
        其中方向='left'表示该邻居是左兄弟，'right'表示右兄弟
        """
        if index >= len(self.leaves):
            return []

        proof = []
        current_level = self.leaves.copy()
        idx = index

        while len(current_level) > 1:
            if len(current_level) % 2 == 1:
                current_level.append(current_level[-1])

            # 确定邻居索引
            if idx % 2 == 0:
                neighbor_idx = idx + 1
                direction = 'right'
            else:
                neighbor_idx = idx - 1
                direction = 'left'

            proof.append((current_level[neighbor_idx], direction))

            # 上升到父节点
            parent_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i+1]
                parent_level.append(self._hash(combined.encode()))

            current_level = parent_level
            idx = idx // 2

        return proof

    def verify_proof(self, index: int, data: str, root: str, proof: List) -> bool:
        """
        验证数据块的Merkle证明

        参数：
            index: 数据块索引
            data: 原始数据
            root: Merkle根
            proof: 验证路径

        返回：是否验证通过
        """
        current_hash = self._hash(data.encode())

        for neighbor_hash, direction in proof:
            if direction == 'left':
                combined = current_hash + neighbor_hash
            else:
                combined = neighbor_hash + current_hash
            current_hash = self._hash(combined.encode())

        return current_hash == root


class SimplifiedMerkleTree:
    """简化版Merkle树"""

    def __init__(self):
        self.nodes = {}  # {(level, index): hash}

    def build(self, data_list: List[str]) -> str:
        """构建树"""
        n = len(data_list)
        level = 0

        # 叶子节点
        for i, data in enumerate(data_list):
            self.nodes[(0, i)] = hashlib.sha256(data.encode()).hexdigest()

        current_level_size = n

        while current_level_size > 1:
            level += 1
            new_size = (current_level_size + 1) // 2

            for i in range(new_size):
                left_idx = i * 2
                right_idx = left_idx + 1

                if right_idx >= current_level_size:
                    # 奇数，复制最后一个
                    right_idx = left_idx

                left_hash = self.nodes[(level-1, left_idx)]
                right_hash = self.nodes[(level-1, right_idx)]

                combined = left_hash + right_hash
                self.nodes[(level, i)] = hashlib.sha256(combined.encode()).hexdigest()

            current_level_size = new_size

        return self.nodes[(level, 0)]


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Merkle树测试 ===\n")

    # 创建数据块
    blocks = [
        "block1: Alice pays Bob 10 BTC",
        "block2: Bob pays Charlie 5 BTC",
        "block3: Charlie pays Dave 3 BTC",
        "block4: Dave pays Eve 2 BTC",
    ]

    print("数据块:")
    for b in blocks:
        print(f"  {b[:30]}...")

    print()

    # 构建Merkle树
    tree = MerkleTree(blocks)

    print(f"Merkle根: {tree.root}")
    print()

    # 获取验证路径
    block_index = 0
    proof = tree.get_proof(block_index)

    print(f"验证块 {block_index} 的证明:")
    print(f"  数据: {blocks[block_index]}")
    print(f"  证明路径:")
    for neighbor, direction in proof:
        print(f"    {direction}: {neighbor[:20]}...")

    # 验证
    is_valid = tree.verify_proof(block_index, blocks[block_index], tree.root, proof)
    print(f"\n验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")

    print("\n说明：")
    print("  - Merkle树允许高效验证部分数据")
    print("  - 比特币用双SHA256")
    print("  - SPV（简单支付验证）就基于Merkle证明")
