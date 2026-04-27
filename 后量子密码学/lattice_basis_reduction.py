# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / lattice_basis_reduction



本文件实现 lattice_basis_reduction 相关的算法功能。

"""



# ============================================================================

# 第一部分：格的基本概念

# ============================================================================



# lattice_definition（格定义）

lattice_definition = {

    "lattice": "n维空间中由一组基向量通过整数线性组合生成的点集",

    "basis": "生成格的线性无关向量组",

    "full_rank": "m >= n时为满秩格",

    "determinant": "格的行列式（基向量的混合积）"

}



# lattice_properties（格的性质）

lattice_properties = {

    "fundamental_parallelepiped": "基向量构成的平行六面体，体积 = |det(B)|",

    "covering_radius": "覆盖半径，球能覆盖整个格的最大半径",

    "shortest_vector": "格中最短非零向量（SVP问题）",

    "successive_minima": "逐次最短向量长度"

}



# ============================================================================

# 第二部分：Gram-Schmidt正交化

# ============================================================================



# gram_schmidt_orthogonalization（Gram-Schmidt正交化）

def gram_schmidt(basis_vectors):

    """

    对基向量进行Gram-Schmidt正交化

    

    Args:

        basis_vectors: 2D list，每行是一个基向量

    

    Returns:

        tuple: (正交基, μ系数矩阵)

    """

    n = len(basis_vectors)

    m = len(basis_vectors[0])

    

    # 正交基

    orthogonal = [[0.0] * m for _ in range(n)]

    # μ系数：orthogonal[i]与basis[j]的投影系数

    mu = [[0.0] * n for _ in range(n)]

    

    for i in range(n):

        orthogonal[i] = basis_vectors[i][:]

        

        for j in range(i):

            # μ[i][j] = <b_i, b_j*> / <b_j*, b_j*>

            dot_ij = sum(basis_vectors[i][k] * orthogonal[j][k] for k in range(m))

            dot_jj = sum(orthogonal[j][k] * orthogonal[j][k] for k in range(m))

            mu[i][j] = dot_ij / dot_jj if dot_jj != 0 else 0

            

            # b_i* = b_i - μ[i][j] * b_j*

            for k in range(m):

                orthogonal[i][k] -= mu[i][j] * orthogonal[j][k]

    

    return orthogonal, mu



# ============================================================================

# 第三部分：LLL算法

# ============================================================================



# lll_reduction_conditions（LLL规约条件）

lll_reduction_conditions = {

    "size_reduced": "|μ[i][j]| <= 1/2 对所有j < i",

    "lovasz_condition": "||b_i*||^2 >= (1/4 - μ[i][i-1]^2) * ||b_{i-1}*||^2"

}



# lll_algorithm（LLL算法实现）

def lll_reduction(basis_vectors, delta=0.75):

    """

    LLL格基规约算法

    

    Args:

        basis_vectors: 输入基向量（2D list）

        delta: Lovasz参数（通常0.75）

    

    Returns:

        list: LLL规约后的基向量

    """

    import copy

    

    n = len(basis_vectors)

    B = copy.deepcopy(basis_vectors)

    k = 1

    

    while k < n:

        # Gram-Schmidt正交化当前基

        orth, mu = gram_schmidt(B)

        

        # Size reduction：对第k个向量

        for i in range(k - 1, -1, -1):

            q = round(mu[k][i])

            if abs(q) > 0:

                # b_k = b_k - q * b_i

                for j in range(len(B[k])):

                    B[k][j] -= q * B[i][j]

                # 更新mu

                mu[k][i] -= q

        

        # 重新计算μ[k][k-1]

        orth, mu = gram_schmidt(B)

        

        # Lovasz条件检查

        if k == 0:

            k += 1

            continue

        

        b_k_norm_sq = sum(orth[k][i] ** 2 for i in range(len(orth[k])))

        b_km1_norm_sq = sum(orth[k-1][i] ** 2 for i in range(len(orth[k-1])))

        

        if b_k_norm_sq >= (delta - mu[k][k-1] ** 2) * b_km1_norm_sq:

            k += 1

        else:

            # 交换b_k和b_{k-1}

            B[k], B[k-1] = B[k-1], B[k]

            k = max(k - 1, 1)

    

    return B



# ============================================================================

# 第四部分：BKZ算法概念

# ============================================================================



# bkz_algorithm（BKZ算法）

bkz_algorithm = {

    "definition": "Block Korkine-Zolotarev算法，LLL的推广",

    "block_size": "参数β，枚举块大小",

    "enum_strategy": "在块内枚举短向量",

    "pruning": "剪枝策略减少枚举数量"

}



# bkz_steps（BKZ主要步骤）

def bkz_enumeration_step(block_basis, block_size, kappa):

    """

    BKZ块枚举步骤（简化版）

    

    Args:

        block_basis: 块内基向量

        block_size: 块大小β

        kappa: 块起始索引

    

    Returns:

        tuple: (枚举找到的短向量, 其长度)

    """

    import random

    

    # 简化的枚举：随机采样短向量

    best_vector = None

    best_norm = float('inf')

    

    for _ in range(100):  # 简化的枚举循环

        # 生成随机系数组合

        coeffs = [random.randint(-5, 5) for _ in range(block_size)]

        # 计算线性组合

        vector = [0.0] * len(block_basis[0])

        for i, c in enumerate(coeffs):

            for j in range(len(vector)):

                vector[j] += c * block_basis[kappa + i][j]

        # 计算范数

        norm = sum(v ** 2 for v in vector) ** 0.5

        if 0 < norm < best_norm:

            best_norm = norm

            best_vector = vector

    

    return best_vector, best_norm



# ============================================================================

# 第五部分：规约基的性质

# ============================================================================



# reduced_basis_properties（规约基的性质）

reduced_basis_properties = {

    "ll_reduced": {

        "orthogonality": "基向量接近正交",

        "length_ordering": "|b_1| <= |b_2| <= ... <= |b_n|",

        "approximation_factor": "第一基向量 <= 2^{(n-1)/2} * 最优短向量"

    },

    "hkz_reduced": {

        "definition": "Hermite-Korkine-Zolotarev规约",

        "svp_in_block": "每个块内向量是SVP最优的",

        "stronger_than_lll": "是LLL的更强条件"

    }

}



# ============================================================================

# 第六部分：应用 - 最近向量问题（CVP）

# ============================================================================



# babai_algorithm（Babai最近平面算法）

def babai_closest_plane(B, target):

    """

    使用规约基解决CVP（最近向量问题）

    

    Args:

        B: LLL规约基

        target: 目标向量

    

    Returns:

        list: 格中最接近目标的向量

    """

    n = len(B)

    m = len(target)

    

    # Gram-Schmidt

    orth, mu = gram_schmidt(B)

    

    # 从后向前贪心投影

    t = target[:]

    result = [0.0] * m

    

    for i in range(n - 1, -1, -1):

        # 计算t在b_i*方向上的投影系数

        dot_ti = sum(t[j] * orth[i][j] for j in range(m))

        dot_ii = sum(orth[i][j] ** 2 for j in range(m))

        coeff = round(dot_ti / dot_ii) if dot_ii != 0 else 0

        

        # 从t中减去投影

        for j in range(m):

            t[j] -= coeff * B[i][j]

            result[j] += coeff * B[i][j]

    

    return result



# ============================================================================

# 第七部分：密码分析应用

# ============================================================================



# lattice_attack_applications（格攻击应用）

lattice_attack_applications = {

    "knapsack_crypto": "背包密码系统的密钥恢复",

    "rsa_small_exponent": "RSA加密使用小公钥e的攻击",

    "ntru_key_recovery": "NTRU密钥恢复攻击",

    "lwe_reduction": "LWE问题求解"

}



# coppersmith_method（Coppersmith方法应用）

coppersmith_method = {

    "description": "使用格基规约求解低指数多项式根",

    "application": "RSA modulus的高位已知时恢复完整模数",

    "lattice_dimension": "根据多项式和根的范围确定格维度"

}



# ============================================================================

# 第八部分：实现示例

# ============================================================================



# lll_usage_example（LLL使用示例）

def lll_usage_example():

    """

    演示LLL算法的典型用途

    """

    # 示例：2D格基

    basis = [

        [1, 0],

        [0, 1]

    ]

    

    # 旋转后的基（高度相关）

    import math

    theta = math.radians(5)

    rotated = [

        [round(100 * math.cos(theta)), round(100 * math.sin(theta))],

        [round(100 * -math.sin(theta)), round(100 * math.cos(theta))]

    ]

    

    print("原始基：")

    for v in basis:

        print(f"  {v}")

    

    print(f"\n旋转后（高度相关）的基：")

    for v in rotated:

        print(f"  {v}")

    

    # LLL规约

    reduced = lll_reduction(rotated)

    

    print(f"\nLLL规约后的基：")

    for v in reduced:

        print(f"  {[round(x) for x in v]}")

    

    # 计算长度

    def vec_norm(v):

        return sum(x**2 for x in v) ** 0.5

    

    print(f"\n基向量长度：")

    print(f"  规约前: {[round(vec_norm(v)) for v in rotated]}")

    print(f"  规约后: {[round(vec_norm(v)) for v in reduced]}")



# ============================================================================

# 主程序：演示格基规约算法

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("格基规约算法：LLL与BKZ")

    print("=" * 70)

    

    # 格定义

    print("\n【格定义】")

    for key, val in lattice_definition.items():

        print(f"  {key}: {val}")

    

    # Gram-Schmidt示例

    print("\n【Gram-Schmidt正交化示例】")

    example_basis = [

        [4, 1, 3],

        [1, 2, 1],

        [2, 1, 4]

    ]

    print("输入基向量：")

    for v in example_basis:

        print(f"  {v}")

    

    orth, mu = gram_schmidt(example_basis)

    print("\n正交基：")

    for v in orth:

        print(f"  {[round(x, 2) for x in v]}")

    

    # LLL规约条件

    print("\n【LLL规约条件】")

    for condition, desc in lll_reduction_conditions.items():

        print(f"  · {condition}: {desc}")

    

    # LLL示例

    print("\n【LLL算法示例】")

    lll_usage_example()

    

    # BKZ算法

    print("\n【BKZ算法】")

    for key, val in bkz_algorithm.items():

        print(f"  {key}: {val}")

    

    # 规约基性质

    print("\n【规约基性质】")

    for reduced_type, properties in reduced_basis_properties.items():

        print(f"\n  [{reduced_type}]")

        for prop, desc in properties.items():

            print(f"    · {prop}: {desc}")

    

    # 密码分析应用

    print("\n【格攻击应用】")

    for attack, desc in lattice_attack_applications.items():

        print(f"  · {attack}: {desc}")

    

    print("\n" + "=" * 70)

    print("LLL是格密码学的基础工具，用于构造攻击和验证方案安全性")

    print("=" * 70)

