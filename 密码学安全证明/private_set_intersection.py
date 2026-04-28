"""
私密集合交集 (PSI)
==========================================

【原理】
两方各自持有集合，只有交集部分被泄露。
可用于隐私联系人发现、广告转化率等。

【时间复杂度】O(n log n) to O(n)
【应用场景】- 隐私联系人匹配
- 联邦学习样本对齐
- 医疗数据协同
"""

import random
import hashlib


class SimplePSI:
    """
    简单PSI（基于哈希）

    【安全性】低（哈希碰撞可攻击）
    """

    def __init__(self):
        pass

    def protocol(self, set_a: list, set_b: list) -> list:
        """求交集"""
        hash_a = {self._hash(x) for x in set_a}
        hash_b = {self._hash(x) for x in set_b}
        intersection = hash_a & hash_b
        return list(intersection)

    def _hash(self, x) -> str:
        return hashlib.sha256(str(x).encode()).hexdigest()


class DHPSI:
    """
    DH-PSI（Diffie-Hellman PSI）

    【协议】
    1. Alice: 对每个元素计算 g^a_i
    2. Bob: 对每个元素计算 (g^a_i)^b
    3. 双方排序后找相同元素

    【安全性】基于DDH假设
    """

    def __init__(self, prime: int = 2**255 - 19):
        self.p = prime
        self.g = 2

    def alice_side(self, set_a: list) -> list:
        """Alice：对每个元素做幂运算"""
        a = random.randint(2, self.p - 2)
        transformed = [pow(self.g, a * self._hash(x), self.p) for x in set_a]
        transformed.sort()
        return transformed, a

    def bob_side(self, set_b: list, alice_transformed: list, a: int) -> list:
        """Bob：做反向变换"""
        b = random.randint(2, self.p - 2)
        bob_transformed = [pow(self.g, b * self._hash(x), self.p) for x in set_b]
        bob_transformed.sort()

        # 找交集
        intersection = []
        for val in alice_transformed:
            if val in bob_transformed:
                intersection.append(val)
        return intersection

    def _hash(self, x: int) -> int:
        h = hashlib.sha256(str(x).encode()).hexdigest()
        return int(h, 16) % self.p


class OTPSI:
    """
    OT-PSI（Oblivious Transfer PSI）

    【使用】
    1. RSA打包（Oblivious Transfer）
    2. Bob选择随机秘钥
    3. Alice用OT发送加密索引

    【更高效但实现复杂】
    """


if __name__ == "__main__":
    print("=" * 50)
    print("PSI - 测试")
    print("=" * 50)

    # 简单PSI
    print("\n【测试1】简单PSI")
    psi = SimplePSI()
    set_a = [1, 2, 3, 4, 5]
    set_b = [4, 5, 6, 7, 8]
    result = psi.protocol(set_a, set_b)
    print(f"  A: {set_a}")
    print(f"  B: {set_b}")
    print(f"  交集: {result}")

    # DH-PSI
    print("\n【测试2】DH-PSI")
    dhpsi = DHPSI()
    set_a = [1, 2, 3, 4, 5]
    set_b = [4, 5, 6, 7, 8]

    alice_result, a = dhpsi.alice_side(set_a)
    bob_intersection = dhpsi.bob_side(set_b, alice_result, a)
    print(f"  A: {set_a}")
    print(f"  B: {set_b}")
    print(f"  Alice变换后: {len(alice_result)} elements")
    print(f"  交集大小: {len(bob_intersection)}")

    print("\n" + "=" * 50)
