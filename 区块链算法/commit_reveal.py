# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / commit_reveal

本文件实现 commit_reveal 相关的算法功能。
"""

import hashlib
import random


class Commitment:
    """承诺"""

    def __init__(self, value: str, nonce: str = None):
        """
        创建承诺

        参数：
            value: 要承诺的值
            nonce: 随机数（防止暴力破解）
        """
        self.value = value
        self.nonce = nonce or self._generate_nonce()
        self.commitment_hash = self._hash(value, self.nonce)

    def _generate_nonce(self) -> str:
        """生成随机nonce"""
        return hex(random.randint(0, 2**256))[2:]

    def _hash(self, value: str, nonce: str) -> str:
        """计算承诺哈希"""
        combined = value + nonce
        return hashlib.sha256(combined.encode()).hexdigest()

    def reveal(self) -> Tuple[str, str]:
        """
        公开承诺的值和nonce

        返回：(value, nonce)
        """
        return self.value, self.nonce

    def verify(self, value: str, nonce: str) -> bool:
        """验证承诺是否匹配"""
        return self.commitment_hash == self._hash(value, nonce)


class PedersenCommitment:
    """Pedersen承诺（同态承诺）"""

    def __init__(self, g, h, p):
        """
        参数：
            g, h: 生成元
            p: 大素数
        """
        self.g = g
        self.h = h
        self.p = p

    def commit(self, value: int, r: int) -> int:
        """
        创建承诺

        commit = g^value * h^r mod p

        参数：
            value: 要承诺的值
            r: 随机盲因子

        返回：承诺值
        """
        # 简化：使用 pow(base, exp, mod)
        g_v = pow(self.g, value, self.p)
        h_r = pow(self.h, r, self.p)
        return (g_v * h_r) % self.p

    def verify(self, commitment: int, value: int, r: int) -> bool:
        """验证承诺"""
        expected = self.commit(value, r)
        return commitment == expected


def commit_reveal_protocol():
    """
    Commit-Reveal协议示例
    """
    print("=== Commit-Reveal 协议 ===\n")

    # 场景：两个人决定谁付账
    players = ["Alice", "Bob"]

    print("场景：抛硬币决定谁付账")
    print()

    # Phase 1: Commit
    print("Phase 1: 承诺阶段")
    choices = {}
    commitments = {}

    for player in players:
        choice = random.choice(["正面", "反面"])
        nonce = hex(random.randint(0, 2**128))[2:]
        choices[player] = (choice, nonce)

        c = Commitment(choice, nonce)
        commitments[player] = c.commitment_hash
        print(f"  {player}: 承诺={c.commitment_hash[:20]}...")

    print()

    # Phase 2: Reveal
    print("Phase 2: 公开阶段")
    revealed = {}

    for player in players:
        value, nonce = choices[player]
        revealed[player] = value

        # 验证
        c = Commitment(value, nonce)
        is_valid = c.verify(value, nonce)
        print(f"  {player}: 公开={value}, 验证={'✅' if is_valid else '❌'}")

    print()

    # Phase 3: 结果
    result = revealed["Alice"] == revealed["Bob"]
    reveal_msg = f"{revealed['Alice']} vs {revealed['Bob']}"
    print(f"结果: {'平局' if result else reveal_msg}")


def mental_poker():
    """
    心理扑克示例

    演示如何在没有可信第三方的线上游戏中发牌
    """
    print()
    print("=== 心理扑克 ===")

    print("""
    问题：如何在没有发牌员的情况下公平发牌？

    Commit-Reveal方案：
    1. Alice随机洗牌并承诺每张牌
    2. Bob随机选择一张（用随机数混淆）
    3. Alice公开她选择的那张牌
    4. Bob可以验证

    重复直到所有人都拿到牌
    """)


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    import random
    random.seed(42)

    commit_reveal_protocol()
    mental_poker()

    print("\n说明：")
    print("  - Commit阶段：承诺值但不能改")
    print("  - Reveal阶段：公开并验证")
    print("  - 应用：投票、随机数、在线游戏")
