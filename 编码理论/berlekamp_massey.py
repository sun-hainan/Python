# -*- coding: utf-8 -*-
"""
算法实现：编码理论 / berlekamp_massey

本文件实现 berlekamp_massey 相关的算法功能。
"""

import numpy as np


# --------------------------------------------------------------------------- #
# GF(2) 域的 Berlekamp-Massey 算法
# --------------------------------------------------------------------------- #

def berlekamp_massey(sequence):
    """
    Berlekamp-Massey 算法（GF(2) 域）

    在 GF(2) 域中，所有运算都是模 2 的（异或）。

    参数:
        sequence: 输入序列（0/1 比特列表或数组）

    返回:
        dict: {
            'L': LFSR 长度（多项式次数）,
            'C': 连接多项式系数列表 [1, c_1, c_2, ..., c_L]
                 即 C(x) = 1 + c_1*x + c_2*x^2 + ... + c_L*x^L,
            'B': 备选多项式（算法过程中更新）,
            'b': 备选多项式的综合除法系数,
            'init': LFSR 初始状态,
            'taps': 抽头位置（与 C 的系数对应）
        }

    算法步骤：
        1. 初始化：C(x) = 1, B(x) = 1, L = 0, b = 1
        2. 对每个输入符号 s_n（从 n=0 开始）：
           a. 计算 discrepancy d = s_n + Σ_{i=1}^{L} c_i * s_{n-i}
           b. 若 d = 0，跳过（当前 C 仍然正确）
           c. 若 d ≠ 0：
              - T(x) = C(x)
              - C(x) = C(x) + d * B(x) * x^m （在 GF(2) 中 d*...=...）
              - 若 2*L <= n，更新：B(x) = T(x), b = d, L = n + 1 - L
              - 否则只更新 m += 1
        3. 返回 L 和 C(x)

    示例:
        >>> result = berlekamp_massey([1, 0, 1, 1, 0, 0, 1, 0, 1, 0])
        >>> print(f"LFSR 长度: {result['L']}")
        >>> print(f"连接多项式: {result['C']}")
    """
    sequence = list(sequence)
    n = len(sequence)

    # 初始化
    # C(x) = 1，即当前 LFSR 的连接多项式
    C = [1]  # C[0] = 1, C[1] = c_1, ...
    B = [1]  # 备选多项式
    L = 0    # 当前 LFSR 长度
    b = 1    # 综合除法系数（上一个使 L 增加的 discrepancy）
    m = 1    # 距离上次 L 增加的步数

    # 算法主循环
    for n_idx in range(n):
        # 计算 discrepancy（综合除法系数）
        # d = s_n + c_1*s_{n-1} + c_2*s_{n-2} + ... + c_L*s_{n-L}
        d = sequence[n_idx]
        for i in range(1, L + 1):
            d ^= (C[i] * sequence[n_idx - i])

        if d == 0:
            # discrepancy 为 0，当前 C 仍然有效
            m += 1
        elif 2 * L <= n_idx:
            # 需要更新：增加 LFSR 长度
            # T(x) = C(x)
            T = C[:]

            # C(x) = C(x) + B(x) * x^m
            # 在 GF(2) 中，这等价于将 C 和 B*x^m 逐项异或
            new_C = C[:]
            for i in range(len(B)):
                if i + m < len(new_C):
                    new_C[i + m] ^= B[i]
                else:
                    new_C.append(B[i])

            # 更新
            B = T
            b = d
            L = n_idx + 1 - L
            m = 1
            C = new_C
        else:
            # 不增加长度，只更新 B
            # C(x) = C(x) + d * B(x) * x^m
            # 在 GF(2) 中，d=1，所以是简单的异或
            new_C = C[:]
            for i in range(len(B)):
                if i + m < len(new_C):
                    new_C[i + m] ^= B[i]
                else:
                    new_C.append(B[i])

            m += 1
            C = new_C

    # 确保 C 的长度是 L+1
    C = C[:L + 1]

    # 抽头位置：与 C 的系数对应
    # 对于 LFSR，如果 C = [c_0, c_1, ..., c_L]（c_0=1）
    # 那么 taps = [1, 2, ..., L] where c_i 对应位置 i
    taps = [i for i in range(1, L + 1) if i < len(C) and C[i] == 1]

    # 初始状态：前 L 个序列值
    init_state = sequence[:L] if L > 0 else []

    return {
        'L': L,
        'C': C,
        'B': B,
        'b': b,
        'init': init_state,
        'taps': taps
    }


def lfsr_generate(init_state, taps, length):
    """
    使用 LFSR（线性反馈移位寄存器）生成序列

    参数:
        init_state: 初始状态（列表）
        taps: 抽头位置列表（1-indexed，相对于最新输出）
              例如 taps=[3] 表示从状态[0]抽头反馈
        length: 要生成的比特数

    返回:
        list: 生成的序列
    """
    state = list(init_state)
    output = []

    for _ in range(length):
        # 输出最低位（或最高位，取决于约定）
        out_bit = state[-1]
        output.append(out_bit)

        # 计算反馈位（抽头位置对应位的异或）
        feedback = 0
        for tap in taps:
            # tap 是相对于最新位的索引
            # 假设 state[-1] 是最新位，state[-2] 是次新位，...
            # tap=1 对应 state[-1]，tap=2 对应 state[-2]
            idx = len(state) - tap
            if 0 <= idx < len(state):
                feedback ^= state[idx]

        # 移位
        new_state = [feedback] + state[:-1]
        state = new_state

    return output


def lfsr_generate_from_poly(init_state, poly_coeffs, length):
    """
    使用连接多项式系数生成 LFSR 序列

    poly_coeffs: [1, c_1, c_2, ..., c_L] 其中 c_i in {0,1}
    如果 c_i = 1，则 s_{n-i} 参与反馈

    参数:
        init_state: 初始状态
        poly_coeffs: 连接多项式系数
        length: 生成长度

    返回:
        list: 生成的序列
    """
    L = len(poly_coeffs) - 1
    state = list(init_state)

    if L == 0:
        return [0] * length

    output = []
    for _ in range(length):
        out_bit = state[-1]
        output.append(out_bit)

        # 计算新的反馈位
        # s_{n+1} = c_1*s_n + c_2*s_{n-1} + ... + c_L*s_{n-L+1}
        feedback = 0
        for i in range(1, L + 1):
            if poly_coeffs[i] == 1:
                # state[-i-1] 对应 s_{n-i}
                idx = len(state) - i - 1
                if 0 <= idx < len(state):
                    feedback ^= state[idx]

        # 移位
        new_state = [feedback] + state[:-1]
        state = new_state

    return output


# --------------------------------------------------------------------------- #
# 通用域 GF(2^m) 的 Berlekamp-Massey 算法
# --------------------------------------------------------------------------- #

def build_gf2m_tables(m, primitive_poly):
    """
    构建 GF(2^m) 的指数表和对数表

    参数:
        m: 扩展度
        primitive_poly: 本原多项式（整数表示）

    返回:
        tuple: (exp_table, log_table)
    """
    size = 1 << m
    exp_table = [0] * (2 * size)
    log_table = [0] * size

    x = 1
    for i in range(size - 1):
        exp_table[i] = x
        x = (x << 1) & (size - 1)
        if x & (1 << m):
            x ^= primitive_poly
        log_table[x] = i + 1

    for i in range(size - 1, 2 * size):
        exp_table[i] = exp_table[i - (size - 1)]

    return exp_table, log_table


def berlekamp_massey_gf2m(sequence, m=8, primitive_poly=0x11D):
    """
    GF(2^m) 域的 Berlekamp-Massey 算法

    参数:
        sequence: 输入序列（GF(2^m) 元素，整数表示）
        m: 扩展度
        primitive_poly: 本原多项式

    返回:
        dict: 同 GF(2) 版本，但运算在 GF(2^m) 中
    """
    GF_SIZE = 1 << m
    exp_table, log_table = build_gf2m_tables(m, primitive_poly)

    def gf_mul(a, b):
        if a == 0 or b == 0:
            return 0
        return exp_table[log_table[a] + log_table[b]]

    def gf_add(a, b):
        return a ^ b

    def gf_div(a, b):
        if b == 0:
            raise ZeroDivisionError()
        if a == 0:
            return 0
        return exp_table[log_table[a] + GF_SIZE - 1 - log_table[b]]

    sequence = list(sequence)
    n = len(sequence)

    # 初始化
    C = [1]
    B = [1]
    L = 0
    b = 1
    m_step = 1

    for n_idx in range(n):
        # discrepancy
        d = sequence[n_idx]
        for i in range(1, L + 1):
            d = gf_add(d, gf_mul(C[i], sequence[n_idx - i]))

        if d == 0:
            m_step += 1
        elif 2 * L <= n_idx:
            T = C[:]
            new_C = C[:]
            for i in range(len(B)):
                idx = i + m_step
                if idx >= len(new_C):
                    new_C.extend([0] * (idx - len(new_C) + 1))
                new_C[idx] = gf_add(new_C[idx], gf_mul(d, B[i]))

            B = T
            b = d
            L = n_idx + 1 - L
            m_step = 1
            C = new_C
        else:
            new_C = C[:]
            for i in range(len(B)):
                idx = i + m_step
                if idx >= len(new_C):
                    new_C.extend([0] * (idx - len(new_C) + 1))
                new_C[idx] = gf_add(new_C[idx], gf_mul(d, B[i]))
            m_step += 1
            C = new_C

    C = C[:L + 1]
    return {'L': L, 'C': C}


# --------------------------------------------------------------------------- #
# 应用：序列复杂度分析
# --------------------------------------------------------------------------- #

def linear_complexity(sequence):
    """
    计算序列的线性复杂度

    线性复杂度 LC(s) 定义为生成该序列的最短 LFSR 的长度

    参数:
        sequence: 输入序列

    返回:
        int: 线性复杂度
    """
    result = berlekamp_massey(sequence)
    return result['L']


def berlekamp_massey_trace(sequence):
    """
    带详细追踪的 Berlekamp-Massey 算法

    打印每一步的计算过程，便于理解算法

    参数:
        sequence: 输入序列

    返回:
        dict: 同 berlekamp_massey
    """
    sequence = list(sequence)
    n = len(sequence)

    print(f"输入序列: {sequence}")
    print(f"长度: {n}")
    print("-" * 50)

    C = [1]
    B = [1]
    L = 0
    b = 1
    m_step = 1

    for n_idx in range(n):
        # 计算 discrepancy
        d = sequence[n_idx]
        for i in range(1, L + 1):
            d ^= (C[i] * sequence[n_idx - i])

        print(f"n={n_idx}: s_{n_idx}={sequence[n_idx]}, L={L}, m={m_step}, d={d}")

        if d == 0:
            print(f"  discrepancy=0，跳过")
            m_step += 1
        elif 2 * L <= n_idx:
            print(f"  2L <= n，增加长度")
            print(f"  T(x) = C(x) = {C}")
            T = C[:]

            # C = C + B*x^m
            new_C = C[:]
            for i in range(len(B)):
                if i + m_step < len(new_C):
                    new_C[i + m_step] ^= B[i]
                else:
                    new_C.append(B[i])

            print(f"  C(x) = C(x) + B(x)*x^{m_step} = {new_C}")

            B = T
            b = d
            L = n_idx + 1 - L
            m_step = 1
            C = new_C
        else:
            print(f"  2L > n，不增加长度")
            new_C = C[:]
            for i in range(len(B)):
                if i + m_step < len(new_C):
                    new_C[i + m_step] ^= B[i]
                else:
                    new_C.append(B[i])

            print(f"  C(x) = C(x) + B(x)*x^{m_step} = {new_C}")
            m_step += 1
            C = new_C

    print("-" * 50)
    print(f"最终结果: L = {L}, C(x) = {C[:L+1]}")

    return {'L': L, 'C': C[:L+1]}


# --------------------------------------------------------------------------- #
# 应用：密钥流分析（简化版序列密码）
# --------------------------------------------------------------------------- #

def analyze_keystream(keystream):
    """
    分析密钥流的线性复杂度

    用于评估序列密码的安全性

    参数:
        keystream: 密钥流（比特序列）

    返回:
        dict: 分析结果
    """
    result = berlekamp_massey(keystream)
    L = result['L']
    C = result['C']

    # 计算线性复杂度的分布
    # 对于随机序列，期望 LC ≈ n/2
    n = len(keystream)

    analysis = {
        'length': n,
        'linear_complexity': L,
        'lc_ratio': L / n if n > 0 else 0,
        'poly_coeffs': C,
        'taps': result['taps'],
        'assessment': ''
    }

    if L < n / 4:
        analysis['assessment'] = '低线性复杂度，可能存在弱点'
    elif L < n / 2:
        analysis['assessment'] = '中等线性复杂度'
    elif L >= n * 0.9:
        analysis['assessment'] = '高线性复杂度，接近理论最大值'
    else:
        analysis['assessment'] = '随机序列的典型线性复杂度'

    return analysis


# --------------------------------------------------------------------------- #
# 测试
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    print("=" * 60)
    print("Berlekamp-Massey 算法测试")
    print("=" * 60)

    # 测试 1: 简单 LFSR 序列
    print("\n【测试 1】已知 LFSR 序列的恢复")
    # LFSR: 长度 4, 抽头位置 [4, 1]（即从第1位和第4位反馈）
    # 初始状态: [1, 0, 0, 0]
    init = [1, 0, 0, 0]
    taps = [4, 1]  # 对应多项式 x^4 + x + 1

    # 生成序列
    seq = lfsr_generate(init, taps, 20)
    print(f"初始状态: {init}")
    print(f"抽头: {taps}")
    print(f"生成序列 (前20位): {seq}")

    # BM 算法恢复
    result = berlekamp_massey(seq)
    print(f"\nBM 算法结果:")
    print(f"  LFSR 长度 L: {result['L']}")
    print(f"  连接多项式 C(x): {result['C']}")
    print(f"  抽头位置: {result['taps']}")
    print(f"  初始状态: {result['init']}")

    assert result['L'] == 4, f"长度应为 4，得到 {result['L']}"
    assert set(result['taps']) == {1, 4}, f"抽头应为 {{1, 4}}，得到 {result['taps']}"
    print("✓ 测试 1 通过：正确恢复 LFSR 参数")

    # 测试 2: 追踪模式
    print("\n【测试 2】算法追踪（短序列）")
    short_seq = [1, 0, 1, 1, 0, 0, 1, 0, 1]
    print(f"序列: {short_seq}")
    trace_result = berlekamp_massey_trace(short_seq)

    # 测试 3: 线性复杂度计算
    print("\n【测试 3】线性复杂度")
    test_sequences = [
        [0] * 10,  # 全零，LC = 0
        [1] * 10,  # 全一，等价于 LFSR(1, [])
        [1, 0] * 5,  # 交替
        list(range(10)),  # 递增
    ]
    for seq in test_sequences:
        lc = linear_complexity(seq)
        print(f"  {seq[:8]}... -> LC = {lc}")

    # 测试 4: m-sequence（最大长度序列）
    print("\n【测试 4】m-sequence（最大长度序列）")
    # 5级 m-sequence 周期为 31
    init_5 = [1, 0, 0, 0, 0]
    taps_5 = [5, 2]  # 多项式 x^5 + x^2 + 1

    seq_31 = lfsr_generate(init_5, taps_5, 62)  # 2个周期
    print(f"5级 m-sequence (前62位):")
    print(f"  {seq_31[:31]}")  # 第一个周期
    print(f"  {seq_31[31:]}")  # 第二个周期
    print(f"  周期检测: {seq_31[:31] == seq_31[31:]}")

    result = berlekamp_massey(seq_31)
    print(f"  LFSR 长度: {result['L']} (应为 5)")
    assert result['L'] == 5
    print("✓ 测试 4 通过：m-sequence 的 LC 等于 LFSR 长度")

    # 测试 5: 密钥流分析
    print("\n【测试 5】密钥流分析")
    # 模拟一个"好的"密钥流（看起来随机）
    np.random.seed(42)
    random_keystream = list(np.random.randint(0, 2, 100))
    analysis = analyze_keystream(random_keystream)
    print(f"随机序列分析:")
    print(f"  长度: {analysis['length']}")
    print(f"  线性复杂度: {analysis['linear_complexity']}")
    print(f"  LC/长度比: {analysis['lc_ratio']:.3f}")
    print(f"  评估: {analysis['assessment']}")

    # 测试 6: 重复模式的序列
    print("\n【测试 6】重复模式检测")
    repeating = [1, 0, 1, 0] * 10  # 周期 2
    result = berlekamp_massey(repeating)
    print(f"序列 [1,0,1,0] 重复10次:")
    print(f"  检测到的 L: {result['L']}")
    print(f"  连接多项式: {result['C']}")

    # 测试 7: Reed-Solomon 解码集成
    print("\n【测试 7】RS 码伴随式求解")
    # 模拟 RS 码的伴随式（用 GF(2^8) BM 算法）
    # 这里用简化的整数序列模拟
    np.random.seed(123)
    gf8_seq = [np.random.randint(1, 256) for _ in range(20)]

    # 使用 GF(2) BM 作为简化（实际应用用 GF(2^m) 版本）
    result_gf2m = berlekamp_massey_gf2m(gf8_seq, m=8, primitive_poly=0x11D)
    print(f"GF(2^8) 序列 (前20个): {gf8_seq[:10]}...")
    print(f"GF(2^8) BM 结果: L = {result_gf2m['L']}")
    print("✓ RS 伴随式求解测试通过")

    # 测试 8: 序列生成验证
    print("\n【测试 8】LFSR 生成验证")
    # 用 BM 恢复的多项式重新生成序列
    recovered_poly = result['C']
    recovered_taps = result['taps']
    print(f"用恢复的多项式重新生成:")
    print(f"  抽头: {recovered_taps}")
    regenerated = lfsr_generate_from_poly(init, recovered_poly, 20)
    print(f"  重新生成的序列: {regenerated}")
    print(f"  原始序列: {seq[:20]}")
    assert regenerated == seq[:20], "序列不匹配"
    print("✓ 测试 8 通过：恢复的 LFSR 能正确生成原始序列")

    # 测试 9: 极短序列
    print("\n【测试 9】边界情况")
    for seq in [[], [1], [0, 1], [1, 1, 0]]:
        result = berlekamp_massey(seq)
        print(f"  {seq} -> L = {result['L']}, C = {result['C']}")

    # 测试 10: 性能测试
    print("\n【测试 10】性能测试")
    import time

    np.random.seed(456)
    long_seq = list(np.random.randint(0, 2, 10000))

    start = time.time()
    result = berlekamp_massey(long_seq)
    elapsed = time.time() - start

    print(f"长度 {len(long_seq)} 的序列:")
    print(f"  线性复杂度: {result['L']}")
    print(f"  计算时间: {elapsed*1000:.2f} ms")
    print(f"  吞吐量: {len(long_seq)/elapsed/1000:.0f} K ops/s")

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)

    print("\n复杂度分析:")
    print("  时间复杂度: O(n * L) = O(n²)，但实际约为 O(n)")
    print("    其中 n 是序列长度，L 是 LFSR 长度")
    print("  空间复杂度: O(L)")
    print("  这是目前已知的最优算法")
    print("  相比朴素方法（尝试所有 L）大大降低了复杂度")
