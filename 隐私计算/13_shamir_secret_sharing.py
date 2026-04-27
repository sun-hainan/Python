# -*- coding: utf-8 -*-
"""
算法实现：隐私计算 / 13_shamir_secret_sharing

本文件实现 13_shamir_secret_sharing 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional


class ShamirSecretSharing:
    """
    Shamir秘密共享

    实现(t, n)阈值秘密分享
    """

    def __init__(self, prime: int = None, threshold: int = None, num_shares: int = None):
        """
        初始化Shamir秘密共享

        Args:
            prime: 大素数,定义有限域GF(prime)
            threshold: 阈值t
            num_shares: 分享份数n
        """
        # 默认使用大素数
        if prime is None:
            # 2^61 - 1 (Mersenne素数,运算高效)
            self.prime = (1 << 61) - 1
        else:
            self.prime = prime

        self.threshold = threshold
        self.num_shares = num_shares

    def _generate_polynomial(self, secret: int, degree: int) -> np.ndarray:
        """
        生成随机多项式

        多项式形式: f(x) = secret + a_1*x + a_2*x^2 + ... + a_{t-1}*x^{t-1}

        Args:
            secret: 秘密值
            degree: 多项式度数(t-1)

        Returns:
            系数数组 [secret, a_1, a_2, ..., a_{t-1}]
        """
        np.random.seed(42)
        coeffs = [secret] + [np.random.randint(1, self.prime) for _ in range(degree)]
        return np.array(coeffs)

    def _evaluate_polynomial(self, coeffs: np.ndarray, x: int) -> int:
        """
        在点x处求值多项式

        使用Horner法则高效计算

        Args:
            coeffs: 多项式系数
            x: 求值点

        Returns:
            f(x) mod prime
        """
        result = 0
        for coeff in reversed(coeffs):
            result = (result * x + coeff) % self.prime
        return result

    def share(self, secret: int, threshold: int = None, num_shares: int = None) -> List[Tuple[int, int]]:
        """
        将秘密分享成n份

        Args:
            secret: 要分享的秘密
            threshold: 阈值t
            num_shares: 总份数n

        Returns:
            份额列表 [(x_1, y_1), (x_2, y_2), ..., (x_n, y_n)]
        """
        if threshold is None:
            threshold = self.threshold
        if num_shares is None:
            num_shares = self.num_shares

        if threshold is None or num_shares is None:
            raise ValueError("必须提供threshold和num_shares")

        # 生成t-1次多项式
        degree = threshold - 1
        coeffs = self._generate_polynomial(secret % self.prime, degree)

        # 在x=1,2,...,n处求值
        shares = []
        for x in range(1, num_shares + 1):
            y = self._evaluate_polynomial(coeffs, x)
            shares.append((x, y))

        return shares

    def _lagrange_interpolate(self, points: List[Tuple[int, int]], x_target: int = 0) -> int:
        """
        拉格朗日插值

        在点x_target处求值由点确定的唯一多项式

        公式: f(x) = sum_{i} f(x_i) * l_i(x)
        其中 l_i(x) = product_{j!=i} (x - x_j) / (x_i - x_j)

        Args:
            points: 已知点列表 [(x_1, y_1), ..., (x_k, y_k)]
            x_target: 目标点(通常为0)

        Returns:
            f(x_target)
        """
        if len(points) < 2:
            return points[0][1] if points else 0

        # 计算拉格朗日基多项式在x_target处的值
        result = 0

        for i, (x_i, y_i) in enumerate(points):
            # 计算l_i(x_target)
            numerator = 1
            denominator = 1

            for j, (x_j, y_j) in enumerate(points):
                if i != j:
                    numerator = (numerator * (x_target - x_j)) % self.prime
                    denominator = (denominator * (x_i - x_j)) % self.prime

            # 模逆元
            denominator_inv = pow(denominator, -1, self.prime)

            # 累加
            l_i = (numerator * denominator_inv) % self.prime
            result = (result + y_i * l_i) % self.prime

        return result

    def reconstruct(self, shares: List[Tuple[int, int]]) -> int:
        """
        从份额重建秘密

        Args:
            shares: 至少t个份额 [(x_1, y_1), ..., (x_t, y_t)]

        Returns:
            秘密值
        """
        if len(shares) < 2:
            raise ValueError(f"需要至少2个份额,只有{len(shares)}个")

        # 使用拉格朗日插值求f(0)
        return self._lagrange_interpolate(shares, 0)

    def reconstruct_with_lagrange(self, shares: List[Tuple[int, int]]) -> Tuple[int, Dict]:
        """
        使用拉格朗日系数重构秘密

        同时返回拉格朗日系数(可用于加权秘密分享)

        Args:
            shares: 份额列表

        Returns:
            (秘密值, 拉格朗日系数字典)
        """
        x_values = [s[0] for s in shares]
        y_values = [s[1] for s in shares]

        # 计算每个份额的拉格朗日系数
        lagrange_coeffs = {}

        for i, x_i in enumerate(x_values):
            numerator = 1
            denominator = 1

            for j, x_j in enumerate(x_values):
                if i != j:
                    numerator = (numerator * (0 - x_j)) % self.prime
                    denominator = (denominator * (x_i - x_j)) % self.prime

            denominator_inv = pow(denominator, -1, self.prime)
            lagrange_coeffs[x_i] = (numerator * denominator_inv) % self.prime

        # 重建秘密
        secret = sum(y * lagrange_coeffs[x] for x, y in zip(x_values, y_values)) % self.prime

        return secret, lagrange_coeffs


class AdditiveSecretSharing:
    """
    加法秘密共享

    最简单的秘密共享: secret = s1 + s2 + ... + sn

    特点:
    - 只需所有n份才能恢复
    - 无法实现(t, n)阈值
    """

    def __init__(self, prime: int = None):
        """初始化加法秘密共享"""
        if prime is None:
            self.prime = (1 << 61) - 1
        else:
            self.prime = prime

    def share(self, secret: int, num_shares: int = 2) -> List[int]:
        """
        加法分享

        生成n-1个随机份额,最后一个份额 = secret - sum(其他份额)

        Args:
            secret: 秘密
            num_shares: 份额数量

        Returns:
            份额列表
        """
        np.random.seed(42)
        shares = []

        # 生成n-1个随机份额
        for _ in range(num_shares - 1):
            share = np.random.randint(0, self.prime)
            shares.append(share)

        # 最后一个份额使得总和等于秘密
        sum_shares = sum(shares) % self.prime
        last_share = (secret - sum_shares) % self.prime
        shares.append(last_share)

        return shares

    def reconstruct(self, shares: List[int]) -> int:
        """
        重建秘密

        Args:
            shares: 所有份额

        Returns:
            秘密
        """
        return sum(shares) % self.prime


class VerifiableSecretSharing:
    """
    可验证秘密共享(VSS)

    允许参与者验证份额的正确性

    使用Pedersen承诺:
    - g^secret * h^random
    - 证明份额与承诺一致
    """

    def __init__(self, prime: int = None):
        """初始化VSS"""
        if prime is None:
            self.prime = (1 << 61) - 1
        else:
            self.prime = prime

        np.random.seed(42)
        # 生成承诺参数
        self.g = 5
        self.h = 7

    def _commit(self, value: int, randomness: int) -> int:
        """
        生成承诺

        Args:
            value: 要承诺的值
            randomness: 随机数

        Returns:
            承诺
        """
        return (pow(self.g, value, self.prime) *
                pow(self.h, randomness, self.prime)) % self.prime

    def share_with_commitments(
        self,
        secret: int,
        threshold: int = 3,
        num_shares: int = 5
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        带承诺的秘密分享

        Args:
            secret: 秘密
            threshold: 阈值t
            num_shares: 份额数n

        Returns:
            (份额列表, 承诺列表, 随机数列表)
        """
        # 生成多项式
        shamir = ShamirSecretSharing(self.prime, threshold, num_shares)
        shares = shamir.share(secret, threshold, num_shares)

        # 为每个份额生成承诺
        np.random.seed(123)
        randomness = [np.random.randint(1, self.prime) for _ in range(len(shares))]
        commitments = [self._commit(share[1], randomness[i])
                       for i, share in enumerate(shares)]

        return shares, commitments, randomness

    def verify_share(
        self,
        share: Tuple[int, int],
        commitment: int,
        randomness: int
    ) -> bool:
        """
        验证份额正确性

        Args:
            share: (x, y)
            commitment: 承诺
            randomness: 随机数

        Returns:
            是否正确
        """
        _, y = share
        expected_commitment = self._commit(y, randomness)
        return commitment == expected_commitment


class SecretSharingDemo:
    """
    秘密分享演示器
    """

    def __init__(self):
        """初始化演示器"""
        self.shamir = ShamirSecretSharing()
        self.additive = AdditiveSecretSharing()
        self.vss = VerifiableSecretSharing()

    def demo_basic_shamir(self):
        """演示基本的Shamir秘密共享"""
        print("1. Shamir秘密共享 (3-out-of-5)")

        secret = 42
        print(f"   原始秘密: {secret}")

        # 分享
        shares = self.shamir.share(secret, threshold=3, num_shares=5)
        print(f"   生成5个份额:")
        for i, (x, y) in enumerate(shares):
            print(f"     份额{x}: {y}")

        # 用3个份额恢复(任意3个都可以)
        print("\n   用前3个份额恢复:")
        recovered = self.shamir.reconstruct(shares[:3])
        print(f"     恢复结果: {recovered}")

        print("\n   用不同的3个份额(2,4,5)恢复:")
        selected_shares = [shares[1], shares[3], shares[4]]  # x=2,4,5
        recovered = self.shamir.reconstruct(selected_shares)
        print(f"     恢复结果: {recovered}")

        # 演示份额不够无法恢复
        print("\n   尝试用2个份额恢复(应该失败):")
        try:
            recovered = self.shamir.reconstruct(shares[:2])
            print(f"     恢复结果: {recovered} (这不应该发生)")
        except Exception as e:
            print(f"     错误: {e}")

    def demo_lagrange_weights(self):
        """演示拉格朗日权重"""
        print("\n2. 拉格朗日权重计算")

        # 假设有5个参与者,阈值t=3
        # 不同份额组合恢复秘密时的权重不同
        points = [(1, 0), (2, 0), (3, 0)]  # 假设的份额

        # 创建测试秘密
        secret = 12345
        shares = self.shamir.share(secret, threshold=3, num_shares=5)

        print(f"   秘密: {secret}")
        print(f"   份额:")
        for x, y in shares:
            print(f"     x={x}: y={y}")

        # 计算不同组合的拉格朗日系数
        for combo_size in [3, 4, 5]:
            print(f"\n   用{combo_size}个份额恢复:")
            selected = shares[:combo_size]
            _, coeffs = self.shamir.reconstruct_with_lagrange(selected)
            print(f"   拉格朗日系数:")
            for x, y in selected:
                print(f"     份额{x}: λ_{x} = {coeffs[x]}")
            print(f"   验证: sum(λ_i * y_i) mod p = {sum(coeffs[s[0]] * s[1] for s in selected) % self.shamir.prime}")

    def demo_additive_vs_shamir(self):
        """对比加法秘密共享和Shamir"""
        print("\n3. 加法秘密共享 vs Shamir秘密共享")

        secret = 100

        # 加法分享
        print(f"   秘密: {secret}")
        print("\n   加法秘密共享 (2-out-of-2):")
        additive_shares = self.additive.share(secret, num_shares=2)
        for i, share in enumerate(additive_shares):
            print(f"     份额{i+1}: {share}")
        recovered = self.additive.reconstruct(additive_shares)
        print(f"   恢复: {recovered}")

        # Shamir分享
        print("\n   Shamir秘密共享 (2-out-of-3):")
        shamir_shares = self.shamir.share(secret, threshold=2, num_shares=3)
        for x, y in shamir_shares:
            print(f"     份额{x}: {y}")
        recovered = self.shamir.reconstruct(shamir_shares[:2])
        print(f"   恢复: {recovered}")

    def demo_large_secret(self):
        """演示大整数秘密"""
        print("\n4. 大整数秘密分享")

        # 使用更大的秘密
        secret = 2**31 - 1  # 接近素数的值

        print(f"   秘密: {secret}")
        print(f"   有限域: GF({self.shamir.prime})")

        shares = self.shamir.share(secret, threshold=3, num_shares=5)
        print(f"   份额:")
        for x, y in shares:
            print(f"     x={x}: y={y}")

        recovered = self.shamir.reconstruct(shares[:3])
        print(f"   恢复: {recovered}")
        print(f"   验证: {'通过 ✓' if recovered == secret % self.shamir.prime else '失败 ✗'}")

    def demo_vss(self):
        """演示可验证秘密共享"""
        print("\n5. 可验证秘密共享(VSS)")

        secret = 999

        shares, commitments, randomness = self.vss.share_with_commitments(
            secret, threshold=3, num_shares=5
        )

        print(f"   秘密: {secret}")
        print(f"   承诺:")
        for i, c in enumerate(commitments):
            print(f"     份额{i+1}的承诺: {c}")

        # 验证所有份额
        print("\n   验证份额:")
        for i, share in enumerate(shares):
            is_valid = self.vss.verify_share(share, commitments[i], randomness[i])
            print(f"     份额{share[0]}: {'有效 ✓' if is_valid else '无效 ✗'}")

        # 模拟一个伪造的份额
        print("\n   尝试验证伪造的份额:")
        fake_share = (6, 12345)  # x=6不在生成范围内
        is_valid = self.vss.verify_share(fake_share, commitments[0], randomness[0])
        print(f"     伪造份额验证: {'有效 ✓ (不应该)' if is_valid else '无效 ✗'}")


def main():
    """主函数"""
    print("=" * 60)
    print("秘密分享: Shamir秘密共享与拉格朗日重构")
    print("=" * 60)

    demo = SecretSharingDemo()

    demo.demo_basic_shamir()
    demo.demo_lagrange_weights()
    demo.demo_additive_vs_shamir()
    demo.demo_large_secret()
    demo.demo_vss()

    print("\n" + "=" * 60)
    print("秘密分享演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
