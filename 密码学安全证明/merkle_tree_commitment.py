"""
Merkle树承诺
==========================================

【算法原理】
Merkle树是一种哈希树结构，用于高效证明数据完整性。
Merkle承诺基于哈希函数，提供绑定和隐藏特性。

【时间复杂度】
- 构建: O(n log n)
- 证明生成: O(log n)
- 验证: O(log n)

【空间复杂度】O(n) 存储

【应用场景】
- 区块链（Merkle Patricia Tree）
- 证书透明度日志
- 去中心化存储验证
- 比特币Merkle Proof
"""

import hashlib
from typing import List, Tuple, Optional


class MerkleNode:
    """Merkle树节点"""
    def __init__(self, left=None, right=None, value=None):
        self.left = left
        self.right = right
        self.value = value  # 哈希值


class MerkleTree:
    """
    Merkle树

    【结构】
    - 叶子节点：数据的哈希
    - 内部节点：两个子节点哈希的拼接后再哈希
    - 根节点：Merkle根

    【特点】
    - 平衡二叉树
    - 验证只需log n个节点
    - 不可伪造（依赖哈希函数抗碰撞性）
    """

    def __init__(self, data: List[str] = None):
        self.leaves = []  # 叶子节点哈希
        self.nodes = []   # 所有节点
        self.root = None  # Merkle根

        if data:
            self.build(data)

    def _hash(self, data: str) -> str:
        """双SHA256（比特币风格）"""
        return hashlib.sha256(hashlib.sha256(data.encode()).digest()).hexdigest()

    def build(self, data: List[str]) -> None:
        """
        构建Merkle树

        【步骤】
        1. 计算所有数据项的哈希作为叶子
        2. 两两配对，父节点哈希 = Hash(左子 || 右子)
        3. 重复直到只剩一个根节点
        """
        # 叶子节点
        self.leaves = [self._hash(d) for d in data]

        # 如果叶子数为奇数，复制最后一个
        if len(self.leaves) % 2 == 1:
            self.leaves.append(self.leaves[-1])

        # 构建树
        current_level = self.leaves[:]
        self.nodes = current_level[:]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                parent = self._hash(left + right)
                next_level.append(parent)
                self.nodes.append(parent)
            current_level = next_level

        self.root = current_level[0] if current_level else None

    def get_proof(self, index: int) -> dict:
        """
        生成Merkle证明

        【参数】
        - index: 数据项索引

        【返回】
        - value: 数据项
        - proof: 路径上需要的兄弟节点
        - root: Merkle根
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError("Index out of range")

        proof = []
        current_index = index

        # 重新构建路径
        level = self.leaves[:]
        while len(level) > 1:
            # 确定兄弟节点位置
            sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1

            # 如果兄弟超出范围，复制自身
            if sibling_index >= len(level):
                sibling_index = current_index

            sibling = level[sibling_index]
            is_left = current_index % 2 == 1  # 当前是右子节点？

            proof.append({
                "hash": sibling,
                "is_left": is_left
            })

            # 向上移动
            current_index = current_index // 2
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else level[i]
                next_level.append(self._hash(left + right))
            level = next_level

        return {
            "leaf": self.leaves[index],
            "proof": proof,
            "root": self.root,
            "index": index
        }

    def verify_proof(self, proof: dict, root: str) -> bool:
        """
        验证Merkle证明

        【步骤】
        1. 从叶子开始
        2. 按路径顺序，计算父节点哈希
        3. 最终与根比较
        """
        current_hash = proof["leaf"]
        index = proof["index"]

        for step in proof["proof"]:
            sibling = step["hash"]
            if step["is_left"]:
                # 兄弟在左边: Hash(sibling || current)
                current_hash = self._hash(sibling + current_hash)
            else:
                # 兄弟在右边: Hash(current || sibling)
                current_hash = self._hash(current_hash + sibling)

        return current_hash == root

    def verify_proof_with_data(self, data: str, proof: dict, root: str) -> bool:
        """用原始数据验证Merkle证明"""
        computed_leaf = self._hash(data)
        if computed_leaf != proof["leaf"]:
            return False
        return self.verify_proof(proof, root)


class MerkleCommitment:
    """
    Merkle承诺

    【与Merkle树的区别】
    - 承诺 = Merkle根 + 随机盲因子
    - 提供隐藏性（但较弱）
    """

    def __init__(self, data: List[str] = None, blinding: str = None):
        self.blinding = blinding or self._random_blinding()
        self.tree = MerkleTree()
        if data:
            self.commit(data)

    def _random_blinding(self) -> str:
        """生成随机盲因子"""
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]

    def commit(self, data: List[str]) -> Tuple[str, str]:
        """
        创建Merkle承诺

        【返回】(commitment, opening)
        """
        # 追加盲因子到数据
        data_with_blinding = data + [self.blinding]
        self.tree.build(data_with_blinding)

        commitment = self.tree.root
        opening = self.blinding

        return commitment, opening

    def open(self, data: List[str]) -> str:
        """生成opening"""
        return self.blinding


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    import time

    print("=" * 50)
    print("Merkle树承诺 - 测试")
    print("=" * 50)

    # 测试1：基本Merkle树
    print("\n【测试1】基本Merkle树")
    data = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape"]
    tree = MerkleTree(data)
    print(f"  数据项数: {len(data)}")
    print(f"  Merkle根: {tree.root}")

    # 测试2：生成和验证证明
    print("\n【测试2】Merkle证明")
    for idx in [0, 3, 6]:
        proof = tree.get_proof(idx)
        valid = tree.verify_proof(proof, tree.root)
        print(f"  数据{idx}='{data[idx]}': 证明长度={len(proof['proof'])}, 验证={valid}")

    # 测试3：篡改检测
    print("\n【测试3】篡改检测")
    proof = tree.get_proof(2)
    print(f"  原数据: '{data[2]}', 验证: {tree.verify_proof_with_data(data[2], proof, tree.root)}")

    # 篡改数据
    tampered_data = "CHERRY"
    print(f"  篡改后: '{tampered_data}', 验证: {tree.verify_proof_with_data(tampered_data, proof, tree.root)}")

    # 测试4：Merkle承诺
    print("\n【测试4】Merkle承诺")
    mc = MerkleCommitment()
    data_to_commit = ["item1", "item2", "item3"]
    commitment, opening = mc.commit(data_to_commit)
    print(f"  承诺: {commitment[:20]}...")
    print(f"  Opening: {opening}")

    # 验证承诺
    opening_check = mc.open(data_to_commit)
    print(f"  Opening验证: {opening_check == opening}")

    # 测试5：性能
    print("\n【测试5】大规模性能")
    import random
    n = 10000
    large_data = [f"data_{i}" for i in range(n)]
    tree_large = MerkleTree(large_data)

    start = time.time()
    proof = tree_large.get_proof(5000)
    proof_time = (time.time() - start) * 1000

    start = time.time()
    valid = tree_large.verify_proof(proof, tree_large.root)
    verify_time = (time.time() - start) * 1000

    print(f"  {n}项数据:")
    print(f"  Merkle根: {tree_large.root[:20]}...")
    print(f"  证明生成: {proof_time:.2f}ms")
    print(f"  验证时间: {verify_time:.2f}ms")
    print(f"  证明长度: {len(proof['proof'])} (log2 {n} ≈ {n.bit_length()})")

    print("\n" + "=" * 50)
    print("Merkle树承诺测试完成！")
    print("=" * 50)
