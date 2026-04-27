# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / quantum_gates



本文件实现 quantum_gates 相关的算法功能。

"""



import numpy as np  # 导入NumPy用于复数向量和矩阵运算





# =============================================================================

# 量子门矩阵定义 (Quantum Gate Matrix Definitions)

# =============================================================================



# Hadamard门矩阵 - 将|0>变为叠加态 (|0> + |1>)/√2

# H = (1/√2) * [[1, 1], [1, -1]]

H_GATE = np.array([[1, 1], [1, -1]]) / np.sqrt(2)



# Pauli-X门矩阵 - 量子非门，类似于经典NOT门

# X = [[0, 1], [1, 0]]

X_GATE = np.array([[0, 1], [1, 0]])



# Pauli-Y门矩阵 - 绕Y轴旋转π

# Y = [[0, -i], [i, 0]]

Y_GATE = np.array([[0, -1j], [1j, 0]])



# Pauli-Z门矩阵 - 绕Z轴旋转π，相位门

# Z = [[1, 0], [0, -1]]

Z_GATE = np.array([[1, 0], [0, -1]])



# S门矩阵 - 相位门，Z门的平方根

# S = [[1, 0], [0, i]]

S_GATE = np.array([[1, 0], [0, 1j]])



# T门矩阵 - π/8门，S门的平方根

# T = [[1, 0], [0, exp(iπ/4)]]

T_GATE = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]])



# CNOT门矩阵 - 受控非门，控制比特为第一个比特，目标比特为第二个

# CNOT = [[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]]

CNOT_GATE = np.array([

    [1, 0, 0, 0],

    [0, 1, 0, 0],

    [0, 0, 0, 1],

    [0, 0, 1, 0]

])



# SWAP门矩阵 - 交换两个量子比特

# SWAP = [[1,0,0,0], [0,0,1,0], [0,1,0,0], [0,0,0,1]]

SWAP_GATE = np.array([

    [1, 0, 0, 0],

    [0, 0, 1, 0],

    [0, 1, 0, 0],

    [0, 0, 0, 1]

])



# Toffoli门 (CCNOT) - 三比特受控门，前两个比特为控制比特

# Toffoli = I⊗I⊗X for first two |1>

TOFFOLI_GATE = np.array([

    [1, 0, 0, 0, 0, 0, 0, 0],

    [0, 1, 0, 0, 0, 0, 0, 0],

    [0, 0, 1, 0, 0, 0, 0, 0],

    [0, 0, 0, 1, 0, 0, 0, 0],

    [0, 0, 0, 0, 1, 0, 0, 0],

    [0, 0, 0, 0, 0, 1, 0, 0],

    [0, 0, 0, 0, 0, 0, 0, 1],

    [0, 0, 0, 0, 0, 0, 1, 0]

])





# =============================================================================

# 量子态类定义 (Quantum State Class)

# =============================================================================



class QuantumState:

    """

    量子态类 - 用复数向量表示n比特量子态

    

    Attributes:

        num_qubits: 量子比特数n

        state_vector: 大小为2^n的复数向量，表示量子态振幅

    """

    

    def __init__(self, num_qubits, initial_state=None):

        """

        初始化量子态

        

        Args:

            num_qubits: 量子比特数

            initial_state: 初始态向量，如果为None则默认为|0...0>

        """

        self.num_qubits = num_qubits  # 设置量子比特数

        self.dimension = 2 ** num_qubits  # 计算向量维度

        

        if initial_state is None:

            # 默认初始化为|0>⊗n，即所有比特都是0

            self.state_vector = np.zeros(self.dimension, dtype=complex)

            self.state_vector[0] = 1.0  # |00...0> = 1

        else:

            # 使用提供的初始态向量

            self.state_vector = np.array(initial_state, dtype=complex)

            # 归一化量子态

            norm = np.linalg.norm(self.state_vector)

            if norm > 0:

                self.state_vector /= norm

        

        self._normalize()  # 确保量子态归一化

    

    def _normalize(self):

        """归一化量子态向量"""

        norm = np.linalg.norm(self.state_vector)

        if norm > 1e-10:  # 避免除以零

            self.state_vector /= norm

    

    def apply_gate(self, gate_matrix, target_qubits=None):

        """

        对量子态施加量子门

        

        Args:

            gate_matrix: 量子门矩阵

            target_qubits: 目标比特索引列表

            

        Returns:

            施加门后的新量子态

        """

        # 复制当前量子态

        new_state = QuantumState(self.num_qubits)

        new_state.state_vector = self.state_vector.copy()

        

        if target_qubits is None or len(target_qubits) == 0:

            # 默认作用于所有比特

            new_state.state_vector = gate_matrix @ new_state.state_vector

        else:

            # 应用多比特门 - 张量积构造

            full_gate = self._expand_gate(gate_matrix, target_qubits)

            new_state.state_vector = full_gate @ new_state.state_vector

        

        new_state._normalize()

        return new_state

    

    def _expand_gate(self, gate_matrix, target_qubits):

        """

        将单比特门或多比特门扩展到完整希尔伯特空间

        

        Args:

            gate_matrix: 量子门矩阵

            target_qubits: 目标比特索引

            

        Returns:

            扩展到完整空间的门矩阵

        """

        num_targets = len(target_qubits)

        

        if num_targets == 1:

            # 单比特门：使用张量积扩展到n比特空间

            full_gate = np.array([[1.0]])

            for i in range(self.num_qubits):

                if i == target_qubits[0]:

                    full_gate = np.kron(full_gate, gate_matrix)

                else:

                    # 单位矩阵 I = [[1,0],[0,1]]

                    full_gate = np.kron(full_gate, np.eye(2))

            return full_gate

        elif num_targets == 2:

            # 两比特门：CNOT等

            return gate_matrix

        

        return gate_matrix

    

    def measure(self):

        """

        测量量子态，返回测量结果索引

        

        基于Born规则：测量结果i的概率为|振幅_i|²

        

        Returns:

            measured_index: 测量到的基态索引 (0 到 2^n-1)

            probabilities: 各基态的测量概率

        """

        probabilities = np.abs(self.state_vector) ** 2  # 计算各基态概率

        measured_index = np.random.choice(self.dimension, p=probabilities)  # 按概率采样

        return measured_index, probabilities

    

    def get_probabilities(self):

        """

        获取各基态的测量概率

        

        Returns:

            各基态的测量概率数组

        """

        return np.abs(self.state_vector) ** 2

    

    def __str__(self):

        """打印量子态的字符串表示"""

        return f"QuantumState(|ψ⟩) with {self.num_qubits} qubits"

    

    def __repr__(self):

        """详细表示"""

        return f"QuantumState(n={self.num_qubits}, dim={self.dimension})"





# =============================================================================

# 量子门操作函数 (Quantum Gate Operation Functions)

# =============================================================================



def apply_hadamard(state, target_qubit):

    """

    对目标比特施加Hadamard门，创建叠加态

    

    H门将|0⟩变为 (|0⟩+|1⟩)/√2，|1⟩变为 (|0⟩-|1⟩)/√2

    

    Args:

        state: 输入量子态

        target_qubit: 目标比特索引 (0-indexed)

        

    Returns:

        应用H门后的新量子态

    """

    return state.apply_gate(H_GATE, [target_qubit])





def apply_pauli_x(state, target_qubit):

    """

    对目标比特施加Pauli-X门（量子非门）

    

    X门将|0⟩→|1⟩，|1⟩→|0⟩

    

    Args:

        state: 输入量子态

        target_qubit: 目标比特索引

        

    Returns:

        应用X门后的新量子态

    """

    return state.apply_gate(X_GATE, [target_qubit])





def apply_pauli_y(state, target_qubit):

    """

    对目标比特施加Pauli-Y门

    

    Y门 = i|1⟩⟨0| - i|0⟩⟨1|

    

    Args:

        state: 输入量子态

        target_qubit: 目标比特索引

        

    Returns:

        应用Y门后的新量子态

    """

    return state.apply_gate(Y_GATE, [target_qubit])





def apply_pauli_z(state, target_qubit):

    """

    对目标比特施加Pauli-Z门（相位门）

    

    Z门将|1⟩的相位翻转-1

    

    Args:

        state: 输入量子态

        target_qubit: 目标比特索引

        

    Returns:

        应用Z门后的新量子态

    """

    return state.apply_gate(Z_GATE, [target_qubit])





def apply_cnot(state, control_qubit, target_qubit):

    """

    对两个比特施加CNOT门（受控非门）

    

    CNOT门规则：当控制比特为|1⟩时，目标比特翻转

    

    Args:

        state: 输入量子态

        control_qubit: 控制比特索引

        target_qubit: 目标比特索引

        

    Returns:

        应用CNOT后的新量子态

    """

    return state.apply_gate(CNOT_GATE, [control_qubit, target_qubit])





def apply_swap(state, qubit1, qubit2):

    """

    交换两个量子比特的位置

    

    Args:

        state: 输入量子态

        qubit1: 第一个比特索引

        qubit2: 第二个比特索引

        

    Returns:

        交换后的新量子态

    """

    return state.apply_gate(SWAP_GATE, [qubit1, qubit2])





def apply_toffoli(state, ctrl1, ctrl2, target):

    """

    施加Toffoli门（CCNOT门，三比特受控门）

    

    当两个控制比特都为|1⟩时，目标比特翻转

    

    Args:

        state: 输入量子态

        ctrl1: 第一个控制比特

        ctrl2: 第二个控制比特

        target: 目标比特

        

    Returns:

        应用Toffoli门后的新量子态

    """

    return state.apply_gate(TOFFOLI_GATE, [ctrl1, ctrl2, target])





def create_bell_state(state, qubit1, qubit2):

    """

    创建Bell态（最大纠缠态）

    

    Bell态是 |Φ+⟩ = (|00⟩ + |11⟩)/√2

    

    步骤：

    1. 对第一个比特施加Hadamard门 → 叠加态

    2. 对两个比特施加CNOT门 → 纠缠态

    

    Args:

        state: 输入量子态

        qubit1: 第一个比特索引

        qubit2: 第二个比特索引

        

    Returns:

        Bell态量子态

    """

    # 施加Hadamard门

    state = apply_hadamard(state, qubit1)

    # 施加CNOT门

    state = apply_cnot(state, qubit1, qubit2)

    return state





# =============================================================================

# 测试代码 (Test Code)

# =============================================================================



if __name__ == "__main__":

    print("=" * 60)

    print("量子计算基础门测试")

    print("=" * 60)

    

    # 测试1：单比特Hadamard门

    print("\n【测试1】Hadamard门 - 创建叠加态")

    state1 = QuantumState(1)  # 初始化|0⟩

    print(f"初始态 |0⟩: 振幅 = {state1.state_vector}")

    

    state1_h = apply_hadamard(state1, 0)  # 施加H门

    print(f"H门后: 振幅 = {state1_h.state_vector}")

    print(f"概率分布: {state1_h.get_probabilities()}")

    

    # 测试2：Pauli门

    print("\n【测试2】Pauli门")

    state_x = QuantumState(1)  # |0⟩

    state_x = apply_pauli_x(state_x, 0)  # X|0⟩ = |1⟩

    print(f"X|0⟩ = |1⟩: 振幅 = {state_x.state_vector}")

    

    state_y = QuantumState(1)

    state_y = apply_pauli_y(state_y, 0)

    print(f"Y|0⟩: 振幅 = {state_y.state_vector}")

    

    state_z = QuantumState(1)

    state_z = apply_pauli_z(state_z, 0)

    print(f"Z|0⟩: 振幅 = {state_z.state_vector}")

    

    # 测试3：CNOT门

    print("\n【测试3】CNOT门")

    state_cnot = QuantumState(2)  # |00⟩

    print(f"初始态 |00⟩: {state_cnot.state_vector}")

    

    # 设置为|10⟩态

    state_cnot.state_vector = np.array([0, 0, 1, 0], dtype=complex)

    print(f"输入态 |10⟩: {state_cnot.state_vector}")

    

    # CNOT: 控制位为1，目标位翻转 → |11⟩

    result = apply_cnot(state_cnot, 0, 1)

    print(f"CNOT|10⟩ = |11⟩: {result.state_vector}")

    

    # 测试4：Bell态（纠缠态）创建

    print("\n【测试4】创建Bell态 |Φ+⟩ = (|00⟩ + |11⟩)/√2")

    bell = QuantumState(2)  # |00⟩

    bell = create_bell_state(bell, 0, 1)  # 创建Bell态

    print(f"Bell态振幅: {bell.state_vector}")

    print(f"测量概率: {bell.get_probabilities()}")

    

    # 测试5：纠缠态的特性

    print("\n【测试5】纠缠态测量特性（不可分离）")

    for i in range(5):

        idx, probs = bell.measure()

        print(f"  测量结果: {format(idx, '02b')} (概率: {probs[idx]:.3f})")

    

    # 测试6：Toffoli门

    print("\n【测试6】Toffoli门（CCNOT）")

    state_toffoli = QuantumState(3)  # |000⟩

    state_toffoli.state_vector = np.array([0, 0, 0, 0, 0, 0, 1, 0], dtype=complex)  # |110⟩

    print(f"输入态 |110⟩: {state_toffoli.state_vector[6]}")

    result_toffoli = apply_toffoli(state_toffoli, 0, 1, 2)

    print(f"Toffoli|110⟩ = |111⟩: {result_toffoli.state_vector[7]}")

    

    # 测试7：量子门矩阵验证

    print("\n【测试7】量子门矩阵验证")

    print(f"Hadamard门矩阵:\n{H_GATE}")

    print(f"\nCNOT门矩阵:\n{CNOT_GATE}")

    

    print("\n" + "=" * 60)

    print("所有测试完成！")

    print("=" * 60)

