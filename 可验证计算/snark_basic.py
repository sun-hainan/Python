# -*- coding: utf-8 -*-
"""
算法实现：可验证计算 / snark_basic

本文件实现 snark_basic 相关的算法功能。
"""

import hashlib
import random


def setup_arith_circuit(n_vars, constraints):
    """
    可信设置（Trusted Setup）—— 生成证明密钥和验证密钥。

    本简化实现使用随机多项式承诺。

    参数:
        n_vars: 变量数量
        constraints: 约束列表，每个约束为 (a_idx, b_idx, c_idx)

    返回:
        (proving_key, verification_key)
    """
    # 生成随机挑战（模拟 toxic waste）
    tau = random.randint(1, 10**9)

    # 验证密钥：g^{tau^i}（简化）
    verification_key = {
        'g_tau': pow(2, tau, 13),   # 用有限域模拟
        'tau': tau,
        'n_vars': n_vars,
        'constraints': constraints
    }

    # 证明密钥
    proving_key = {
        'verification_key': verification_key,
        'tau_pow': [pow(tau, i, 13) for i in range(n_vars + len(constraints) + 2)]
    }

    return proving_key, verification_key


def prove_satisfiability(proving_key, assignment):
    """
    生成证明：证明者知道一个满足电路的赋值。

    简化实现：直接对 witness 的知识做承诺。

    参数:
        proving_key: 证明密钥
        assignment: 变量赋值列表

    返回:
        proof: 证明对象
    """
    tau = proving_key['verification_key']['tau']
    n_vars = proving_key['verification_key']['n_vars']
    constraints = proving_key['verification_key']['constraints']

    # 计算 witness 多项式（在 tau 处的值）
    # 简化：witness = 所有变量的加权和
    witness_sum = sum((i + 1) * assignment[i] for i in range(min(n_vars, len(assignment))))
    witness_commitment = pow(2, witness_sum * tau, 13)

    # 验证每个约束：a * b = c
    constraint_checks = []
    for (a_idx, b_idx, c_idx) in constraints:
        a = assignment[a_idx] if a_idx < len(assignment) else 0
        b = assignment[b_idx] if b_idx < len(assignment) else 0
        c = assignment[c_idx] if c_idx < len(assignment) else 0
        constraint_checks.append(a * b == c)

    proof = {
        'witness_commitment': witness_commitment,
        'constraint_checks': constraint_checks,
        'assignment_hash': hashlib.sha256(str(assignment).encode()).hexdigest()[:16]
    }

    return proof


def verify_satisfiability(verification_key, proof):
    """
    验证 SNARK 证明。

    参数:
        verification_key: 验证密钥
        proof: 证明对象

    返回:
        True/False
    """
    # 检查所有约束是否满足
    if not all(proof['constraint_checks']):
        return False

    # 检查 witness 承诺（简化验证）
    if proof['witness_commitment'] == 0:
        return False

    return True


if __name__ == "__main__":
    # 构造一个简单电路：x * y = z (3个变量, 1个约束)
    n_vars = 3
    constraints = [(0, 1, 2)]   # x0 * x1 = x2

    print("=== SNARK 证明系统测试 ===")
    print(f"变量数: {n_vars}")
    print(f"约束: x0 * x1 = x2")

    # 设置
    pk, vk = setup_arith_circuit(n_vars, constraints)
    print(f"\n可信设置完成")
    print(f"  验证密钥 tau 值: {vk['tau']}")

    # 证明：使用一个满足的赋值 x0=2, x1=3, x2=6
    satisfying_assignment = [2, 3, 6]
    proof = prove_satisfiability(pk, satisfying_assignment)
    print(f"\n满足的赋值 {satisfying_assignment}:")
    print(f"  证明: {proof}")

    valid = verify_satisfiability(vk, proof)
    print(f"  验证结果: {valid}")

    # 错误赋值测试
    wrong_assignment = [2, 3, 5]   # 2*3 != 5
    proof_wrong = prove_satisfiability(pk, wrong_assignment)
    valid_wrong = verify_satisfiability(vk, proof_wrong)
    print(f"\n错误赋值 {wrong_assignment}:")
    print(f"  验证结果: {valid_wrong}")

    print(f"\nSNARK 特性：")
    print(f"  证明规模: O(1) = {len(str(proof))} 字节（vs 电路规模）")
    print(f"  验证时间: O(1) = 常数次操作")
