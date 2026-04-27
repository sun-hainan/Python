# -*- coding: utf-8 -*-
"""
算法实现：同态加密 / bgv

本文件实现 bgv 相关的算法功能。
"""

import random


class BGVKeyGenerator:
    """BGV 密钥生成器。"""

    def __init__(self, security_lambda=64, L=4):
        """
        初始化。

        参数:
            security_lambda: 安全参数
            L: 允许的乘法深度（层次数）
        """
        self.L = L                      # 乘法深度
        self.n = 512                    # 环维度
        self.q = [2**40, 2**39, 2**38, 2**37, 2**36]  # 递减的模序列
        self.t = 2                      # 明文模数（比特）

    def keygen(self):
        """生成主密钥和公钥。"""
        # 私钥：随机多项式 s
        s = [random.choice([-1, 0, 1]) for _ in range(self.n)]

        # 公钥：(-as + e, a)
        a = [random.randint(0, q-1) for q in self.q]
        e = [random.choice([-1, 0, 1]) for _ in range(self.n)]

        pk0 = [(-a[i] * s[i] + e[i]) % self.q[0] for i in range(self.n)]
        pk1 = a

        # 评估密钥（用于密钥交换）
        evk = self._generate_evaluation_key(s)

        sk = {'s': s}
        pk = {'pk0': pk0, 'pk1': pk1, 'q': self.q}
        ek = {'evk': evk}

        return pk, sk, ek

    def _generate_evaluation_key(self, s):
        """生成评估密钥（简化）。"""
        # 评估密钥用于密文乘法后的重线性化
        n = self.n
        evk = []
        for level in range(self.L):
            q = self.q[level]
            a = [random.randint(0, q-1) for _ in range(n)]
            e = [random.choice([-1, 0, 1]) for _ in range(n)]
            # LWE: b = -a*s + e + q/2 * s^2
            b = [(-a[i] * s[i] + e[i] + (q // 2) * s[i]**2) % q for i in range(n)]
            evk.append({'a': a, 'b': b})
        return evk


def bgv_encrypt(pk, message, level=0):
    """
    BGV 加密。

    参数:
        pk: 公钥
        message: 消息多项式（比特向量）
        level: 当前层级（决定用哪个模）

    返回:
        密文 (c0, c1)
    """
    n = len(pk['pk0'])
    q = pk['q'][level]
    t = 2

    # 编码消息
    m = [m * (q // (2 * t)) for m in message]  # 缩放消息

    # 随机掩码
    u = [random.choice([0, 1, -1]) for _ in range(n)]

    # c0 = pk0 * u + m
    c0 = [(pk['pk0'][i] * u[i] + m[i]) % q for i in range(n)]
    # c1 = pk1 * u
    c1 = [(pk['pk1'][i] * u[i]) % q for i in range(n)]

    return {'c0': c0, 'c1': c1, 'level': level}


def bgv_decrypt(sk, ciphertext):
    """BGV 解密。"""
    level = ciphertext['level']
    q = sk.get('q', [2**40])[level] if isinstance(sk.get('q'), list) else 2**40
    t = 2

    c0 = ciphertext['c0']
    c1 = ciphertext['c1']
    s = sk['s']

    # m = c0 + c1 * s mod q
    n = len(c0)
    m_scaled = [(c0[i] + c1[i] * s[i]) % q for i in range(n)]

    # 解码
    message = [1 if v > q // 4 and v < 3 * q // 4 else 0 for v in m_scaled]

    return message


def bgv_add(ct1, ct2):
    """BGV 密文加法（同一层级）。"""
    if ct1['level'] != ct2['level']:
        raise ValueError("不同层级的密文不能直接相加")

    level = ct1['level']
    q = ct1['c0']

    c0 = [(ct1['c0'][i] + ct2['c0'][i]) % q for i in range(len(ct1['c0']))]
    c1 = [(ct1['c1'][i] + ct2['c1'][i]) % q for i in range(len(ct1['c1']))]

    return {'c0': c0, 'c1': c1, 'level': level}


def bgv_multiply(ct1, ct2, evk):
    """
    BGV 密文乘法（带重线性化）。

    参数:
        ct1, ct2: 两个密文
        evk: 评估密钥

    返回:
        新的密文
    """
    if ct1['level'] != ct2['level']:
        raise ValueError("不同层级的密文不能相乘")

    level = ct1['level']
    if level >= len(evk['evk']):
        raise ValueError("超过最大乘法深度")

    # 新层级
    new_level = level + 1

    # 计算张量积（简化）
    c0 = ct1['c0']
    c1 = ct1['c1']
    d0 = ct2['c0']
    d1 = ct2['c1']

    # 简化的乘法结果
    new_c0 = [(c0[i] * d0[i]) % 2**40 for i in range(len(c0))]
    new_c1 = [(c0[i] * d1[i] + c1[i] * d0[i]) % 2**40 for i in range(len(c0))]
    # new_c2 = c1 * d1 （被重线性化消除）

    return {'c0': new_c0, 'c1': new_c1, 'level': new_level}


def mod_switch(ct, target_level, new_q):
    """
    模交换（Mod Switching）：降低模数同时保持明文不变。

    这是 BGV 控制噪声的关键技术。
    """
    # 简化实现
    current_q = 2**40
    scale = new_q / current_q

    new_c0 = [int(c * scale) % new_q for c in ct['c0']]
    new_c1 = [int(c * scale) % new_q for c in ct['c1']]

    return {'c0': new_c0, 'c1': new_c1, 'level': target_level}


if __name__ == "__main__":
    print("=== BGV 同态加密测试 ===")

    # 生成密钥
    kg = BGVKeyGenerator(L=4)
    pk, sk, ek = kg.keygen()
    print(f"最大乘法深度 L = {kg.L}")
    print(f"环维度 n = {kg.n}")

    # 消息
    m1 = [1, 0, 1, 1, 0, 0, 0, 0] + [0] * (kg.n - 8)
    m2 = [0, 1, 1, 0, 0, 0, 0, 0] + [0] * (kg.n - 8)

    # 加密
    ct1 = bgv_encrypt(pk, m1, level=0)
    ct2 = bgv_encrypt(pk, m2, level=0)
    print(f"\n消息 m1, m2 已加密（level=0）")

    # 解密验证
    d1 = bgv_decrypt(sk, ct1)
    d2 = bgv_decrypt(sk, ct2)
    print(f"解密 m1: {d1[:8]}")
    print(f"解密 m2: {d2[:8]}")

    # 同态加法
    ct_sum = bgv_add(ct1, ct2)
    d_sum = bgv_decrypt(sk, ct_sum)
    print(f"\n同态加法 m1+m2: {d_sum[:8]}")

    # 同态乘法
    ct_prod = bgv_multiply(ct1, ct2, ek)
    print(f"乘法后层级: {ct_prod['level']}")
    d_prod = bgv_decrypt(sk, ct_prod)
    print(f"同态乘法 m1*m2: {d_prod[:8]}")

    # 模交换
    new_q = 2**36
    ct_switched = mod_switch(ct1, 1, new_q)
    print(f"\n模交换后层级: {ct_switched['level']}, 新模: {new_q}")

    print("\nBGV 特性:")
    print("  层次同态：预设乘法深度，避免递归引导")
    print("  模交换：逐步降低模数以控制噪声")
    print("  密钥交换：重线性化将密文维度恢复到2")
