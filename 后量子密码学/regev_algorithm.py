# -*- coding: utf-8 -*-
"""
算法实现：后量子密码学 / regev_algorithm

本文件实现 regev_algorithm 相关的算法功能。
"""

# ============================================================================
# 第一部分：LWE问题定义
# ============================================================================

# lwe_problem（LWE问题）
lwe_problem = {
    "definition": "给定A·s + e = b，求解短向量s",
    "A": "随机m×n矩阵",
    "s": "秘密短向量（n维）",
    "e": "小误差向量（m维）",
    "b": "结果向量"
}

# lwe_variants（LWE变体）
lwe_variants = {
    "search_lwe": "给定(A, b)，恢复s",
    "decision_lwe": "区分(A, A·s+e)和(A, random)",
    "promise_lwe": "假设e是小量"
}

# ============================================================================
# 第二部分：Regev加密方案
# ============================================================================

# regev_scheme（Regev方案）
regev_scheme = {
    "public_key": "矩阵A",
    "secret_key": "向量s",
    "encryption": "使用A和噪声对位加密",
    "decryption": "利用s提取明文"
}

# ============================================================================
# 第三部分：密钥生成
# ============================================================================

# regev_keygen（Regev密钥生成）
def regev_keygen(n=50, m=200, q=12289):
    """
    Regev密钥生成
    
    Args:
        n: 维度
        m: 样本数
        q: 模数
    
    Returns:
        dict: 公钥和私钥
    """
    import random
    
    # 私钥s：短向量（每个分量很小）
    s = [random.randint(0, 1) for _ in range(n)]
    
    # 随机矩阵A
    A = [[random.randint(0, q-1) for _ in range(n)] for _ in range(m)]
    
    # 计算b = A·s + e (mod q)
    e = [random.choice([0, 0, 0, 1, -1]) for _ in range(m)]  # 小误差
    
    b = []
    for i in range(m):
        bi = sum(A[i][j] * s[j] for j in range(n)) + e[i]
        b.append(bi % q)
    
    return {
        "public_key": {"A": A, "b": b, "q": q},
        "secret_key": {"s": s},
        "params": {"n": n, "m": m, "q": q}
    }

# ============================================================================
# 第四部分：加密
# ============================================================================

# regev_encrypt（Regev加密）
def regev_encrypt(public_key, plaintext_bit):
    """
    Regev加密单个比特
    
    Args:
        public_key: 公钥(A, b, q)
        plaintext_bit: 0或1
    
    Returns:
        tuple: 密文(u, v)
    """
    import random
    
    A = public_key["A"]
    b = public_key["b"]
    q = public_key["q"]
    m = len(A)
    
    # 随机选择子集S
    subset = random.sample(range(m), m // 2)
    
    # 计算u = sum(A_i for i in S)
    u = [0] * len(A[0])
    for i in subset:
        for j in range(len(A[0])):
            u[j] = (u[j] + A[i][j]) % q
    
    # 计算v = sum(b_i for i in S) + plaintext * q/2
    v = sum(b[i] for i in subset) % q
    v = (v + plaintext_bit * (q // 2)) % q
    
    return (u, v)

# ============================================================================
# 第五部分：解密
# ============================================================================

# regev_decrypt（Regev解密）
def regev_decrypt(ciphertext, secret_key, q=12289):
    """
    Regev解密
    
    Args:
        ciphertext: 密文(u, v)
        secret_key: 私钥s
        q: 模数
    
    Returns:
        int: 明文比特
    """
    u, v = ciphertext
    s = secret_key["s"]
    
    # 计算w = v - u·s mod q
    w = v - sum(u[i] * s[i] for i in range(len(s)))
    w = w % q
    
    # 判断w接近0还是q/2
    threshold = q // 4
    if w < threshold or w > q - threshold:
        return 0
    else:
        return 1

# ============================================================================
# 第六部分：完整示例
# ============================================================================

# full_example（完整示例）
def regev_demo():
    """演示Regev加密系统"""
    import random
    
    # 密钥生成
    keys = regev_keygen(n=50, m=200, q=12289)
    
    # 测试加密解密
    test_bits = [0, 1, 0, 1, 1, 0, 1, 0]
    print("Regev加密解密演示:")
    print(f"  参数: n={keys['params']['n']}, m={keys['params']['m']}, q={keys['params']['q']}")
    
    for bit in test_bits:
        ciphertext = regev_encrypt(keys["public_key"], bit)
        decrypted = regev_decrypt(ciphertext, keys["secret_key"], keys["params"]["q"])
        status = "✓" if bit == decrypted else "✗"
        print(f"  {bit} -> 密文 -> {decrypted} {status}")
    
    return True

# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Regev算法：Learning With Errors（LWE）")
    print("=" * 70)
    
    # LWE问题
    print("\n【LWE问题】")
    for key, val in lwe_problem.items():
        print(f"  {key}: {val}")
    
    print("\n【LWE变体】")
    for key, val in lwe_variants.items():
        print(f"  · {key}: {val}")
    
    # 方案
    print("\n【Regev方案】")
    for key, val in regev_scheme.items():
        print(f"  {key}: {val}")
    
    # 演示
    regev_demo()
    
    # 安全性
    print("\n【安全性】")
    print("  · LWE问题难度基于最坏情况格问题")
    print("  · 量子算法无显著加速")
    print("  · 参数选择关键：q大小、误差分布")
    
    print("\n" + "=" * 70)
    print("Regev方案是现代格密码的基础（Ring-LWE、Module-LWE）")
    print("=" * 70)
