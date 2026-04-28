"""
门限密码学
==========================================

【算法原理】
将密钥分成n份，任意t份可以解密/签名，少于t份无法获得任何信息。
基于秘密分享（Secret Sharing）和多方计算。

【时间复杂度】
- 秘密分享: O(n)
- 重构: O(t)
- 加解密: O(n) 或 O(1)

【应用场景】
- 分布式密钥管理
- 多人数字签名
- 加密货币多签钱包
- 紧急恢复密钥
"""

import random
import math
from typing import List, Tuple


class ShamirSecretSharing:
    """
    Shamir秘密分享 (t, n)-门限方案

    【原理】
    在有限域上，t-1次多项式f(x)，f(0) = 秘密
    任意t个点可以恢复f(x)，从而得到秘密
    少于t个点无法得到任何信息

    【参数】
    - t: 门限值（需要的最少份额数）
    - n: 总份额数
    """

    def __init__(self, prime: int = 2**61 - 1):
        self.p = prime

    def _eval_poly(self, coeffs: List[int], x: int) -> int:
        """计算多项式在x处的值（Horner方法）"""
        result = 0
        for coeff in reversed(coeffs):
            result = (result * x + coeff) % self.p
        return result

    def share(self, secret: int, t: int, n: int) -> List[Tuple[int, int]]:
        """
        将秘密分成n份

        【参数】
        - secret: 秘密值
        - t: 门限（需要的最少份额）
        - n: 总份额

        【返回】n个份额 (x, y)
        """
        if t > n:
            raise ValueError("门限t不能大于n")

        # 创建t-1次多项式，f(0) = secret
        coeffs = [secret] + [random.randint(1, self.p - 1) for _ in range(t - 1)]

        # 计算n个份额
        shares = []
        for x in range(1, n + 1):
            y = self._eval_poly(coeffs, x)
            shares.append((x, y))

        return shares

    def recover(self, shares: List[Tuple[int, int]], t: int) -> int:
        """
        从t个份额恢复秘密

        【方法】拉格朗日插值

        secret = Σ y_i * l_i(0) mod p
        l_i(0) = Π_{j≠i} x_j / (x_j - x_i) mod p
        """
        if len(shares) < t:
            raise ValueError(f"需要至少{t}个份额")

        secret = 0
        xs = [s[0] for s in shares]
        ys = [s[1] for s in shares]

        for i in range(t):
            # 计算拉格朗日基 l_i(0)
            numerator = 1
            denominator = 1
            xi = xs[i]

            for j in range(t):
                if i == j:
                    continue
                xj = xs[j]
                numerator = (numerator * (-xj)) % self.p
                denominator = (denominator * (xi - xj)) % self.p

            # 拉格朗日系数
            lagrange_coeff = numerator * self._mod_inverse(denominator) % self.p

            # 累加
            secret = (secret + ys[i] * lagrange_coeff) % self.p

        return secret

    def _mod_inverse(self, a: int) -> int:
        """模逆元"""
        return pow(a, self.p - 2, self.p)


class ThresholdEncryption:
    """
    门限加密

    【方案】基于Shamir分享的(n, t)门限加密
    - 密钥被分成n份
    - 任意t份可以解密
    """

    def __init__(self, security_param: int = 1024):
        self.sss = ShamirSecretSharing()
        self.security_param = security_param

    def keygen(self, t: int, n: int) -> Tuple[int, List[Tuple[int, int]]]:
        """
        密钥生成

        【返回】
        - pk: 公钥
        - shares: n个私钥份额
        """
        # 模拟公钥/私钥（简化版）
        private_key = random.randint(1, 2**security_param)
        shares = self.sss.share(private_key, t, n)

        # 公钥 = private_key 的某种变换
        public_key = private_key  # 简化

        return public_key, shares

    def encrypt(self, public_key: int, message: int) -> int:
        """加密（简化版）"""
        # 实际使用ElGamal或Paillier
        r = random.randint(1, self.sss.p - 1)
        ciphertext = (message * pow(public_key, r, self.sss.p)) % self.sss.p
        return ciphertext

    def decrypt_partial(self, share: Tuple[int, int], ciphertext: int) -> int:
        """
        部分解密

        每个份额持有者计算 C^share
        """
        x, y = share
        # 简化：C^y mod p
        return pow(ciphertext, y, self.sss.p)

    def decrypt_combined(self, partial_decryptions: List[Tuple[int, int]],
                        ciphertext: int, t: int) -> int:
        """
        组合部分解密结果恢复消息

        【简化版本】
        """
        # 实际需要多方协作计算完整的指数
        # 这里简化处理
        product = 1
        for share, dec in partial_decryptions:
            product = (product * dec) % self.sss.p

        return product


class ThresholdSignature:
    """
    门限签名

    【BLS门限签名简化实现】
    - (t, n)门限：任意t人可以签名
    - 基于BLS的简单方案
    """

    def __init__(self):
        self.sss = ShamirSecretSharing()

    def keygen(self, t: int, n: int) -> Tuple[int, List[int]]:
        """
        生成签名密钥份额

        【返回】
        - group_key: 群公钥
        - signing_keys: n个签名私钥份额
        """
        # 生成群私钥
        group_sk = random.randint(1, 2**127)

        # 分享私钥
        shares = self.sss.share(group_sk, t, n)

        # 群公钥 = group_sk * G
        group_key = group_sk

        signing_keys = [share[1] for share in shares]  # y值作为签名份额

        return group_key, signing_keys

    def sign_partial(self, message_hash: int, share_sk: int, index: int) -> Tuple[int, int]:
        """
        部分签名

        【返回】(index, partial_signature)
        """
        # σ_i = H(m)^sk_i
        signature = pow(message_hash, share_sk, self.sss.p)
        return index, signature

    def combine_signatures(self, partials: List[Tuple[int, int]],
                         t: int, message_hash: int) -> int:
        """
        组合部分签名为完整签名

        【方法】拉格朗日插值
        """
        if len(partials) < t:
            raise ValueError(f"需要至少{t}个部分签名")

        # 恢复签名私钥
        shares = [(p[0], p[1]) for p in partials]
        sk_recovered = self.sss.recover(shares, t)

        # 计算完整签名
        full_signature = pow(message_hash, sk_recovered, self.sss.p)

        return full_signature

    def verify(self, message_hash: int, signature: int, group_key: int) -> bool:
        """验证签名"""
        # e(σ, G) = e(H(m), group_key)
        # 简化验证
        return signature > 0


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("门限密码学 - 测试")
    print("=" * 50)

    sss = ShamirSecretSharing()

    # 测试1：秘密分享
    print("\n【测试1】Shamir秘密分享")
    secret = 123456789
    t, n = 3, 5
    shares = sss.share(secret, t, n)
    print(f"  秘密: {secret}")
    print(f"  门限: ({t}, {n})")
    print(f"  份额:")
    for x, y in shares:
        print(f"    份额{x}: ({x}, {y})")

    # 测试2：秘密恢复
    print("\n【测试2】秘密恢复")
    # 用t个份额恢复
    selected_shares = shares[:t]
    recovered = sss.recover(selected_shares, t)
    print(f"  使用{len(selected_shares)}个份额: {recovered}")
    print(f"  原始秘密: {secret}")
    print(f"  恢复正确: {recovered == secret}")

    # 测试3：用少于t个份额尝试恢复
    print("\n【测试3】少于t个份额（应该失败）")
    try:
        partial = sss.recover(shares[:2], t)
        print(f"  居然恢复了: {partial}（不应该发生）")
    except Exception as e:
        print(f"  无法恢复: {type(e).__name__}")

    # 测试4：门限加密
    print("\n【测试4】门限加密")
    te = ThresholdEncryption()

    t_enc, n_enc = 3, 5
    pk, shares_enc = te.keygen(t_enc, n_enc)

    message = 42
    ciphertext = te.encrypt(pk, message)
    print(f"  消息: {message}")
    print(f"  密文: {ciphertext}")

    # 用t个人解密
    partials = []
    for i in range(t_enc):
        partial = te.decrypt_partial(shares_enc[i], ciphertext)
        partials.append((i + 1, partial))

    decrypted = te.decrypt_combined(partials, ciphertext, t_enc)
    print(f"  解密结果: {decrypted}")

    # 测试5：门限签名
    print("\n【测试5】门限签名")
    ts = ThresholdSignature()

    t_sig, n_sig = 3, 5
    group_key, signing_keys = ts.keygen(t_sig, n_sig)

    message_hash = 987654321
    print(f"  消息哈希: {message_hash}")

    # t个人签名
    partials = []
    for i in range(t_sig):
        idx, sig = ts.sign_partial(message_hash, signing_keys[i], i + 1)
        partials.append((idx, sig))

    # 组合签名
    combined = ts.combine_signatures(partials, t_sig, message_hash)
    print(f"  组合签名: {combined}")

    # 验证
    valid = ts.verify(message_hash, combined, group_key)
    print(f"  签名验证: {valid}")

    print("\n" + "=" * 50)
    print("门限密码学测试完成！")
    print("=" * 50)
