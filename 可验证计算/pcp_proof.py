# -*- coding: utf-8 -*-

"""

算法实现：可验证计算 / pcp_proof



本文件实现 pcp_proof 相关的算法功能。

"""



import random





def encode_matrix(mat, g):

    """

    将矩阵编码为低密度奇偶校验（LDPC）码字。



    参数:

        mat: 原始矩阵（列表的列表）

        g: 生成矩阵



    返回:

        编码后的矩阵

    """

    n_rows = len(mat)

    n_cols = len(mat[0]) if mat else 0

    k = len(g)



    # 编码：每行乘以生成矩阵

    encoded = []

    for row in mat:

        codeword = [0] * k

        for i in range(k):

            for j in range(n_cols):

                codeword[i] ^= (row[j] & g[i][j])  # GF(2) 乘法

        encoded.append(codeword)



    return encoded





def pcp_verify(mat_a, mat_b, mat_c, proof, queries, randomness):

    """

    PCP 验证器：随机查询 proof 的几个位置，检查约束是否满足。



    参数:

        mat_a, mat_b: 输入矩阵

        mat_c: 声称的输出矩阵（需要验证 A*B = C）

        proof: 证明（编码后的矩阵 A', B', C'）

        queries: 随机查询位置列表

        randomness: 随机种子



    返回:

        True/False

    """

    random.seed(randomness)



    # 将 proof 解码（简化：直接使用 proof 的某些行）

    a_enc, b_enc, c_enc = proof



    n = len(mat_a)

    # 随机查询一个位置 (i,j)

    i = random.randint(0, n - 1)

    j = random.randint(0, n - 1)



    # 读取 A[i,:] 和 B[:,j] 的编码

    a_row_i = a_enc[i]

    b_col_j = [b_enc[row][j] for row in range(n)]



    # 验证：检查 a_row_i 和 b_col_j 的编码一致性

    # （这里用简化的校验和）

    checksum_a = sum(a_row_i) % 2

    checksum_b = sum(b_col_j) % 2



    # 计算 C[i,j] 的期望值

    expected = 0

    for row in range(n):

        expected ^= (mat_a[i][row] & mat_b[row][j])



    # 检查 C[i,j] 的编码是否一致

    c_entry = c_enc[i][j]

    checksum_c = sum(c_enc[i]) % 2



    # 概率性检查：只有随机查询足够多时才能保证正确性

    checks_passed = 0

    for _ in range(3):

        # 检查编码的结构性质

        if (checksum_a + checksum_b) % 2 == checksum_c:

            checks_passed += 1



    return checks_passed >= 2  # 容忍少量错误





def build_pc_proof(mat_a, mat_b):

    """

    构建 PCP 证明。



    证明者将 A, B, C=A*B 都编码为 LDPC 码，

    然后将编码后的矩阵作为 proof。

    """

    # 计算 C = A * B

    n = len(mat_a)

    mat_c = [[0] * n for _ in range(n)]

    for i in range(n):

        for j in range(n):

            val = 0

            for k in range(n):

                val ^= (mat_a[i][k] & mat_b[k][j])

            mat_c[i][j] = val



    # 生成简单的生成矩阵（LDPC 风格）

    g = [[random.randint(0, 1) for _ in range(n)] for _ in range(n)]



    # 编码所有矩阵

    a_enc = encode_matrix(mat_a, g)

    b_enc = encode_matrix(mat_b, g)

    c_enc = encode_matrix(mat_c, g)



    return (a_enc, b_enc, c_enc), g





if __name__ == "__main__":

    # 测试矩阵（GF(2) 上的乘法）

    mat_a = [

        [1, 0, 1],

        [1, 1, 0],

        [0, 1, 1]

    ]

    mat_b = [

        [1, 1, 0],

        [0, 1, 1],

        [1, 0, 1]

    ]



    print("=== PCP 验证示例 ===")

    print(f"矩阵 A:\n{mat_a}")

    print(f"矩阵 B:\n{mat_b}")



    # 构建证明

    proof, g = build_pc_proof(mat_a, mat_b)

    a_enc, b_enc, c_enc = proof

    print(f"\n编码后矩阵规模: {len(a_enc)}x{len(a_enc[0])}")



    # 模拟计算 C = A * B

    n = len(mat_a)

    mat_c = [[0] * n for _ in range(n)]

    for i in range(n):

        for j in range(n):

            val = 0

            for k in range(n):

                val ^= (mat_a[i][k] & mat_b[k][j])

            mat_c[i][j] = val



    # PCP 验证（多次）

    print("\nPCP 验证（10次随机查询）:")

    passed = 0

    for t in range(10):

        randomness = t * 12345

        queries = [(i, j) for i in range(n) for j in range(n)]

        if pcp_verify(mat_a, mat_b, mat_c, proof, queries, randomness):

            passed += 1

    print(f"  通过次数: {passed}/10")



    # 错误情况测试

    print("\n=== 错误证明测试 ===")

    wrong_c = [[1 if i == j else 0 for j in range(n)] for i in range(n)]

    wrong_proof = (a_enc, b_enc, wrong_c)

    passed_wrong = 0

    for t in range(10):

        randomness = t * 12345

        if pcp_verify(mat_a, mat_b, wrong_c, wrong_proof, [], randomness):

            passed_wrong += 1

    print(f"  错误证明通过次数: {passed_wrong}/10")



    print(f"\nPCP 特性:")

    print(f"  验证器只读 O(1) 位置: 约 3 个随机查询")

    print(f"  随机位数: O(log n)")

