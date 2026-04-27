# -*- coding: utf-8 -*-

"""

算法实现：区块链算法 / spv_proof



本文件实现 spv_proof 相关的算法功能。

"""



import hashlib

from typing import List, Tuple



class MerkleNode:

    """默克尔树节点"""

    def __init__(self, left=None, right=None, value: str = ""):

        self.left = left

        self.right = right

        self.value = value



class SimpleBlock:

    """简化区块"""

    def __init__(self, transactions: List[str]):

        self.transactions = transactions

        self.merkle_root = ""

        if transactions:

            self.merkle_root = self.build_merkle_tree(transactions)



def compute_hash(data: str) -> str:

    """计算双SHA256哈希"""

    return hashlib.sha256(hashlib.sha256(data.encode()).hexdigest().encode()).hexdigest()



def build_merkle_tree(transactions: List[str]) -> str:

    """构建默克尔树，返回根哈希"""

    if not transactions:

        return ""

    

    # 如果交易数为奇数，复制最后一个

    if len(transactions) % 2 == 1:

        transactions.append(transactions[-1])

    

    # 计算第一层哈希

    current_level = [compute_hash(t) for t in transactions]

    

    # 逐层向上计算

    while len(current_level) > 1:

        next_level = []

        for i in range(0, len(current_level), 2):

            combined = current_level[i] + current_level[i + 1]

            next_level.append(compute_hash(combined))

        current_level = next_level

    

    return current_level[0] if current_level else ""



def create_merkle_proof(transactions: List[str], target_index: int) -> Tuple[str, List[str]]:

    """

    创建SPV证明（默克尔证明）

    

    Args:

        transactions: 交易列表

        target_index: 目标交易的索引

    

    Returns:

        (目标交易哈希, 路径哈希列表)

    """

    if target_index >= len(transactions):

        return "", []

    

    # 计算所有层的哈希

    level = [compute_hash(t) for t in transactions]

    proof_path = []

    

    # 记录每层的配对信息

    is_left = []

    

    while len(level) > 1:

        if len(level) % 2 == 1:

            level.append(level[-1])

        

        next_level = []

        for i in range(0, len(level), 2):

            combined = level[i] + level[i + 1]

            next_level.append(compute_hash(combined))

            

            if i // 2 == target_index // 2:

                # 记录路径

                if i == target_index:

                    proof_path.append(level[i + 1])

                    is_left.append(True)

                else:

                    proof_path.append(level[i])

                    is_left.append(False)

        

        level = next_level

        target_index = target_index // 2

    

    return compute_hash(transactions[target_index * (2 ** len(proof_path))]), proof_path



def verify_merkle_proof(target_hash: str, proof_path: List[str], merkle_root: str) -> bool:

    """

    验证SPV证明

    

    Args:

        target_hash: 目标交易哈希

        proof_path: 证明路径

        merkle_root: 默克尔根

    

    Returns:

        是否验证通过

    """

    current_hash = target_hash

    

    for sibling_hash in proof_path:

        combined = current_hash + sibling_hash

        current_hash = compute_hash(combined)

    

    return current_hash == merkle_root



if __name__ == "__main__":

    print("=== SPV证明测试 ===")

    

    transactions = [

        "tx1: Alice -> Bob 10 BTC",

        "tx2: Bob -> Charlie 5 BTC",

        "tx3: Charlie -> Dave 3 BTC",

        "tx4: Dave -> Eve 2 BTC",

    ]

    

    # 创建默克尔根

    merkle_root = build_merkle_tree(transactions)

    print(f"交易列表: {transactions}")

    print(f"默克尔根: {merkle_root}")

    

    # 为每个交易创建证明

    print("\n=== 默克尔证明 ===")

    for i in range(len(transactions)):

        target_hash, proof = create_merkle_proof(transactions, i)

        print(f"交易{i+1}:")

        print(f"  哈希: {target_hash}")

        print(f"  证明路径: {[h[:16] + '...' for h in proof]}")

        

        # 验证

        is_valid = verify_merkle_proof(target_hash, proof, merkle_root)

        print(f"  验证结果: {'通过' if is_valid else '失败'}")

    

    print("\n=== 验证不存在的交易 ===")

    # 尝试用错误的哈希验证

    fake_hash = "0" * 64

    is_valid = verify_merkle_proof(fake_hash, proof, merkle_root)

    print(f"假哈希验证: {'通过' if is_valid else '失败'} (应为失败)")

