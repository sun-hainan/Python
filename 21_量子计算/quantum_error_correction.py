# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / quantum_error_correction

本文件实现 quantum_error_correction 相关的算法功能。
"""

import numpy as np


# =============================================================================
# 基础量子门 - Basic Quantum Gates
# =============================================================================

def hadamard():
    """
    返回Hadamard门：H = (1/√2)[[1,1],[1,-1]]
    用于在X基和Z基之间切换。
    """
    return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def pauli_x():
    """Pauli-X门（量子非门）：比特翻转。X|0⟩=|1⟩, X|1⟩=|0⟩"""
    return np.array([[0, 1], [1, 0]], dtype=complex)


def pauli_z():
    """Pauli-Z门：相位翻转。Z|0⟩=|0⟩, Z|1⟩=-|1⟩"""
    return np.array([[1, 0], [0, -1]], dtype=complex)


def cnot(control_qubit=0, target_qubit=1, total_qubits=2):
    """
    构建n量子比特CNOT门。

    参数：
        control_qubit: 控制比特索引（从0开始）
        target_qubit: 目标比特索引
        total_qubits: 总量子比特数

    返回：
        CNOT门矩阵（维度 2^total_qubits × 2^total_qubits）
    """
    dim = 2 ** total_qubits
    cnot_gate = np.zeros((dim, dim), dtype=complex)

    for row in range(dim):
        for col in range(dim):
            # 检查是否为恒等映射
            if row == col:
                cnot_gate[row, col] = 1.0

        # 如果控制位为1，则翻转目标位
        control_bit = (row >> (total_qubits - 1 - control_qubit)) & 1
        if control_bit == 1:
            target_bit = (row >> (total_qubits - 1 - target_qubit)) & 1
            flipped_row = row ^ (1 << (total_qubits - 1 - target_qubit))
            cnot_gate[flipped_row, row] = 1.0
            cnot_gate[row, row] = 0.0

    return cnot_gate


# =============================================================================
# 3-qubit Bit-Flip编码 - 3-Qubit Bit-Flip Code
# =============================================================================

def encode_3qubit_bitflip(logical_state):
    """
    将单量子比特逻辑态编码到3个物理量子比特。

    编码电路：
        |0_L⟩ = |000⟩, |1_L⟩ = |111⟩
        编码：|ψ⟩ → |ψ⟩|0⟩|0⟩ 然后用CNOT复制

    参数：
        logical_state: 2元素数组，[α, β]，逻辑量子比特状态

    返回：
        8元素数组，3物理量子比特的编码态向量
    """
    # |ψ⟩ = α|0⟩ + β|1⟩ 编码为 α|000⟩ + β|111⟩
    encoded = np.zeros(8, dtype=complex)
    encoded[0] = logical_state[0]  # |000⟩
    encoded[7] = logical_state[1]  # |111⟩

    return encoded


def apply_bit_flip_error(state, qubit_index, probability=1.0):
    """
    对指定量子比特施加bit-flip（X）错误。

    参数：
        state: 当前态向量
        qubit_index: 出错量子比特的索引（0,1,2）
        probability: 错误概率（1.0表示确定发生）

    返回：
        施加错误后的态向量
    """
    if np.random.random() > probability:
        return state  # 无错误

    dim = len(state)
    n_qubits = int(np.log2(dim))
    x_gate = np.kron(np.eye(2**qubit_index, dtype=complex),
                     np.kron(pauli_x(), np.eye(2**(n_qubits - qubit_index - 1), dtype=complex)))

    return x_gate @ state


def measure_syndrome_3qubit(state):
    """
    测量3-qubit bit-flip码的错误综合征（syndrome）。

    Stabilizer测量：
        Z₁Z₂（测量qubit 0和1的parity）
        Z₂Z₃（测量qubit 1和2的parity）

    Syndrome结果：
        (0,0) = 无错误
        (1,0) = qubit 0翻转
        (0,1) = qubit 2翻转
        (1,1) = qubit 1翻转

    参数：
        state: 编码后的3量子比特态向量（8维）

    返回：
        tuple[int,int]: (syndrome_bit_1, syndrome_bit_2)
    """
    dim = len(state)
    n_qubits = 3

    # 构建测量算符 Z⊗Z⊗I（对应Z₁Z₂）
    def z_z_measure(q1, q2):
        """测量q1和q2的Z⊗Z期望值"""
        # 测量矩阵：对应对角矩阵，|00⟩和|11⟩为+1，|01⟩和|10⟩为-1
        measure_op = np.zeros((dim, dim), dtype=complex)
        for i in range(dim):
            bit1 = (i >> (n_qubits - 1 - q1)) & 1
            bit2 = (i >> (n_qubits - 1 - q2)) & 1
            # Z⊗Z的本征值：相同为+1，不同为-1
            measure_op[i, i] = 1 if bit1 == bit2 else -1
        expectation = np.real(np.vdot(state, measure_op @ state))
        # 舍入到±1
        return 1 if expectation > 0 else -1

    # Z₁Z₂测量
    z1z2 = z_z_measure(0, 1)
    # Z₂Z₃测量
    z2z3 = z_z_measure(1, 2)

    # syndrome：+1对应0，-1对应1
    syndrome_1 = 0 if z1z2 == 1 else 1
    syndrome_2 = 0 if z2z3 == 1 else 1

    return syndrome_1, syndrome_2


def correct_bit_flip(state, syndrome):
    """
    根据syndrome纠正bit-flip错误。

    纠错规则：
        syndrome (0,0) → 无错误，无需纠正
        syndrome (1,0) → qubit 0翻转，施加X₀
        syndrome (0,1) → qubit 2翻转，施加X₂
        syndrome (1,1) → qubit 1翻转，施加X₁

    参数：
        state: 可能出错的编码态向量
        syndrome: (syndrome_bit1, syndrome_bit2)

    返回：
        纠正后的态向量
    """
    s1, s2 = syndrome
    n_qubits = 3
    dim = 8

    # 无错误
    if s1 == 0 and s2 == 0:
        return state

    # 确定需要翻转的量子比特
    if s1 == 1 and s2 == 0:
        flip_qubit = 0  # q0翻转
    elif s1 == 0 and s2 == 1:
        flip_qubit = 2  # q2翻转
    elif s1 == 1 and s2 == 1:
        flip_qubit = 1  # q1翻转
    else:
        return state

    # 构建X门作用于flip_qubit
    x_gate = np.kron(np.eye(2**flip_qubit, dtype=complex),
                     np.kron(pauli_x(), np.eye(2**(n_qubits - flip_qubit - 1), dtype=complex)))

    corrected = x_gate @ state

    return corrected


# =============================================================================
# 完整编码-错误-测量-纠错流程 - Full Encode-Error-Measure-Correct Pipeline
# =============================================================================

def quantum_error_correction_pipeline(logical_state, error_probability=0.3, verbose=True):
    """
    完整的量子错误纠正流程演示。

    流程：
        1. 编码：将逻辑量子比特编码为3个物理量子比特
        2. 信道错误：以给定概率施加bit-flip错误
        3. 测量：提取错误综合征（不破坏逻辑量子比特）
        4. 纠错：根据syndrome纠正错误
        5. 验证：解码并检查恢复的量子态

    参数：
        logical_state: 2元素复数数组 [α, β]，逻辑量子比特状态
        error_probability: 单个量子比特发生bit-flip错误的概率
        verbose: 是否打印详细信息

    返回：
        dict: 包含各步骤结果
    """
    if verbose:
        print(f"{'='*60}")
        print(f"量子错误纠正演示（bit-flip码）")
        print(f"{'='*60}")
        print(f"逻辑量子态: α={logical_state[0]:.4f}, β={logical_state[1]:.4f}")
        print(f"单比特错误概率: {error_probability}")

    # 步骤1：编码
    encoded_state = encode_3qubit_bitflip(logical_state)
    if verbose:
        print(f"\n[步骤1] 编码")
        print(f"  编码后态: {encoded_state}")

    # 步骤2：施加错误（每个量子比特独立可能出错）
    error_qubits = []
    state_after_error = encoded_state.copy()

    for q in range(3):
        if np.random.random() < error_probability:
            error_qubits.append(q)
            state_after_error = apply_bit_flip_error(state_after_error, q, probability=1.0)

    if verbose:
        print(f"\n[步骤2] 量子信道错误")
        if error_qubits:
            print(f"  发生bit-flip的量子比特: {error_qubits}")
        else:
            print(f"  无错误发生")

    # 步骤3：测量syndrome
    syndrome = measure_syndrome_3qubit(state_after_error)
    if verbose:
        print(f"\n[步骤3] Stabilizer测量")
        print(f"  Syndrome: {syndrome} → ", end="")
        syndrome_names = {
            (0, 0): "无错误",
            (1, 0): "q0翻转",
            (0, 1): "q2翻转",
            (1, 1): "q1翻转"
        }
        print(syndrome_names.get(syndrome, "未知"))

    # 步骤4：纠错
    corrected_state = correct_bit_flip(state_after_error, syndrome)
    if verbose:
        print(f"\n[步骤4] 纠错")
        print(f"  纠错后态: {corrected_state}")

    # 步骤5：解码并验证
    # 解码：从|ψ⟩|00⟩中提取|ψ⟩（取qubit 0的状态，边信息忽略）
    # 对于3-qubit码，解码就是取第一个量子比特的约化密度矩阵
    # 这里简化：直接比较纠正后的振幅与原始编码态
    fidelity = np.abs(np.vdot(encoded_state, corrected_state)) ** 2
    if verbose:
        print(f"\n[步骤5] 验证")
        print(f"  原始编码态: {encoded_state}")
        print(f"  纠正后态:   {corrected_state}")
        print(f"  态保真度: {fidelity:.4f}")
        print(f"  {'✓ 纠错成功' if fidelity > 0.99 else '✗ 纠错失败'}")

    return {
        'encoded': encoded_state,
        'error_qubits': error_qubits,
        'syndrome': syndrome,
        'corrected': corrected_state,
        'fidelity': fidelity
    }


def run_error_correction_trials(n_trials=20, error_prob=0.2):
    """
    运行多次纠错试验，统计成功率。

    参数：
        n_trials: 试验次数
        error_prob: 每量子比特错误概率

    返回：
        float: 纠错成功率
    """
    np.random.seed(42)  # 可重复性

    successes = 0
    for _ in range(n_trials):
        # 随机逻辑态
        alpha = np.random.rand() + 1j * np.random.rand()
        beta = np.random.rand() + 1j * np.random.rand()
        norm = np.sqrt(np.abs(alpha)**2 + np.abs(beta)**2)
        logical_state = np.array([alpha / norm, beta / norm])

        result = quantum_error_correction_pipeline(logical_state, error_prob, verbose=False)
        if result['fidelity'] > 0.99:
            successes += 1

    success_rate = successes / n_trials
    print(f"\n{'='*60}")
    print(f"纠错性能统计（{n_trials}次试验）")
    print(f"{'='*60}")
    print(f"错误概率: {error_prob}")
    print(f"成功率: {success_rate:.2%}")
    print(f"失败次数: {n_trials - successes}")

    return success_rate


# =============================================================================
# Shor码（9-qubit）简介 - Shor Code Introduction
# =============================================================================

def explain_shor_code():
    """
    打印Shor码（[9,1,3]码）的原理说明。
    Shor码是第一个能同时纠正bit-flip和phase-flip错误的量子码。
    """
    explanation = """
    ==============================================================
    9-qubit Shor码 [9, 1, 3]
    ==============================================================

    编码结构：
        |0_L⟩ = (|000⟩+|111⟩)(|000⟩+|111⟩)(|000⟩+|111⟩) / √8
        |1_L⟩ = (|000⟩-|111⟩)(|000⟩-|111⟩)(|000⟩-|111⟩) / √8

    可纠正错误：
        - 任意单量子比特的bit-flip错误（X错误）
        - 任意单量子比特的phase-flip错误（Z错误）
        - 距离d=3，能纠正最多1个任意量子错误

    电路结构：
        物理比特分组：[q0,q1,q2] [q3,q4,q5] [q6,q7,q8]
        - bit-flip保护：每组用3-qubit重复码
        - phase-flip保护：用Hadamard基纠缠三组

    与bit-flip码的比较：
        bit-flip码：只保护X错误
        phase-flip码：只保护Z错误
        Shor码：同时保护X和Z错误

    纠错开销：
        编码率 1/9（1个逻辑比特用9个物理比特）
        这是量子纠错的典型代价
    """
    print(explanation)


if __name__ == '__main__':
    # 设置随机种子以便调试
    np.random.seed(0)

    # 准备逻辑量子态
    alpha = 1.0 / np.sqrt(2)
    beta = 1.0 / np.sqrt(2)
    logical_state = np.array([alpha, beta])

    # 单次演示
    quantum_error_correction_pipeline(logical_state, error_probability=0.3)

    print()

    # 统计测试
    run_error_correction_trials(n_trials=20, error_prob=0.2)

    print()

    # Shor码说明
    explain_shor_code()
