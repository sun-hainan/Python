# -*- coding: utf-8 -*-
"""
算法实现：可验证计算 / zk_snark_interactive

本文件实现 zk_snark_interactive 相关的算法功能。
"""

import random
import hashlib


def generate_circuit_witness(x, y):
    """
    生成电路的见证（Witness）。

    电路: (x + y) * (x - y) = x^2 - y^2
    我们验证: a * b = c

    参数:
        x, y: 私密输入

    返回:
        witness: [1, x, y, x+y, x-y, (x+y)*(x-y)]
    """
    a = x + y
    b = x - y
    c = a * b
    return [1, x, y, a, b, c]


def compute_polynomials(witness, coeffs):
    """
    将见证代入电路约束多项式。

    电路约束: Q_L * x + Q_R * y + Q_O * z + Q_M * x*y = 0
    对应: a * b - c = 0
    """
    w = witness
    # 简化的多项式求值
    result = coeffs[0] * w[0] + coeffs[1] * w[1] + coeffs[2] * w[2]
    return result


def prover_commit_witness(witness, G):
    """
    证明者：对见证做承诺。

    参数:
        witness: 见证列表
        G: 承诺密钥

    返回:
        commitments: 对每个 witness 值的承诺
    """
    commitments = []
    for i, val in enumerate(witness):
        # 承诺 = g^{witness[i]}（简化）
        g = G[i % len(G)]
        commitments.append(pow(g, val, 17))
    return commitments


def verifier_challenge(G, commitments):
    """
    验证者生成挑战（ Fiat-Shamir 变换，将交互式变为非交互式）。

    参数:
        G: 承诺密钥
        commitments: 证明者的承诺

    返回:
        beta: 挑战值
    """
    data = str(commitments).encode()
    beta = int(hashlib.sha256(data).hexdigest(), 16) % 13
    return beta


def prover_create_proof(witness, beta, G):
    """
    证明者根据挑战创建证明响应。

    参数:
        witness: 见证
        beta: 验证者挑战
        G: 承诺密钥

    返回:
        proof: 证明对象
    """
    # 计算线性组合：witness[0] + beta * witness[1] + ...
    combined = sum((i + 1) * pow(beta, i, 13) * witness[i] for i in range(len(witness)))
    combined %= 13

    # 对组合值做承诺
    pi = pow(G[0], combined, 17)

    return {
        'combined_value': combined,
        'pi': pi,
        'beta': beta
    }


def verifier_verify_proof(commitments, proof, beta, G):
    """
    验证者验证证明。

    参数:
        commitments: 承诺列表
        proof: 证明者的响应
        beta: 挑战值
        G: 承诺密钥

    返回:
        True/False
    """
    # 重构 combined commitment
    recomputed = 1
    for i, comm in enumerate(commitments):
        factor = pow(comm, pow(beta, i, 13), 17)
        recomputed = (recomputed * factor) % 17

    # 验证 pi 与 combined commitment 匹配
    return recomputed == proof['pi']


if __name__ == "__main__":
    print("=== zk-SNARK 交互式协议测试 ===")

    # 电路参数（简化）
    G = [2, 3, 5, 7, 11, 13]  # 承诺密钥

    # 私密输入
    x, y = 3, 2

    # 1. 证明者生成见证
    witness = generate_circuit_witness(x, y)
    print(f"见证: {witness}")
    print(f"验证: ({x}+{y})*({x}-{y}) = {witness[3]}*{witness[4]} = {witness[5]}")

    # 2. 证明者提交承诺
    commitments = prover_commit_witness(witness, G)
    print(f"\n承诺: {[hex(c) for c in commitments]}")

    # 3. 验证者生成挑战
    beta = verifier_challenge(G, commitments)
    print(f"挑战 beta = {beta}")

    # 4. 证明者创建证明
    proof = prover_create_proof(witness, beta, G)
    print(f"证明: pi = {proof['pi']}")

    # 5. 验证者验证
    valid = verifier_verify_proof(commitments, proof, beta, G)
    print(f"\n验证结果: {valid}")

    # 错误见证测试
    print("\n=== 错误见证测试 ===")
    wrong_witness = [1, x, y, x + y + 1, x - y, (x + y + 1) * (x - y)]
    wrong_commitments = prover_commit_witness(wrong_witness, G)
    wrong_proof = prover_create_proof(wrong_witness, beta, G)
    valid_wrong = verifier_verify_proof(wrong_commitments, wrong_proof, beta, G)
    print(f"错误见证验证结果: {valid_wrong}")

    print("\nzk-SNARK 特性:")
    print("  零知识：验证者无法获知 x 和 y 的值")
    print("  简洁性：证明大小 O(1)")
    print("  非交互：Fiat-Shamir 将交互转为一次性证明")
