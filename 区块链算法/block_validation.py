# -*- coding: utf-8 -*-

"""

算法实现：区块链算法 / block_validation



本文件实现 block_validation 相关的算法功能。

"""



import hashlib

import time

from typing import List, Tuple, Optional

from dataclasses import dataclass



@dataclass

class BlockHeader:

    """区块头"""

    version: int

    prev_block_hash: str

    merkle_root: str

    timestamp: int

    bits: int  # 难度目标

    nonce: int



@dataclass

class Block:

    """区块"""

    header: BlockHeader

    transactions: List[dict]



class BlockValidator:

    """

    区块验证

    

    验证:

    1. 工作量证明（难度目标）

    2. 默克尔根正确性

    3. 时间戳有效性

    4. 交易有效性

    """

    

    def __init__(self):

        self.target_block_time = 600  # 10分钟

    

    def calculate_target_from_bits(self, bits: int) -> int:

        """从bits计算难度目标"""

        exponent = bits >> 24

        coefficient = bits & 0x007FFFFF

        

        if bits & 0x00800000:

            coefficient |= 0x00800000

        

        target = coefficient * (2 ** (8 * (exponent - 3)))

        return target

    

    def verify_proof_of_work(self, block_hash: str, bits: int) -> bool:

        """

        验证工作量证明

        

        hash <= target

        """

        target = self.calculate_target_from_bits(bits)

        hash_int = int(block_hash, 16)

        return hash_int <= target

    

    def verify_merkle_root(self, transactions: List[dict], merkle_root: str) -> bool:

        """验证默克尔根"""

        if not transactions:

            return merkle_root == "0" * 64

        

        # 计算所有交易的哈希

        tx_hashes = []

        for tx in transactions:

            tx_id = tx.get('tx_id', hashlib.sha256(str(tx).encode()).hexdigest())

            tx_hashes.append(tx_id)

        

        # 构建默克尔树

        current_level = tx_hashes

        

        while len(current_level) > 1:

            if len(current_level) % 2 == 1:

                current_level.append(current_level[-1])

            

            next_level = []

            for i in range(0, len(current_level), 2):

                combined = current_level[i] + current_level[i + 1]

                next_level.append(hashlib.sha256(combined.encode()).hexdigest())

            

            current_level = next_level

        

        calculated_merkle = current_level[0] if current_level else "0" * 64

        return calculated_merkle == merkle_root

    

    def verify_timestamp(self, timestamp: int, prev_timestamp: int) -> bool:

        """

        验证时间戳

        

        时间戳必须:

        1. 大于前11个区块的中位数时间

        2. 小于网络时间 + 2小时

        """

        # 简化验证

        if timestamp < prev_timestamp:

            return False

        

        max_future = int(time.time()) + 7200  # 2小时

        if timestamp > max_future:

            return False

        

        return True

    

    def verify_block_size(self, transactions: List[dict], max_size: int = 1000000) -> bool:

        """验证区块大小"""

        import sys

        size = sys.getsizeof(str(transactions))

        return size <= max_size

    

    def validate_block(self, block: Block, prev_block_hash: str, prev_timestamp: int) -> Tuple[bool, List[str]]:

        """

        完整区块验证

        

        Returns:

            (是否有效, 错误列表)

        """

        errors = []

        header = block.header

        

        # 1. 验证前一个区块哈希

        if header.prev_block_hash != prev_block_hash:

            errors.append("前一个区块哈希不匹配")

        

        # 2. 验证工作量证明

        block_hash = self.compute_block_hash(header)

        if not self.verify_proof_of_work(block_hash, header.bits):

            errors.append("工作量证明无效")

        

        # 3. 验证默克尔根

        if not self.verify_merkle_root(block.transactions, header.merkle_root):

            errors.append("默克尔根无效")

        

        # 4. 验证时间戳

        if not self.verify_timestamp(header.timestamp, prev_timestamp):

            errors.append("时间戳无效")

        

        # 5. 验证区块大小

        if not self.verify_block_size(block.transactions):

            errors.append("区块过大")

        

        return (len(errors) == 0, errors)

    

    def compute_block_hash(self, header: BlockHeader) -> str:

        """计算区块哈希"""

        content = f"{header.version}{header.prev_block_hash}{header.merkle_root}"

        content += f"{header.timestamp}{header.bits}{header.nonce}"

        return hashlib.sha256(content.encode()).hexdigest()



if __name__ == "__main__":

    print("=== 区块验证测试 ===")

    

    validator = BlockValidator()

    

    # 创建测试区块

    header = BlockHeader(

        version=1,

        prev_block_hash="0" * 64,

        merkle_root="abc123",

        timestamp=int(time.time()),

        bits=0x1d00ffff,  # 比特币难度目标

        nonce=0

    )

    

    block = Block(header=header, transactions=[

        {"tx_id": "tx1", "sender": "alice", "receiver": "bob", "amount": 100},

        {"tx_id": "tx2", "sender": "bob", "receiver": "charlie", "amount": 50},

    ])

    

    print(f"区块头: version={header.version}, bits=0x{header.bits:08X}")

    print(f"难度目标: {validator.calculate_target_from_bits(header.bits)}")

    

    # 验证区块

    is_valid, errors = validator.validate_block(block, "0" * 64, int(time.time()) - 600)

    print(f"\n验证结果: {'有效' if is_valid else '无效'}")

    if errors:

        print(f"错误: {errors}")

    

    # 模拟恶意区块

    print("\n=== 恶意区块测试 ===")

    malicious_header = BlockHeader(

        version=1,

        prev_block_hash="deadbeef" * 8,  # 错误的前一个哈希

        merkle_root="abc123",

        timestamp=int(time.time()),

        bits=0x1d00ffff,

        nonce=0

    )

    

    malicious_block = Block(header=malicious_header, transactions=[])

    is_valid, errors = validator.validate_block(malicious_block, "0" * 64, int(time.time()) - 600)

    print(f"恶意区块验证: {'有效' if is_valid else '无效'}")

    print(f"错误: {errors}")

    

    # 难度目标转换

    print("\n=== 难度目标转换 ===")

    for bits in [0x1d00ffff, 0x1d3fffff, 0x1effffff]:

        target = validator.calculate_target_from_bits(bits)

        print(f"Bits: 0x{bits:08X} -> Target: {target}")

        print(f"  目标哈希前4字节: 0x{(target >> 224):08X}")

