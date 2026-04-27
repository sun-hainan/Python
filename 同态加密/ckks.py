# -*- coding: utf-8 -*-

"""

算法实现：同态加密 / ckks



本文件实现 ckks 相关的算法功能。

"""



import random

import math





class CKKSEncoder:

    """CKKS 编码器：将复数向量编码为多项式。"""



    def __init__(self, poly_degree=8, scale=2**40):

        self.n = poly_degree

        self.scale = scale

        self.xi = complex(math.cos(math.pi / self.n), math.sin(math.pi / self.n))



    def encode(self, message):

        """

        将复数消息编码为多项式系数。



        参数:

            message: 复数向量，长度为 n/2



        返回:

            多项式系数向量

        """

        m = len(message)

        if m > self.n // 2:

            raise ValueError("消息长度不能超过 n/2")



        # 填充到 n/2

        msg_padded = list(message) + [0] * (self.n // 2 - m)



        # 调制到 [0, scale)

        v = [int(msg_padded[i].real * self.scale) % (2**30) for i in range(self.n // 2)]



        # 共轭对称扩展

        coeffs = v + [0] + [(-v[-(i+1)]) % (2**30) for i in range(self.n // 2 - 1)]



        return coeffs



    def decode(self, coeffs):

        """将多项式系数解码为复数消息。"""

        n = self.n // 2

        v = coeffs[:n]

        messages = [complex(x / self.scale, 0) for x in v]

        return messages





class CKKSKeyGenerator:

    """CKKS 密钥生成器。"""



    def __init__(self, n=8, q_bits=40):

        self.n = n

        self.q = 2**q_bits



    def keygen(self):

        """生成密钥对。"""

        # 私钥

        s = [random.choice([-1, 0, 1]) for _ in range(self.n)]



        # 公钥

        a = [random.randint(0, self.q - 1) for _ in range(self.n)]

        e = [random.choice([0, 1, -1]) for _ in range(self.n)]

        b = [(-a[i] * s[i] + e[i]) % self.q for i in range(self.n)]



        pk = {'b': b, 'a': a}

        sk = {'s': s}



        # 评估密钥（用于乘法）

        evk = self._generate_evk(s)



        return pk, sk, evk



    def _generate_evk(self, s):

        """生成评估密钥（简化）。"""

        n = self.n

        q = self.q

        a = [random.randint(0, q - 1) for _ in range(n)]

        e = [random.choice([0, 1, -1]) for _ in range(n)]

        # b = -a*s + e + q/4 * s^2

        b = [(-a[i] * s[i] + e[i] + (q // 4) * s[i]**2) % q for i in range(n)]

        return {'a': a, 'b': b}





def ckks_encrypt(pk, message_coeffs):

    """CKKS 加密。"""

    n = len(pk['b'])

    q = 2**40

    m = message_coeffs



    # 缩放消息

    m_scaled = [int(m[i] * 2**20) % q for i in range(len(m))]



    # 掩码

    u = [random.choice([0, 1, -1]) for _ in range(n)]



    c0 = [(pk['b'][i] * u[i] + m_scaled[i]) % q for i in range(n)]

    c1 = [(pk['a'][i] * u[i]) % q for i in range(n)]



    return {'c0': c0, 'c1': c1, 'scale': 2**20}





def ckks_decrypt(sk, ciphertext):

    """CKKS 解密（近似）。"""

    c0 = ciphertext['c0']

    c1 = ciphertext['c1']

    s = sk['s']

    scale = ciphertext['scale']

    n = len(c0)



    # m ≈ c0 + c1 * s

    m_scaled = [(c0[i] + c1[i] * s[i]) % 2**40 for i in range(n)]



    # 解码：逆缩放

    m = [v / scale for v in m_scaled]



    return m





def ckks_rotate(ct, offset):

    """

    CKKS 旋转：重排密文中的槽位。



    参数:

        ct: 密文

        offset: 旋转偏移量



    返回:

        旋转后的密文

    """

    n = len(ct['c0'])

    new_c0 = ct['c0'][offset:] + ct['c0'][:offset]

    new_c1 = ct['c1'][offset:] + ct['c1'][:offset]

    return {'c0': new_c0, 'c1': new_c1, 'scale': ct['scale']}





def ckks_rescale(ct, q_new):

    """

    CKKS 重缩放：除以 scale 以控制噪声。



    参数:

        ct: 密文

        q_new: 新的模数



    返回:

        重缩放后的密文

    """

    scale = ct['scale']

    # 模拟重缩放：除以 scale

    new_c0 = [int(c / scale) % q_new for c in ct['c0']]

    new_c1 = [int(c / scale) % q_new for c in ct['c1']]

    return {'c0': new_c0, 'c1': new_c1, 'scale': 1}





if __name__ == "__main__":

    print("=== CKKS 同态加密测试 ===")



    # 初始化

    encoder = CKKSEncoder(poly_degree=8, scale=2**40)

    kg = CKKSKeyGenerator(n=8, q_bits=40)

    pk, sk, evk = kg.keygen()



    print(f"多项式次数 n = {kg.n}")

    print(f"密文模数 q = {kg.q}")



    # 消息（复数向量）

    m1 = [1.5, 2.3, 0.0, 0.0]

    m2 = [0.8, 1.1, 0.0, 0.0]



    # 编码

    coeffs1 = encoder.encode(m1)

    coeffs2 = encoder.encode(m2)

    print(f"\n消息 m1: {m1}")

    print(f"消息 m2: {m2}")



    # 加密

    ct1 = ckks_encrypt(pk, coeffs1)

    ct2 = ckks_encrypt(pk, coeffs2)



    # 解密验证

    d1_coeffs = ckks_decrypt(sk, ct1)

    d1 = encoder.decode(d1_coeffs)

    print(f"\n解密 m1: {[round(x, 2) for x in d1]}")



    # 同态加法（简化）

    def add_ct(ct1, ct2):

        c0 = [(ct1['c0'][i] + ct2['c0'][i]) % 2**40 for i in range(len(ct1['c0']))]

        c1 = [(ct1['c1'][i] + ct2['c1'][i]) % 2**40 for i in range(len(ct1['c1']))]

        return {'c0': c0, 'c1': c1, 'scale': ct1['scale']}



    ct_sum = add_ct(ct1, ct2)

    d_sum_coeffs = ckks_decrypt(sk, ct_sum)

    d_sum = encoder.decode(d_sum_coeffs)

    print(f"同态加法 m1+m2: {[round(x, 2) for x in d_sum]}")



    # 旋转

    ct_rot = ckks_rotate(ct1, 2)

    print(f"旋转 offset=2: c0 前4位 = {ct_rot['c0'][:4]}")



    print("\nCKKS 特性:")

    print("  支持实数/复数向量的近似同态运算")

    print("  近似乘法后需要重缩放（rescale）控制精度")

    print("  旋转操作用于高效计算内积和卷积")

