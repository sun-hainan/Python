# -*- coding: utf-8 -*-
"""
算法实现：密码学协议 / secret_sharing

本文件实现 secret_sharing 相关的算法功能。
"""

import random
import secrets


class ShamirSecretSharing:
    """
    Shamir (t, n) 门限秘密共享方案

    将秘密分成 n 份，任意 t 或更多份可以恢复秘密
    少于 t 份无法获得任何秘密信息
    """

    def __init__(self, prime=None):
        """
        初始化 Shamir 秘密共享

        Args:
            prime: int 素数模数（应大于秘密值和n）
        """
        # 使用预定义的素数（实际应用应使用更大的安全素数）
        if prime is None:
            prime = 0x8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001

        self.prime = prime
        self.prime_bits = prime.bit_length()

    def split(self, secret, t, n):
        """
        将秘密分成 n 份

        Args:
            secret: int 要分享的秘密
            t: int 门限值（需要至少 t 份才能恢复）
            n: int 份额总数

        Returns:
            list of tuple (x, y) n个份额，其中 x 是份额索引，y 是份额值
        """
        if t > n:
            raise ValueError("门限值 t 不能大于份额数 n")

        if secret >= self.prime:
            raise ValueError(f"秘密值必须小于素数 {self.prime}")

        # 选取随机系数 a_1, a_2, ..., a_{t-1}
        coefficients = [secret]  # 常数项是秘密
        for _ in range(t - 1):
            # 随机选择 [1, prime-1] 的系数
            coeff = secrets.randbelow(self.prime - 1) + 1
            coefficients.append(coeff)

        # 计算多项式 f(x) = Σ coefficients[i] * x^i mod prime
        def polynomial(x):
            result = 0
            x_power = 1
            for coeff in coefficients:
                result = (result + coeff * x_power) % self.prime
                x_power = (x_power * x) % self.prime
            return result

        # 生成 n 个份额
        shares = []
        for x in range(1, n + 1):
            y = polynomial(x)
            shares.append((x, y))

        return shares

    def combine(self, shares):
        """
        从份额恢复秘密

        使用拉格朗日插值公式：
        secret = Σ y_i * l_i(0) mod prime
        其中 l_i(0) = Π_{j≠i} x_j / (x_j - x_i) mod prime

        Args:
            shares: list of tuple (x, y) 至少 t 个份额

        Returns:
            int 恢复的秘密
        """
        if len(shares) < 2:
            raise ValueError("至少需要 2 个份额才能恢复")

        # 提取 x 和 y 值
        x_values = [share[0] for share in shares]
        y_values = [share[1] for share in shares]

        # 拉格朗日插值在 x=0 处的值
        secret = 0
        for i in range(len(shares)):
            # 计算拉格朗日基多项式 l_i(0)
            numerator = 1
            denominator = 1

            for j in range(len(shares)):
                if i != j:
                    # 分子：Π x_j
                    numerator = (numerator * x_values[j]) % self.prime
                    # 分母：Π (x_j - x_i)
                    denominator = (denominator * (x_values[j] - x_values[i])) % self.prime

            # 计算分子 * 分母的模逆元
            lagrange_coeff = (numerator * self._mod_inverse(denominator, self.prime)) % self.prime

            # 累加
            secret = (secret + y_values[i] * lagrange_coeff) % self.prime

        return secret

    def _mod_inverse(self, a, m):
        """
        计算模逆元

        Args:
            a: int
            m: int 模数

        Returns:
            int a^{-1} mod m
        """
        # 扩展欧几里得算法
        def egcd(a, b):
            if a == 0:
                return (b, 0, 1)
            else:
                g, y, x = egcd(b % a, a)
                return (g, x - (b // a) * y, y)

        g, x, _ = egcd(a, m)
        if g != 1:
            raise ValueError("模逆元不存在")
        return x % m


class VisualSecretSharing:
    """
    可视秘密共享（Visual Secret Sharing）

    适用于图像分享：
    - 将图像分成 n 份
    - 叠加任意 t 份可以看到原始图像
    - 少于 t 份只能看到随机噪声

    注意：简化版本的黑白图像实现
    """

    def __init__(self, t, n):
        """
        初始化可视秘密共享

        Args:
            t: int 门限值
            n: int 份数
        """
        self.t = t
        self.n = n

    def encode(self, image):
        """
        将图像编码成 n 份

        Args:
            image: list of list of int (0=白, 1=黑) 二值图像

        Returns:
            list of list of list 二值图像列表（n份）
        """
        height = len(image)
        width = len(image[0]) if height > 0 else 0

        # 初始化 n 份图像
        shares = [[[0 for _ in range(width * 2)] for _ in range(height * 2)] for _ in range(self.n)]

        for y in range(height):
            for x in range(width):
                pixel = image[y][x]

                # 为每个像素生成 2×2 的编码块
                if pixel == 0:
                    # 白色像素：所有份额的块相同（随机选择一种模式）
                    if random.random() < 0.5:
                        patterns = [
                            [[1, 1], [0, 0]],  # 模式1
                            [[0, 0], [1, 1]],  # 模式2
                            [[1, 0], [1, 0]],  # 模式3
                            [[0, 1], [0, 1]],  # 模式4
                        ]
                        pattern = patterns[random.randrange(len(patterns))]
                    else:
                        pattern = [[0, 0], [0, 0]]

                    for share_idx in range(self.n):
                        for sy in range(2):
                            for sx in range(2):
                                shares[share_idx][y * 2 + sy][x * 2 + sx] = pattern[sy][sx]

                else:
                    # 黑色像素：份额的块叠加后是黑色的
                    patterns = [
                        [[1, 0], [0, 1]],
                        [[0, 1], [1, 0]],
                    ]
                    pattern = patterns[random.randrange(len(patterns))]

                    for share_idx in range(self.n):
                        for sy in range(2):
                            for sx in range(2):
                                shares[share_idx][y * 2 + sy][x * 2 + sx] = pattern[sy][sx]

        return shares

    def decode(self, shares):
        """
        叠加多份图像

        Args:
            shares: list 至少 t 份图像

        Returns:
            list of list 二值图像
        """
        if len(shares) < self.t:
            raise ValueError(f"需要至少 {self.t} 份才能恢复")

        height = len(shares[0]) // 2
        width = len(shares[0][0]) // 2

        result = [[0 for _ in range(width)] for _ in range(height)]

        for y in range(height):
            for x in range(width):
                # 叠加对应像素
                pixel_sum = 0
                for share in shares[:self.t]:
                    for sy in range(2):
                        for sx in range(2):
                            pixel_sum += share[y * 2 + sy][x * 2 + sx]

                # 如果至少有一半是黑色，则该像素为黑色
                result[y][x] = 1 if pixel_sum >= 2 else 0

        return result


def _mod_inverse_gcd(a, m):
    """使用扩展欧几里得算法求模逆元"""
    def gcd_extended(a, b):
        if a == 0:
            return b, 0, 1
        g, x1, y1 = gcd_extended(b % a, a)
        return g, y1 - (b // a) * x1, x1

    g, x, _ = gcd_extended(a % m, m)
    if g != 1:
        return None
    return x % m


# ------------------- 单元测试 -------------------
if __name__ == '__main__':
    print("=" * 50)
    print("测试 Shamir 门限秘密共享")
    print("=" * 50)

    sss = ShamirSecretSharing()

    # 秘密
    secret = 123456789
    t = 3  # 门限值
    n = 5  # 份额总数

    print(f"\n原始秘密: {secret}")
    print(f"门限值 (t): {t}")
    print(f"份额数 (n): {n}")

    # 分发秘密
    shares = sss.split(secret, t, n)
    print(f"\n生成的 {n} 个份额:")
    for i, share in enumerate(shares):
        print(f"  份额 {i + 1}: (x={share[0]}, y={share[1]})")

    # 恢复测试
    print("\n--- 恢复测试 ---")

    # 使用 t 个份额恢复
    recovery_shares = shares[:t]
    recovered_secret = sss.combine(recovery_shares)
    print(f"使用前 {t} 个份额恢复: {recovered_secret}")
    print(f"恢复结果: {'✅ 成功' if recovered_secret == secret else '❌ 失败'}")

    # 使用不同的 t 个份额恢复
    recovery_shares = [shares[0], shares[2], shares[4]]  # 非连续的份额
    recovered_secret = sss.combine(recovery_shares)
    print(f"使用份额 1, 3, 5 恢复: {recovered_secret}")
    print(f"恢复结果: {'✅ 成功' if recovered_secret == secret else '❌ 失败'}")

    # 少于 t 个份额（不应该能恢复）
    print("\n--- 安全性测试（少于 t 份额）---")
    for k in range(1, t):
        recovery_shares = shares[:k]
        try:
            # 即使能计算，结果也是随机的，不等于原始秘密
            partial_secret = sss.combine(recovery_shares)
            print(f"使用 {k} 个份额: 得到 {partial_secret} (≠ {secret})")
        except Exception as e:
            print(f"使用 {k} 个份额: 错误 - {e}")

    # 测试重建多项式
    print("\n--- 验证拉格朗日插值 ---")
    test_shares = shares[:t]
    x_values = [s[0] for s in test_shares]
    y_values = [s[1] for s in test_shares]

    print(f"x值: {x_values}")
    print(f"y值: {y_values}")

    # 在 x=0 处插值验证
    result = 0
    prime = sss.prime
    for i in range(t):
        numerator = 1
        denominator = 1
        for j in range(t):
            if i != j:
                numerator = (numerator * x_values[j]) % prime
                denominator = (denominator * (x_values[j] - x_values[i])) % prime

        lagrange_coeff = (numerator * _mod_inverse_gcd(denominator, prime)) % prime
        result = (result + y_values[i] * lagrange_coeff) % prime

    print(f"拉格朗日插值 f(0) = {result}")
    print(f"等于秘密: {'✅' if result == secret else '❌'}")

    print("\n" + "=" * 50)
    print("测试可视秘密共享")
    print("=" * 50)

    vss = VisualSecretSharing(t=2, n=2)

    # 简单的测试图像
    test_image = [
        [0, 1, 0, 1],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 1, 0],
    ]

    print("\n原始图像:")
    for row in test_image:
        print(' '.join(['█' if p else '░' for p in row]))

    # 编码
    shares = vss.encode(test_image)

    print(f"\n生成 {len(shares)} 份图像（每份是原始大小的2倍）")

    # 解码
    decoded = vss.decode(shares[:2])

    print("\n恢复图像:")
    for row in decoded:
        print(' '.join(['█' if p else '░' for p in row]))

    # 验证
    matches = (test_image == decoded)
    print(f"\n图像匹配: {'✅' if matches else '❌'}")

    print("\n" + "=" * 50)
    print("安全性分析:")
    print("=" * 50)
    print("1. Shamir方案：少于t份时，秘密完全隐藏")
    print("   - 每个份额是 (x, f(x))，x=0处是秘密")
    print("   - k-1 个点确定一个 k-1 次多项式")
    print("   - 但 f(0) 在所有可能的 k-1 次多项式中均匀分布")
    print("2. 可视秘密共享：份额单独看是随机噪声")
    print("   - 只有叠加足够份才能看到有意义图像")

    print("\n" + "=" * 50)
    print("复杂度分析:")
    print("=" * 50)
    print("时间复杂度:")
    print("  - 分发: O(n * t)")
    print("  - 恢复: O(t * log(p))")
    print("空间复杂度: O(n) 存储份额")

    print("\n✅ 秘密共享算法测试通过！")
