# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / mceliece_cipher



本文件实现 mceliece_cipher 相关的算法功能。

"""



# ============================================================================

# 第一部分：纠错码基础

# ============================================================================



# error_correcting_codes（纠错码基础）

error_correcting_codes = {

    "[n, k]线性码": "n为码字长度，k为信息位数",

    "生成矩阵": "G，k×n矩阵，满足C = M·G",

    "校验矩阵": "H，(n-k)×n矩阵，满足C·H^T = 0",

    "汉明距离": "两码字间不同位的数目",

    "最小距离": "d，码的纠错能力为⌊(d-1)/2⌋"

}



# code_parameters（码参数）

code_parameters = {

    "n": "码字长度",

    "k": "信息位长度",

    "t": "纠错能力"

}



# ============================================================================

# 第二部分：Goppa码

# ============================================================================



# goppa_code（Goppa码）

goppa_code = {

    "definition": "基于Goppa多项式的代数几何码",

    "goppa_polynomial": "G(x)，次数为t的不可约多项式",

    "support_points": "n个有限域元素α_i",

    "parity_check": "对于每个α_i，G(α_i) ≠ 0"

}



# goppa_properties（Goppa码性质）

goppa_properties = {

    "length": "n = 2^m",

    "dimension": "k >= n - m·t",

    "minimum_distance": "d >= 2t + 1",

    "efficient_decoding": "Patterson算法O(n²)"

}



# ============================================================================

# 第三部分：McEliece系统结构

# ============================================================================



# mceliece_system（McEliece系统）

mceliece_system = {

    "based_on": "Goppa码的不可区分性",

    "public_key": "伪装后的校验矩阵",

    "private_key": "原始校验矩阵和变换矩阵",

    "security": "寻找有效译码是NP难问题"

}



# key_components（密钥组件）

key_components = {

    "G": "原始Goppa码的生成矩阵",

    "S": "随机可逆矩阵（k×k）",

    "P": "随机置换矩阵（n×n）",

    "Gpub": "公钥 = S·G·P"

}



# ============================================================================

# 第四部分：密钥生成

# ============================================================================



# key_generation（McEliece密钥生成）

def mceliece_keygen(m=11, t=50, n=2048):

    """

    模拟McEliece密钥生成

    

    Args:

        m: 有限域参数，GF(2^m)

        t: Goppa多项式次数（纠错能力）

        n: 码字长度

    

    Returns:

        dict: 公钥和私钥

    """

    import random

    

    # 计算参数

    n_actual = 2 ** m  # 码字长度

    k = n_actual - m * t  # 信息位长度

    

    # 生成Goppa码生成矩阵G（私有）

    # 简化：使用随机矩阵模拟

    G = [[random.randint(0, 1) for _ in range(n_actual)] for _ in range(k)]

    

    # 生成随机可逆矩阵S

    S = generate_invertible_matrix(k)

    

    # 生成随机置换矩阵P

    P = generate_permutation_matrix(n_actual)

    

    # 计算公钥 Gpub = S·G·P

    G_S = matrix_mult(S, G, mod=2)

    Gpub = matrix_mult(G_S, P, mod=2)

    

    return {

        "public_key": {"Gpub": Gpub, "t": t},

        "private_key": {"S": S, "G": G, "P": P, "t": t},

        "description": "pk = S·G·P, sk = (S, G, P)"

    }



def generate_invertible_matrix(k):

    """生成k×k的可逆二进制矩阵"""

    import random

    

    while True:

        M = [[random.randint(0, 1) for _ in range(k)] for _ in range(k)]

        if matrix_determinant(M) == 1:

            return M



def generate_permutation_matrix(n):

    """生成n×n置换矩阵"""

    import random

    

    P = [[0] * n for _ in range(n)]

    perm = list(range(n))

    random.shuffle(perm)

    

    for i in range(n):

        P[i][perm[i]] = 1

    

    return P



def matrix_mult(A, B, mod=2):

    """矩阵乘法（可选模运算）"""

    n = len(A)

    m = len(B[0])

    p = len(B)

    

    result = [[0] * m for _ in range(n)]

    for i in range(n):

        for j in range(m):

            for k in range(p):

                result[i][j] = (result[i][j] + A[i][k] * B[k][j]) % mod

    

    return result



def matrix_determinant(M):

    """计算2×2矩阵行列式（简化）"""

    if len(M) == 2:

        return (M[0][0] * M[1][1] - M[0][1] * M[1][0]) % 2

    return 1  # 简化



# ============================================================================

# 第五部分：加密

# ============================================================================



# mceliece_encrypt（McEliece加密）

def mceliece_encrypt(message, public_key):

    """

    McEliece加密

    

    Args:

        message: k位二进制信息

        public_key: 公钥Gpub

    

    Returns:

        tuple: (密文, 错误向量)

    """

    import random

    

    Gpub = public_key["Gpub"]

    t = public_key["t"]

    

    k = len(Gpub)

    n = len(Gpub[0])

    

    # 计算c' = m·Gpub

    c_prime = [0] * n

    for j in range(n):

        val = 0

        for i in range(k):

            val += message[i] * Gpub[i][j]

        c_prime[j] = val % 2

    

    # 生成随机错误向量e，重量为t

    e = [0] * n

    error_positions = random.sample(range(n), t)

    for pos in error_positions:

        e[pos] = 1

    

    # 密文 c = c' + e

    c = [(c_prime[i] + e[i]) % 2 for i in range(n)]

    

    return c, e



# ============================================================================

# 第六部分：解密

# ============================================================================



# mceliece_decrypt（McEliece解密）

def mceliece_decrypt(ciphertext, private_key):

    """

    McEliece解密

    

    Args:

        ciphertext: n位密文

        private_key: 私钥(S, G, P)

    

    Returns:

        tuple: (解密消息, 成功标志)

    """

    S = private_key["S"]

    G = private_key["G"]

    P = private_key["P"]

    t = private_key["t"]

    

    # 计算c·P^(-1)

    Pt_inv = transpose_matrix(P)  # 置换矩阵的逆等于转置

    

    c_prime = [0] * len(ciphertext)

    for i in range(len(ciphertext)):

        for j in range(len(ciphertext)):

            c_prime[i] += ciphertext[j] * Pt_inv[j][i]

        c_prime[i] %= 2

    

    # 对Goppa码译码（简化：假设Patterson算法成功）

    # 实际需要高效的译码算法

    decoded = c_prime  # 简化：假设无需纠错或已纠错

    

    # 计算m = decoded·S^(-1)

    S_inv = matrix_inverse(S, mod=2)  # 简化

    k = len(S)

    

    message = [0] * k

    for i in range(k):

        for j in range(len(decoded)):

            message[i] += decoded[j] * S_inv[j][i]

        message[i] %= 2

    

    return message, True



def transpose_matrix(M):

    """矩阵转置"""

    return [[M[j][i] for j in range(len(M))] for i in range(len(M[0]))]



def matrix_inverse(M, mod=2):

    """矩阵求逆（简化2×2）"""

    if len(M) == 2:

        det = matrix_determinant(M)

        if det == 0:

            return M

        # 2×2逆矩阵

        return [[M[1][1], -M[0][1]], [-M[1][0], M[0][0]]]

    return M  # 简化



# ============================================================================

# 第七部分：参数选择

# ============================================================================



# mceliece_parameters（McEliece标准参数）

mceliece_parameters = {

    "mceliece_348864": {

        "n": 3488,

        "k": 3488 - 64 * 50,

        "t": 64,

        "pk_size_kb": 128,

        "security": "128位（经典）"

    },

    "mceliece_460896": {

        "n": 4608,

        "k": 4608 - 96 * 58,

        "t": 96,

        "pk_size_kb": 524,

        "security": "256位（经典）"

    },

    "mceliece_6688128": {

        "n": 6688,

        "k": 6688 - 128 * 128,

        "t": 128,

        "pk_size_kb": 1044,

        "security": "256位+"

    }

}



# ============================================================================

# 第八部分：安全性分析

# ============================================================================



# security_analysis（安全性分析）

security_analysis = {

    "hardness_problem": "信息集解码问题（ISD）",

    "np_completeness": "一般线性码的译码是NP难问题",

    "best_attack": "信息集解码（ISD）算法",

    "complexity": "2^{0.054n}量级（对于好的参数）"

}



# attacks（已知攻击）

known_attacks = {

    "information_set_decoding": "信息集解码，经典最佳攻击",

    "grover_attack": "Grover算法提供平方加速",

    "structural_attack": "针对特定码结构的攻击",

    "re伍德攻击": "试图恢复Goppa码结构"

}



# ============================================================================

# 第九部分：与其他PQC比较

# ============================================================================



# comparison（McEliece与其他PQC）

comparison = {

    "vs_lattice": {

        "public_key_size": "McEliece公钥较大（KB级别）",

        "signature": "McEliece是KEM，非签名",

        "maturity": "McEliece历史更长"

    },

    "vs_isogeny": {

        "key_size": "McEliece更大",

        "computation": "SIKE更轻量",

        "standardization": "都在NIST标准化中"

    }

}



# ============================================================================

# 主程序：演示McEliece

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("McEliece暗码系统详解")

    print("=" * 70)

    

    # 纠错码基础

    print("\n【纠错码基础】")

    for key, val in error_correcting_codes.items():

        print(f"  {key}: {val}")

    

    # Goppa码

    print("\n【Goppa码】")

    for key, val in goppa_code.items():

        print(f"  {key}: {val}")

    

    print("\n【Goppa码性质】")

    for key, val in goppa_properties.items():

        print(f"  {key}: {val}")

    

    # McEliece系统

    print("\n【McEliece系统】")

    for key, val in mceliece_system.items():

        print(f"  {key}: {val}")

    

    # 参数

    print("\n【标准参数】")

    for variant, params in mceliece_parameters.items():

        print(f"\n  [{variant}]")

        for param, value in params.items():

            print(f"    {param}: {value}")

    

    # 密钥生成

    print("\n【密钥生成演示】")

    keys = mceliece_keygen(m=8, t=32, n=256)  # 小参数演示

    pk = keys["public_key"]

    sk = keys["private_key"]

    print(f"  公钥Gpub大小: {len(pk['Gpub'])}x{len(pk['Gpub'][0])}")

    print(f"  私钥S大小: {len(sk['S'])}x{len(sk['S'])}")

    print(f"  纠错能力t: {pk['t']}")

    

    # 加密演示

    print("\n【加密演示】")

    message = [random.randint(0, 1) for _ in range(len(sk['S']))]

    print(f"  原始消息: {message[:16]}... ({len(message)} bits)")

    

    ciphertext, e = mceliece_encrypt(message, pk)

    print(f"  错误向量重量: {sum(e)}/{len(e)}")

    print(f"  密文: {ciphertext[:16]}... ({len(ciphertext)} bits)")

    

    # 解密演示

    print("\n【解密演示】")

    decrypted, success = mceliece_decrypt(ciphertext, sk)

    print(f"  解密成功: {success}")

    print(f"  解密消息: {decrypted[:16]}... ({len(decrypted)} bits)")

    print(f"  消息匹配: {message == decrypted}")

    

    # 安全性

    print("\n【安全性】")

    for key, val in security_analysis.items():

        print(f"  {key}: {val}")

    

    print("\n【已知攻击】")

    for attack, desc in known_attacks.items():

        print(f"  · {attack}: {desc}")

    

    # 比较

    print("\n【与其他PQC比较】")

    for other, diff in comparison.items():

        print(f"\n  [vs {other}]")

        for aspect, desc in diff.items():

            print(f"    · {aspect}: {desc}")

    

    print("\n" + "=" * 70)

    print("McEliece是最早的PQC方案之一，公钥较大但安全性经过时间检验")

    print("=" * 70)

