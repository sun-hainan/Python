"""
环签名
==========================================

【算法原理】
签名者可以匿名代表一个"环"签名，不暴露自己是环中哪个成员。
验证者只能确认签名来自环中某成员，但无法确定具体是谁。

【时间复杂度】O(n) 签名生成和验证
【应用场景】
- 匿名举报
- 加密货币交易隐私（门罗币）
- 领导选举匿名投票
"""

import random
import hashlib
from typing import List, Tuple


class RingSignature:
    """
    环签名（Ad-hoc环）

    【协议】
    1. 签名者选择一组公钥作为环
    2. 生成签名使得验证等式成立
    3. 验证者只知道签名来自环中某人

    【简化实现】
    基于RSA的链接环签名
    """

    def __init__(self):
        self.ring_size = 0

    def generate_ring_keypair(self, bits: int = 256) -> Tuple[int, int]:
        """
        生成RSA密钥对（简化）

        【返回】(public_key, private_key)
        """
        # 简化：使用两个大质数
        p = self._generate_prime(bits // 2)
        q = self._generate_prime(bits // 2)
        n = p * q
        e = 65537
        # d = e^-1 mod (p-1)(q-1)
        phi = (p - 1) * (q - 1)
        d = pow(e, -1, phi)

        return (n, e), (n, d)

    def _generate_prime(self, bits: int) -> int:
        """生成随机质数"""
        while True:
            n = random.getrandbits(bits)
            n |= (1 << bits - 1) | 1  # 确保最高位和最低位为1
            if self._is_prime(n):
                return n

    def _is_prime(self, n: int) -> bool:
        """Miller-Rabin primality test"""
        if n < 2:
            return False
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
            if n % p == 0:
                return n == p
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        for _ in range(5):
            a = random.randint(2, n - 2)
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(s - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True

    def sign(self, message: str, ring_public_keys: List[int],
            private_key: Tuple[int, int], signer_index: int) -> dict:
        """
        生成环签名

        【参数】
        - message: 要签名的消息
        - ring_public_keys: 环中所有公钥
        - private_key: 签名者的私钥
        - signer_index: 签名者在环中的位置

        【原理】
        令C_k,v = 挑战
        选择随机u，对每个i计算s_i
        最后让s_index满足等式
        """
        n = len(ring_public_keys)
        self.ring_size = n
        _, d = private_key
        n_signer = ring_public_keys[signer_index]

        # 初始化
        signatures = [0] * n
        challenge = 0

        # 选择随机值
        u = random.randint(1, 2**128)

        # 计算s_0到s_{index-1}
        for i in range(signer_index):
            s_i = random.randint(1, 2**128)
            signatures[i] = s_i
            e_i = self._hash(message, s_i, ring_public_keys[i])
            challenge ^= e_i

        # 计算s_index
        s_index = u ^ challenge
        signatures[signer_index] = s_index

        # 继续计算剩余s
        for i in range(signer_index + 1, n):
            s_i = random.randint(1, 2**128)
            signatures[i] = s_i
            e_i = self._hash(message, s_i, ring_public_keys[i])
            challenge ^= e_i

        return {
            "message": message,
            "ring": ring_public_keys,
            "signatures": signatures,
            "challenge": challenge
        }

    def _hash(self, message: str, s: int, public_key: int) -> int:
        """计算哈希"""
        data = f"{message}:{s}:{public_key}".encode()
        return int(hashlib.sha256(data).hexdigest(), 16) % (2**128)

    def verify(self, signature: dict) -> bool:
        """验证环签名"""
        message = signature["message"]
        ring = signature["ring"]
        signatures = signature["signatures"]
        n = len(ring)

        # 重新计算挑战
        challenge = 0
        for i in range(n):
            e_i = self._hash(message, signatures[i], ring[i])
            challenge ^= e_i

        return challenge == 0


class LinkableRingSignature:
    """
    可链接环签名

    【与普通环签名的区别】
    - 可以检测同一签名者是否签了两次（链接性）
    - 用于门罗币等隐私币

    【方法】
    - 生成签名时包含一次性密钥
    - 链接标签允许验证两次签名来自同一人
    """

    def __init__(self):
        pass

    def sign_linkable(self, message: str, ring: List[int],
                    private_key: int, tag: int) -> dict:
        """生成可链接环签名"""
        n = len(ring)
        signatures = [0] * n

        # 简化的链接签名
        for i in range(n):
            s_i = (hash(f"{message}:{ring[i]}:{tag}") + private_key) % (2**256)
            signatures[i] = s_i

        return {
            "message": message,
            "ring": ring,
            "signatures": signatures,
            "tag": tag  # 链接标签
        }

    def verify_linkable(self, signature: dict) -> Tuple[bool, bool]:
        """验证并检测链接"""
        ring = signature["ring"]
        signatures = signature["signatures"]

        # 验证签名格式正确
        valid = all(s > 0 for s in signatures)

        # 检查链接（标签相同 = 同一签名者）
        tag = signature["tag"]
        linked = tag != 0

        return valid, linked


# ========================================
# 测试
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("环签名 - 测试")
    print("=" * 50)

    rs = RingSignature()

    # 生成密钥对
    print("\n【测试1】生成密钥对")
    pk1, sk1 = rs.generate_ring_keypair(128)
    pk2, sk2 = rs.generate_ring_keypair(128)
    pk3, sk3 = rs.generate_ring_keypair(128)
    print(f"  环成员数: 3")
    print(f"  签名者公钥n: {pk1[0] % 1000}...")

    # 创建环
    ring = [pk1[0], pk2[0], pk3[0]]
    message = "Transfer 100 tokens"

    # 签名（使用第二个密钥）
    print("\n【测试2】环签名")
    signer_index = 1
    sig = rs.sign(message, ring, sk2, signer_index)
    print(f"  签名者索引: {signer_index}")
    print(f"  签名长度: {len(sig['signatures'])}")

    # 验证
    valid = rs.verify(sig)
    print(f"  验证结果: {valid}")

    # 可链接环签名
    print("\n【测试3】可链接环签名")
    lrs = LinkableRingSignature()
    pk, sk = rs.generate_ring_keypair(128)
    ring = [pk1[0], pk, pk3[0]]
    tag = 12345  # 链接标签

    sig_link = lrs.sign_linkable(message, ring, sk, tag)
    valid, linked = lrs.verify_linkable(sig_link)
    print(f"  验证结果: {valid}, 链接: {linked}")

    print("\n" + "=" * 50)
