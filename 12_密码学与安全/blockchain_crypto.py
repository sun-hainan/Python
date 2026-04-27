# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / blockchain_crypto



本文件实现 blockchain_crypto 相关的算法功能。

"""



import hashlib

from typing import List, Tuple, Optional

from dataclasses import dataclass





@dataclass

class Transaction:

    """交易数据结构"""

    sender: str      # 发送者地址

    receiver: str    # 接收者地址

    amount: float    # 金额

    data: str        # 附加数据

    timestamp: float # 时间戳



    def to_string(self) -> str:

        """转换为字符串用于哈希"""

        return f"{self.sender}|{self.receiver}|{self.amount}|{self.data}|{self.timestamp}"



    def hash(self) -> str:

        """计算交易哈希"""

        return hashlib.sha256(self.to_string().encode()).hexdigest()





@dataclass

class MerkleNode:

    """Merkle树节点"""

    left: Optional['MerkleNode']   # 左子节点

    right: Optional['MerkleNode'] # 右子节点

    hash: str                      # 节点哈希



    @staticmethod

    def leaf(data: str) -> 'MerkleNode':

        """创建叶子节点"""

        return MerkleNode(None, None, data)



    def is_leaf(self) -> bool:

        """是否为叶子节点"""

        return self.left is None and self.right is None





class MerkleTree:

    """Merkle树实现"""



    def __init__(self, data_list: List[str]):

        """

        初始化Merkle树



        参数：

            data_list: 数据列表（叶子节点数据）

        """

        self.root = self._build_tree(data_list)

        self.leaves = [MerkleNode.leaf(d) for d in data_list]



    def _hash_pair(self, left_hash: str, right_hash: str) -> str:

        """

        哈希一对节点



        参数：

            left_hash: 左节点哈希

            right_hash: 右节点哈希



        返回：父节点哈希

        """

        combined = left_hash + right_hash

        return hashlib.sha256(combined.encode()).hexdigest()



    def _build_tree(self, data_list: List[str]) -> MerkleNode:

        """

        构建Merkle树



        参数：

            data_list: 叶子节点数据列表



        返回：根节点

        """

        if not data_list:

            raise ValueError("数据列表不能为空")



        # 已经是哈希值，创建叶子节点

        if len(data_list) == 1:

            return MerkleNode.leaf(data_list[0])



        # 如果是奇数个，复制最后一个

        if len(data_list) % 2 == 1:

            data_list = data_list + [data_list[-1]]



        # 递归构建

        next_level = []

        for i in range(0, len(data_list), 2):

            left_hash = data_list[i]

            right_hash = data_list[i + 1]

            parent_hash = self._hash_pair(left_hash, right_hash)

            node = MerkleNode(

                MerkleNode.leaf(left_hash),

                MerkleNode.leaf(right_hash),

                parent_hash

            )

            next_level.append(node)



        # 递归构建上层

        return self._build_tree([n.hash for n in next_level])



    def get_merkle_root(self) -> str:

        """

        获取Merkle根



        返回：Merkle树根哈希

        """

        return self.root.hash



    def get_proof(self, index: int) -> List[Tuple[str, bool]]:

        """

        获取Merkle证明（验证某数据在树中）



        参数：

            index: 叶子节点索引



        返回：验证路径 [(邻居哈希, 是否为左邻居), ...]

        """

        if index < 0 or index >= len(self.leaves):

            raise ValueError("索引超出范围")



        proof = []

        current_level = self.leaves

        current_index = index



        while len(current_level) > 1:

            # 如果是奇数个，复制最后一个

            if len(current_level) % 2 == 1:

                current_level = current_level + [current_level[-1]]



            # 确定兄弟节点

            if current_index % 2 == 0:

                sibling_index = current_index + 1

                is_left = False

            else:

                sibling_index = current_index - 1

                is_left = True



            proof.append((current_level[sibling_index].hash, is_left))



            # 移动到上一层

            next_level = []

            for i in range(0, len(current_level), 2):

                left = current_level[i]

                right = current_level[i + 1]

                parent_hash = self._hash_pair(left.hash, right.hash)

                parent = MerkleNode(left, right, parent_hash)

                next_level.append(parent)



            current_level = next_level

            current_index = current_index // 2



        return proof



    def verify_proof(self, data_hash: str, proof: List[Tuple[str, bool]], root: str) -> bool:

        """

        验证Merkle证明



        参数：

            data_hash: 数据哈希

            proof: Merkle证明

            root: Merkle根



        返回：验证结果

        """

        current_hash = data_hash



        for sibling_hash, is_left in proof:

            if is_left:

                current_hash = self._hash_pair(current_hash, sibling_hash)

            else:

                current_hash = self._hash_pair(sibling_hash, current_hash)



        return current_hash == root





class BlockchainSignature:

    """区块链交易签名（简化实现）"""



    def __init__(self, private_key: int, public_key: int):

        """

        初始化签名器



        参数：

            private_key: 私钥

            public_key: 公钥

        """

        self.private_key = private_key

        self.public_key = public_key



    def sign(self, transaction: Transaction) -> str:

        """

        签名交易



        参数：

            transaction: 待签名交易



        返回：签名（简化：交易哈希的简单变换）

        """

        tx_hash = transaction.hash()

        # 简化：实际应使用ECDSA

        signature = hashlib.sha256(

            (tx_hash + str(self.private_key)).encode()

        ).hexdigest()

        return signature



    def verify(self, transaction: Transaction, signature: str) -> bool:

        """

        验证签名



        参数：

            transaction: 交易

            signature: 签名



        返回：验证结果

        """

        expected_sig = hashlib.sha256(

            (transaction.hash() + str(self.private_key)).encode()

        ).hexdigest()

        return signature == expected_sig





def merkle_tree_use_cases():

    """Merkle树应用场景"""

    print("=== Merkle树应用场景 ===")

    print()

    print("1. 区块链")

    print("   - 比特币：快速验证交易")

    print("   - 以太坊：状态树、交易树、收据树")

    print()

    print("2. 分布式系统")

    print("   - Git版本控制")

    print("   - IPFS内容寻址")

    print()

    print("3. 证书透明度日志")

    print("   - 验证证书颁发记录")

    print()

    print("4. 数据完整性验证")

    print("   - 大文件分段校验")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 区块链密码学测试 ===\n")



    # 创建测试交易

    transactions = [

        Transaction("Alice", "Bob", 1.0, "Payment 1", 1000000.0),

        Transaction("Bob", "Charlie", 0.5, "Payment 2", 1000001.0),

        Transaction("Charlie", "Alice", 0.25, "Payment 3", 1000002.0),

        Transaction("Alice", "David", 0.75, "Payment 4", 1000003.0),

    ]



    print("交易列表：")

    for i, tx in enumerate(transactions):

        print(f"  {i}: {tx.sender} -> {tx.receiver}: {tx.amount} ETH")

    print()



    # 构建Merkle树

    tx_hashes = [tx.hash() for tx in transactions]

    merkle = MerkleTree(tx_hashes)



    print(f"Merkle根: {merkle.get_merkle_root()}")

    print()



    # 获取Merkle证明

    for i, tx in enumerate(transactions):

        proof = merkle.get_proof(i)

        data_hash = tx.hash()



        # 验证证明

        verified = merkle.verify_proof(data_hash, proof, merkle.get_merkle_root())



        print(f"交易{i}的Merkle证明验证: {'通过' if verified else '失败'}")

    print()



    # 交易签名测试

    print("交易签名测试：")

    tx = transactions[0]



    # 简化：使用固定密钥

    signer = BlockchainSignature(private_key=12345, public_key=67890)



    signature = signer.sign(tx)

    print(f"  交易哈希: {tx.hash()}")

    print(f"  签名: {signature[:32]}...")

    print(f"  签名验证: {'通过' if signer.verify(tx, signature) else '失败'}")

    print()



    # 篡改检测

    tampered_tx = Transaction(tx.sender, tx.receiver, 100.0, tx.data, tx.timestamp)

    print(f"篡改交易（金额改为100）后验证: {'通过' if signer.verify(tampered_tx, signature) else '失败'}")

    print()



    # 应用场景

    merkle_tree_use_cases()



    print()

    print("说明：")

    print("  - Merkle树提供高效的完整性验证")

    print("  - 只需O(log n)数据即可验证")

    print("  - 区块链中轻节点依赖此技术")

