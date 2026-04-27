# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / ring_lwe_crypto



本文件实现 ring_lwe_crypto 相关的算法功能。

"""



from math import log2, sqrt, pi





class LWEConsiderations:

    """LWE参数考虑"""



    @staticmethod

    def security_bound(n: int, log_q: float, log_sigma: float) -> float:

        """

        估计安全性



        参数：

            n: 维度

            log_q: log(q)

            log_sigma: log(σ)



        返回：安全位估计

        """

        # BKZ复杂度估计

        # LWE约化为SIVP，需要BKZ求解



        # 近似：log₂(σ/q) * n / 2

        return (log_q - log_sigma) * n / 2



    @staticmethod

    def modulus_chaining() -> None:

        """模数链"""

        print("=== 模数链 ===")

        print()

        print("现代格密码使用多个模数：")

        print("  - q₁ > q₂ > q₃ > ...")

        print("  - 每个用于不同的计算阶段")

        print()

        print("好处：")

        print("  - 减少噪声累积")

        print("  - 保持安全性")

        print("  - 提高效率")





class RLWEParameters:

    """Ring-LWE参数"""



    def __init__(self, n: int, q: int, std: float):

        self.n = n  # 多项式阶数

        self.q = q  # 模数

        self.std = std  # 噪声标准差



    def check_adequacy(self) -> bool:

        """检查参数是否足够"""

        # 检查: q > n * std^2

        return self.q > self.n * (self.std ** 2)



    def report(self) -> dict:

        """报告参数信息"""

        return {

            'n': self.n,

            'q': self.q,

            'std': self.std,

            'log_q': log2(self.q),

            'security_bits': (log2(self.q) - log2(self.std)) * self.n / 2

        }





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== LWE参数考虑测试 ===\n")



    # Kyber-512参数

    kyber = RLWEParameters(n=256, q=3329, std=2.0)



    info = kyber.report()

    print("Kyber-512参数：")

    print(f"  n = {info['n']}")

    print(f"  q = {info['q']} (log q ≈ {info['log_q']:.1f})")

    print(f"  σ = {info['std']}")

    print(f"  安全位估计: {info['security_bits']:.0f}")

    print(f"  参数适当: {'是' if kyber.check_adequacy() else '否'}")



    print()

    print("参数选择指南：")

    print("  - n 越大越安全，但更慢")

    print("  - q 越大效率越高（但要注意噪声）")

    print("  - σ 越小越安全，但要能处理")

    print()

    print("推荐值（Kyber）：")

    print("  - n = 256, 512, 768")

    print("  - q = 3329")

    print("  - σ ≈ 1-2")



    LWEConsiderations.modulus_chaining()



    print()

    print("说明：")

    print("  - 参数选择是密码系统设计的关键")

    print("  - 需要在安全性、效率、噪声之间权衡")

    print("  - 参考NIST后量子标准建议")

