"""
zk-SNARK有限域实现 - Polynomial Commitment & KZG Protocol
=============================================================

本模块实现有限域上的基本运算、多项式承诺以及KZG协议的核心组件。
KZG (Kate-Zaverucha-Goldberg) 协议是一种基于双线性配对的常数级证明多项式承诺方案。

核心概念:
- 有限域 F_p 上的多项式运算
- 多项式承诺: prover 对多项式 f(x) 生成承诺 C，verifier 可随机挑战 τ 验证 f(τ)
- 配对友好椭圆曲线: BLS12-381, 支持 e(G^a, H^b) = e(G, H)^{ab}

作者: OpenClaw Agent
版本: 1.0
"""

import os
import random
import hashlib
import sys
sys.path.insert(0, os.path.dirname(__file__))


# --------------------------------------------------------------------
# 有限域算术 (Finite Field Arithmetic)
# --------------------------------------------------------------------

class FiniteField:
    """
    有限域 F_p 的实现，支持基本的加减乘除、模指数运算。
    
    有限域是zk-SNARK的基础，所有标量和多项式系数都在有限域上运算。
    选取一个安全的素数 p（此处使用 BLS12-381 曲线的素数）。
    """
    
    # BLS12-381 曲线的素数模数
    # p = (2^381 - 2^32 - 2^9 - 2^7 - 2^6 - 2^4 - 1)
    P = 0x73eda753299d7d483339d80809a1d80553bda402fffe5b850761c49dd5
    # 生成元 g (群 G1 的生成元，椭圆曲线上的点)
    G = 2
    
    def __init__(self, value):
        """
        初始化有限域元素。
        
        参数:
            value: 整数值，自动对 P 取模
        """
        # 取模确保值在 [0, P-1] 范围内
        self.value = value % FiniteField.P
    
    # 运算符重载: 加法
    def __add__(self, other):
        """有限域加法: (a + b) mod p"""
        return FiniteField(self.value + other.value)
    
    # 运算符重载: 减法
    def __sub__(self, other):
        """有限域减法: (a - b) mod p"""
        return FiniteField(self.value - other.value)
    
    # 运算符重载: 乘法
    def __mul__(self, other):
        """有限域乘法: (a * b) mod p"""
        return FiniteField(self.value * other.value)
    
    # 运算符重载: 幂运算
    def __pow__(self, exponent):
        """
        有限域幂运算: a^e mod p
        使用快速幂算法 (exponentiation by squaring)
        """
        result = FiniteField(1)          # 初始化为乘法单位元
        base = self                     # 底数
        exp = exponent % (FiniteField.P - 1)  # 费马小定理: a^{p-1} = 1 (当 a != 0)
        while exp > 0:
            if exp & 1:                 # 如果当前位为 1，累乘底数
                result = result * base
            base = base * base          # 底数平方
            exp >>= 1                   # 指数右移（除以2）
        return result
    
    # 运算符重载: 反转/除法
    def __truediv__(self, other):
        """有限域除法: a / b = a * b^{-1} mod p"""
        return self * other.inv()      # 利用乘法的逆元实现除法
    
    # 求乘法逆元
    def inv(self):
        """
        使用扩展欧几里得算法求乘法逆元: a^{-1} mod p
        
        费马小定理: a^{p-2} ≡ a^{-1} (mod p) 当 p 为素数
        这里使用扩展欧几里得算法，对小素数更高效
        """
        # 扩展欧几里得算法
        # 求解: a*x + p*y = gcd(a, p) = 1, 则 x 即为 a 的逆元
        a, m = self.value, FiniteField.P
        # 初始化
        orig_m = m
        y, x = 0, 1
        # 迭代计算
        while m:
            # 计算商和余数
            quotient = a // m
            a, m = m, a - quotient * m   # Euclid 步骤
            x, y = y, x - quotient * y
        # 此时 a = gcd(orig_a, orig_m) = 1
        return FiniteField(x % orig_m)
    
    # 字符串表示
    def __repr__(self):
        return f"FF({self.value})"
    
    # 判断相等
    def __eq__(self, other):
        return self.value == other.value


# --------------------------------------------------------------------
# 椭圆曲线点 (Elliptic Curve Point) - 简化版 G1
# --------------------------------------------------------------------

class ECPoint:
    """
    椭圆曲线点（简化版，用于演示 KZG 协议原理）
    
    使用简化的 Weierstrass 曲线: y^2 = x^3 + b
    实际 zk-SNARK 使用的是 BLS12-381 曲线，这里用简化版本演示概念
    """
    
    # 曲线参数 y^2 = x^3 + b (简化曲线)
    A = 0
    B = 7   # 标准 secp256k1 使用的 b 值
    
    def __init__(self, x, y, infinity=False):
        """
        初始化椭圆曲线点。
        
        参数:
            x: x 坐标（有限域元素）
            y: y 坐标（有限域元素）
            infinity: 是否为零点（无穷远点）
        """
        self.x = x      # x 坐标
        self.y = y      # y 坐标
        self.infinity = infinity  # 无穷远点标志
    
    # 创建无穷远点
    @classmethod
    def infinity_point(cls):
        """返回无穷远点（群的单位元）"""
        return cls(FiniteField(0), FiniteField(0), infinity=True)
    
    # 创建生成元点
    @classmethod
    def generator(cls):
        """
        返回群的生成元 G
        这里使用简化的生成元
        """
        gx = FiniteField(550662630222773436695812)   # 简化的生成元 x 坐标
        gy = FiniteField(552715254493039471604389)   # 简化的生成元 y 坐标
        return cls(gx, gy)
    
    # 椭圆曲线加法
    def __add__(self, other):
        """
        椭圆曲线点加法
        
        若 self == O（无穷远点），返回 other
        若 other == O，返回 self
        若 self == -other，返回 O
        否则使用弦切法计算加法
        """
        # 无穷远点的情况
        if self.infinity:
            return other
        if other.infinity:
            return self
        
        # 判断是否是同一点（倍点）或互为逆元
        if self.x == other.x:
            if self.y == other.y:
                # 倍点: P + P = 2P，使用切线斜率
                # λ = (3*x^2 + a) / (2*y)
                numerator = (self.x ** FiniteField(2)) * FiniteField(3) + FiniteField(ECPoint.A)
                denominator = self.y * FiniteField(2)
                lam = numerator / denominator
            else:
                # 互为逆元: P + (-P) = O
                return ECPoint.infinity_point()
        else:
            # 不同点加法
            # λ = (y2 - y1) / (x2 - x1)
            numerator = other.y - self.y
            denominator = other.x - self.x
            lam = numerator / denominator
        
        # 计算新点坐标
        x_r = lam ** FiniteField(2) - self.x - other.x
        y_r = lam * (self.x - x_r) - self.y
        
        return ECPoint(x_r, y_r)
    
    # 标量乘法（重复加法）
    def __mul__(self, scalar):
        """
        椭圆曲线标量乘法: Q = k * P
        
        使用二进制展开法（double-and-add）:
        - 将标量 k 展开为二进制
        - 遍历每一位，遇到 1 则加，遇到 0 则倍
        - 时间复杂度: O(log k)
        """
        result = ECPoint.infinity_point()  # 初始化为单位元
        addend = self                       # 要累加的基点
        
        # 处理负数标量（取模）
        k = scalar.value % FiniteField.P
        
        while k > 0:
            if k & 1:                       # 如果当前位为 1，累加
                result = result + addend
            addend = addend + addend         # 倍点
            k >>= 1                          # 右移
        
        return result
    
    # 右乘（支持 scalar * point 语法）
    def __rmul__(self, scalar):
        return self.__mul__(scalar)
    
    # 字符串表示
    def __repr__(self):
        if self.infinity:
            return "EC_O"  # 无穷远点
        return f"EC({self.x.value:#x},{self.y.value:#x})"


# --------------------------------------------------------------------
# 配对 (Bilinear Pairing) - 简化版
# --------------------------------------------------------------------

class Pairing:
    """
    双线性配对的简化实现
    
    双线性配对 e: G1 × G2 -> GT 满足:
    - 双线性: e(a*P, b*Q) = e(P, Q)^{ab}
    - 非退化: e(P, Q) != 1（生成元情况下）
    - 可计算性: 配对可以高效计算
    
    注意: 实际实现需要使用密码学库（如 charm、RELIC、或 pysmx）
    这里使用简化的数学表示来演示原理
    """
    
    @staticmethod
    def pair(g1, g2):
        """
        计算配对 e(g1, g2)
        
        参数:
            g1: G1 群中的点 (椭圆曲线点)
            g2: G2 群中的点 (简化表示)
        
        返回:
            配对结果（简化表示为一个数）
        """
        # 简化实现：返回配对的"模拟值"
        # 真实实现需要使用椭圆曲线配对（Miller 算法 + 指数运算）
        # 这里用 hash 表示配对结果的确定性
        seed = f"pairing_{g1.x.value}_{g1.y.value}_{g2}"
        result = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
        return result % FiniteField.P
    
    @staticmethod
    def verify_pairing(g, h, e_g_h, expected):
        """
        验证配对等式: e(g, h)^x == expected
        
        用于验证 KZG 承诺的正确性
        """
        computed = Pairing.pair(g, h)
        # 简化验证
        return computed == expected


# --------------------------------------------------------------------
# 多项式 (Polynomial)
# --------------------------------------------------------------------

class Polynomial:
    """
    有限域上的多项式表示和运算
    
    多项式 f(x) = a_0 + a_1*x + a_2*x^2 + ... + a_n*x^n
    系数存储在有限域 FiniteField 中
    """
    
    def __init__(self, coefficients):
        """
        初始化多项式。
        
        参数:
            coefficients: 系数列表 [a_0, a_1, a_2, ...]
                         索引 i 对应 x^i 的系数
        """
        # 去除高阶零系数
        self.coeffs = coefficients[:]
        while len(self.coeffs) > 0 and self.coeffs[-1].value == 0:
            self.coeffs.pop()
        if len(self.coeffs) == 0:
            self.coeffs = [FiniteField(0)]
    
    # 获取多项式次数
    def degree(self):
        """返回多项式的次数（最高非零次项的指数）"""
        return max(0, len(self.coeffs) - 1)
    
    # 系数访问
    def __getitem__(self, index):
        """获取 x^index 项的系数"""
        if index < len(self.coeffs):
            return self.coeffs[index]
        return FiniteField(0)
    
    def __setitem__(self, index, value):
        """设置 x^index 项的系数"""
        # 如果需要扩展系数列表
        while len(self.coeffs) <= index:
            self.coeffs.append(FiniteField(0))
        self.coeffs[index] = value
    
    # 多项式加法
    def __add__(self, other):
        """多项式加法: (f + g)(x)"""
        result = []
        max_len = max(len(self.coeffs), len(other.coeffs))
        for i in range(max_len):
            a = self[i] if i < len(self.coeffs) else FiniteField(0)
            b = other[i] if i < len(other.coeffs) else FiniteField(0)
            result.append(a + b)
        return Polynomial(result)
    
    # 多项式乘法
    def __mul__(self, other):
        """多项式乘法: (f * g)(x)"""
        if self.degree() == -1 or other.degree() == -1:
            return Polynomial([FiniteField(0)])
        result = [FiniteField(0) for _ in range(len(self.coeffs) + len(other.coeffs) - 1)]
        for i, a in enumerate(self.coeffs):
            for j, b in enumerate(other.coeffs):
                result[i + j] = result[i + j] + a * b
        return Polynomial(result)
    
    # 多项式求值
    def eval(self, x):
        """
        Horner 法则求值: f(x)
        
        使用 Horner 法则高效计算多项式值:
        f(x) = a_0 + x*(a_1 + x*(a_2 + ...))
        """
        result = FiniteField(0)
        for coeff in reversed(self.coeffs):
            result = result * x + coeff
        return result
    
    # 多项式除法（长除法）
    def __divmod__(self, other):
        """
        多项式除法: 返回 (商, 余数)
        
        使用经典长除法算法
        """
        if other.degree() == -1:
            raise ValueError("除数多项式不能为零")
        
        # 复制被除数
        remainder = Polynomial(self.coeffs[:])
        # 初始化商
        quotient_coeffs = [FiniteField(0) for _ in range(len(self.coeffs))]
        
        while remainder.degree() >= other.degree() and remainder.degree() >= 0:
            # 计算当前商的项
            degree_diff = remainder.degree() - other.degree()
            coeff = remainder[remainder.degree()] / other[other.degree()]
            quotient_coeffs[degree_diff] = coeff
            
            # 从余数中减去
            for i in range(other.degree() + 1):
                idx = i + degree_diff
                remainder.coeffs[idx] = remainder.coeffs[idx] - coeff * other.coeffs[i]
            
            # 去除高阶零系数
            while len(remainder.coeffs) > 0 and remainder.coeffs[-1].value == 0:
                remainder.coeffs.pop()
        
        # 构建商多项式
        quotient = Polynomial(quotient_coeffs)
        return quotient, remainder
    
    # 字符串表示
    def __repr__(self):
        terms = []
        for i, c in enumerate(self.coeffs):
            if c.value != 0:
                if i == 0:
                    terms.append(f"{c.value}")
                elif i == 1:
                    terms.append(f"{c.value}*x")
                else:
                    terms.append(f"{c.value}*x^{i}")
        return " + ".join(terms) if terms else "0"


# --------------------------------------------------------------------
# KZG 承诺方案 (Kate-Zaverucha-Goldberg Commitment)
# --------------------------------------------------------------------

class KZGCommitment:
    """
    KZG 多项式承诺协议的实现
    
    KZG 承诺允许 Prover 对多项式 f(x) 生成常数大小的承诺，
    然后可以对任意点 z 证明 f(z) 的值。
    
    协议流程:
    1. Setup: 可信第三方生成公共参考串 (G, G^a, G^{a^2}, ..., G^{a^n})
    2. Commit: C = f(a) * G，使用 Powers of Tau
    3. Open: 证明者计算商多项式 q(x) = (f(x) - f(z)) / (x - z)
    4. Verify: 验证 e(C - f(z)*G, H) = e(q(a)*G, [a-z]*H)
    """
    
    def __init__(self, max_degree=64):
        """
        初始化 KZG 承诺系统。
        
        参数:
            max_degree: 支持的最大多项式次数
        """
        self.max_degree = max_degree
        self.G = ECPoint.generator()       # 生成元 G
        # 模拟: H = G * 2（另一个生成元，实际中是不同群）
        self.H = self.G * FiniteField(2)
        
        # 模拟"powers of tau": [G, G^a, G^{a^2}, ..., G^{a^n}]
        # 实际中 a 是秘密的随机值，这里用确定性序列代替
        self.powers_of_tau = []
        for i in range(max_degree + 1):
            self.powers_of_tau.append(self.G * FiniteField(i + 1))
    
    def commit(self, polynomial):
        """
        对多项式生成承诺。
        
        参数:
            polynomial: 要承诺的多项式
        
        返回:
            commitment: 承诺值 C = f(a) * G
        """
        commitment = ECPoint.infinity_point()
        # C = sum(f_i * G^{a^i}) = f(a) * G
        for i, coeff in enumerate(polynomial.coeffs):
            if i < len(self.powers_of_tau):
                commitment = commitment + self.powers_of_tau[i] * coeff
        return commitment
    
    def open(self, polynomial, point_z):
        """
        在点 z 处打开多项式承诺，生成证明。
        
        参数:
            polynomial: 原多项式
            point_z: 挑战点 z
        
        返回:
            value: f(z) 的值
            witness: 见证多项式 q(x) = (f(x) - f(z)) / (x - z) 的承诺
        """
        # 计算 f(z)
        value = polynomial.eval(point_z)
        
        # 构建分子: f(x) - f(z)
        f_minus_v = polynomial.coeffs[:]
        f_minus_v[0] = f_minus_v[0] - value
        
        numerator_poly = Polynomial(f_minus_v)
        
        # 构建分母: (x - z)
        denominator_poly = Polynomial([FiniteField(-point_z.value), FiniteField(1)])
        
        # 计算商多项式 q(x) = (f(x) - f(z)) / (x - z)
        quotient, remainder = numerator_poly.__divmod__(denominator_poly)
        
        # 确保余数为零（数学上应该为零）
        assert remainder.degree() == -1 or all(c.value == 0 for c in remainder.coeffs), \
            "除法有余数，分子应被 (x-z) 整除"
        
        # 计算见证承诺: W = q(a) * G
        witness = self.commit(quotient)
        
        return value, witness
    
    def verify(self, commitment, point_z, value, witness):
        """
        验证 KZG 承诺的正确性。
        
        验证方程: e(C - v*G, H) = e(W, [a-z]*H)
        
        参数:
            commitment: 承诺 C
            point_z: 挑战点 z
            value: 声称的 f(z) 值
            witness: 见证 W
        
        返回:
            valid: 验证是否通过
        """
        # 计算左侧: C - v*G
        vG = self.G * value
        left_input = commitment + ECPoint(vG.x, FiniteField(-vG.y.value))
        
        # 计算右侧基点: [a-z]*H
        a_minus_z = FiniteField(42 - point_z.value)  # 模拟 a - z
        right_base = self.H * a_minus_z
        
        # 简化验证（真实场景需要实际配对计算）
        # 验证: W 是否为 q(x) 的正确承诺
        # 这是一个简化的占位验证
        seed = f"verify_{commitment.x.value}_{point_z.value}_{value.value}_{witness.x.value}"
        expected = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % FiniteField.P
        
        # 使用配对验证（简化版）
        pairing_result = Pairing.pair(left_input, self.H)
        expected_pairing = Pairing.pair(witness, right_base)
        
        return pairing_result == expected_pairing


# --------------------------------------------------------------------
# 主程序测试
# --------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("zk-SNARK 有限域实现 - KZG 多项式承诺")
    print("=" * 60)
    
    # 1. 测试有限域运算
    print("\n--- 测试 1: 有限域运算 ---")
    a = FiniteField(10)
    b = FiniteField(3)
    print(f"a = {a.value}")
    print(f"b = {b.value}")
    print(f"a + b = {(a + b).value}")
    print(f"a - b = {(a - b).value}")
    print(f"a * b = {(a * b).value}")
    print(f"a / b = {(a / b).value}")
    print(f"a^3 = {(a ** 3).value}")
    
    # 2. 测试椭圆曲线
    print("\n--- 测试 2: 椭圆曲线点运算 ---")
    G = ECPoint.generator()
    print(f"生成元 G: {G}")
    
    # 标量乘法
    k = FiniteField(7)
    kG = G * k
    print(f"7 * G = {kG}")
    
    # 3. 测试多项式
    print("\n--- 测试 3: 多项式运算 ---")
    # f(x) = 1 + 2*x + 3*x^2
    f = Polynomial([FiniteField(1), FiniteField(2), FiniteField(3)])
    print(f"f(x) = {f}")
    print(f"f(x) 的次数 = {f.degree()}")
    
    # 在 x = 2 处求值
    x_val = FiniteField(2)
    f_2 = f.eval(x_val)
    print(f"f(2) = {f_2.value}")
    
    # g(x) = 1 + x
    g = Polynomial([FiniteField(1), FiniteField(1)])
    print(f"g(x) = {g}")
    
    # 多项式乘法
    fg = f * g
    print(f"f(x) * g(x) = {fg}")
    
    # 4. 测试 KZG 承诺
    print("\n--- 测试 4: KZG 多项式承诺 ---")
    kzg = KZGCommitment(max_degree=8)
    
    # 定义一个多项式
    # f(x) = 1 + 2x + 3x^2 + 4x^3
    f_coeff = [FiniteField(1), FiniteField(2), FiniteField(3), FiniteField(4)]
    f = Polynomial(f_coeff)
    print(f"承诺的多项式: {f}")
    
    # 生成承诺
    commitment = kzg.commit(f)
    print(f"承诺 C = f(a)*G: {commitment}")
    
    # 随机选择一个挑战点
    point_z = FiniteField(5)
    print(f"挑战点 z = {point_z.value}")
    
    # 打开承诺
    value, witness = kzg.open(f, point_z)
    print(f"f(z) = {value.value}")
    print(f"见证 W = q(a)*G: {witness}")
    
    # 验证承诺
    valid = kzg.verify(commitment, point_z, value, witness)
    print(f"验证结果: {'通过 ✓' if valid else '失败 ✗'}")
    
    print("\n--- 额外测试: 证明的正确性 ---")
    # 直接计算并验证
    direct_eval = f.eval(point_z)
    print(f"直接计算 f({point_z.value}) = {direct_eval.value}")
    print(f"KZG 证明给出 f({point_z.value}) = {value.value}")
    print(f"一致性: {'匹配 ✓' if direct_eval == value else '不匹配 ✗'}")
    
    # 5. 演示 zk-SNARK 的零知识性质
    print("\n--- 测试 5: 零知识演示 ---")
    print("承诺后，验证者只知道:")
    print(f"  - 承诺 C = {commitment}")
    print(f"  - 验证点 z = {point_z.value}")
    print("验证者无法从 C 恢复原多项式 f(x) (零知识性)")
    
    print("\n" + "=" * 60)
    print("KZG 协议演示完成")
    print("=" * 60)
