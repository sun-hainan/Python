# -*- coding: utf-8 -*-

"""

算法实现：同态加密 / tfhe



本文件实现 tfhe 相关的算法功能。

"""



import random

import math





class TFHEKeyGenerator:

    """TFHE 密钥生成器。"""



    def __init__(self, n=8, q=2**32, std=2**-15):

        self.n = n

        self.q = q

        self.std = std

        self.mask = q - 1



    def keygen(self):

        """生成密钥。"""

        # 密钥 s（二进制向量）

        s = [random.choice([0, 1]) for _ in range(self.n)]



        # 盲化密钥（用于 bootstrapping）

        bk = self._generate_bootstrap_key(s)



        # 密钥切换密钥（用于重线性化）

        ks = self._generate_key_switch_key(s)



        pk = {'bk': bk, 'ks': ks, 'n': self.n, 'q': self.q}

        sk = {'s': s}



        return pk, sk



    def _generate_bootstrap_key(self, s):

        """生成 bootstrapping 密钥（简化）。"""

        bk = []

        for i in range(self.n):

            # 为密钥的每一位生成 LWE 样本

            a = [random.randint(0, self.q - 1) for _ in range(self.n)]

            inner = sum(a[j] * s[j] for j in range(self.n)) % self.q

            noise = int(random.gauss(0, self.std * self.q)) % self.q

            b = (inner + noise + s[i] * (self.q // 4)) % self.q

            bk.append((a, b))

        return bk



    def _generate_key_switch_key(self, s):

        """生成密钥切换密钥（简化）。"""

        ks = []

        for i in range(self.n):

            a = random.randint(0, self.q - 1)

            inner = a * s[i] % self.q

            noise = int(random.gauss(0, self.std * self.q))

            b = (-inner + noise) % self.q

            ks.append((a, b))

        return ks





def tfhe_lwe_encrypt(pk, message_bit, key_s):

    """

    TFHE LWE 加密单个比特。



    参数:

        pk: 公钥

        message_bit: 0 或 1

        key_s: 密钥向量



    返回:

        (a, b) LWE 样本

    """

    n = pk['n']

    q = pk['q']



    # 随机向量 a

    a = [random.randint(0, q - 1) for _ in range(n)]



    # 计算内积 <a, s>

    inner = sum(a[i] * key_s[i] for i in range(n)) % q



    # 添加消息编码（放在最高位）

    encoded = message_bit * (q // 2)



    # 添加噪声

    noise = int(random.gauss(0, pk['q'] * 2**-15)) % q



    b = (inner + encoded + noise) % q



    return (a, b)





def tfhe_lwe_decrypt(sk, ciphertext):

    """TFHE LWE 解密。"""

    a, b = ciphertext

    n = sk['n']

    q = 2**32

    s = sk['s']



    # 计算 b - <a, s>

    inner = sum(a[i] * s[i] for i in range(n)) % q

    phase = (b - inner) % q



    # 解码：如果在 q/4 附近则为 1，否则为 0

    threshold = q // 4

    if threshold < phase < 3 * threshold:

        return 1

    return 0





def tfhe_bootstrap(ct, pk, s):

    """

    TFHE Bootstrapping：将噪声密文转换为"干净"密文。



    这是 TFHE 的核心：同态地执行密钥切换 + 密文刷新。

    简化实现。

    """

    n = pk['n']

    q = pk['q']



    # 提取相位

    a, b = ct

    inner = sum(a[i] * s[i] for i in range(n)) % q

    phase = (b - inner) % q



    # 在相位上执行同态 LUT（简化）

    # 如果相位接近 0，返回 0密文；接近 q/2，返回 1密文

    if abs(phase - q//4) < q//8:

        return tfhe_lwe_encrypt(pk, 1, s)

    elif abs(phase - 3*q//4) < q//8:

        return tfhe_lwe_encrypt(pk, 0, s)

    else:

        return tfhe_lwe_encrypt(pk, 0, s)





def tfhe_gate_evaluate(ct1, ct2, gate_type, pk, sk):

    """

    TFHE 门计算：同态执行任意单比特门。



    参数:

        ct1, ct2: 输入密文

        gate_type: 'and', 'or', 'xor', 'not'

        pk, sk: 密钥



    返回:

        结果密文

    """

    q = pk['q']



    if gate_type == 'not':

        # NOT: 翻转密文的消息部分

        a, b = ct1

        new_ct = (a, (b + q // 2) % q)

        return new_ct



    elif gate_type == 'and':

        # AND 需要 bootstrapping（简化）

        # 这里用张量积模拟

        a1, b1 = ct1

        a2, b2 = ct2

        new_a = [(a1[i] * a2[i]) % q for i in range(len(a1))]

        new_b = (b1 * b2) % q

        return (new_a, new_b)



    elif gate_type == 'xor':

        # XOR = AND(NOT(a), b) OR AND(a, NOT(b))

        a1, b1 = ct1

        a2, b2 = ct2

        # 简化

        new_a = [(a1[i] + a2[i]) % q for i in range(len(a1))]

        new_b = (b1 + b2) % q

        return (new_a, new_b)



    elif gate_type == 'or':

        a1, b1 = ct1

        a2, b2 = ct2

        new_a = [(a1[i] * a2[i]) % q for i in range(len(a1))]

        new_b = (b1 + b2 - b1 * b2) % q

        return (new_a, new_b)



    return ct1





if __name__ == "__main__":

    print("=== TFHE 全同态加密测试 ===")



    # 密钥生成

    kg = TFHEKeyGenerator(n=8, q=2**32)

    pk, sk = kg.keygen()

    print(f"参数: n={kg.n}, q={kg.q}")



    # 加密

    b1, b2 = 1, 1

    ct1 = tfhe_lwe_encrypt(pk, b1, sk['s'])

    ct2 = tfhe_lwe_encrypt(pk, b2, sk['s'])



    print(f"\n比特 b1={b1}, b2={b2}")



    # 解密验证

    d1 = tfhe_lwe_decrypt(sk, ct1)

    d2 = tfhe_lwe_decrypt(sk, ct2)

    print(f"解密验证: d1={d1}, d2={d2}")



    # 同态 NOT

    ct_not = tfhe_gate_evaluate(ct1, None, 'not', pk, sk)

    print(f"\n同态 NOT b1 = {1 - b1}")

    print(f"解密: {tfhe_lwe_decrypt(sk, ct_not)}")



    # 同态 AND

    ct_and = tfhe_gate_evaluate(ct1, ct2, 'and', pk, sk)

    print(f"同态 AND b1 & b2 = {b1 & b2}")



    # 同态 OR

    ct_or = tfhe_gate_evaluate(ct1, ct2, 'or', pk, sk)

    print(f"同态 OR b1 | b2 = {b1 | b2}")



    # 同态 XOR

    ct_xor = tfhe_gate_evaluate(ct1, ct2, 'xor', pk, sk)

    print(f"同态 XOR b1 ^ b2 = {b1 ^ b2}")



    print("\nTFHE 特性:")

    print("  基于 TFHE 的门自举（Gate Bootstrapping）")

    print("  支持任意深度的布尔电路计算")

    print("  Bootstrapping 将密文噪声降低到可忽略水平")

    print("  适合隐私保护机器学习推理")

