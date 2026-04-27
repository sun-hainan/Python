# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / distributed_compressed_sensing

本文件实现 distributed_compressed_sensing 相关的算法功能。
"""

import numpy as np



class JointSparsityModel:
    """联合稀疏模型"""

    JSM1 = "jsm1"  # 共享稀疏支撑 + 独立稀疏系数
    JSM2 = "jsm2"  # 所有信号共享同一个稀疏表示（完全相关）
    TJR_S = "tsparse"  # 树结构联合稀疏


@dataclass
class SensorNode:
    """传感器节点"""
    node_id: int
    x_true: np.ndarray       # 原始信号
    A: np.ndarray            # 测量矩阵
    y: np.ndarray             # 测量值
    s_i: int                  # 该节点独立非零元数量
    shared_support: np.ndarray = None  # 共享支撑集


def dcs_jsm1_recover(nodes: List[SensorNode], 
                     s_total: int) -> Tuple[List[np.ndarray], int]:
    """
    分布式压缩感知 - JSM-1恢复算法

    JSM-1模型：
    - 所有信号共享一个稀疏支撑集 S（大小为s）
    - 每个信号 x_j = θ_S + z_j，其中 z_j 是独立稀疏分量

    恢复策略：
    1. 估计共享支撑集
    2. 联合恢复共享系数
    3. 分别恢复独立系数

    输入：
        nodes: 传感器节点列表
        s_total: 总稀疏度（共享+独立）
    输出：
        x_recovered: 恢复的信号列表
        iterations: 迭代次数
    """
    num_nodes = len(nodes)
    n = nodes[0].x_true.shape[0]

    # 收集所有测量
    Y = np.stack([node.y for node in nodes], axis=1)  # (m, num_nodes)
    A_list = [node.A for node in nodes]

    # 步骤1：估计共享支撑集
    # 方法：计算所有残差的平均相关度
    residual = Y.copy()
    support_votes = np.zeros(n)

    for iteration in range(20):
        for j in range(num_nodes):
            # 相关性
            c = nodes[j].A.T @ residual[:, j]

            # 对所有传感器求平均（共享支撑应该有高相关性）
            if iteration == 0:
                support_votes += np.abs(c)
            else:
                support_votes += np.abs(c) * 0.5

    # 选择支持票数最高的
    shared_support = np.argsort(support_votes)[-s_total:]

    # 步骤2：在共享支撑上联合求解
    A_shared = np.stack([A[:, shared_support] for A in A_list], axis=0)

    # 堆叠测量：每个传感器一行
    Y_stacked = Y.flatten().reshape(-1, 1)  # (m * num_nodes, 1)

    # 构建块对角测量矩阵
    A_block = np.zeros((0, s_total))
    for A_j in A_list:
        A_block = np.vstack([A_block, A_j[:, shared_support]])

    # 最小二乘联合求解
    theta_shared, _, _, _ = np.linalg.lstsq(A_block, Y_stacked, rcond=None)
    theta_shared = theta_shared.flatten()

    # 步骤3：独立分量求解
    x_recovered = []
    for j in range(num_nodes):
        # 计算残差（共享分量已去除）
        y_independent = nodes[j].y - nodes[j].A[:, shared_support] @ theta_shared

        # 独立稀疏恢复（OMP）
        x_independent = omp_independent(nodes[j].A, y_independent, nodes[j].s_i)
        x_j = np.zeros(n)
        x_j[shared_support] = theta_shared

        # 合并（简化处理）
        x_recovered.append(x_j)

    return x_recovered, 1


def dcs_jsm2_recover(nodes: List[SensorNode], 
                     s: int) -> Tuple[List[np.ndarray], int]:
    """
    JSM-2恢复：所有信号完全相关（共享稀疏表示）

    模型：x_j = θ * s_j，其中 θ 是公共基，s_j 是系数向量
    """
    num_nodes = len(nodes)
    m = nodes[0].y.shape[0]
    n = nodes[0].x_true.shape[0]

    # 堆叠测量
    Y = np.stack([node.y for node in nodes], axis=1)  # (m, num_nodes)

    # 构建联合测量矩阵
    # 核心思想：用总测量矩阵联合求解
    A_stack = np.vstack([node.A for node in nodes])  # (m*num_nodes, n)
    y_stack = Y.flatten()  # (m*num_nodes,)

    # 协作稀疏恢复
    x_recovered = np.zeros(n)

    # 使用l1范数最小化（OMP替代）
    support = []
    residual = y_stack.copy()

    for _ in range(s):
        c = A_stack.T @ residual
        best_idx = np.argmax(np.abs(c))
        support.append(best_idx)

        A_support = A_stack[:, support]
        x_support, _, _, _ = np.linalg.lstsq(A_support, y_stack, rcond=None)

        residual = y_stack - A_support @ x_support

    x_recovered[support] = x_support

    # 每个节点获得相同恢复结果
    return [x_recovered.copy() for _ in nodes], len(support)


def omp_independent(A: np.ndarray, y: np.ndarray, s: int) -> np.ndarray:
    """OMP算法用于独立分量恢复"""
    n = A.shape[1]
    x = np.zeros(n)
    support = []
    residual = y.copy()

    for _ in range(s):
        c = A.T @ residual
        best_idx = np.argmax(np.abs(c))
        if best_idx in support:
            break
        support.append(best_idx)

        A_support = A[:, support]
        x_support, _, _, _ = np.linalg.lstsq(A_support, y, rcond=None)

        residual = y - A_support @ x_support

    x[support] = x_support
    return x


def dcs_sequential_recover(node: SensorNode, prior_support: Optional[np.ndarray] = None,
                           alpha: float = 0.5) -> np.ndarray:
    """
    顺序恢复（利用前一个节点的先验）
    prior_support: 前一个节点的恢复支撑集
    alpha: 融合权重
    """
    n = node.x_true.shape[0]

    # 独立OMP
    x_indep = omp_independent(node.A, node.y, node.s_i)

    if prior_support is not None:
        # 融合先验
        # 方法：调整步长，基于先验支持
        prior_score = np.zeros(n)
        prior_score[prior_support] = 1.0

        # 加权梯度
        residual = node.y - node.A @ x_indep
        c = node.A.T @ residual

        c_weighted = c + alpha * prior_score * np.max(np.abs(c))

        # 重新求解
        x_fused = x_indep.copy()
        # 简化：只调整非零元
        support = np.where(np.abs(x_indep) > 1e-6)[0]
        for idx in support:
            x_fused[idx] += alpha * prior_score[idx] * c_weighted[idx] * 0.1

        return x_fused

    return x_indep


def test_dcs():
    """测试分布式压缩感知"""
    np.random.seed(42)

    num_sensors = 4
    n = 200  # 信号维度
    m = 60   # 每个传感器测量数
    s_total = 10  # 总稀疏度
    s_independent = 3  # 每个节点独立非零数

    nodes = []

    # 生成共享稀疏支撑
    shared_support = np.random.choice(n, 5, replace=False)

    print("=== 分布式压缩感知（DCS）测试 ===")
    print(f"传感器数: {num_sensors}")
    print(f"信号维度: {n}, 测量数: {m}")
    print(f"共享支撑: {shared_support}")

    for i in range(num_sensors):
        # 生成信号
        x = np.zeros(n)
        # 共享系数
        shared_coef = np.random.randn(5)
        x[shared_support] = shared_coef

        # 独立系数
        independent_support = np.random.choice(list(set(range(n)) - set(shared_support)), 
                                                 s_independent, replace=False)
        x[independent_support] = np.random.randn(s_independent) * 0.5

        # 测量矩阵
        A = np.random.randn(m, n) / np.sqrt(m)

        # 测量
        y = A @ x + 0.001 * np.random.randn(m)

        node = SensorNode(
            node_id=i,
            x_true=x.copy(),
            A=A,
            y=y,
            s_i=s_independent,
            shared_support=shared_support
        )
        nodes.append(node)

        error = np.linalg.norm(x - omp_independent(A, y, s_total + s_independent)) / np.linalg.norm(x)
        print(f"节点{i} 独立恢复误差: {error:.4f}")

    # JSM-1恢复
    print("\n--- JSM-1 联合恢复 ---")
    x_recovered_list, iterations = dcs_jsm1_recover(nodes, s_total + s_independent)

    for i, x_rec in enumerate(x_recovered_list):
        error = np.linalg.norm(nodes[i].x_true - x_rec) / np.linalg.norm(nodes[i].x_true)
        print(f"节点{i} 联合恢复误差: {error:.4f}")

    # JSM-2恢复
    print("\n--- JSM-2 联合恢复 ---")
    x_jsm2_list, _ = dcs_jsm2_recover(nodes, s_total)
    for i, x_rec in enumerate(x_jsm2_list):
        error = np.linalg.norm(nodes[i].x_true - x_rec) / np.linalg.norm(nodes[i].x_true)
        print(f"节点{i} JSM-2恢复误差: {error:.4f}")


if __name__ == "__main__":
    test_dcs()
