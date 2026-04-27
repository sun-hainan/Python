# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / quantum_ftqc



本文件实现 quantum_ftqc 相关的算法功能。

"""



import numpy as np





# =============================================================================

# 常量 - Constants

# =============================================================================



PI = np.pi  # 圆周率





# =============================================================================

# 基础量子门 - Basic Quantum Gates

# =============================================================================



def hadamard():

    """

    返回单量子比特Hadamard门。

    H = (1/√2) [[1, 1], [1, -1]]

    作用：H|0⟩ = |+⟩, H|1⟩ = |−⟩

    """

    return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)





def phase_gate(angle):

    """

    返回相位门 T_k = diag(1, e^{2πi/2^k})，即绕Z轴旋转 2π/2^k。

    等价于 R_k gate。

    """

    return np.array([[1, 0], [0, np.exp(2j * PI / 2**angle)]], dtype=complex)





def controlled_phase(angle):

    """

    返回2量子比特受控相位门 CPhase(2π/2^angle)。



    矩阵形式：

    [[1, 0, 0, 0],

     [0, 1, 0, 0],

     [0, 0, 1, 0],

     [0, 0, 0, e^{2πi/2^angle}]]



    当控制比特为|1⟩且目标比特为|1⟩时，施加全局相位。

    """

    return np.array([

        [1, 0, 0, 0],

        [0, 1, 0, 0],

        [0, 0, 1, 0],

        [0, 0, 0, np.exp(2j * PI / 2**angle)]

    ], dtype=complex)





# =============================================================================

# QFT矩阵构建（矩阵乘法方式）- QFT Matrix Construction

# =============================================================================



def qft_matrix(n_qubits):

    """

    直接构建n量子比特QFT矩阵。

    用于验证电路实现的正确性。



    QFT|j⟩ = (1/√N) Σ_{k=0}^{N-1} e^{2πi·j·k/N} |k⟩



    参数：

        n_qubits: 量子比特数n



    返回：

        QFT矩阵（维度 2^n × 2^n）

    """

    N = 2 ** n_qubits

    qft = np.zeros((N, N), dtype=complex)



    for j in range(N):

        for k in range(N):

            qft[k, j] = np.exp(2j * PI * j * k / N) / np.sqrt(N)



    return qft





def iqft_matrix(n_qubits):

    """

    构建n量子比特逆QFT（IQFT）矩阵。

    IQFT = (QFT)^dagger / √N

    即 IQFT[j,k] = e^{-2πi·j·k/N} / √N

    """

    N = 2 ** n_qubits

    iqft = np.zeros((N, N), dtype=complex)



    for j in range(N):

        for k in range(N):

            iqft[k, j] = np.exp(-2j * PI * j * k / N) / np.sqrt(N)



    return iqft





# =============================================================================

# QFT电路构建 - QFT Circuit Construction (Gate-by-gate)

# =============================================================================



def build_qft_circuit_matrix(n_qubits, with_swaps=True):

    """

    构建QFT电路对应的总矩阵，模拟电路执行过程。



    QFT标准电路结构（n=3为例）：

        q0 ── H ── S ── T ── ●SWAP──

        q1 ── ●── H ── S ── ●SWAP──

        q2 ── ●── ●── H ── ●SWAP──



    其中：

        - 第i个量子比特先做Hadamard

        - 然后对所有 j>i 的比特施加受控-S/T门（角度 = 2π/2^{j-i+1}）

        - 末尾可能需要SWAP交换（因为QFT输出是倒位的）



    参数：

        n_qubits: 量子比特数

        with_swaps: 是否包含末尾的SWAP层（修正输出顺序）



    返回：

        QFT电路总矩阵（维度 2^n × 2^n）

    """

    dim = 2 ** n_qubits

    circuit_matrix = np.eye(dim, dtype=complex)



    # 对每个量子比特应用Hadamard + 受控旋转

    for i in range(n_qubits):

        # 第i个量子比特的Hadamard（需要提升到全空间）

        h_i = 1

        for _ in range(i):

            h_i = np.kron(h_i, np.eye(2))

        h_i = np.kron(h_i, hadamard())

        for _ in range(n_qubits - i - 1):

            h_i = np.kron(h_i, np.eye(2))



        circuit_matrix = h_i @ circuit_matrix



        # 对所有 j > i 的量子比特施加受控旋转

        for j in range(i + 1, n_qubits):

            angle = j - i + 1  # 旋转角度参数

            c_phase = controlled_phase(angle)

            # 将受控相位门提升到全空间

            gate = 1

            for k in range(n_qubits):

                if k == i:

                    gate = np.kron(gate, np.array([[1, 0], [0, 0]], dtype=complex))  # |0⟩⟨0| 投影

                elif k == j:

                    gate = np.kron(gate, np.array([[1, 0], [0, 1]], dtype=complex))  # 目标比特 |1⟩⟨1|

                else:

                    gate = np.kron(gate, np.eye(2))

            # 更简单的方法：直接用受控门构造

            gate = controlled_phase_gate_full(n_qubits, i, j, angle)

            circuit_matrix = gate @ circuit_matrix



    # 末尾SWAP层：QFT的输出是位序反转的，需要修正

    if with_swaps:

        swap_matrix = build_swap_circuit_matrix(n_qubits)

        circuit_matrix = swap_matrix @ circuit_matrix



    return circuit_matrix





def controlled_phase_gate_full(n_qubits, control_idx, target_idx, angle):

    """

    在n量子比特系统中构建受控相位门。



    参数：

        n_qubits: 总量子比特数

        control_idx: 控制比特索引（从0开始，左侧最高位）

        target_idx: 目标比特索引

        angle: 相位角度参数（对应 e^{2πi/2^angle}）



    返回：

        完整的受控相位门矩阵

    """

    dim = 2 ** n_qubits

    gate = np.eye(dim, dtype=complex)



    # 找到受控相位对应的行/列索引

    # 当 control_idx 比特为1 且 target_idx 比特为1 时施加相位

    for row in range(dim):

        for col in range(dim):

            # 检查 control_idx 位是否为1

            control_bit = (row >> (n_qubits - 1 - control_idx)) & 1

            target_bit_row = (row >> (n_qubits - 1 - target_idx)) & 1

            target_bit_col = (col >> (n_qubits - 1 - target_idx)) & 1

            if control_bit == 1 and target_bit_row == 1 and target_bit_col == 1:

                gate[row, col] = np.exp(2j * PI / 2**angle)



    return gate





def build_swap_circuit_matrix(n_qubits):

    """

    构建SWAP门序列矩阵，用于修正QFT输出的位序反转。



    SWAP(i, j) 交换量子比特i和j的位置。

    对于n量子比特，输出是自然顺序（高位是q0，低位是qn-1）。

    """

    dim = 2 ** n_qubits

    swap_full = np.eye(dim, dtype=complex)



    for i in range(n_qubits // 2):

        j = n_qubits - 1 - i

        if i >= j:

            break

        swap_full = swap_layer(swap_full, i, j, n_qubits)



    return swap_full





def swap_layer(matrix, i, j, n_qubits):

    """

    对n量子比特矩阵左乘一个SWAP(i,j)门。

    """

    dim = 2 ** n_qubits

    swap = np.eye(dim, dtype=complex)



    # 构建SWAP矩阵

    for row in range(dim):

        for col in range(dim):

            # 检查 row 和 col 是否仅在 i,j 位置不同

            row_i = (row >> (n_qubits - 1 - i)) & 1

            row_j = (row >> (n_qubits - 1 - j)) & 1

            col_i = (col >> (n_qubits - 1 - i)) & 1

            col_j = (col >> (n_qubits - 1 - j)) & 1



            if (row_i == col_i and row_j == col_j and

                (row >> (n_qubits - 1 - i)) & 1 == (col >> (n_qubits - 1 - j)) & 1 and

                (row >> (n_qubits - 1 - j)) & 1 == (col >> (n_qubits - 1 - i)) & 1):

                # 交换后的行索引

                new_row = row ^ (1 << (n_qubits - 1 - i)) ^ (1 << (n_qubits - 1 - j))

                new_col = col ^ (1 << (n_qubits - 1 - i)) ^ (1 << (n_qubits - 1 - j))

                if new_row == col and new_col == row:

                    swap[row, col] = 1



    return swap @ matrix





# =============================================================================

# 量子态的QFT变换 - QFT on Quantum State

# =============================================================================



def apply_qft_to_state(state_vector, n_qubits, with_swaps=True):

    """

    对n量子比特量子态向量应用QFT变换。



    参数：

        state_vector: 长度为2^n的态向量

        n_qubits: 量子比特数

        with_swaps: 是否包含末尾SWAP



    返回：

        变换后的态向量

    """

    # 方法1：直接用QFT矩阵

    qft = qft_matrix(n_qubits)

    result = qft @ state_vector



    if not with_swaps:

        # 需要补偿SWAP的逆效应（再次SWAP或直接取位序反转）

        # 这里我们用另一种电路模拟方式

        pass



    return result





# =============================================================================

# 电路门序列可视化 - Circuit Gate Sequence Visualization

# =============================================================================



def print_qft_circuit(n_qubits):

    """

    打印QFT电路的门序列（文本艺术形式）。



    参数：

        n_qubits: 量子比特数

    """

    print(f"\n{'='*60}")

    print(f"QFT电路（n={n_qubits}）门序列图示")

    print(f"{'='*60}")



    for i in range(n_qubits):

        label = f"q{i}"

        line = [label]



        # Hadamard on qubit i

        line.append("[H]")



        # Controlled phases to qubits j > i

        for j in range(i + 1, n_qubits):

            k = j - i

            gate_name = f"C{k}"

            line.append(f"──{gate_name}──")



        print(" ".join(line))



    print()





# =============================================================================

# 与经典FFT对比验证 - Comparison with Classical FFT

# =============================================================================



def verify_qft_classical_fft():

    """

    验证量子QFT与经典FFT的关系。

    两者数学上等价，但输入/输出形式不同：

    - 经典FFT：输入输出都是长度为N的复数列向量

    - 量子QFT：输入输出是量子态振幅（幅度相同，但意义不同）



    这里验证QFT矩阵的数学正确性（酉性、与经典FFT系数一致）。

    """

    print("=" * 60)

    print("验证QFT矩阵的数学性质")

    print("=" * 60)



    for n in [2, 3, 4, 5]:

        qft = qft_matrix(n)

        iqft = iqft_matrix(n)



        # 验证酉性：QFT · QFT^dagger = I

        identity_check = qft @ qft.conj().T

        is_unitary = np.allclose(identity_check, np.eye(2**n))



        # 验证IQFT是QFT的逆

        is_inverse = np.allclose(qft @ iqft, np.eye(2**n))



        # 验证FFT系数对应关系

        from numpy.fft import fft

        test_input = np.random.rand(2**n) + 1j * np.random.rand(2**n)

        fft_result = fft(test_input)

        qft_result = qft @ test_input

        # 两者只差全局相位因子，验证幅度相等

        magnitudes_match = np.allclose(np.abs(fft_result), np.abs(qft_result))



        print(f"n={n}: 酉性={is_unitary}, 逆QFT={is_inverse}, FFT幅度一致={magnitudes_match}")





def demo_qft_circuit():

    """

    演示QFT电路对|0⟩和|5⟩（二进制0101）状态的变换。

    """

    print("=" * 60)

    print("QFT电路演示")

    print("=" * 60)



    n_qubits = 4



    print_qft_circuit(n_qubits)



    # 对 |0⟩ 状态做QFT

    state_0 = np.zeros(2**n_qubits, dtype=complex)

    state_0[0] = 1.0



    qft = qft_matrix(n_qubits)

    state_qft_0 = qft @ state_0



    print(f"输入态 |0⟩")

    print(f"QFT|0⟩ 的振幅分布：")

    for k in range(min(8, len(state_qft_0))):

        amp = state_qft_0[k]

        prob = abs(amp) ** 2

        bar = "█" * int(prob * 40)

        print(f"  |{k:0{n_qubits}b}⟩: 幅值={amp:.4f}  概率={prob:.4f} {bar}")



    print()



    # 对 |5⟩ = |0101⟩ 状态做QFT

    state_5 = np.zeros(2**n_qubits, dtype=complex)

    state_5[5] = 1.0



    state_qft_5 = qft @ state_5



    print(f"输入态 |5⟩ = |0101⟩")

    print(f"QFT|5⟩ 的振幅分布（前8个基矢）：")

    for k in range(min(8, len(state_qft_5))):

        amp = state_qft_5[k]

        prob = abs(amp) ** 2

        bar = "█" * int(prob * 40)

        print(f"  |{k:0{n_qubits}b}⟩: 幅值={amp:.4f}  概率={prob:.4f} {bar}")



    print()





if __name__ == '__main__':

    demo_qft_circuit()

    print()

    verify_qft_classical_fft()

