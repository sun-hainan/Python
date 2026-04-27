# -*- coding: utf-8 -*-

"""

算法实现：密码学协议 / pedersen_commitment



本文件实现 pedersen_commitment 相关的算法功能。

"""



import random

import hashlib





def generate_large_prime(bits=16):

    """生成大素数。"""

    while True:

        p = random.randrange(2**(bits-1), 2**bits, 2)

        if is_prime(p):

            return p





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





def egcd(a, b):

    """扩展欧几里得算法。"""

    if a == 0:

        return b, 0, 1

    g, x1, y1 = egcd(b % a, a)

    x = y1 - (b // a) * x1

    y = x1

    return g, x, y





def modinv(a, m):

    """模逆元。"""

    g, x, _ = egcd(a % m, m)

    if g != 1:

        return None

    return x % m





class PedersenCommit:

    """Pedersen 承诺方案。"""



    def __init__(self, q_bits=16):

        # 选择素数 q 和 p = 2*q + 1（安全素数）

        self.q = generate_large_prime(q_bits)

        self.p = 2 * self.q + 1



        # 在 Z_p* 中找阶为 q 的生成元 g

        self.g = self._find_generator()



        # 随机选择第二个生成元 h = g^k

        k = random.randint(2, self.q - 1)

        self.h = pow(self.g, k, self.p)



        # 私钥就是 k

        self.private_key = k



    def _find_generator(self):

        """找到阶为 q 的生成元。"""

        # g 是 Z_p* 的 q 阶子群的生成元

        while True:

            h = random.randint(2, self.p - 1)

            g = pow(h, 2, self.p)  # 确保阶为 q

            if pow(g, self.q, self.p) == 1 and pow(g, 2, self.p) != 1:

                return g



    def commit(self, value, randomness=None):

        """

        生成承诺。



        参数:

            value: 要承诺的值 m

            randomness: 随机数 r（可选）



        返回:

            commitment: c = g^m * h^r mod p

        """

        if randomness is None:

            randomness = random.randint(1, self.q - 1)



        # c = g^m * h^r mod p

        g_pow_m = pow(self.g, value, self.p)

        h_pow_r = pow(self.h, randomness, self.p)

        commitment = (g_pow_m * h_pow_r) % self.p



        return {

            'c': commitment,

            'r': randomness

        }



    def open(self, value, randomness):

        """打开承诺（验证）。"""

        return self.commit(value, randomness)



    def verify(self, commitment, value, randomness):

        """验证承诺是否正确。"""

        expected = self.commit(value, randomness)

        return expected['c'] == commitment['c']





class PedersenVectorCommit:

    """

    Pedersen 向量承诺：可以对多个值生成单一承诺。



    c = g_1^{m_1} * g_2^{m_2} * ... * h^r

    """



    def __init__(self, num_values, q_bits=12):

        self.q = generate_large_prime(q_bits)

        self.p = 2 * self.q + 1



        # 生成多个生成元

        self.g = []

        for i in range(num_values):

            g = random.randint(2, self.p - 1)

            # 确保阶为 q

            g = pow(g, 2, self.p)

            self.g.append(g)



        # 随机选择 h

        h = random.randint(2, self.p - 1)

        self.h = pow(h, 2, self.p)



    def commit(self, values, randomness=None):

        """

        承诺多个值。



        参数:

            values: 值列表 [m_1, m_2, ..., m_n]

            randomness: 随机数 r



        返回:

            commitment 和随机数

        """

        if randomness is None:

            randomness = random.randint(1, self.q - 1)



        if len(values) != len(self.g):

            raise ValueError("值数量与生成元数量不匹配")



        # c = prod(g_i^{m_i}) * h^r

        c = 1

        for g, m in zip(self.g, values):

            c = (c * pow(g, m, self.p)) % self.p



        c = (c * pow(self.h, randomness, self.p)) % self.p



        return {'c': c, 'r': randomness}



    def verify(self, commitment, values, randomness):

        """验证承诺。"""

        expected = self.commit(values, randomness)

        return expected['c'] == commitment['c']





def pedersen_range_proof(value, commit, pc):

    """

    Pedersen 范围证明（简化）：证明 m 在 [0, 2^n-1] 范围内。



    使用二进制分解：

    m = sum(b_i * 2^i)，其中 b_i ∈ {0, 1}



    证明者发送 c_i = g^{b_i} * h^{r_i}

    验证者检查 prod(c_i) = g^m * h^{sum(r_i)}

    """

    n = 8  # 位数

    bits = [(value >> i) & 1 for i in range(n)]



    commitments = []

    for i, bit in enumerate(bits):

        c = pc.commit(bit)

        commitments.append(c)



    # 验证

    prod_c = 1

    for c in commitments:

        prod_c = (prod_c * c['c']) % pc.p



    # 计算 g^m

    g_pow_m = pow(pc.g, value, pc.p)

    # 计算 h^{sum(r)}

    sum_r = sum(c['r'] for c in commitments)

    h_pow_sumr = pow(pc.h, sum_r, pc.p)



    expected = (g_pow_m * h_pow_sumr) % pc.p



    return prod_c == expected





if __name__ == "__main__":

    print("=== Pedersen 承诺测试 ===")



    # 创建承诺方案

    pc = PedersenCommit(q_bits=12)

    print(f"素数 p: {pc.p}")

    print(f"阶 q: {pc.q}")

    print(f"生成元 g: {pc.g}")

    print(f"生成元 h: {pc.h}")



    # 承诺单个值

    m = 42

    commit = pc.commit(m)

    print(f"\n承诺值 m={m}:")

    print(f"  承诺 c: {commit['c']}")

    print(f"  随机数 r: {commit['r']}")



    # 验证承诺

    valid = pc.verify(commit, m, commit['r'])

    print(f"  验证结果: {valid}")



    # 范围证明

    print("\n=== 范围证明测试 ===")

    for value in [15, 100, 255]:

        proof_valid = pedersen_range_proof(value, None, pc)

        print(f"  值 {value} 的范围证明: {proof_valid}")



    # 向量承诺

    print("\n=== 向量承诺测试 ===")

    pvc = PedersenVectorCommit(num_values=4, q_bits=12)

    values = [1, 2, 3, 4]

    v_commit = pvc.commit(values)

    print(f"承诺向量 {values}:")

    print(f"  承诺 c: {v_commit['c']}")



    v_valid = pvc.verify(v_commit, values, v_commit['r'])

    print(f"  验证结果: {v_valid}")



    # 隐藏性测试

    print("\n=== 隐藏性测试 ===")

    m1, m2 = 10, 20

    c1 = pc.commit(m1)

    c2 = pc.commit(m2)

    print(f"m1={m1} 的承诺: {c1['c']}")

    print(f"m2={m2} 的承诺: {c2['c']}")

    print("从承诺无法区分 m1 和 m2（信息论隐藏）")



    print("\nPedersen 承诺特性:")

    print("  信息论安全：即使敌手无限算力也无法伪造承诺")

    print("  绑定性：承诺者无法将承诺改为另一个值")

    print("  同态性：c(m1,r1) * c(m2,r2) = c(m1+m2, r1+r2)")

    print("  应用：零知识证明、区块链保密交易")

