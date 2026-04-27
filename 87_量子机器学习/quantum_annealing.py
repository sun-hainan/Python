# -*- coding: utf-8 -*-

"""

算法实现：量子机器学习 / quantum_annealing



本文件实现 quantum_annealing 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Optional, Callable

from dataclasses import dataclass

from enum import Enum





@dataclass

class Ising_Model:

    """Ising模型 H = -Σ J_ij σ_i σ_j - Σ h_i σ_i"""

    num_spins: int

    J: np.ndarray           # 耦合矩阵 (num_spins, num_spins)

    h: np.ndarray           # 局部场 (num_spins,)

    coupling_range: str = "all-to-all"  # 耦合范围





@dataclass

class Annealing_Schedule:

    """退火时间表"""

    total_time: float

    num_steps: int

    gamma_initial: float = 1.0   # 初始横向场强度

    gamma_final: float = 0.0     # 最终横向场强度





class Quantum_Annealer:

    """量子退火器"""

    def __init__(self, ising: Ising_Model, schedule: Annealing_Schedule):

        self.ising = ising

        self.schedule = schedule

        self.state: np.ndarray = np.random.choice([-1, 1], size=ising.num_spins)  # 初始自旋

        self.energy_history: List[float] = []





    def compute_energy(self, state: np.ndarray = None) -> float:

        """计算Ising能量"""

        if state is None:

            state = self.state

        # H = -Σ J_ij σ_i σ_j - Σ h_i σ_i

        interaction_energy = -np.sum(self.ising.J * np.outer(state, state))

        field_energy = -np.sum(self.ising.h * state)

        return interaction_energy + field_energy





    def compute_quantum_term(self, state: np.ndarray, gamma: float) -> float:

        """计算量子项（横向场）"""

        # H_q = -Γ Σ σ_x^i

        return -gamma * np.sum(state)  # 简化





    def annealing_step(self, time_step: float, gamma: float) -> np.ndarray:

        """

        单步退火

        使用简化的量子Monte Carlo或直接模拟

        """

        new_state = self.state.copy()

        # 横向场导致自旋翻转（隧穿概率）

        flip_prob = gamma / (1 + gamma)  # 简化的翻转概率

        for i in range(self.ising.num_spins):

            if np.random.random() < flip_prob:

                # 尝试翻转

                trial_state = new_state.copy()

                trial_state[i] *= -1

                # Metropolis准则

                delta_E = self.compute_energy(trial_state) - self.compute_energy(new_state)

                if delta_E < 0 or np.random.random() < np.exp(-delta_E / (time_step + 1e-10)):

                    new_state[i] *= -1

        return new_state





    def anneal(self, verbose: bool = True) -> Tuple[np.ndarray, float, List[float]]:

        """执行退火过程"""

        dt = self.schedule.total_time / self.schedule.num_steps

        energies = []

        for step in range(self.schedule.num_steps):

            # 计算当前γ（横向场强度）

            progress = step / self.schedule.num_steps

            gamma = self.schedule.gamma_initial * (1 - progress) + self.schedule.gamma_final * progress

            # 执行退火步骤

            self.state = self.annealing_step(dt, gamma)

            # 记录能量

            energy = self.compute_energy()

            energies.append(energy)

            if verbose and step % 10 == 0:

                print(f"  Step {step:3d}: γ = {gamma:.4f}, E = {energy:.4f}")

        self.energy_history = energies

        best_idx = np.argmin(energies)

        return self.state, energies[best_idx], energies





class Classical_Ising_Simulator:

    """经典Ising模型模拟器（用于对比）"""

    def __init__(self, ising: Ising_Model, temperature: float = 1.0):

        self.ising = ising

        self.T = temperature

        self.state = np.random.choice([-1, 1], size=ising.num_spins)

        self.energy_history: List[float] = []





    def metropolis_step(self) -> np.ndarray:

        """Metropolis算法单步"""

        new_state = self.state.copy()

        i = np.random.randint(0, self.ising.num_spins)

        trial_state = new_state.copy()

        trial_state[i] *= -1

        delta_E = self.compute_energy(trial_state) - self.compute_energy(new_state)

        if delta_E < 0 or np.random.random() < np.exp(-delta_E / self.T):

            new_state[i] *= -1

        return new_state





    def compute_energy(self, state: np.ndarray = None) -> float:

        """计算Ising能量"""

        if state is None:

            state = self.state

        interaction_energy = -np.sum(self.ising.J * np.outer(state, state))

        field_energy = -np.sum(self.ising.h * state)

        return interaction_energy + field_energy





    def simulate(self, num_steps: int = 1000, verbose: bool = False) -> Tuple[np.ndarray, float]:

        """运行模拟"""

        energies = []

        for step in range(num_steps):

            self.state = self.metropolis_step()

            energies.append(self.compute_energy())

            if verbose and step % 100 == 0:

                print(f"  Step {step}: E = {energies[-1]:.4f}")

        self.energy_history = energies

        best_idx = np.argmin(energies)

        return self.state, energies[best_idx]





def create_tsp_ising(num_cities: int) -> Ising_Model:

    """将TSP问题转换为Ising模型"""

    num_spins = num_cities * num_cities  # 每个城市一行

    # 随机距离矩阵

    np.random.seed(42)

    dist_matrix = np.random.randint(1, 10, size=(num_cities, num_cities))

    dist_matrix = (dist_matrix + dist_matrix.T) / 2

    np.fill_diagonal(dist_matrix, 0)

    # 简化的Ising耦合

    J = np.zeros((num_spins, num_spins))

    h = np.zeros(num_spins)

    return Ising_Model(num_spins=num_spins, J=J, h=h, coupling_range="sparse")





def create_maxcut_ising(num_vertices: int, edges: List[Tuple[int, int]]) -> Ising_Model:

    """将MaxCut问题转换为Ising模型"""

    # MaxCut: 最大化切割边权重

    num_spins = num_vertices

    J = np.zeros((num_spins, num_spins))

    for i, j in edges:

        J[i, j] = -1.0  # 负号因为要最大化

        J[j, i] = -1.0

    h = np.zeros(num_spins)

    return Ising_Model(num_spins=num_spins, J=J, h=h, coupling_range="sparse")





def basic_test():

    """基本功能测试"""

    print("=== 量子退火和Ising模型测试 ===")

    # 创建简单的Ising模型

    print("\n[简化的Ising模型测试]")

    num_spins = 5

    # 随机耦合

    J = np.random.randn(num_spins, num_spins) * 0.1

    J = (J + J.T) / 2  # 对称化

    np.fill_diagonal(J, 0)

    h = np.random.randn(num_spins) * 0.1

    ising = Ising_Model(num_spins=num_spins, J=J, h=h)

    # 量子退火

    print("\n量子退火:")

    schedule = Annealing_Schedule(total_time=100.0, num_steps=100)

    annealer = Quantum_Annealer(ising, schedule)

    best_state, best_energy, energies = annealer.anneal(verbose=False)

    print(f"  最优能量: {best_energy:.4f}")

    print(f"  最优态: {best_state}")

    # 经典模拟对比

    print("\n经典Metropolis模拟对比:")

    classical = Classical_Ising_Simulator(ising, temperature=1.0)

    classical_state, classical_energy = classical.simulate(num_steps=500, verbose=False)

    print(f"  最优能量: {classical_energy:.4f}")

    print(f"  最优态: {classical_state}")

    # MaxCut问题测试

    print("\n" + "=" * 50)

    print("\n[MaxCut问题测试]")

    num_vertices = 6

    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 3), (1, 4)]

    maxcut_ising = create_maxcut_ising(num_vertices, edges)

    schedule = Annealing_Schedule(total_time=50.0, num_steps=50)

    annealer = Quantum_Annealer(maxcut_ising, schedule)

    best_state, best_energy, _ = annealer.anneal(verbose=False)

    # 计算切割边数

    cut_edges = sum(1 for i, j in edges if best_state[i] != best_state[j])

    print(f"  切割边数: {cut_edges}/{len(edges)}")

    print(f"  Ising能量: {best_energy:.4f}")





if __name__ == "__main__":

    basic_test()

