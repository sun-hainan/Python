# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / newhope_protocol



本文件实现 newhope_protocol 相关的算法功能。

"""



# ============================================================================

# 第一部分：NewHope协议概述

# ============================================================================



# newhope_overview（NewHope概述）

newhope_overview = {

    "full_name": "NewHope: Post-quantum key exchange based on RLWE",

    "proposers": "Alkim, Ducas, Pöppelmann, Schwabe (2016)",

    "based_on": "Ring-LWE问题",

    "nist_round": "NIST PQC标准化候选（已进入第4轮）",

    "variant": "NewHope-Compact, NewHope-Simple等"

}



# design_goals（设计目标）

design_goals = {

    "security": "基于最坏情况下格问题的安全性证明",

    "performance": "优化的NTT实现，高效快速",

    "simplicity": "简化的协议，易于实现",

    "bandwidth": "合理的密钥大小"

}



# ============================================================================

# 第二部分：参数选择

# ============================================================================



# newhope_parameters（NewHope参数）

newhope_parameters = {

    "n": 1024,  # 多项式次数（Ring维度）

    "q": 12289,  # 模数（素数）,

    "k": 8,  # 噪声参数

    "poly_bytes": 1824,  # 多项式字节数

    "seed_bytes": 32,  # 种子字节数

    "shared_key_bytes": 32  # 共享密钥长度

}



# ring_definition（环定义）

ring_definition = {

    "ring": "R_q = Z_q[x]/(x^n + 1)",

    "n_power_of_2": "n为2的幂次，便于FFT/NTT实现",

    "cyclotomic": "分圆多项式 x^n + 1",

    "invertible": "当n为2的幂次且q ≡ 1 mod 2n时，x^n+1的根在Z_q中"

}



# parameter_table（参数表）

parameter_table = {

    "newhope_512": {"n": 512, "q": 1065089},

    "newhope_1024": {"n": 1024, "q": 12289},

    "newhope_758": {"n": 758, "q": 4591},

    "newhope_1024_kem": {"n": 1024, "q": 12289}

}



# ============================================================================

# 第三部分：核心算法

# ============================================================================



# polynomial_sampling（多项式采样）

def sample_uniform(poly_bytes, q):

    """

    从均匀分布采样多项式系数

    

    Args:

        poly_bytes: 字节串

        q: 模数

    

    Returns:

        list: 系数数组

    """

    import struct

    

    coefficients = []

    for i in range(0, len(poly_bytes), 3):

        if i + 2 < len(poly_bytes):

            # 使用三个字节生成两个系数

            b0, b1, b2 = poly_bytes[i], poly_bytes[i+1], poly_bytes[i+2]

            d1 = (b0 + 256 * b1) % q

            d2 = (b1 + 256 * b2) % q

            coefficients.extend([d1, d2])

        else:

            break

    

    return coefficients[:1024]  # 截断到n=1024



def sample_gaussian(error_bytes, n, k, q):

    """

    从离散高斯分布采样（模拟）

    

    Args:

        error_bytes: 随机种子

        n: 多项式次数

        k: 噪声参数

        q: 模数

    

    Returns:

        list: 系数数组

    """

    import hashlib

    import random

    

    # 使用种子生成确定性随机数

    seed = int(hashlib.sha256(error_bytes).hexdigest()[:8], 16)

    random.seed(seed)

    

    coefficients = []

    for _ in range(n):

        # 简化的二项分布模拟

        noise = sum(random.randint(0, 1) for _ in range(k)) - k // 2

        coefficients.append(noise % q)

    

    return coefficients



# ============================================================================

# 第四部分：密钥生成

# ============================================================================



# newhope_key_generation（NewHope密钥生成）

def newhope_keygen(seed):

    """

    模拟NewHope密钥生成

    

    Args:

        seed: 随机种子（32字节）

    

    Returns:

        dict: 公钥和私钥

    """

    import hashlib

    

    n = newhope_parameters["n"]

    q = newhope_parameters["q"]

    k = newhope_parameters["k"]

    

    # 从种子派生随机字节

    hash_obj = hashlib.sha256(seed)

    random_bytes = hash_obj.digest() * 10  # 扩展

    

    # 生成秘密多项式s（噪声）

    s = sample_gaussian(random_bytes[:32], n, k, q)

    

    # 生成错误多项式e

    e = sample_gaussian(random_bytes[32:64], n, k, q)

    

    # 生成a（公开多项式，从种子生成或随机）

    a = sample_uniform(random_bytes[64:96], q)

    

    # 计算b = a * s + e (mod q)

    b = poly_mul(a, s, q)

    b = poly_add(b, e, q)

    

    return {

        "public_key": {"a": a, "b": b, "seed": seed[:32]},

        "secret_key": {"s": s},

        "description": "pk = (a, b = a*s + e), sk = s"

    }



# ============================================================================

# 第五部分：多项式运算

# ============================================================================



# poly_mul（多项式乘法，使用简化的O(n^2)实现）

def poly_mul(a, b, q):

    """

    多项式乘法 (a * b) mod (x^n + 1, q)

    """

    n = len(a)

    result = [0] * n

    

    for i in range(n):

        for j in range(n):

            idx = (i + j) % n

            if i + j >= n:  # x^n ≡ -1

                result[idx] = (result[idx] - a[i] * b[j]) % q

            else:

                result[idx] = (result[idx] + a[i] * b[j]) % q

    

    return result



def poly_add(a, b, q):

    """多项式加法"""

    return [(a[i] + b[i]) % q for i in range(len(a))]



def poly_sub(a, b, q):

    """多项式减法"""

    return [(a[i] - b[i]) % q for i in range(len(a))]



# ============================================================================

# 第六部分：密钥交换流程

# ============================================================================



# newhope_key_exchange（NewHope密钥交换）

def newhope_key_exchange():

    """

    模拟NewHope密钥交换流程

    """

    import secrets

    

    steps = {"alice": [], "bob": [], "shared": []}

    

    # 公共参数

    n = newhope_parameters["n"]

    q = newhope_parameters["q"]

    shared_key_bytes = newhope_parameters["shared_key_bytes"]

    

    steps["shared"].append(f"公共参数: n={n}, q={q}")

    

    # ===== Bob =====

    # Bob生成密钥对

    bob_seed = secrets.token_bytes(32)

    bob_keys = newhope_keygen(bob_seed)

    steps["bob"].append(f"Bob生成密钥对")

    steps["bob"].append(f"  发送: pk_bob = (a, b)")

    

    # ===== Alice =====

    # Alice收到pk_bob

    alice_seed = secrets.token_bytes(32)

    alice_keys = newhope_keygen(alice_seed)

    steps["alice"].append(f"Alice生成密钥对")

    

    # Alice计算 shared secret ss_a

    # ss_a = b * s_a + e_a'（使用pk_bob和s_a）

    pk_bob = bob_keys["public_key"]

    s_a = alice_keys["secret_key"]["s"]

    

    # 模拟计算

    b_sa = poly_mul(pk_bob["b"], s_a, q)

    steps["alice"].append(f"  计算: ss_a = b * s_a + e'")

    alice_ss = b_sa[:shared_key_bytes]  # 简化为取前几个系数

    

    # Alice发送enc_a给Bob

    enc_a = {"a": pk_bob["a"], "b": b_sa}

    steps["alice"].append(f"  发送: enc_a = (a, b')")

    

    # ===== Bob收到enc_a =====

    s_b = bob_keys["secret_key"]["s"]

    

    # Bob计算 ss_b = enc_a[1] * s_b

    enc_b1 = enc_a["b"]

    ss_b = poly_mul(enc_b1, s_b, q)

    steps["bob"].append(f"  计算: ss_b = b' * s_b")

    steps["bob"].append(f"  验证: ss_a == ss_b")

    

    # 模拟密钥匹配

    steps["shared"].append(f"  共享密钥（前8字节）: {ss_b[:8]}")

    

    return steps



# ============================================================================

# 第七部分：安全性分析

# ============================================================================



# security_reduction（安全性归约）

security_reduction = {

    "worst_case_to_average": "从最坏情况下Ring-LWE归约到平均情况",

    "ring_hardness": "格问题的难度与环的结构相关",

    "quantum_security": "抗量子攻击，无已知有效量子算法"

}



# security_parameters（安全参数）

security_parameters = {

    "classical_security": "约256位安全（NewHope-1024）",

    "quantum_security": "约128位安全（Grover加速后）",

    "nist_security_levels": "符合NIST PQC的5级安全标准"

}



# ============================================================================

# 第八部分：与其他PQC KEX比较

# ============================================================================



# comparison_with_other_kex（与其他密钥交换比较）

comparison_with_other_kex = {

    "vs_kyber": {

        "efficiency": "两者都使用优化的NTT",

        "key_size": "NewHope: 1824 bytes, Kyber-768: 1184 bytes",

        "maturity": "Kyber已被NIST选中"

    },

    "vs_ntru": {

        "bandwidth": "NewHope略高",

        "performance": "两者性能相近",

        "consistency": "NTRU有更长的历史"

    },

    "vs_sidh": {

        "key_size": "SIDH最小（378字节）",

        "computation": "NewHope更快",

        "maturity": "两者都在NIST标准化中"

    }

}



# ============================================================================

# 主程序：演示NewHope协议

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("NewHope密钥交换协议详解")

    print("=" * 70)

    

    # 概述

    print("\n【NewHope概述】")

    for key, val in newhope_overview.items():

        print(f"  {key}: {val}")

    

    print("\n【设计目标】")

    for key, val in design_goals.items():

        print(f"  · {key}: {val}")

    

    # 参数

    print("\n【参数选择】")

    for param, value in newhope_parameters.items():

        print(f"  {param}: {value}")

    

    print("\n【环定义】")

    for key, val in ring_definition.items():

        print(f"  {key}: {val}")

    

    print("\n【参数变体】")

    for variant, params in parameter_table.items():

        print(f"  {variant}: n={params['n']}, q={params['q']}")

    

    # 密钥交换流程

    print("\n【密钥交换流程】")

    exchange = newhope_key_exchange()

    

    print("\n  [公共参数]")

    for s in exchange["shared"]:

        print(f"    {s}")

    

    print("\n  [Alice]")

    for s in exchange["alice"]:

        print(f"    {s}")

    

    print("\n  [Bob]")

    for s in exchange["bob"]:

        print(f"    {s}")

    

    # 安全性

    print("\n【安全性归约】")

    for key, val in security_reduction.items():

        print(f"  · {key}: {val}")

    

    print("\n【安全参数】")

    for key, val in security_parameters.items():

        print(f"  · {key}: {val}")

    

    # 比较

    print("\n【与其他PQC密钥交换比较】")

    for other, diff in comparison_with_other_kex.items():

        print(f"\n  [vs {other}]")

        for aspect, desc in diff.items():

            print(f"    · {aspect}: {desc}")

    

    print("\n" + "=" * 70)

    print("NewHope是基于Ring-LWE的高效后量子密钥交换方案")

    print("=" * 70)

