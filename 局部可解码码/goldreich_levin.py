# -*- coding: utf-8 -*-
"""
算法实现：局部可解码码 / goldreich_levin

本文件实现 goldreich_levin 相关的算法功能。
"""

import random
import hashlib


def is_prime(n):
    """素性测试。"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def generate_prime(bits=8):
    """生成素数。"""
    while True:
        p = random.randrange(2**(bits-1), 2**bits, 2)
        if is_prime(p):
            return p


def dot_product_bits(a, b):
    """计算两个比特向量的点积（模 2）。"""
    return sum(ai * bi for ai, bi in zip(a, b)) % 2


class GoldreichLevin:
    """
    Goldreich-Levin 编码和解码。

    GL 定理允许从"大部分是线性的"函数中恢复线性部分。
    """

    def __init__(self, n, delta=0.1, epsilon=0.1):
        """
        初始化 GL 方案。

        参数:
            n: 输入长度
            delta: 容许的误差
            epsilon: 成功概率参数
        """
        self.n = n
        self.delta = delta
        self.epsilon = epsilon
        # 随机选择的哈希函数参数
        self.r = [random.randint(0, 1) for _ in range(n)]

    def encode(self, x):
        """
        编码：计算 <r, x> mod 2。

        参数:
            x: n 比特向量

        返回:
            单个比特：<r, x>
        """
        return dot_product_bits(self.r, x)

    def gl_iteration(self, f_oracle, x):
        """
        GL 迭代：恢复 x 的一个比特。

        参数:
            f_oracle: 函数 oracle（访问 f）
            x: 候选输入

        返回:
            x 的一个比特的估计
        """
        # 随机选择 y
        y = [random.randint(0, 1) for _ in range(self.n)]

        # 查询 f(x + y) 和 f(y)
        f_xy = f_oracle(x, y)
        f_y = f_oracle(x, [0] * self.n)

        # 计算 b = f(x+y) + f(y) = <r, x> + 2<r, y> = <r, x>
        # （因为 <r, y> 在某些情况下会被抵消）
        b = (f_xy + f_y) % 2

        return b

    def recover_linear_function(self, f_oracle, num_trials=None):
        """
        使用 GL 迭代恢复线性函数 f 的系数。

        参数:
            f_oracle: 函数 oracle
            num_trials: 试验次数

        返回:
            恢复的系数向量 r
        """
        if num_trials is None:
            num_trials = int(1 / self.epsilon**2)

        n = self.n
        r_recovered = []

        for i in range(n):
            # 用 GL 恢复第 i 个比特
            votes = []
            for _ in range(num_trials):
                # 构造特殊的 x 来隔离第 i 个比特
                x = [0] * n
                x[i] = 1

                # 随机 y
                y = [random.randint(0, 1) for _ in range(n)]

                # 查询
                f_xy = f_oracle(x, y)
                f_y = f_oracle([0] * n, y)

                # 结果
                b = (f_xy + f_y) % 2
                votes.append(b)

            # 多数投票
            bit = 1 if sum(votes) > num_trials // 2 else 0
            r_recovered.append(bit)

        return r_recovered


class GLHardFunction:
    """
    Goldreich-Levin 难函数实例。

    基于底层伪随机生成器构建。
    """

    def __init__(self, seed_length=8):
        self.seed_length = seed_length
        self.seed = [random.randint(0, 1) for _ in range(seed_length)]

    def compute(self, x):
        """
        计算 GL 难函数。

        简化实现：f(x) = PRG(G(seed) XOR x)

        参数:
            x: 输入比特向量

        返回:
            单个比特
        """
        # 生成伪随机序列
        random.seed(int(''.join(map(str, self.seed)), 2))
        g = [random.randint(0, 1) for _ in range(len(x))]

        # XOR
        result_bit = dot_product_bits(g, x)

        # 更新 seed（模拟扩展）
        self.seed = [random.randint(0, 1) for _ in range(self.seed_length)]

        return result_bit


def gl_oracle_wrapper(f, x, y):
    """
    GL oracle 包装器。

    参数:
        f: 底层函数
        x: 第一个输入
        y: 第二个输入

    返回:
        f(x XOR y) + f(y) mod 2
    """
    # 简化：x XOR y
    xy = [x[i] ^ y[i] for i in range(len(x))]
    return (f(xy) + f(y)) % 2


def goldreich_levin_iteration(f, x, r=None, n=8):
    """
    Goldreich-Levin 迭代的单次执行。

    参数:
        f: 函数 f
        x: 要恢复的输入
        r: 随机向量（已知）
        n: 输入长度

    返回:
        <r, x> 的估计
    """
    if r is None:
        r = [random.randint(0, 1) for _ in range(n)]

    # 计算 <r, x>
    expected = dot_product_bits(r, x)

    return expected


def verify_gl_recovery(r_original, r_recovered):
    """
    验证 GL 恢复是否成功。

    参数:
        r_original: 原始系数
        r_recovered: 恢复的系数

    返回:
        True/False
    """
    return r_original == r_recovered


if __name__ == "__main__":
    print("=== Goldreich-Levin 定理测试 ===")

    # 设置
    n = 8
    delta = 0.1
    epsilon = 0.2

    # 创建 GL 编码器
    gl = GoldreichLevin(n, delta, epsilon)
    r = gl.r

    print(f"输入长度 n = {n}")
    print(f"随机向量 r = {r}")

    # 编码测试
    x = [1, 0, 1, 1, 0, 0, 1, 0]
    encoded = gl.encode(x)
    print(f"\n输入 x = {x}")
    print(f"编码 <r, x> = {encoded}")

    # 定义一个 oracle 函数
    def simple_oracle(x_input, y_input):
        """简单的线性函数 oracle：f(x) = <r, x>"""
        return dot_product_bits(r, x_input)

    # GL 恢复测试
    print("\n=== GL 恢复测试 ===")
    r_recovered = gl.recover_linear_function(simple_oracle, num_trials=50)

    print(f"原始 r:  {r}")
    print(f"恢复 r:  {r_recovered}")
    print(f"恢复成功: {verify_gl_recovery(r, r_recovered)}")

    # 难函数测试
    print("\n=== GL 难函数测试 ===")
    gl_hard = GLHardFunction(seed_length=8)

    def hard_oracle(x_input, y_input):
        """GL 难函数 oracle。"""
        return gl_hard.compute(x_input)

    # 难函数难以恢复
    print("GL 难函数 f(x) = <r, G(seed)> 的行为:")
    for i in range(4):
        test_input = [random.randint(0, 1) for _ in range(8)]
        result = gl_hard.compute(test_input)
        print(f"  f({test_input}) = {result}")

    print("\nGoldreich-Levin 定理特性:")
    print("  核心：可以从大部分线性的函数中恢复线性部分")
    print("  应用：构建伪随机生成器（GGM）")
    print("  本地解码：O(1/epsilon^2) 查询恢复单个比特")
    print("  密码学意义：基于单向函数构建硬核谓词")
