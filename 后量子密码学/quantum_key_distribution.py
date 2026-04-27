# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / quantum_key_distribution



本文件实现 quantum_key_distribution 相关的算法功能。

"""



# ============================================================================

# 第一部分：量子信息基础

# ============================================================================



# quantum_bit（量子比特）

quantum_bit = {

    "qubit": "量子比特，|0>或|1>的叠加态",

    "superposition": "|ψ> = α|0> + β|1>，α,β为复数振幅",

    "measurement": "测量导致波函数坍缩，|α|²概率得到0，|β|²概率得到1",

    "no_cloning": "量子不可克隆定理：无法复制未知量子态"

}



# quantum_bases（量子测量基）

quantum_bases = {

    "rectilinear_basis（Z基）": {"|0>": (1, 0), "|1>": (0, 1), "测量": "区分|0>和|1>"},

    "diagonal_basis（X基）": {"|+>": (1/math.sqrt(2), 1/math.sqrt(2)), "|->": (1/math.sqrt(2), -1/math.sqrt(2)), "测量": "区分|+>和|->"}

}



# qubit_representation（量子比特表示）

qubit_representation = {

    "photon_polarization": "光子偏振态（H/V或+/×）",

    "horizontal": "H态（相当于|0>）",

    "vertical": "V态（相当于|1>）",

    "diagonal_plus": "+45°（相当于|+>）",

    "diagonal_minus": "-45°（相当于|->）"

}



# ============================================================================

# 第二部分：BB84协议原理

# ============================================================================



# bb84_protocol_overview（BB84协议概述）

bb84_protocol_overview = {

    "inventors": "Bennett和Brassard（1984）",

    "security_basis": "量子不可克隆定理 + 测量扰动原理",

    "key_element": "使用随机基编码，利用窃听必被检测的特性"

}



# bb84_encoding（BB84编码规则）

bb84_encoding = {

    "bit_0_in_Z": "水平偏振H（|0>）",

    "bit_1_in_Z": "垂直偏振V（|1>）",

    "bit_0_in_X": "+45°偏振（|+>）",

    "bit_1_in_X": "-45°偏振（|->）"

}



# bb84_decoding（BB84解码规则）

bb88_decoding = {

    "Z_basis_measurement": "测量H/V，区分0和1",

    "X_basis_measurement": "测量+/-，区分0和1",

    "wrong_basis": "用X基测量H/V，或用Z基测量+/-，结果随机"

}



# ============================================================================

# 第三部分：协议流程

# ============================================================================



# bb84_protocol_steps（BB84协议完整步骤）

def bb84_protocol_simulation(n_bits=20):

    """

    模拟BB84量子密钥分发协议

    

    Args:

        n_bits: 要分发的比特数

    

    Returns:

        dict: 协议执行记录

    """

    import random

    import secrets

    

    record = {

        "alice_bits": [],

        "alice_bases": [],

        "bob_bases": [],

        "alice_qubits": [],

        "bob_measurements": [],

        "sifted_bits": [],

        "sifted_bases": [],

        "error_positions": []

    }

    

    # Alice生成随机比特串

    alice_bits = [random.randint(0, 1) for _ in range(n_bits)]

    record["alice_bits"] = alice_bits

    

    # Alice随机选择测量基

    alice_bases = [random.choice(['Z', 'X']) for _ in range(n_bits)]

    record["alice_bases"] = alice_bases

    

    # Alice编码量子比特

    # Z基：0=H, 1=V

    # X基：0=+, 1=-

    alice_qubits = []

    for bit, base in zip(alice_bits, alice_bases):

        if base == 'Z':

            qubit = 'H' if bit == 0 else 'V'

        else:

            qubit = '+' if bit == 0 else '-'

        alice_qubits.append(qubit)

    record["alice_qubits"] = alice_qubits

    

    # Bob随机选择测量基

    bob_bases = [random.choice(['Z', 'X']) for _ in range(n_bits)]

    record["bob_bases"] = bob_bases

    

    # Bob测量（模拟）

    bob_measurements = []

    for qubit, base in zip(alice_qubits, bob_bases):

        if base == 'Z':

            # Z基测量：H->0, V->1

            if qubit in ['H', '+']:

                result = 0

            elif qubit in ['V', '-']:

                result = 1

            else:

                result = random.randint(0, 1)  # 错误基，随机结果

        else:

            # X基测量：+->0, -->1

            if qubit in ['+', 'H']:

                result = 0

            elif qubit in ['-', 'V']:

                result = 1

            else:

                result = random.randint(0, 1)  # 错误基，随机结果

        bob_measurements.append(result)

    record["bob_measurements"] = bob_measurements

    

    # 基底筛选（Sifting）：只保留相同基的比特

    sifted_indices = []

    sifted_alice_bits = []

    sifted_bob_bits = []

    

    for i in range(n_bits):

        if alice_bases[i] == bob_bases[i]:

            sifted_indices.append(i)

            sifted_alice_bits.append(alice_bits[i])

            sifted_bob_bits.append(bob_measurements[i])

    

    record["sifted_bits"] = {

        "alice": sifted_alice_bits,

        "bob": sifted_bob_bits

    }

    record["sifted_bases"] = alice_bases

    record["sifted_count"] = len(sifted_indices)

    

    # 错误检测：抽样比较部分比特

    sample_size = min(20, len(sifted_indices) // 2)

    error_positions = []

    

    if sample_size > 0:

        sample_indices = random.sample(range(len(sifted_alice_bits)), sample_size)

        for idx in sample_indices:

            if sifted_alice_bits[idx] != sifted_bob_bits[idx]:

                error_positions.append(idx)

    

    record["error_positions"] = error_positions

    record["error_rate"] = len(error_positions) / sample_size if sample_size > 0 else 0

    

    return record



# ============================================================================

# 第四部分：窃听检测

# ============================================================================



# eavesdropping_detection（窃听检测原理）

eavesdropping_detection = {

    "interceptor_attack": "窃听者拦截光子并用随机基测量",

    "measurement_disturbance": "错误基测量会扰动量子态",

    "error_rate_increase": "窃听导致错误率上升到50%",

    "detection_threshold": "错误率超过阈值则判定存在窃听"

}



# intercept_resend_attack（截取-重发攻击）

def intercept_resend_attack_simulation(n_bits=20):

    """

    模拟截取-重发攻击

    """

    import random

    

    # Alice生成

    alice_bits = [random.randint(0, 1) for _ in range(n_bits)]

    alice_bases = [random.choice(['Z', 'X']) for _ in range(n_bits)]

    

    # Alice编码

    alice_qubits = []

    for bit, base in zip(alice_bits, alice_bases):

        if base == 'Z':

            qubit = 'H' if bit == 0 else 'V'

        else:

            qubit = '+' if bit == 0 else '-'

        alice_qubits.append(qubit)

    

    # Eve截取并随机测量

    eve_bases = [random.choice(['Z', 'X']) for _ in range(n_bits)]

    eve_measurements = []

    for qubit, base in zip(alice_qubits, eve_bases):

        if base == 'Z':

            result = 0 if qubit in ['H', '+'] else 1

        else:

            result = 0 if qubit in ['+', 'H'] else 1

        eve_measurements.append(result)

    

    # Eve用测量结果重新编码并发送给Bob

    eve_qubits = []

    for result, base in zip(eve_measurements, eve_bases):

        if base == 'Z':

            qubit = 'H' if result == 0 else 'V'

        else:

            qubit = '+' if result == 0 else '-'

        eve_qubits.append(qubit)

    

    # Bob随机测量

    bob_bases = [random.choice(['Z', 'X']) for _ in range(n_bits)]

    bob_measurements = []

    for qubit, base in zip(eve_qubits, bob_bases):

        if base == 'Z':

            result = 0 if qubit in ['H', '+'] else 1

        else:

            result = 0 if qubit in ['+', 'H'] else 1

        bob_measurements.append(result)

    

    # 计算错误率

    sifted_indices = [i for i in range(n_bits) if alice_bases[i] == bob_bases[i]]

    errors = sum(1 for i in sifted_indices if alice_bits[i] != bob_measurements[i])

    error_rate = errors / len(sifted_indices) if sifted_indices else 0

    

    return error_rate



# ============================================================================

# 第五部分：密钥提炼

# ============================================================================



# key_distillation（密钥提炼步骤）

key_distillation = {

    "basis_sifting": "只保留相同基的比特",

    "error_estimation": "抽样比较检测错误率",

    "parameter_estimation": "如果错误率过高则丢弃",

    "information_reconciliation": "通过纠错消除比特差异",

    "privacy amplification": "哈希函数减少泄露信息给窃听者"

}



# privacy_amplification（隐私放大）

def privacy_amplification(raw_key, epsilon=0.1):

    """

    隐私放大：使用哈希函数从原始密钥提取安全密钥

    

    Args:

        raw_key: 原始密钥比特列表

        epsilon: 泄露给窃听者的信息比例上限

    

    Returns:

        list: 压缩后的安全密钥

    """

    import hashlib

    

    # 计算安全密钥长度

    n = len(raw_key)

    secure_len = int(n * (1 - epsilon))

    

    # 使用哈希函数提取

    key_bytes = bytes(raw_key)

    hash_obj = hashlib.sha256(key_bytes)

    digest = hash_obj.digest()

    

    # 从哈希值中提取secure_len比特

    secure_key = []

    bit_count = 0

    for byte in digest:

        for i in range(8):

            secure_key.append((byte >> (7 - i)) & 1)

            bit_count += 1

            if bit_count >= secure_len:

                return secure_key[:secure_len]

    

    return secure_key



# ============================================================================

# 第六部分：实际系统考虑

# ============================================================================



# practical_considerations（实际系统考虑）

practical_considerations = {

    "single_photon_source": "理想单光子源，实际使用概率性源",

    "detector_efficiency": "单光子探测器效率约50-80%",

    "dark_counts": "探测器暗计数导致错误",

    "quantum_channel_loss": "光纤损耗约0.2dB/km",

    "distance_limitation": "无中继约100km，有中继可达1000km+",

    "rate_vs_distance": "密钥生成率随距离指数下降"

}



# qkd_implementations（QKD实现方案）

qkd_implementations = {

    "fiber_based": "光纤QKD，商业化较成熟",

    "free_space": "自由空间QKD，卫星到地面",

    "decoy_state": "诱骗态QKD，应对光子数分离攻击",

    "measurement_device_independent": "MDI-QKD，排除探测器漏洞"

}



# ============================================================================

# 第七部分：安全性证明概要

# ============================================================================



# security_proof_outline（安全性证明概要）

security_proof_outline = {

    "quantum_channel_model": "Eve在量子通道上的操作受量子力学约束",

    "entanglement-based": "基于纠缠的安全性证明更一般",

    "devices_assumptions": "设备无关QKD无需信任设备",

    "composability": "组合安全性证明最终密钥安全"

}



# ============================================================================

# 主程序：演示BB84协议

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("量子密钥分发（QKD）：BB84协议实现")

    print("=" * 70)

    

    # 量子基础

    print("\n【量子比特】")

    for key, val in quantum_bit.items():

        print(f"  {key}: {val}")

    

    print("\n【测量基】")

    for basis, info in quantum_bases.items():

        print(f"  · {basis}")

        for k, v in info.items():

            print(f"    {k}: {v}")

    

    # BB84协议

    print("\n【BB84协议概述】")

    for key, val in bb84_protocol_overview.items():

        print(f"  {key}: {val}")

    

    print("\n【编码规则】")

    for encoding, desc in bb84_encoding.items():

        print(f"  · {encoding}: {desc}")

    

    # 协议执行

    print("\n【协议执行演示】")

    result = bb84_protocol_simulation(n_bits=20)

    

    print(f"  Alice原始比特: {result['alice_bits']}")

    print(f"  Alice测量基: {result['alice_bases']}")

    print(f"  Bob测量基: {result['bob_bases']}")

    print(f"  Bob测量结果: {result['bob_measurements']}")

    print(f"  筛选后比特数: {result['sifted_count']}")

    print(f"  Alice筛选后: {result['sifted_bits']['alice']}")

    print(f"  Bob筛选后: {result['sifted_bits']['bob']}")

    print(f"  抽样错误数: {len(result['error_positions'])}")

    print(f"  错误率: {result['error_rate']:.2%}")

    

    # 窃听检测

    print("\n【窃听检测】")

    for key, val in eavesdropping_detection.items():

        print(f"  · {key}: {val}")

    

    error_rate_with_eve = intercept_resend_attack_simulation(20)

    print(f"\n  窃听存在时的错误率: {error_rate_with_eve:.2%}")

    

    # 密钥提炼

    print("\n【密钥提炼步骤】")

    for step, desc in key_distillation.items():

        print(f"  · {step}: {desc}")

    

    # 隐私放大示例

    print("\n【隐私放大示例】")

    raw_key = result["sifted_bits"]["alice"]

    if raw_key:

        secure_key = privacy_amplification(raw_key)

        print(f"  原始密钥长度: {len(raw_key)} bits")

        print(f"  安全密钥长度: {len(secure_key)} bits")

    

    # 实际考虑

    print("\n【实际系统考虑】")

    for concern, desc in practical_considerations.items():

        print(f"  · {concern}: {desc}")

    

    print("\n【QKD实现方案】")

    for impl, desc in qkd_implementations.items():

        print(f"  · {impl}: {desc}")

    

    print("\n" + "=" * 70)

    print("BB84是量子密码学基础，利用量子力学原理实现理论安全的密钥分发")

    print("=" * 70)

