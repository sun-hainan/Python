# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / pow_mining

本文件实现 pow_mining 相关的算法功能。
"""

import hashlib
import time
from typing import Tuple

class Block:
    """区块"""
    def __init__(self, index: int, prev_hash: str, data: str, difficulty: int):
        self.index = index
        self.prev_hash = prev_hash
        self.data = data
        self.timestamp = time.time()
        self.difficulty = difficulty
        self.nonce = 0
        self.hash = ""
    
    def compute_hash(self) -> str:
        """计算区块哈希"""
        content = f"{self.index}{self.prev_hash}{self.data}{self.timestamp}{self.nonce}"
        return hashlib.sha256(content.encode()).hexdigest()

def mine_block(block: Block, max_attempts: int = 1000000) -> Tuple[str, int, bool]:
    """
    PoW挖矿 - 寻找满足难度的nonce
    
    Args:
        block: 待挖矿的区块
        max_attempts: 最大尝试次数
    
    Returns:
        (有效哈希, nonce, 是否成功)
    """
    target = "0" * block.difficulty
    start_time = time.time()
    
    while block.nonce < max_attempts:
        block.hash = block.compute_hash()
        
        if block.hash.startswith(target):
            elapsed = time.time() - start_time
            print(f"挖矿成功! nonce={block.nonce}, hash={block.hash[:16]}..., 耗时={elapsed:.2f}s")
            return block.hash, block.nonce, True
        
        block.nonce += 1
        
        if block.nonce % 100000 == 0:
            print(f"  已尝试nonce={block.nonce}, 当前hash={block.hash[:16]}...")
    
    return "", 0, False

if __name__ == "__main__":
    print("=== PoW挖矿测试 ===")
    
    block = Block(
        index=0,
        prev_hash="0" * 64,
        data="Hello, Blockchain!",
        difficulty=4
    )
    
    print(f"区块信息: index={block.index}, data={block.data}")
    print(f"难度: {block.difficulty} 个前导0")
    
    valid_hash, nonce, success = mine_block(block, max_attempts=5000000)
    
    if success:
        print(f"\n挖矿结果:")
        print(f"  区块哈希: {valid_hash}")
        print(f"  Nonce: {nonce}")
        print(f"  验证: {valid_hash.startswith('0' * block.difficulty)}")
    
    print("\n=== 难度影响 ===")
    for diff in [2, 3, 4]:
        block = Block(0, "0" * 64, "test", diff)
        target = "0" * diff
        
        start = time.time()
        attempts = 0
        while attempts < 1000000:
            block.hash = block.compute_hash()
            if block.hash.startswith(target):
                break
            block.nonce += 1
            attempts += 1
        
        elapsed = time.time() - start
        print(f"难度{diff}个0: nonce={block.nonce}, 耗时={elapsed:.3f}s")
