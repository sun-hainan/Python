# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / amplitude_amplification



本文件实现 amplitude_amplification 相关的算法功能。

"""



import numpy as np

from collections import deque





class GroverSearch:

    """

    Grover 搜索算法

    

    在无结构数据库中搜索 M 个解

    """

    

    def __init__(self, n_qubits, marked_states):

        """

        参数：

            n_qubits: 量子比特数

            marked_states: 好状态的列表（如 [0, 5, 7] 表示 |0⟩,|5⟩,|7⟩ 是解）

        """

        self.n = n_qubits

        self.N = 2 ** n_qubits  # 总状态数

        self.marked = set(marked_states)

        self.M = len(marked_states)

        

        # 振幅

        self.amplitude_good = np.sqrt(self.M / self.N)

        self.amplitude_bad = np.sqrt((self.N - self.M) / self.N)

    

    def one_grover_iteration(self):

        """

        一步 Grover 迭代

        

        振幅变化：

        - 好状态的振幅：a_g -> (2/N - 1) * a_g + 2 * a_bad

        - 坏状态的振幅：a_b -> 2 * a_g - (2/N - 1) * a_b

        

        对于大 N 近似：

        - 好状态振幅增加

        - 坏状态振幅减少

        """

        a_g = self.amplitude_good

        a_b = self.amplitude_bad

        

        # 神谕相位翻转

        a_g = -a_g

        

        # 扩散算子（关于平均振幅）

        avg = (a_g + (self.N - 1) * a_b) / self.N

        

        new_a_g = 2 * avg - a_g

        new_a_b = 2 * avg - a_b

        

        self.amplitude_good = new_a_g

        self.amplitude_bad = new_a_b

    

    def simulate(self, n_iterations):

        """

        模拟 Grover 搜索

        

        返回：测量到好状态的概率

        """

        for _ in range(n_iterations):

            self.one_grover_iteration()

        

        return self.amplitude_good ** 2

    

    def optimal_iterations(self):

        """计算最优迭代次数"""

        if self.M == 0:

            return 0

        return int(np.floor(np.pi / 4 * np.sqrt(self.N / self.M)))

    

    def success_probability(self, iterations):

        """

        计算给定迭代次数的成功概率

        

        精确公式（对于单个解 M=1）：

        P = sin²((2t+1)θ) 其中 sin²θ = 1/N

        """

        if self.M == 1:

            theta = np.arcsin(1 / np.sqrt(self.N))

            return np.sin((2 * iterations + 1) * theta) ** 2

        else:

            # 近似

            return self.M / self.N * (4 * iterations * self.M / self.N + 1)





class AmplitudeAmplification:

    """

    广义幅度放大

    

    基于 Choi-Ambainis-Mosca 框架

    """

    

    def __init__(self, n, success_amplitude):

        """

        参数：

            n: 量子比特数

            success_amplitude: 初始成功振幅（复数）

        """

        self.n = n

        self.N = 2 ** n

        self.a = success_amplitude

        

        # 好状态振幅

        self.alpha = np.abs(success_amplitude)

        # 坏状态振幅

        self.beta = np.sqrt(1 - np.abs(success_amplitude) ** 2)

    

    def diffuser(self):

        """

        扩散算子 D = 2|ψ⟩⟨ψ| - I

        

        在两维子空间中的矩阵表示：

        D = [[2a²-1, 2ab*], [2ab, 2b²-1]]

        """

        a = self.alpha

        b = self.beta

        

        # 简化：只跟踪振幅

        new_alpha = (2 * a ** 2 - 1) * a + 2 * b ** 2 * a

        new_beta = 2 * a * b - (2 * a ** 2 - 1) * b

        

        self.alpha = np.abs(new_alpha)

        self.beta = np.abs(new_beta)

    

    def one_iteration(self, oracle_phase=-1):

        """

        一步幅度放大

        

        oracle_phase: 神谕添加的相位（-1 表示翻转）

        """

        # 神谕

        self.alpha *= oracle_phase

        

        # 扩散

        self.diffuser()

    

    def simulate(self, n_iterations):

        """

        运行 n_iterations 次幅度放大

        """

        for _ in range(n_iterations):

            self.one_iteration()

        

        return self.alpha ** 2  # 成功概率





class FixedPointAmplitudeAmplification:

    """

    固定点幅度放大

    

    确保每次迭代都增加成功概率（不会超调）

    

    适用于成功概率未知的情况

    """

    

    def __init__(self, n, success_amplitude):

        self.n = n

        self.N = 2 ** n

        self.alpha = success_amplitude

    

    def quantum_search_operator(self):

        """

        固定点搜索算子

        

        S = -U_0 U_f

        

        其中 U_f 是神谕，U_0 = I - 2|0⟩⟨0|

        """

        # 简化的固定点迭代

        # 每次迭代使振幅更接近 1

        a = self.alpha

        

        # 固定点条件：a -> 1 - (1-a)^3（对于特定形式）

        self.alpha = a / np.sqrt(a ** 2 + (1 - a ** 2) * (1 - a ** 2))

    

    def simulate(self, n_iterations):

        """运行固定点幅度放大"""

        for _ in range(n_iterations):

            self.quantum_search_operator()

        

        return np.abs(self.alpha) ** 2





def grover_oracle(state_index, target_states):

    """

    Grover 神谕

    

    |x⟩ -> -|x⟩ 如果 x 是解，否则不变

    """

    if state_index in target_states:

        return -1

    return 1





def simulate_grover_circuit(n_qubits, target_states, n_iterations):

    """

    模拟 Grover 电路

    

    参数：

        n_qubits: 量子比特数

        target_states: 解状态列表

        n_iterations: Grover 迭代次数

    """

    N = 2 ** n_qubits

    M = len(target_states)

    

    # 初始叠加态（每个状态的振幅）

    amplitude = 1.0 / np.sqrt(N)

    

    # 振幅向量

    amplitudes = np.ones(N, dtype=complex) * amplitude

    

    for _ in range(n_iterations):

        # 神谕

        for t in target_states:

            amplitudes[t] *= -1

        

        # 扩散算子（在计算基上）

        avg_amplitude = np.mean(amplitudes)

        amplitudes = 2 * avg_amplitude - amplitudes

    

    # 测量概率

    probs = np.abs(amplitudes) ** 2

    

    return probs





if __name__ == "__main__":

    print("=" * 55)

    print("幅度放大（Amplitude Amplification）")

    print("=" * 55)

    

    # Grover 搜索示例

    print("\n1. Grover 搜索算法")

    print("-" * 40)

    

    n = 10  # 10 量子比特，1024 个状态

    N = 2 ** n

    

    # 100 个解

    M = 100

    np.random.seed(42)

    targets = np.random.choice(N, M, replace=False).tolist()

    

    grover = GroverSearch(n, targets)

    

    optimal_t = grover.optimal_iterations()

    print(f"数据库大小: N = {N}")

    print(f"解的数量: M = {M}")

    print(f"最优迭代次数: t = {optimal_t}")

    

    # 概率曲线

    print(f"\n不同迭代次数的成功概率：")

    for t in [0, optimal_t // 4, optimal_t // 2, optimal_t, optimal_t + 1, 2 * optimal_t]:

        p = grover.success_probability(t)

        bar = '█' * int(p * 50)

        print(f"  t={t:2d}: P={p:.4f} {bar}")

    

    # 精确模拟

    print(f"\n精确模拟（{optimal_t}次迭代）：")

    probs = simulate_grover_circuit(n, targets, optimal_t)

    

    # 找到最大概率

    max_prob_idx = np.argmax(probs)

    max_prob = probs[max_prob_idx]

    

    is_target = max_prob_idx in targets

    print(f"  最大概率状态: {max_prob_idx}, P={max_prob:.4f}, 是解: {is_target}")

    

    # 幅度放大示例

    print("\n2. 广义幅度放大")

    print("-" * 40)

    

    # 初始成功概率 0.01

    initial_prob = 0.01

    aa = AmplitudeAmplification(10, np.sqrt(initial_prob))

    

    print(f"初始成功概率: {initial_prob}")

    

    for t in [1, 5, 10, 20]:

        prob = aa.simulate(t)

        bar = '█' * int(prob * 50)

        print(f"  t={t:2d}: P={prob:.4f} {bar}")

    

    # 固定点幅度放大

    print("\n3. 固定点幅度放大")

    print("-" * 40)

    

    fp_aa = FixedPointAmplitudeAmplification(10, np.sqrt(0.01))

    

    print(f"初始成功概率: 0.01")

    

    for t in [1, 5, 10]:

        prob = fp_aa.simulate(t)

        print(f"  t={t}: P={prob:.4f}")

