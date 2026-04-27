# -*- coding: utf-8 -*-
"""
算法实现：密码学协议 / secure_multiplication

本文件实现 secure_multiplication 相关的算法功能。
"""

import random


class SecureMultiplier:
    """安全乘法协议"""

    def __init__(self, field_size: int = 2**31):
        self.field = field_size

    def generate_triplet(self) -> tuple:
        """
        生成 Beaver 三元组

        (a, b, c) 满足 a * b = c

        注意：在实际应用中，这由可信第三方或分布式生成
        """
        a = random.randint(0, self.field - 1)
        b = random.randint(0, self.field - 1)
        c = (a * b) % self.field
        return a, b, c

    def share(self, secret: int, num_shares: int = 2) -> list:
        """
        秘密共享：将秘密分成n份

        参数：
            secret: 要共享的秘密
            num_shares: 份数（这里用2-out-of-2）

        返回：共享份额列表
        """
        shares = [random.randint(0, self.field - 1) for _ in range(num_shares - 1)]
        shares.append((secret - sum(shares)) % self.field)
        return shares

    def reconstruct(self, shares: list) -> int:
        """从共享重建秘密"""
        return sum(shares) % self.field

    def secure_multiply(self, x_shares: list, y_shares: list,
                       triplet: tuple) -> list:
        """
        安全乘法（使用Beaver三元组）

        参数：
            x_shares: x的份额 [x1, x2]
            y_shares: y的份额 [y1, y2]
            triplet: (a, b, c) 三元组

        返回：xy的份额
        """
        a, b, c = triplet

        # 各方计算 d = x - a, e = y - b
        # 这里简化处理，实际需要两方分别计算
        d = (x_shares[0] - a) % self.field
        e = (y_shares[0] - b) % self.field

        # 开放d和e（通信）
        # d_open = d, e_open = e

        # 计算结果份额
        # z = c + d*b + e*a + d*e
        z0 = (c + d * b + e * a + d * e) % self.field
        z1 = (0) % self.field  # 简化

        return [z0, z1]


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 安全乘法测试 ===\n")

    sm = SecureMultiplier()

    # 模拟两方：Alice和Bob
    # Alice有x，Bob有y
    x = 12345
    y = 67890

    print(f"Alice的输入: {x}")
    print(f"Bob的输入: {y}")
    print(f"期望乘积: {x * y}")

    # 秘密共享
    x_shares = sm.share(x, 2)
    y_shares = sm.share(y, 2)

    print(f"\n秘密共享:")
    print(f"  x的份额: {x_shares}")
    print(f"  y的份额: {y_shares}")
    print(f"  x重建: {sm.reconstruct(x_shares)}")
    print(f"  y重建: {sm.reconstruct(y_shares)}")

    # 生成Beaver三元组
    triplet = sm.generate_triplet()
    print(f"\nBeaver三元组: {triplet}")

    # 安全乘法
    result_shares = sm.secure_multiply(x_shares, y_shares, triplet)
    result = sm.reconstruct(result_shares)

    print(f"\n安全乘法结果: {result}")
    print(f"验证: {'✅ 正确' if result == x * y else '❌ 错误'}")

    print("\n说明：")
    print("  - 各方只知道自己的输入和份额")
    print("  - 第三方也不知道真实输入")
    print("  - Beaver三元组可以预生成")
    print("  - 这是安全多方计算的基础组件")
