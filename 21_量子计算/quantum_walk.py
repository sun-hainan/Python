# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / quantum_walk



本文件实现 quantum_walk 相关的算法功能。

"""



import numpy as np

from collections import defaultdict





class DiscreteQuantumWalk:

    """

    离散时间量子游走

    

    在一条线上（一维格）的量子游走：

    - 位置 Hilbert 空间：|x⟩ for x in integers

    - 硬币 Hilbert 空间：|0⟩, |1⟩

    - 每步：先掷硬币（coin operation），再移动（shift operation）

    

    硬币算符：Hadamard 硬币 H = (|0⟩⟨0| + |0⟩⟨1| + |1⟩⟨0| - |1⟩⟨1|) / sqrt(2)

    移动算符：S = |0⟩⟨0| ⊗ Σ|x+1⟩⟨x| + |1⟩⟨1| ⊗ Σ|x-1⟩⟨x|

    """

    

    def __init__(self, n_positions, coin_type='hadamard'):

        self.n = n_positions

        self.positions = list(range(n_positions))

        self.coin_type = coin_type

        

        # 定义硬币算符

        if coin_type == 'hadamard':

            # Hadamard 硬币

            self.coin = np.array([

                [1, 1],

                [1, -1]

            ]) / np.sqrt(2)

        elif coin_type == 'grover':

            # Grover 硬币（扩散器）

            self.coin = 2 * np.ones((2, 2)) / 2 - np.eye(2)

        else:

            self.coin = np.eye(2)

    

    def step(self, state):

        """

        执行一步量子游走

        

        参数：

            state: 当前状态向量 (2 * n 维)

        

        返回：下一步状态

        """

        n = self.n

        

        # 分解为位置和硬币部分

        # 状态向量格式：[p0_0, p0_1, p1_0, p1_1, ...]

        # 其中 pi_j 表示位置 i、硬币 j 的振幅

        

        # Step 1: 应用硬币算符（只作用于硬币空间）

        new_state = np.zeros(2 * n, dtype=complex)

        

        for pos in range(n):

            amp0 = state[2 * pos]      # 位置 pos, 硬币 0

            amp1 = state[2 * pos + 1]  # 位置 pos, 硬币 1

            

            # 应用硬币

            new0 = self.coin[0, 0] * amp0 + self.coin[0, 1] * amp1

            new1 = self.coin[1, 0] * amp0 + self.coin[1, 1] * amp1

            

            new_state[2 * pos] = new0

            new_state[2 * pos + 1] = new1

        

        # Step 2: 移动（shift operation）

        shifted = np.zeros(2 * n, dtype=complex)

        

        for pos in range(n):

            # 硬币 0：向右移动

            new_pos = pos + 1

            if new_pos < n:

                shifted[2 * new_pos] += new_state[2 * pos]

            

            # 硬币 1：向左移动

            new_pos = pos - 1

            if new_pos >= 0:

                shifted[2 * new_pos + 1] += new_state[2 * pos + 1]

        

        return shifted

    

    def simulate(self, n_steps, initial_pos=None):

        """

        模拟 n 步量子游走

        

        参数：

            n_steps: 步数

            initial_pos: 初始位置（默认居中）

        

        返回：最终状态和各步的概率分布

        """

        if initial_pos is None:

            initial_pos = self.n // 2

        

        # 初始化：位置 initial_pos，叠加硬币状态

        state = np.zeros(2 * self.n, dtype=complex)

        state[2 * initial_pos] = 1.0 / np.sqrt(2)

        state[2 * initial_pos + 1] = 1.0 / np.sqrt(2)

        

        # 记录每步的概率分布

        probabilities = []

        

        current_state = state

        for step in range(n_steps):

            # 计算概率分布

            probs = np.abs(current_state) ** 2

            # 边缘化硬币空间

            pos_probs = [probs[2*p] + probs[2*p+1] for p in range(self.n)]

            probabilities.append(pos_probs)

            

            # 执行一步

            current_state = self.step(current_state)

        

        # 最后一歩

        probs = np.abs(current_state) ** 2

        pos_probs = [probs[2*p] + probs[2*p+1] for p in range(self.n)]

        probabilities.append(pos_probs)

        

        return current_state, probabilities





class ContinuousQuantumWalk:

    """

    连续时间量子游走

    

    在图 G 上的连续时间量子游走：

    - 哈密顿量 H = L（图 Laplacian）

    - 状态随时间演变：|ψ(t)⟩ = exp(-iHt) |ψ(0)⟩

    

    对于无向图，L = D - A

    D: 度对角矩阵

    A: 邻接矩阵

    """

    

    def __init__(self, adjacency):

        """

        参数：

            adjacency: 邻接矩阵

        """

        self.adj = np.array(adjacency)

        self.n = len(adjacency)

        self.degree = np.sum(adjacency, axis=1)

        self.laplacian = np.diag(self.degree) - self.adj

    

    def simulate(self, time, initial_node):

        """

        模拟连续时间量子游走

        

        参数：

            time: 演化时间

            initial_node: 初始节点（单激发态）

        

        返回：最终状态

        """

        # 初始状态

        psi0 = np.zeros(self.n, dtype=complex)

        psi0[initial_node] = 1.0

        

        # 使用谱分解计算 exp(-iHt)

        eigenvalues, eigenvectors = np.linalg.eigh(self.laplacian)

        

        # exp(-iHt) = V @ diag(exp(-i*lambda*t)) @ V^dagger

        phase = np.exp(-1j * eigenvalues * time)

        evolution = eigenvectors @ np.diag(phase) @ eigenvectors.conj().T

        

        psi_t = evolution @ psi0

        

        return psi_t

    

    def probability_distribution(self, psi):

        """从状态计算概率分布"""

        return np.abs(psi) ** 2





if __name__ == "__main__":

    print("=" * 55)

    print("量子游走（Quantum Walk）")

    print("=" * 55)

    

    # 离散量子游走示例

    print("\n1. 离散时间量子游走（线）")

    print("-" * 40)

    

    n_pos = 31  # 奇数确保对称

    qw = DiscreteQuantumWalk(n_pos, coin_type='hadamard')

    

    n_steps = 10

    final_state, probs = qw.simulate(n_steps)

    

    print(f"位置数: {n_pos}, 步数: {n_steps}")

    print(f"\n最终概率分布（前10个位置）：")

    for i in range(min(10, n_pos)):

        bar = '█' * int(probs[-1][i] * 30)

        print(f"  {i:2d}: {probs[-1][i]:.4f} {bar}")

    

    # 连续量子游走示例

    print("\n2. 连续时间量子游走（星形图）")

    print("-" * 40)

    

    # 星形图：中心节点0，连接节点1-4

    star_adj = [

        [0, 1, 1, 1, 1],

        [1, 0, 0, 0, 0],

        [1, 0, 0, 0, 0],

        [1, 0, 0, 0, 0],

        [1, 0, 0, 0, 0],

    ]

    

    cqw = ContinuousQuantumWalk(star_adj)

    

    times = [0.5, 1.0, 2.0, 5.0]

    print(f"节点数: {cqw.n}（1个中心，4个叶节点）")

    print("\n从节点1（叶）开始的概率分布：")

    

    for t in times:

        psi = cqw.simulate(t, initial_node=1)

        probs = cqw.probability_distribution(psi)

        print(f"  t={t:.1f}: {probs.round(3)}")

