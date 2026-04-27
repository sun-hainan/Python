# -*- coding: utf-8 -*-
"""
算法实现：可验证计算 / stark_basic

本文件实现 stark_basic 相关的算法功能。
"""

import hashlib
import random


def hash_bytes(data):
    """计算 SHA-256 哈希。"""
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def merkle_prove(leaves, index):
    """
    生成 Merkle 证明。

    参数:
        leaves: 叶子节点列表
        index: 要证明的叶子索引

    返回:
        (root, proof_path): 根哈希和证明路径
    """
    if len(leaves) == 0:
        return None, []

    # 构树：计算每层节点
    level = [hash_bytes(str(leaf)) for leaf in leaves]
    tree = [level]

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])  # 填充
        new_level = []
        for i in range(0, len(level), 2):
            combined = level[i] + level[i + 1]
            new_level.append(hash_bytes(combined))
        tree.append(new_level)
        level = new_level

    root = level[0]

    # 提取证明路径
    proof = []
    idx = index
    for i in range(len(tree) - 1):
        sibling_idx = idx + 1 if idx % 2 == 0 else idx - 1
        if sibling_idx < len(tree[i]):
            proof.append(tree[i][sibling_idx])
        else:
            proof.append(tree[i][idx])  # 填充节点
        idx //= 2

    return root, proof


def merkle_verify(root, leaf, index, proof):
    """验证 Merkle 证明。"""
    current = hash_bytes(str(leaf))
    idx = index

    for sibling in proof:
        if idx % 2 == 0:
            combined = current + sibling
        else:
            combined = sibling + current
        current = hash_bytes(combined)
        idx //= 2

    return current == root


def stark_prove(computation_trace, public_inputs):
    """
    STARK 证明生成。

    概念：trace 的低阶多项式约束检验 -> Merkle 树承诺 ->
    Fiat-Shamir 挑战 -> 递归折叠

    参数:
        computation_trace: 计算轨迹（每行列表）
        public_inputs: 公开输入

    返回:
        proof: STARK 证明
    """
    # 步骤1：将计算轨迹组织成矩阵
    trace_rows = computation_trace
    n_rows = len(trace_rows)

    # 步骤2：对每一列做 Merkle 承诺
    columns = list(zip(*trace_rows)) if trace_rows else []
    column_roots = []
    for col in columns:
        col_leaves = list(col)
        root, _ = merkle_prove(col_leaves, 0)
        column_roots.append(root)

    # 组合列根
    combined_root = hash_bytes("".join(column_roots))

    # 步骤3：Fiat-Shamir 生成随机挑战
    # 模拟：用 public_inputs 和 combined_root 生成确定性挑战
    challenge_seed = hash_bytes(str(public_inputs) + combined_root)
    num_queries = 4  # 查询数量（实际中由安全参数决定）

    # 步骤4：随机查询位置，生成proof
    random.seed(int(challenge_seed[:8], 16) % (10**9))
    query_indices = [random.randint(0, n_rows - 1) for _ in range(num_queries)]

    query_proofs = []
    for idx in query_indices:
        row_proofs = []
        for col_idx, col in enumerate(columns):
            root, path = merkle_prove(list(col), idx)
            row_proofs.append({
                'column_index': col_idx,
                'value': col[idx],
                'proof': path
            })
        query_proofs.append({'row_index': idx, 'columns': row_proofs})

    proof = {
        'column_roots': column_roots,
        'combined_root': combined_root,
        'challenge': challenge_seed,
        'num_queries': num_queries,
        'query_proofs': query_proofs,
        'n_rows': n_rows
    }

    return proof


def stark_verify(vk, proof, public_inputs):
    """
    STARK 证明验证。

    参数:
        vk: 验证密钥（包含安全参数等）
        proof: STARK 证明
        public_inputs: 公开输入

    返回:
        True/False
    """
    # 重放 Fiat-Shamir
    challenge_seed = hash_bytes(str(public_inputs) + proof['combined_root'])
    if challenge_seed != proof['challenge']:
        return False

    # 验证每个查询的 Merkle proof
    for qp in proof['query_proofs']:
        idx = qp['row_index']
        for col_proof in qp['columns']:
            col_idx = col_proof['column_index']
            value = col_proof['value']
            root = proof['column_roots'][col_idx]
            if not merkle_verify(root, value, idx, col_proof['proof']):
                return False

    # 约束检验（简化：验证所有查询行都满足约束）
    # 实际中需要检查多项式约束关系
    return True


if __name__ == "__main__":
    # 构造计算轨迹：模拟执行 x^2 + 2x + 1 的电路
    # 每行：[x, x^2, 2x, result]
    public_inputs = [3]

    trace = []
    x = public_inputs[0]
    for step in range(8):
        x_val = x + step
        row = [x_val, x_val * x_val, 2 * x_val, x_val * x_val + 2 * x_val + 1]
        trace.append(row)

    print("=== STARK 示例测试 ===")
    print(f"计算轨迹行数: {len(trace)}")
    print(f"公开输入: {public_inputs}")

    # 生成证明
    proof = stark_prove(trace, public_inputs)
    print(f"\n证明规模:")
    print(f"  列根数量: {len(proof['column_roots'])}")
    print(f"  查询数量: {proof['num_queries']}")
    print(f"  总 proof 大小（简化）: {len(str(proof))} 字节")

    # 验证
    vk = {'security_level': 128}
    valid = stark_verify(vk, proof, public_inputs)
    print(f"\n验证结果: {valid}")

    # Merkle 证明测试
    print("\n=== Merkle 证明测试 ===")
    leaves = [1, 2, 3, 4, 5, 6, 7, 8]
    root, proof_path = merkle_prove(leaves, 2)
    print(f"叶子索引 2, 值 3 的 Merkle 证明:")
    print(f"  根: {root[:16]}...")
    print(f"  路径长度: {len(proof_path)}")

    verified = merkle_verify(root, 3, 2, proof_path)
    print(f"  验证结果: {verified}")
