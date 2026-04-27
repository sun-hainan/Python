# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / quantum_gradient_estimation



本文件实现 quantum_gradient_estimation 相关的算法功能。

"""



import numpy as np

from collections import defaultdict





class HamiltonianSimulation:

    """

    哈密顿量模拟

    

    目标：高效模拟 e^{-iHt}

    

    方法：

    1. 一阶 Trotterization

    2. 高阶 Trotter-Suzuki

    """

    

    def __init__(self, hamiltonian):

        """

        参数：

            hamiltonian: 哈密顿量字典

            格式：{term: coefficient}

            term 是 Pauli 字符串如 'XYZI', coefficient 是复数

        """

        self.hamiltonian = hamiltonian

        self.n_qubits = len(list(hamiltonian.keys())[0])

    

    def pauli_matrix(self, pauli):

        """获取 Pauli 矩阵"""

        mapping = {

            'I': np.eye(2),

            'X': np.array([[0, 1], [1, 0]]),

            'Y': np.array([[0, -1j], [1j, 0]]),

            'Z': np.array([[1, 0], [0, -1]])

        }

        return mapping[pauli]

    

    def tensor_product(self, pauli_string):

        """计算 Pauli 字符串的张量积"""

        matrices = [self.pauli_matrix(p) for p in pauli_string]

        

        result = matrices[0]

        for m in matrices[1:]:

            result = np.kron(result, m)

        

        return result

    

    def build_matrix(self):

        """构建完整哈密顿量矩阵"""

        H = np.zeros((2 ** self.n_qubits, 2 ** self.n_qubits), dtype=complex)

        

        for term, coeff in self.hamiltonian.items():

            H += coeff * self.tensor_product(term)

        

        return H

    

    def first_order_trotter(self, t, n_steps):

        """

        一阶 Trotterization

        

        e^{-iHt} ≈ (e^{-iH1t/n} e^{-iH2t/n} ...)^n

        """

        H = self.build_matrix()

        dt = t / n_steps

        

        # 简化的 Trotter 步骤

        U = np.eye(2 ** self.n_qubits, dtype=complex)

        

        for _ in range(n_steps):

            U_step = np.eye(2 ** self.n_qubits, dtype=complex)

            for term, coeff in self.hamiltonian.items():

                U_term = self.tensor_product(term)

                U_step = U_step @ np.linalg.matrix_power(U_term, int(np.round(np.real(coeff) * dt)))

            U = U_step @ U

        

        return U

    

    def simulate_evolution(self, initial_state, time):

        """模拟时间演化"""

        H = self.build_matrix()

        eigenvalues, eigenvectors = np.linalg.eigh(H)

        

        # 转换到特征基

        c = eigenvectors.conj().T @ initial_state

        

        # 演化的相位

        phases = np.exp(-1j * eigenvalues * time)

        

        # 演化后的状态

        evolved_c = c * phases

        

        return eigenvectors @ evolved_c





class MolecularHamiltonian:

    """

    分子哈密顿量（简化量子化学）

    

    H = Σ_i h_i a_i^dagger a_i + Σ_{ijkl} h_{ijkl} a_i^dagger a_j a_k^dagger a_l

    """

    

    def __init__(self, n_orbitals, n_electrons):

        self.n_orbitals = n_orbitals

        self.n_electrons = n_electrons

        self.n_spin_orbitals = 2 * n_orbitals

    

    def create_hamiltonian(self, one_body, two_body):

        """

        构建二次量子化哈密顿量

        

        参数：

            one_body: 单体项 h_{pq}

            two_body: 双体项 h_{pqrs}

        """

        hamiltonian = {}

        

        # 单体项

        for p in range(self.n_spin_orbitals):

            for q in range(self.n_spin_orbitals):

                if abs(one_body[p, q]) > 1e-10:

                    # a_p^dagger a_q 项

                    pauli = 'I' * self.n_spin_orbitals

                    # 简化：用 Pauli Z 表示

                    if p == q:

                        # Z on qubit p

                        pauli_list = list(pauli)

                        pauli_list[p] = 'Z'

                        pauli_string = ''.join(pauli_list)

                        hamiltonian[pauli_string] = one_body[p, q] / 2

        

        return hamiltonian

    

    def hartree_fock_energy(self, one_body, two_body):

        """

        Hartree-Fock 近似能量

        

        简化：计算基态能量估计

        """

        n = self.n_electrons

        

        # 简化能量计算

        energy = 0.0

        

        for i in range(n):

            for j in range(n):

                energy += one_body[i, j]

        

        return energy





class TimeEvolutionCircuit:

    """

    时间演化量子电路

    

    使用门分解模拟时间演化

    """

    

    def __init__(self, n_qubits):

        self.n = n_qubits

        self.gates = []

    

    def add_rotation(self, qubit, axis, angle):

        """添加单比特旋转"""

        self.gates.append(('R' + axis.upper(), qubit, angle))

    

    def add_cnot(self, control, target):

        """添加 CNOT 门"""

        self.gates.append(('CNOT', control, target))

    

    def add_controlled_rotation(self, control, target, axis, angle):

        """添加受控旋转"""

        self.gates.append(('CR' + axis.upper(), control, target, angle))

    

    def circuit_depth(self):

        """估算电路深度"""

        return len(self.gates)

    

    def simulate_circuit(self, initial_state):

        """

        模拟电路

        

        简化：假设单位演化

        """

        return initial_state





def ising_model_transverse_field(n_sites, J, h):

    """

    构建横场 Ising 模型哈密顿量

    

    H = -J Σ σ_i^z σ_{i+1}^z - h Σ σ_i^x

    """

    hamiltonian = {}

    

    for i in range(n_sites - 1):

        # Z_i Z_{i+1} 项

        term = ['I'] * n_sites

        term[i] = 'Z'

        term[i + 1] = 'Z'

        pauli_string = ''.join(term)

        hamiltonian[pauli_string] = -J

    

    for i in range(n_sites):

        # X_i 项

        term = ['I'] * n_sites

        term[i] = 'X'

        pauli_string = ''.join(term)

        hamiltonian[pauli_string] = -h

    

    return HamiltonianSimulation(hamiltonian)





if __name__ == "__main__":

    print("=" * 55)

    print("量子模拟（Quantum Simulation）")

    print("=" * 55)

    

    # Ising 模型

    print("\n1. 横场 Ising 模型")

    print("-" * 40)

    

    n_sites = 4

    J = 1.0  # 相互作用强度

    h = 0.5  # 横场

    

    ising = ising_model_transverse_field(n_sites, J, h)

    

    print(f"系统大小: {n_sites} sites")

    print(f"相互作用 J = {J}, 横场 h = {h}")

    print(f"哈密顿量项数: {len(ising.hamiltonian)}")

    

    # 构建哈密顿量矩阵

    H = ising.build_matrix()

    print(f"哈密顿量维度: {H.shape}")

    

    # 对角化

    eigenvalues, eigenvectors = np.linalg.eigh(H)

    print(f"\n能量本征值（前5个）:")

    for i, e in enumerate(eigenvalues[:5]):

        print(f"  E_{i} = {e:.6f}")

    

    # 基态能量

    print(f"\n基态能量: {eigenvalues[0]:.6f}")

    

    # 时间演化

    print("\n2. 时间演化模拟")

    print("-" * 40)

    

    initial_state = np.zeros(2 ** n_sites, dtype=complex)

    initial_state[0] = 1.0  # |00...0⟩

    

    times = [0.1, 0.5, 1.0]

    

    for t in times:

        evolved = ising.simulate_evolution(initial_state, t)

        probs = np.abs(evolved) ** 2

        max_prob = np.max(probs)

        max_idx = np.argmax(probs)

        

        print(f"  t={t:.1f}: 最大概率 P={max_prob:.4f} at |{max_idx:0{n_sites}b}⟩")

    

    # 量子化学示例

    print("\n3. 量子化学模拟")

    print("-" * 40)

    

    n_orbitals = 2

    n_electrons = 2

    

    mol = MolecularHamiltonian(n_orbitals, n_electrons)

    

    # 简化的一体和二体积分

    one_body = np.random.randn(4, 4) * 0.5

    two_body = np.random.randn(4, 4, 4, 4) * 0.1

    

    # 确保厄米性

    one_body = (one_body + one_body.T) / 2

    

    hf_energy = mol.hartree_fock_energy(one_body, two_body)

    

    print(f"分子: {n_orbitals} 轨道, {n_electrons} 电子")

    print(f"Hartree-Fock 能量估计: {hf_energy:.6f}")

