# -*- coding: utf-8 -*-
"""
算法实现：可验证计算 / vrf_verifiable_random

本文件实现 vrf_verifiable_random 相关的算法功能。
"""

import hashlib
import random


def generate_rsa_keypair(bits=64):
    """
    生成 RSA 密钥对（简化版，实际使用大素数）。

    参数:
        bits: 密钥位数（这里用小数字便于演示）

    返回:
        (public_key, private_key)
    """
    # 简化的素数（实际应用中使用大素数）
    p = 61
    q = 53
    n = p * q          # 3233
    phi = (p - 1) * (q - 1)
    e = 17             # 公开指数
    d = pow(e, -1, phi)  # 模逆

    pk = (n, e)
    sk = (n, d)
    return pk, sk


def vrf_prove(sk, alpha):
    """
    计算 VRF 证明。

    VRF(sk, alpha) = RSA-DH(sk, H(alpha)) 的哈希

    参数:
        sk: 私钥 (n, d)
        alpha: 输入字节串
        d: 私钥指数

    返回:
        (beta, pi): VRF 输出 beta 和证明 pi
    """
    n, d = sk

    # 将输入哈希为域元素
    h = int(hashlib.sha256(alpha.encode()).hexdigest(), 16) % n

    # 计算 RSA 签名（伪随机输出）
    r = pow(h, d, n)

    # VRF 输出：对签名做哈希
    beta = hashlib.sha256(str(r).encode()).hexdigest()

    # 证明就是 RSA 签名值本身
    pi = r

    return beta, pi


def vrf_verify(pk, alpha, beta, pi):
    """
    验证 VRF 证明。

    参数:
        pk: 公钥 (n, e)
        alpha: 输入
        beta: 声称的 VRF 输出
        pi: 证明（RSA 签名）

    返回:
        True/False
    """
    n, e = pk

    # 重新计算 h = H(alpha)
    h = int(hashlib.sha256(alpha.encode()).hexdigest(), 16) % n

    # 验证 pi 是正确的 RSA 签名：h == pi^e mod n
    recomputed = pow(pi, e, n)

    if recomputed != h:
        return False

    # 重新计算 beta
    expected_beta = hashlib.sha256(str(pi).encode()).hexdigest()

    return expected_beta == beta


if __name__ == "__main__":
    print("=== VRF 可验证随机数测试 ===")

    # 生成密钥对
    pk, sk = generate_rsa_keypair()
    print(f"公钥 n = {pk[0]}, e = {pk[1]}")
    print(f"私钥 d = {sk[1]}")

    # 测试多个输入
    test_inputs = ["hello", "world", "test123", "random_seed"]

    print("\nVRF 计算结果:")
    for alpha in test_inputs:
        beta, pi = vrf_prove(sk, alpha)
        print(f"\n输入: {alpha}")
        print(f"  beta (前16字符): {beta[:16]}...")
        print(f"  pi: {pi}")

        # 验证
        valid = vrf_verify(pk, alpha, beta, pi)
        print(f"  验证结果: {valid}")

    # 不一致性测试
    print("\n=== 不一致输入测试 ===")
    beta, pi = vrf_prove(sk, "test")
    # 尝试用错误输入验证
    valid_wrong = vrf_verify(pk, "wrong_input", beta, pi)
    print(f"错误输入验证结果: {valid_wrong}")

    # 尝试用错误 beta 验证
    valid_beta = vrf_verify(pk, "test", "fake_beta" + beta[8:], pi)
    print(f"错误 beta 验证结果: {valid_beta}")

    print("\nVRF 特性:")
    print("  唯一性：每个输入对应唯一输出")
    print("  伪随机性：输出看起来随机（无私钥无法预测）")
    print("  可验证性：任何人都能用公钥验证证明正确性")
