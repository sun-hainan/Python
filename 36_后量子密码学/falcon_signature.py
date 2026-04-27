# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / falcon_signature



本文件实现 falcon_signature 相关的算法功能。

"""



# ============================================================================

# 第一部分：Falcon概述

# ============================================================================



# falcon_overview（Falcon概述）

falcon_overview = {

    "full_name": "Fast Fourier Lattice-based Compact Signatures over NTRU",

    "proposers": "Prest, Gürel, Lyubashevsky, Pöppelmann (2016)",

    "based_on": "NTRU格 + Fiat-Shamir框架",

    "nist_round": "NIST PQC标准化，第3轮进入",

    "signature_size": "约666字节（Falcon-512），非常紧凑"

}



# design_goals（设计目标）

falcon_design_goals = {

    "compactness": "签名大小紧凑（比Dilithium小）",

    "fast_verification": "使用FFT/NTT加速验证",

    "security": "基于NTRU问题的安全性证明",

    "practicality": "适合实际部署"

}



# ============================================================================

# 第二部分：参数

# ============================================================================



# falcon_parameters（Falcon参数）

falcon_parameters = {

    "falcon_512": {

        "n": 512,

        "q": 12289,

        "sigma": 1.2,

        "bits_security": 128,

        "pk_size": 897,

        "sk_size": 1281,

        "sig_size": 666

    },

    "falcon_1024": {

        "n": 1024,

        "q": 12289,

        "sigma": 1.2,

        "bits_security": 256,

        "pk_size": 1793,

        "sk_size": 2593,

        "sig_size": 1280

    }

}



# ring_definition（环定义）

falcon_ring = {

    "ring": "R = Z[x]/(x^n + 1)",

    "n_power_of_2": "n为2的幂次（512或1024）",

    "coefficient_modulus": "q = 12289（素数）"

}



# ============================================================================

# 第三部分：NTRU格

# ============================================================================



# ntru_lattice（NTRU格定义）

ntru_lattice = {

    "definition": "由(f, g)对生成的网格",

    "h": "公钥，h = g/f mod q",

    "f": "私钥，短多项式",

    "g": "私钥，短多项式",

    "basis": "[[qI, h], [0, I]]形式的2n×2n矩阵"

}



# ntru_problem（NTRU问题）

ntru_problem = {

    "problem": "给定h = g/f mod q，恢复短多项式f, g",

    "hardness": "在适当参数下无已知有效算法",

    "quantum_resistance": "抗量子攻击"

}



# ============================================================================

# 第四部分：高斯采样

# ============================================================================



# gaussian_sampling（高斯采样）

def gaussian_sample_centered(n, sigma):

    """

    从中心高斯分布采样整数向量

    

    Args:

        n: 采样维度

        sigma: 标准差

    

    Returns:

        list: 采样结果

    """

    import random

    import math

    

    samples = []

    for _ in range(n):

        # 简化的离散高斯采样

        # 使用拒绝采样

        while True:

            x = int(random.gauss(0, sigma))

            if abs(x) <= 3 * sigma:  # 截断

                samples.append(x)

                break

    

    return samples



# falcon_sampling（Falcon特定的采样）

def falcon_gaussian_sampling(z, sigma, B):

    """

    模拟Falcon的FFT域高斯采样

    

    Args:

        z: 输入多项式（频域）

        sigma: 标准差

        B: 范数界

    

    Returns:

        tuple: (采样结果, 范数)

    """

    import math

    

    # 简化的采样过程

    n = len(z)

    result = []

    total_norm_sq = 0

    

    for coeff in z:

        # 在FFT域采样（简化）

        sample = int(random.gauss(0, sigma))

        result.append(sample)

        total_norm_sq += sample ** 2

    

    norm = math.sqrt(total_norm_sq)

    

    # 验证是否在界内

    within_bound = norm <= B

    

    return result, norm, within_bound



# ============================================================================

# 第五部分：密钥生成

# ============================================================================



# falcon_key_generation（Falcon密钥生成）

def falcon_keygen(n=512, q=12289):

    """

    模拟Falcon密钥生成

    

    Args:

        n: 多项式次数

        q: 模数

    

    Returns:

        dict: 公钥和私钥

    """

    import random

    import math

    

    # 生成短多项式f和g

    # 模拟：从高斯分布采样

    def sample_short_poly(length, std=1.2):

        coeffs = []

        for _ in range(length):

            x = int(random.gauss(0, std))

            if abs(x) > 3:

                x = random.choice([-1, 0, 1])

            coeffs.append(x)

        return coeffs

    

    f = sample_short_poly(n)

    g = sample_short_poly(n)

    

    # 计算F和G使得 f*G - g*F = q

    # 简化：使用伪逆计算

    F = [-gi % q for gi in g]

    G = [fi % q for fi in f]

    

    # 调整使得 f*G - g*F = q

    # 简化处理

    for i in range(n):

        F[i] = (-g[i] + q) % q

        G[i] = f[i] % q

    

    # 计算公钥 h = g * f^{-1} mod q

    # 简化：h = g/f mod q

    h = []

    for i in range(n):

        # 模拟 f^{-1} * g

        h_val = (g[i] * 1) % q  # 简化

        h.append(h_val)

    

    return {

        "public_key": {"h": h, "n": n, "q": q},

        "secret_key": {"f": f, "F": F, "g": g, "G": G},

        "description": "pk = h = g/f, sk = (f, F, g, G) where f*G - g*F = q"

    }



# ============================================================================

# 第六部分：签名

# ============================================================================



# falcon_signing（Falcon签名过程）

def falcon_sign(message, secret_key, n=512, q=12289, sigma=1.2):

    """

    模拟Falcon签名

    

    Args:

        message: 待签名消息

        secret_key: 私钥

        n: 多项式次数

        q: 模数

        sigma: 高斯参数

    

    Returns:

        tuple: (签名, 成功标志)

    """

    import hashlib

    

    f = secret_key["f"]

    F = secret_key["F"]

    g = secret_key["g"]

    G = secret_key["G"]

    

    # 计算消息哈希

    m_hash = hashlib.sha256(message).digest()

    

    # 生成随机种子（实际使用哈希和计数器）

    random.seed(int.from_bytes(m_hash[:8], 'big'))

    

    # 生成c（挑战多项式）

    c = [random.randint(0, q-1) for _ in range(n)]

    

    # 计算s = c * f mod (x^n+1)

    s_f = []

    for i in range(n):

        val = 0

        for j in range(n):

            idx = (i + j) % n

            if i + j >= n:

                val -= c[j] * f[idx]

            else:

                val += c[j] * f[idx]

        s_f.append(val % q)

    

    # 采样s_g（从分布D_{Z^n, sigma}采样）

    s_g = gaussian_sample_centered(n, sigma)

    

    # 计算s = s_g + s_f * G/F 近似

    # 简化：组合

    s = [(s_g[i] + s_f[i]) % q for i in range(n)]

    

    # 计算范数

    norm_sq = sum(x**2 for x in s)

    norm = math.sqrt(norm_sq)

    

    # 验证签名条件：||s|| <= B

    B = sigma * math.sqrt(n) * 2  # 范数界

    

    if norm <= B:

        return {

            "c": c,

            "s": s,

            "norm": norm,

            "B": B,

            "success": True

        }

    else:

        return {"success": False, "norm": norm, "B": B}



# ============================================================================

# 第七部分：验证

# ============================================================================



# falcon_verify（Falcon验证）

def falcon_verify(message, signature, public_key, B):

    """

    验证Falcon签名

    

    Args:

        message: 消息

        signature: 签名 (c, s)

        public_key: 公钥h

        B: 范数界

    

    Returns:

        bool: 验证结果

    """

    import hashlib

    

    c = signature["c"]

    s = signature["s"]

    h = public_key["h"]

    

    # 检查||s|| <= B

    norm_sq = sum(x**2 for x in s)

    norm = math.sqrt(norm_sq)

    

    if norm > B:

        return False

    

    # 计算t = s + c * h

    t = []

    for i in range(len(s)):

        t_val = s[i]

        for j in range(len(c)):

            idx = (i + j) % len(s)

            if i + j >= len(s):

                t_val -= c[j] * h[idx]

            else:

                t_val += c[j] * h[idx]

        t.append(t_val % public_key["q"])

    

    # 重新计算c' = Hash(message || t)

    combined = message + bytes(t[:32])

    c_hash = hashlib.sha256(combined).digest()

    

    # 比较c和c'

    c_bytes = bytes(c[:32])

    verified = (c_bytes == c_hash[:len(c_bytes)])

    

    return verified



# ============================================================================

# 第八部分：安全性分析

# ============================================================================



# falcon_security（Falcon安全性）

falcon_security = {

    "hardness_assumption": "NTRU问题 + Hash函数抗碰撞",

    "classical_security": "128位（Falcon-512），256位（Falcon-1024）",

    "quantum_security": "Grover加速后约64-128位",

    "reduction": "从NTRU最坏情况到平均情况的证明"

}



# attacks_on_falcon（潜在攻击）

attacks_on_falcon = {

    "pruning_attack": "对签名范数的攻击",

    "lattice_reduction": "BKZ/LLL攻击NTRU格",

    "forgery_attack": "构造有效签名的尝试"

}



# ============================================================================

# 主程序：演示Falcon

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("Falcon签名算法详解")

    print("=" * 70)

    

    # 概述

    print("\n【Falcon概述】")

    for key, val in falcon_overview.items():

        print(f"  {key}: {val}")

    

    print("\n【设计目标】")

    for key, val in falcon_design_goals.items():

        print(f"  · {key}: {val}")

    

    # 参数

    print("\n【参数】")

    for variant, params in falcon_parameters.items():

        print(f"\n  [{variant}]")

        for param, value in params.items():

            print(f"    {param}: {value}")

    

    # NTRU格

    print("\n【NTRU格】")

    for key, val in ntru_lattice.items():

        print(f"  {key}: {val}")

    

    # 密钥生成

    print("\n【密钥生成演示】")

    keys = falcon_keygen(n=512, q=12289)

    print(f"  公钥h长度: {len(keys['public_key']['h'])}")

    print(f"  私钥f长度: {len(keys['secret_key']['f'])}")

    

    # 签名

    print("\n【签名演示】")

    message = b"Hello, Falcon!"

    sig_result = falcon_sign(message, keys["secret_key"])

    

    if sig_result["success"]:

        print(f"  签名成功")

        print(f"  签名范数: {sig_result['norm']:.2f}")

        print(f"  范数界B: {sig_result['B']:.2f}")

        print(f"  c长度: {len(sig_result['c'])}")

        print(f"  s长度: {len(sig_result['s'])}")

    else:

        print(f"  签名失败（范数{ sig_result['norm']:.2f}超过界{sig_result['B']:.2f}）")

    

    # 验证

    print("\n【验证演示】")

    if sig_result["success"]:

        B = sig_result["B"]

        verified = falcon_verify(message, sig_result, keys["public_key"], B)

        print(f"  验证结果: {verified}")

    

    # 安全性

    print("\n【安全性】")

    for key, val in falcon_security.items():

        print(f"  {key}: {val}")

    

    print("\n【潜在攻击】")

    for attack, desc in attacks_on_falcon.items():

        print(f"  · {attack}: {desc}")

    

    # 与其他签名比较

    print("\n【与Dilithium比较】")

    print("  · 签名大小: Falcon < Dilithium（更紧凑）")

    print("  · 密钥大小: Dilithium < Falcon（更小）")

    print("  · 验证速度: Falcon（FFT）通常更快")

    print("  · 实现复杂度: Dilithium更简单")

    

    print("\n" + "=" * 70)

    print("Falcon是最高效的基于格签名之一，签名非常紧凑")

    print("=" * 70)

