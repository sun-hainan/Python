# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / bb84_protocol



本文件实现 bb84_protocol 相关的算法功能。

"""



import numpy as np

import random





# =============================================================================

# 基矢定义 (Basis Definitions)

# =============================================================================



# Z基（计算基）

Z_BASIS = {

    '0': np.array([1, 0], dtype=complex),

    '1': np.array([0, 1], dtype=complex)

}



# X基（对角基/哈达玛基）

X_BASIS = {

    '0': np.array([1, 1], dtype=complex) / np.sqrt(2),  # |+⟩

    '1': np.array([1, -1], dtype=complex) / np.sqrt(2)  # |−⟩

}



# 基矢名称到矩阵的映射

BASIS_MATRICES = {

    'Z': np.array([[1, 0], [0, 1]], dtype=complex),  # 单位矩阵

    'X': np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)  # Hadamard门

}





# =============================================================================

# 量子态编码与解码 (Quantum State Encoding and Decoding)

# =============================================================================



def encode_qubit(bit_value, basis):

    """

    使用指定基矢编码比特为量子态

    

    Args:

        bit_value: 比特值 (0 或 1)

        basis: 基矢类型 ('Z' 或 'X')

        

    Returns:

        量子态向量 (2维复数)

    """

    bit_str = str(bit_value)

    if basis == 'Z':

        return Z_BASIS[bit_str].copy()

    elif basis == 'X':

        return X_BASIS[bit_str].copy()

    else:

        raise ValueError(f"未知的基矢类型: {basis}")





def measure_qubit(state, basis):

    """

    使用指定基矢测量量子态

    

    基于Born规则返回测量结果

    

    Args:

        state: 量子态向量

        basis: 测量基矢 ('Z' 或 'X')

        

    Returns:

        measurement_result: 0 或 1

        probabilities: 各结果的概率

    """

    if basis == 'Z':

        # Z基测量：|0⟩和|1⟩基

        probs = np.abs(state) ** 2

        result = np.random.choice(2, p=probs)

    elif basis == 'X':

        # X基测量：|+⟩和|−⟩基

        plus = np.array([1, 1], dtype=complex) / np.sqrt(2)

        minus = np.array([1, -1], dtype=complex) / np.sqrt(2)

        

        prob_plus = np.abs(np.vdot(plus, state)) ** 2

        prob_minus = 1 - prob_plus

        

        probs = [prob_plus, prob_minus]

        result = np.random.choice(2, p=probs)

        if result == 1:

            result = 1  # |−⟩

        else:

            result = 0  # |+⟩

    else:

        raise ValueError(f"未知的基矢类型: {basis}")

    

    return result, probs





def apply_eavesdropper_attack(state, basis):

    """

    模拟窃听者的截取-重发攻击

    

    Eve随机选择基矢测量，然后根据测量结果重新发送

    

    Args:

        state: 被拦截的量子态

        basis: Eve选择的测量基矢

        

    Returns:

        eve_state: Eve重发的量子态

        eve_measurement: Eve的测量结果

    """

    # Eve随机选择基矢测量

    eve_basis = random.choice(['Z', 'X'])

    result, _ = measure_qubit(state, eve_basis)

    

    # Eve根据测量结果准备新态

    new_state = encode_qubit(result, eve_basis)

    

    return new_state, eve_basis, result





# =============================================================================

# BB84协议模拟 (BB84 Protocol Simulation)

# =============================================================================



class BB84Protocol:

    """

    BB84量子密钥分发协议模拟类

    

    Attributes:

        num_bits: 原始比特数

        alice_bits: Alice的随机比特

        alice_bases: Alice的基矢选择

        bob_bases: Bob的基矢选择

        alice_states: Alice发送的量子态

        bob_results: Bob的测量结果

        sifted_key: 基矢一致时的密钥

        error_rate: 误码率

    """

    

    def __init__(self, num_bits=100, eavesdropping=False):

        """

        初始化BB84协议

        

        Args:

            num_bits: 原始比特数

            eavesdropping: 是否模拟窃听

        """

        self.num_bits = num_bits

        self.eavesdropping = eavesdropping

        

        # Alice的设置

        self.alice_bits = None

        self.alice_bases = None

        self.alice_states = None

        

        # Bob的设置

        self.bob_bases = None

        self.bob_results = None

        

        # 结果

        self.sifted_key_alice = []

        self.sifted_key_bob = []

        self.error_rate = 0.0

    

    def alice_prepare(self):

        """Alice准备随机比特和基矢，编码量子态"""

        # Alice生成随机比特

        self.alice_bits = [random.randint(0, 1) for _ in range(self.num_bits)]

        

        # Alice随机选择基矢

        self.alice_bases = [random.choice(['Z', 'X']) for _ in range(self.num_bits)]

        

        # Alice编码量子态

        self.alice_states = []

        for i in range(self.num_bits):

            state = encode_qubit(self.alice_bits[i], self.alice_bases[i])

            self.alice_states.append(state)

        

        return self.alice_states

    

    def bob_measure(self, states):

        """

        Bob测量接收到的量子态

        

        Args:

            states: Alice发送的量子态列表

            

        Returns:

            Bob的测量结果

        """

        # Bob随机选择测量基矢

        self.bob_bases = [random.choice(['Z', 'X']) for _ in range(self.num_bits)]

        

        # Bob测量每个量子态

        self.bob_results = []

        for i, state in enumerate(states):

            if self.eavesdropping and random.random() < 0.5:

                # 模拟窃听

                state, _, _ = apply_eavesdropper_attack(state, self.bob_bases[i])

            

            result, _ = measure_qubit(state, self.bob_bases[i])

            self.bob_results.append(result)

        

        return self.bob_results

    

    def sifting(self):

        """基矢筛选：只保留基矢一致时的比特"""

        self.sifted_key_alice = []

        self.sifted_key_bob = []

        matching_indices = []

        

        for i in range(self.num_bits):

            if self.alice_bases[i] == self.bob_bases[i]:

                # 基矢一致，保留

                self.sifted_key_alice.append(self.alice_bits[i])

                self.sifted_key_bob.append(self.bob_results[i])

                matching_indices.append(i)

        

        return matching_indices

    

    def calculate_error_rate(self, sample_indices=None, sample_size=20):

        """

        计算误码率（通过抽样）

        

        Args:

            sample_indices: 指定抽样索引

            sample_size: 抽样大小

            

        Returns:

            估计的误码率

        """

        if sample_indices is None:

            # 随机选择抽样位置

            if len(self.sifted_key_alice) < sample_size:

                sample_indices = range(len(self.sifted_key_alice))

            else:

                sample_indices = random.sample(

                    range(len(self.sifted_key_alice)), 

                    sample_size

                )

        

        errors = 0

        total = 0

        

        for i in sample_indices:

            if self.sifted_key_alice[i] != self.sifted_key_bob[i]:

                errors += 1

            total += 1

        

        if total > 0:

            self.error_rate = errors / total

        else:

            self.error_rate = 0

        

        return self.error_rate

    

    def error_correction(self):

        """

        经典纠错（简化版本）

        

        实际使用奇偶校验级联码或LDPC码

        

        Returns:

            纠错后的密钥

        """

        # 简化：假设纠错完美，密钥一致

        return self.sifted_key_alice.copy()

    

    def privacy_amplification(self, key, final_length=None):

        """

        隐私放大：从原始密钥提取更短的最终密钥

        

        使用哈希函数减少Eve可能知道的信息

        

        Args:

            key: 纠错后的密钥

            final_length: 最终密钥长度

            

        Returns:

            最终密钥

        """

        if final_length is None:

            # 简化：最终长度为原始长度的一半

            final_length = len(key) // 2

        

        # 简化实现：随机选择final_length个比特

        if final_length > len(key):

            final_length = len(key)

        

        selected_indices = random.sample(range(len(key)), final_length)

        final_key = [key[i] for i in selected_indices]

        

        return final_key

    

    def run_protocol(self, verbose=True):

        """

        运行完整的BB84协议

        

        Args:

            verbose: 是否打印详细信息

            

        Returns:

            最终密钥

        """

        if verbose:

            print("=" * 60)

            print("BB84量子密钥分发协议")

            print("=" * 60)

            print(f"原始比特数: {self.num_bits}")

        

        # Alice准备

        if verbose:

            print("\n[Alice] 生成随机比特和基矢...")

        self.alice_prepare()

        

        # Bob测量

        if verbose:

            print("[Bob] 随机选择测量基矢并测量...")

        self.bob_measure(self.alice_states)

        

        # 基矢筛选

        if verbose:

            print("\n[基矢筛选] 公布基矢，只保留一致的...")

        matching = self.sifting()

        if verbose:

            print(f"  匹配比特数: {len(self.sifted_key_alice)}/{self.num_bits}")

        

        # 误码率估计

        if verbose:

            print("\n[误码率检测] 抽样比较...")

        error_rate = self.calculate_error_rate()

        if verbose:

            print(f"  估计误码率: {error_rate:.1%}")

        

        if self.eavesdropping and error_rate > 0:

            if verbose:

                print("  ⚠️ 检测到窃听！误码率异常")

        elif error_rate == 0:

            if verbose:

                print("  ✓ 误码率为零，可能存在窃听或无窃听")

        # 纠错

        if verbose:

            print("\n[纠错] 经典纠错...")

        corrected_key = self.error_correction()

        

        # 隐私放大

        if verbose:

            print("[隐私放大] 提取最终密钥...")

        final_key = self.privacy_amplification(corrected_key)

        

        if verbose:

            print(f"\n最终密钥长度: {len(final_key)}")

            print(f"最终密钥: {''.join(map(str, final_key[:20]))}...")

            print("=" * 60)

        

        return final_key





# =============================================================================

# 安全性分析 (Security Analysis)

# =============================================================================



def simulate_eavesdropping_attack(num_bits=100, eve_attack_prob=0.5):

    """

    模拟存在窃听者的BB84协议

    

    Args:

        num_bits: 原始比特数

        eve_attack_prob: Eve攻击的概率

        

    Returns:

        (without_eve, with_eve): 无窃听和有窃听时的结果

    """

    # 无窃听

    protocol_clean = BB84Protocol(num_bits, eavesdropping=False)

    key_clean = protocol_clean.run_protocol(verbose=False)

    

    # 有窃听

    protocol_eve = BB84Protocol(num_bits, eavesdropping=True)

    key_eve = protocol_eve.run_protocol(verbose=False)

    

    return {

        'without_eve': {

            'key_length': len(key_clean),

            'error_rate': protocol_clean.error_rate

        },

        'with_eve': {

            'key_length': len(key_eve),

            'error_rate': protocol_eve.error_rate

        }

    }





def calculate_key_rate(error_rate, security_parameter=0.1):

    """

    计算最终密钥率

    

    基于私密区(privacy region)模型

    

    Args:

        error_rate: 误码率

        security_parameter: 安全参数

        

    Returns:

        密钥率（密钥长度/原始比特数）

    """

    if error_rate > security_parameter:

        # 误码率过高，存在窃听

        return 0

    

    # 简化：密钥率 = 1 - 2 * error_rate（粗略估计）

    # 实际需要考虑纠错开销和隐私放大

    key_rate = max(0, 0.5 - error_rate)

    

    return key_rate





# =============================================================================

# 测试代码 (Test Code)

# =============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("BB84量子密钥分发协议测试")

    print("=" * 70)

    

    # 测试1：基本编码和解码

    print("\n【测试1】量子态编码与解码")

    

    print("Z基编码:")

    for bit in [0, 1]:

        state = encode_qubit(bit, 'Z')

        print(f"  比特{bit} → Z基态: {state}")

    

    print("\nX基编码:")

    for bit in [0, 1]:

        state = encode_qubit(bit, 'X')

        print(f"  比特{bit} → X基态: {state}")

    

    # 测试2：测量

    print("\n" + "-" * 70)

    print("\n【测试2】量子测量")

    

    test_states = [

        (np.array([1, 0], dtype=complex), 'Z', 0),  # |0⟩用Z基测量

        (np.array([1, 0], dtype=complex), 'X', 0),  # |0⟩用X基测量

        (np.array([0, 1], dtype=complex), 'Z', 1),  # |1⟩用Z基测量

    ]

    

    for state, basis, expected in test_states:

        result, probs = measure_qubit(state, basis)

        print(f"  测量态{state} in {basis}基: 结果={result}, 概率={probs}")

    

    # 测试3：无窃听的BB84协议

    print("\n" + "-" * 70)

    print("\n【测试3】无窃听的BB84协议")

    

    protocol = BB84Protocol(num_bits=50, eavesdropping=False)

    final_key = protocol.run_protocol()

    

    print(f"\n最终密钥: {final_key}")

    print(f"密钥长度: {len(final_key)}")

    

    # 测试4：有窃听的BB84协议

    print("\n" + "-" * 70)

    print("\n【测试4】有窃听的BB84协议")

    

    protocol_eve = BB84Protocol(num_bits=50, eavesdropping=True)

    final_key_eve = protocol_eve.run_protocol()

    

    print(f"\n误码率: {protocol_eve.error_rate:.1%}")

    print(f"最终密钥: {final_key_eve}")

    

    # 测试5：多次实验统计

    print("\n" + "-" * 70)

    print("\n【测试5】多次实验统计")

    

    n_trials = 20

    clean_errors = []

    eve_errors = []

    

    for _ in range(n_trials):

        # 无窃听

        p1 = BB84Protocol(100, eavesdropping=False)

        p1.run_protocol(verbose=False)

        clean_errors.append(p1.error_rate)

        

        # 有窃听

        p2 = BB84Protocol(100, eavesdropping=True)

        p2.run_protocol(verbose=False)

        eve_errors.append(p2.error_rate)

    

    print(f"无窃听 平均误码率: {np.mean(clean_errors):.3f}")

    print(f"有窃听 平均误码率: {np.mean(eve_errors):.3f}")

    

    # 测试6：安全性验证

    print("\n" + "-" * 70)

    print("\n【测试6】安全性验证")

    

    print("BB84协议安全性原理：")

    print("""

    1. 量子不可克隆：Eve无法完美复制量子态

    2. 测量扰动：Eve的测量会引入误差

    3. 基矢不匹配：随机基矢选择防止Eve获取全部信息

    

    Eve的策略：

    - 截取-重发：测量后重新发送，会引入25%误码率

    - 纠缠测量：最优攻击，但也引入10%误码率

    

    检测窃听：

    - 抽样检查误码率

    - 如果误码率超过阈值，放弃密钥

    """)

    

    # 测试7：密钥率计算

    print("\n" + "-" * 70)

    print("\n【测试7】密钥率与误码率关系")

    

    error_rates = [0, 0.05, 0.10, 0.15, 0.20]

    for er in error_rates:

        rate = calculate_key_rate(er)

        print(f"  误码率 {er:.0%} → 密钥率 {rate:.3f}")

    

    print("\n" + "=" * 70)

    print("BB84量子密钥分发协议测试完成！")

    print("=" * 70)

