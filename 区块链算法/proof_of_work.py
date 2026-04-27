# -*- coding: utf-8 -*-

"""

算法实现：区块链算法 / proof_of_work



本文件实现 proof_of_work 相关的算法功能。

"""



import hashlib

import random

from typing import Tuple





class ProofOfWork:

    """工作量证明"""



    def __init__(self, difficulty: int = 4):

        """

        参数：

            difficulty: 难度（前导0的数量）

        """

        self.difficulty = difficulty

        self.target = '0' * difficulty



    def compute_proof(self, data: str, start_nonce: int = 0) -> Tuple[int, str]:

        """

        计算证明



        参数：

            data: 区块数据

            start_nonce: 起始随机数



        返回：(随机数, 哈希)

        """

        nonce = start_nonce



        while True:

            # 创建候选哈希

            candidate = f"{data}{nonce}".encode()

            hash_result = hashlib.sha256(candidate).hexdigest()



            # 检查是否满足难度

            if hash_result[:self.difficulty] == self.target:

                return nonce, hash_result



            nonce += 1



            # 防止无限循环

            if nonce > 10000000:

                return -1, ""



    def verify_proof(self, data: str, nonce: int, hash_result: str) -> bool:

        """

        验证证明



        返回：是否有效

        """

        candidate = f"{data}{nonce}".encode()

        computed_hash = hashlib.sha256(candidate).hexdigest()



        return computed_hash == hash_result and hash_result[:self.difficulty] == self.target



    def estimate_difficulty(self, n_miners: int, block_time: float) -> int:

        """

        估计难度（根据目标出块时间）



        参数：

            n_miners: 矿工数量

            block_time: 目标出块时间（秒）



        返回：建议难度

        """

        # 简化：假设每个矿工每秒尝试 10^6 次

        total_hashes_per_second = n_miners * 1e6



        # 需要在 block_time 内找到

        needed_hashes = total_hashes_per_second * block_time



        # 计算难度（需要 2^difficulty 次尝试）

        # 2^difficulty ≈ needed_hashes

        import math

        difficulty = int(math.log2(needed_hashes))



        return max(1, min(difficulty, 20))  # 限制在1-20





def pow_optimizations():

    """PoW优化"""

    print("=== PoW优化 ===")

    print()

    print("问题：")

    print("  - 能源消耗大")

    print("  - 中心化风险")

    print()

    print("改进方案：")

    print("  - PoS（权益证明）")

    print("  - PoSpace（空间证明）")

    print("  - PoReputation（声誉证明）")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 工作量证明测试 ===\n")



    pow_system = ProofOfWork(difficulty=4)



    # 数据

    data = "Block data: transactions, hash of previous block, timestamp"



    print(f"数据: {data[:50]}...")

    print(f"难度: {pow_system.difficulty} (前{pow_system.difficulty}个0)")

    print()



    # 计算证明

    print("计算证明...")

    nonce, hash_result = pow_system.compute_proof(data)



    print(f"随机数: {nonce}")

    print(f"哈希: {hash_result}")

    print()



    # 验证

    is_valid = pow_system.verify_proof(data, nonce, hash_result)

    print(f"验证: {'✅ 有效' if is_valid else '❌ 无效'}")

    print()



    # 难度估计

    suggested_diff = pow_system.estimate_difficulty(n_miners=1000, block_time=600)

    print(f"建议难度 (1000矿工, 600秒出块): {suggested_diff}")



    print()

    pow_optimizations()



    print()

    print("说明：")

    print("  - 工作量证明是比特币的核心")

    print("  - 消耗大量能源但提供安全")

    print("  - 新的区块链倾向于PoS等替代方案")

