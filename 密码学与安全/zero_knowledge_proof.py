# -*- coding: utf-8 -*-
"""
算法实现：密码学与安全 / zero_knowledge_proof

本文件实现 zero_knowledge_proof 相关的算法功能。
"""

import hashlib
import random
from typing import Tuple, List


class SchnorrProtocol:
    """Schnorr零知识证明协议"""

    def __init__(self, p: int, g: int, q: int):
        """
        初始化Schnorr协议

        参数：
            p: 大素数（模数）
            g: 生成元
            q: 群的阶
        """
        self.p = p
        self.g = g
        self.q = q

    def generate_keypair(self) -> Tuple[int, int]:
        """
        生成密钥对

        返回：(私钥x, 公钥y = g^x mod p)
        """
        x = random.randint(2, self.q - 1)  # 私钥
        y = pow(self.g, x, self.p)        # 公钥
        return x, y

    def prove(self, secret_x: int, public_y: int) -> Tuple[int, int, int]:
        """
        证明者生成证明

        参数：
            secret_x: 私钥
            public_y: 公钥

        返回：(随机数r, 挑战c, 响应s)
        """
        # 1. 承诺阶段：随机选择v，计算t = g^v mod p
        v = random.randint(2, self.q - 1)
        t = pow(self.g, v, self.p)

        # 2. 挑战阶段：验证者发送随机挑战c
        # 这里简化：使用哈希生成确定性挑战
        c = self._compute_challenge(t, public_y)

        # 3. 响应阶段：s = v - c * x mod q
        s = (v - c * secret_x) % self.q

        return v, c, s

    def _compute_challenge(self, commitment: int, public_key: int) -> int:
        """
        计算挑战（通常由验证者随机选择）

        参数：
            commitment: 承诺值t
            public_key: 公钥

        返回：挑战值
        """
        # 简化：使用哈希模拟随机挑战
        h = hashlib.sha256(
            str(commitment).encode() + str(public_key).encode()
        ).hexdigest()
        return int(h, 16) % self.q

    def verify(self, public_y: int, c: int, s: int) -> bool:
        """
        验证者验证证明

        参数：
            public_y: 公钥
            c: 挑战
            s: 响应

        返回：验证结果
        """
        # 重新计算 t' = g^s * y^c mod p
        t_prime = (pow(self.g, s, self.p) * pow(public_y, c, self.p)) % self.p

        # 验证 c = H(t' || y)
        expected_c = self._compute_challenge(t_prime, public_y)

        return c == expected_c


class SimpleZKSNARK:
    """简化的zk-SNARK（用于理解原理）"""

    def __init__(self):
        """初始化zk-SNARK参数"""
        # 简化参数
        self.g1 = 2   # 生成元（实际是椭圆曲线点）
        self.g2 = 3
        self.p = 23  # 素数域

    def setup(self) -> Tuple[int, int]:
        """
        可信设置（简化）

        返回：(proving_key, verification_key)
        """
        # 随机有毒废物（trusted setup）
        toxic_x = random.randint(2, self.p - 1)

        proving_key = pow(self.g1, toxic_x, self.p)
        verification_key = pow(self.g2, toxic_x, self.p)

        return proving_key, verification_key

    def prove_knowledge(self, secret: int, proving_key: int) -> Tuple[int, int]:
        """
        证明知道某个数的知识

        参数：
            secret: 秘密值
            proving_key: 证明密钥

        返回：(承诺, 响应)
        """
        # 简化的证明
        r = random.randint(2, self.p - 1)  # 随机数

        commitment = pow(self.g1, r, self.p)
        response = (r + secret * proving_key) % (self.p - 1)

        return commitment, response

    def verify(self, commitment: int, response: int, verification_key: int) -> bool:
        """
        验证证明

        参数：
            commitment: 承诺
            response: 响应
            verification_key: 验证密钥

        返回：验证结果
        """
        # g1^response ?= commitment * verification_key^commitment
        left = pow(self.g1, response, self.p)
        right = (commitment * pow(verification_key, commitment, self.p)) % self.p

        return left == right


class CommitmentScheme:
    """承诺方案（Pedersen Commitment）"""

    def __init__(self, p: int, g: int, h: int):
        """
        初始化承诺方案

        参数：
            p: 素数
            g, h: 生成元（椭圆曲线点）
        """
        self.p = p
        self.g = g
        self.h = h

    def commit(self, value: int, randomness: int) -> int:
        """
        创建承诺

        参数：
            value: 要承诺的值
            randomness: 随机盲因子

        返回：承诺 C = g^value * h^randomness mod p
        """
        return (pow(self.g, value, self.p) * pow(self.h, randomness, self.p)) % self.p

    def open(self, value: int, randomness: int, commitment: int) -> bool:
        """
        打开承诺验证

        参数：
            value: 原值
            randomness: 随机盲因子
            commitment: 承诺

        返回：是否匹配
        """
        expected = self.commit(value, randomness)
        return commitment == expected


def zk_proof_applications():
    """零知识证明应用"""
    print("=== 零知识证明应用 ===")
    print()
    print("1. 区块链隐私")
    print("   - Zcash：完全隐私交易")
    print("   - 以太坊：zkEVM")
    print()
    print("2. 身份认证")
    print("   - 证明年龄而不泄露生日")
    print("   - 证明信用分而不泄露分数")
    print()
    print("3. 可验证计算")
    print("   - 外包计算结果可验证")
    print("   - 区块链 Layer 2 扩容")
    print()
    print("4. 访问控制")
    print("   - 证明有权限而不暴露权限细节")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 零知识证明测试 ===\n")

    # Schnorr协议测试
    print("Schnorr协议测试：")
    # 使用小素数便于演示
    p = 23  # 素数
    g = 5   # 生成元（满足g是原根）
    q = 11  # 群的阶

    schnorr = SchnorrProtocol(p, g, q)

    # 生成密钥对
    x, y = schnorr.generate_keypair()

    print(f"  素数p: {p}")
    print(f"  生成元g: {g}")
    print(f"  私钥x: {x}")
    print(f"  公钥y: {y}")
    print()

    # 证明
    v, c, s = schnorr.prove(x, y)

    print(f"  承诺v: {v}")
    print(f"  挑战c: {c}")
    print(f"  响应s: {s}")
    print()

    # 验证
    valid = schnorr.verify(y, c, s)
    print(f"  验证结果: {'通过' if valid else '失败'}")
    print()

    # 错误私钥测试
    print("欺骗检测测试：")
    wrong_x = (x + 1) % q
    v2, c2, s2 = schnorr.prove(wrong_x, y)
    valid2 = schnorr.verify(y, c2, s2)
    print(f"  用错误私钥的验证: {'通过' if valid2 else '失败（预期）'}")
    print()

    # Pedersen承诺测试
    print("Pedersen承诺测试：")
    pedersen = CommitmentScheme(p=23, g=2, h=3)

    secret_value = 7
    blinding = 5

    commitment = pedersen.commit(secret_value, blinding)

    print(f"  秘密值: {secret_value}")
    print(f"  盲因子: {blinding}")
    print(f"  承诺: {commitment}")
    print()

    # 打开承诺
    opened = pedersen.open(secret_value, blinding, commitment)
    print(f"  承诺打开验证: {'通过' if opened else '失败'}")

    # 错误打开
    wrong_open = pedersen.open(secret_value + 1, blinding, commitment)
    print(f"  错误值打开验证: {'通过' if wrong_open else '失败（预期）'}")
    print()

    # 应用场景
    zk_proof_applications()

    print()
    print("说明：")
    print("  - 零知识证明保护隐私的同时提供验证")
    print("  - Schnorr协议是零知识证明的基础")
    print("  - zk-SNARK是更复杂的零知识证明系统")
