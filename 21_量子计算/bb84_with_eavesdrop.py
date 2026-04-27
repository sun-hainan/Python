# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / bb84_with_eavesdrop

本文件实现 bb84_with_eavesdrop 相关的算法功能。
"""

import numpy as np
import random


# =============================================================================
# 基矢定义 - Basis Definitions
# =============================================================================

# Z基（计算基）光电离方向：|0⟩和|1⟩
Z_BASIS = {
    '0': np.array([1, 0], dtype=complex),   # 水平偏振|0⟩
    '1': np.array([0, 1], dtype=complex)    # 垂直偏振|1⟩
}

# X基（对角基/哈达玛基）：|+⟩和|−⟩
X_BASIS = {
    '0': np.array([1, 1], dtype=complex) / np.sqrt(2),   # |+⟩ = (|0⟩+|1⟩)/√2
    '1': np.array([1, -1], dtype=complex) / np.sqrt(2)  # |−⟩ = (|0⟩−|1⟩)/√2
}

# Hadamard门矩阵（用于基矢切换）
HADAMARD = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


# =============================================================================
# 模拟光子生成与测量 - Photon Generation and Measurement
# =============================================================================

def generate_photon(bit_value, basis):
    """
    生成一个单光子态。

    参数：
        bit_value: str, '0'或'1'，编码的比特值
        basis: str, 'Z'或'X'，使用的基矢

    返回：
        np.ndarray, 2维复数向量，表示光子态
    """
    if basis == 'Z':
        return Z_BASIS[bit_value].copy()
    else:  # basis == 'X'
        return X_BASIS[bit_value].copy()


def measure_photon(photon_state, basis):
    """
    测量光子态在指定基下的结果。

    测量规则：
        - 若测量基与发送基相同，结果确定（完美关联）
        - 若测量基与发送基不同，结果随机（50/50，无关联）

    参数：
        photon_state: 光子态向量
        basis: 测量基'Z'或'X'

    返回：
        str: '0'或'1'，测量结果
    """
    if basis == 'Z':
        # 在Z基下测量：直接取投影概率
        prob_0 = np.abs(photon_state[0]) ** 2
        result = '0' if np.random.random() < prob_0 else '1'
    else:  # basis == 'X'
        # 变换到X基：H @ |ψ⟩
        transformed = HADAMARD @ photon_state
        prob_0 = np.abs(transformed[0]) ** 2
        result = '0' if np.random.random() < prob_0 else '1'

    return result


# =============================================================================
# Alice端：发送方 - Alice: Sender
# =============================================================================

def alice_send_qubits(n_bits):
    """
    Alice生成随机比特和随机基矢，发送量子态。

    参数：
        n_bits: 要发送的比特数量

    返回：
        tuple: (alice_bits, alice_bases, photon_states)
            alice_bits: 随机比特列表
            alice_bases: 基矢列表（'Z'或'X'）
            photon_states: 发送的光子态列表
    """
    alice_bits = [random.choice(['0', '1']) for _ in range(n_bits)]
    alice_bases = [random.choice(['Z', 'X']) for _ in range(n_bits)]
    photon_states = [generate_photon(alice_bits[i], alice_bases[i])
                     for i in range(n_bits)]

    return alice_bits, alice_bases, photon_states


# =============================================================================
# Eve端：窃听者 - Eavesdropper
# =============================================================================

def eve_intercept(photon_states, eavesdrop_strategy='random'):
    """
    Eve的窃听策略：截获-测量-重发。

    窃听方法：
        1. 随机选择测量基（50% Z基，50% X基）
        2. 测量光子获取比特
        3. 按原基矢重发（若猜对基矢则无错误，若猜错则引错误）

    关键问题：
        - Eve不知道Alice使用的真实基矢
        - 随机测量导致25%比特出错（因为只有50%概率猜对基矢）

    参数：
        photon_states: 光子态列表
        eavesdrop_strategy: 窃听策略（目前只实现随机策略）

    返回：
        list: Eve测得的比特列表
    """
    eve_bits = []
    eve_bases = [random.choice(['Z', 'X']) for _ in range(len(photon_states))]

    for photon, eve_basis in zip(photon_states, eve_bases):
        eve_bit = measure_photon(photon, eve_basis)
        eve_bits.append(eve_bit)

    return eve_bits, eve_bases


def eve_resend(photon_states, eve_bits, eve_bases):
    """
    Eve将测量后的比特以自己的基矢重发给Bob。

    注意：Eve测量会改变原始态（若猜错基矢），所以重发的态可能是错的。
    """
    resent_states = [generate_photon(eve_bits[i], eve_bases[i])
                     for i in range(len(photon_states))]
    return resent_states


# =============================================================================
# Bob端：接收方 - Bob: Receiver
# =============================================================================

def bob_receive(photon_states, n_bits):
    """
    Bob随机选择测量基，测量接收到的光子。

    参数：
        photon_states: 接收的光子态列表（可能被Eve修改）
        n_bits: 比特数量

    返回：
        tuple: (bob_bits, bob_bases)
    """
    bob_bases = [random.choice(['Z', 'X']) for _ in range(n_bits)]
    bob_bits = [measure_photon(photon_states[i], bob_bases[i])
                for i in range(n_bits)]

    return bob_bits, bob_bases


# =============================================================================
# 经典协商过程 - Classical Sifting and Key Generation
# =============================================================================

def sift_keys(alice_bits, alice_bases, bob_bits, bob_bases):
    """
    基矢筛选：保留Alice和Bob使用相同基矢的比特。

    公开信道：
        Alice告诉Bob她使用了哪些基矢（但不透露比特值）
        Bob告诉Alice他使用了哪些基矢
        双方保留基矢一致的位置

    参数：
        alice_bits, alice_bases: Alice的比特和基矢
        bob_bits, bob_bases: Bob的比特和基矢

    返回：
        tuple: (sifted_alice_bits, sifted_bob_bits, sifted_indices)
    """
    sifted_alice = []
    sifted_bob = []
    sifted_indices = []

    for i in range(len(alice_bits)):
        if alice_bases[i] == bob_bases[i]:
            sifted_indices.append(i)
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(bob_bits[i])

    return sifted_alice, sifted_bob, sifted_indices


def check_error_rate(alice_bits, bob_bits, sample_size=None):
    """
    计算两串比特之间的误码率（用于窃听检测）。

    参数：
        alice_bits, bob_bits: 两串比特
        sample_size: 抽样大小（若为None则用全部）

    返回：
        float: 误码率（0到1之间）
    """
    if len(alice_bits) == 0:
        return 0.0

    if sample_size is None or sample_size >= len(alice_bits):
        sample_indices = list(range(len(alice_bits)))
    else:
        sample_indices = random.sample(range(len(alice_bits)), sample_size)

    errors = sum(1 for i in sample_indices if alice_bits[i] != bob_bits[i])
    return errors / len(sample_indices)


# =============================================================================
# 窃听检测与安全判定 - Eavesdrop Detection
# =============================================================================

def detect_eavesdropper(alice_bits, bob_bits, security_threshold=0.15, verbose=True):
    """
    通过抽样比较检测是否存在窃听。

    安全标准：
        - 无窃听时，误码率来自信道噪声（通常<1%）
        - 有窃听时，Eve随机测量引入约25%错误
        - 阈值通常设为11%（BB84标准）

    参数：
        alice_bits, bob_bits: 筛选后的比特串
        security_threshold: 安全阈值，超过此值判定为有窃听
        verbose: 是否打印详细信息

    返回：
        bool: True表示安全（无窃听），False表示检测到窃听
    """
    if len(alice_bits) < 10:
        if verbose:
            print(f"[窃听检测] 比特数太少（{len(alice_bits)}），无法有效检测")
        return True

    # 抽取一部分公开比较
    check_count = min(len(alice_bits) // 2, 100)  # 最多检查100个
    check_indices = random.sample(range(len(alice_bits)), check_count)

    alice_check = [alice_bits[i] for i in check_indices]
    bob_check = [bob_bits[i] for i in check_indices]

    # 计算抽样误码率
    sampled_error_rate = check_error_rate(alice_check, bob_check, sample_size=None)

    if verbose:
        print(f"\n[窃听检测]")
        print(f"  抽样数量: {check_count}")
        print(f"  抽样误码率: {sampled_error_rate:.2%}")
        print(f"  安全阈值: {security_threshold:.2%}")
        print(f"  抽样比较的比特（已公开，不用于最终密钥）")

    # 移除已公开比较的比特，保留剩余比特作为最终密钥
    kept_indices = [i for i in range(len(alice_bits)) if i not in check_indices]
    final_alice = [alice_bits[i] for i in kept_indices]
    final_bob = [bob_bits[i] for i in kept_indices]

    if sampled_error_rate > security_threshold:
        if verbose:
            print(f"  判定: ⚠️  检测到窃听！误码率超过阈值")
        return False
    else:
        if verbose:
            print(f"  判定: ✓   信道安全，继续生成最终密钥")
        return True


# =============================================================================
# 完整BB84协议模拟（带窃听检测）- Full BB84 Protocol Simulation
# =============================================================================

def run_bb84_with_eavesdrop(n_bits=100, eavesdrop=True, eavesdrop_prob=1.0,
                             security_threshold=0.15, verbose=True):
    """
    完整的BB84协议运行模拟，包含可选的窃听检测。

    完整流程：
        1. Alice生成随机比特和基矢，发送光子
        2. (可选) Eve截获测量并重发
        3. Bob随机基矢测量接收光子
        4. 基矢筛选：保留使用相同基矢的比特
        5. 窃听检测：抽样比较，判定安全性
        6. 输出最终安全密钥（或报警）

    参数：
        n_bits: 发送的光子总数
        eavesdrop: 是否启用窃听
        eavesdrop_prob: Eve窃听每个光子的概率
        security_threshold: 窃听检测阈值
        verbose: 是否打印详细过程

    返回：
        dict: 包含各步骤结果
    """
    if verbose:
        print(f"{'='*60}")
        print(f"BB84量子密钥分发协议")
        print(f"{'='*60}")
        print(f"参数: n_bits={n_bits}, eavesdrop={eavesdrop}, threshold={security_threshold}")

    # 步骤1: Alice生成并发送
    alice_bits, alice_bases, photon_states = alice_send_qubits(n_bits)
    if verbose:
        print(f"\n[步骤1] Alice生成{n_bits}个随机比特和基矢，发送量子态")

    # 步骤2: Eve窃听（如果启用）
    if eavesdrop:
        # Eve以一定概率截获
        eve_photon_indices = [i for i in range(n_bits) if random.random() < eavesdrop_prob]
        if verbose:
            print(f"\n[步骤2] Eve窃听（截获{len(eve_photon_indices)}/{n_bits}个光子）")

        # Eve测量并重发
        eve_bits, eve_bases = eve_intercept(
            [photon_states[i] for i in eve_photon_indices],
            eavesdrop_strategy='random'
        )
        photon_states_with_eave = photon_states.copy()
        resent = eve_resend(
            [photon_states[i] for i in eve_photon_indices],
            eve_bits, eve_bases
        )
        for idx, resent_state in zip(eve_photon_indices, resent):
            photon_states_with_eave[idx] = resent_state

        photon_states = photon_states_with_eave

    # 步骤3: Bob接收并测量
    bob_bits, bob_bases = bob_receive(photon_states, n_bits)
    if verbose:
        print(f"\n[步骤3] Bob随机基矢测量接收光子")

    # 步骤4: 基矢筛选
    sifted_alice, sifted_bob, sifted_indices = sift_keys(
        alice_bits, alice_bases, bob_bits, bob_bases
    )
    if verbose:
        print(f"\n[步骤4] 基矢筛选")
        print(f"  原始比特数: {n_bits}")
        print(f"  筛选后比特数: {len(sifted_alice)}")
        print(f"  筛选率: {len(sifted_alice)/n_bits:.2%}（理论≈50%）")

    # 步骤5: 窃听检测
    is_secure = detect_eavesdropper(
        sifted_alice, sifted_bob,
        security_threshold=security_threshold,
        verbose=verbose
    )

    # 步骤6: 生成最终密钥（如果安全）
    final_key = []
    if is_secure:
        # 去除抽样检测用的比特
        final_key = sifted_alice  # Alice和Bob的密钥相同（无误码）
        if verbose:
            print(f"\n[步骤6] 最终安全密钥生成成功")
            print(f"  密钥长度: {len(final_key)} bits")
            print(f"  密钥预览: {''.join(final_key[:20])}...")
    else:
        if verbose:
            print(f"\n[步骤6] ⚠️ 检测到窃听，协议中止，不生成密钥")

    return {
        'alice_bits': alice_bits,
        'alice_bases': alice_bases,
        'bob_bits': bob_bits,
        'bob_bases': bob_bases,
        'sifted_alice': sifted_alice,
        'sifted_bob': sifted_bob,
        'sifted_indices': sifted_indices,
        'is_secure': is_secure,
        'final_key': final_key if is_secure else None,
        'eavesdrop_detected': not is_secure
    }


def compare_eavesdrop_strategies(n_bits=200):
    """
    比较无窃听vs有窃听时的BB84表现。

    参数：
        n_bits: 每次运行的比特数
    """
    print(f"{'='*60}")
    print(f"窃听策略对比实验")
    print(f"{'='*60}")

    # 无窃听
    result_no_eave = run_bb84_with_eavesdrop(
        n_bits=n_bits, eavesdrop=False, verbose=False
    )

    # 有窃听（Eve截获所有光子）
    result_eave = run_bb84_with_eavesdrop(
        n_bits=n_bits, eavesdrop=True, eavesdrop_prob=1.0,
        security_threshold=0.15, verbose=False
    )

    # 窃听50%的光子
    result_partial = run_bb84_with_eavesdrop(
        n_bits=n_bits, eavesdrop=True, eavesdrop_prob=0.5,
        security_threshold=0.15, verbose=False
    )

    print(f"\n实验结果汇总（n={n_bits}）：")
    print(f"{'策略':<20} {'安全':<10} {'密钥长度':<10} {'检测结果':<15}")
    print(f"{'-'*55}")
    print(f"{'无窃听':<20} {'✓':<10} {len(result_no_eave['final_key']):<10} {'—':<15}")
    print(f"{'Eve截获100%':<20} {'✗' if not result_eave['is_secure'] else '✓':<10} "
          f"{len(result_eave['final_key']) if result_eave['final_key'] else 0:<10} "
          f"{'检测到窃听' if result_eave['eavesdrop_detected'] else '未检测':<15}")
    print(f"{'Eve截获50%':<20} {'✗' if not result_partial['is_secure'] else '✓':<10} "
          f"{len(result_partial['final_key']) if result_partial['final_key'] else 0:<10} "
          f"{'检测到窃听' if result_partial['eavesdrop_detected'] else '未检测':<15}")


if __name__ == '__main__':
    random.seed(42)
    np.random.seed(42)

    # 单次演示（带窃听）
    run_bb84_with_eavesdrop(n_bits=100, eavesdrop=True,
                              eavesdrop_prob=1.0, security_threshold=0.15)

    print()
    compare_eavesdrop_strategies(n_bits=200)
