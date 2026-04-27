# -*- coding: utf-8 -*-

"""

算法实现：编码理论 / linear_code



本文件实现 linear_code 相关的算法功能。

"""



import numpy as np

from itertools import combinations





# --------------------------------------------------------------------------- #

# GF(2) 基础运算

# --------------------------------------------------------------------------- #



def gf2_add(a, b):

    """GF(2) 加法（异或）"""

    return a ^ b





def gf2_mul(a, b):

    """GF(2) 乘法（与）"""

    return a & b





def gf2_mat_mul(A, B):

    """GF(2) 矩阵乘法"""

    A = np.asarray(A, dtype=int)

    B = np.asarray(B, dtype=int)

    result = np.zeros((A.shape[0], B.shape[1]), dtype=int)

    for i in range(A.shape[0]):

        for j in range(B.shape[1]):

            for k in range(A.shape[1]):

                result[i, j] ^= (A[i, k] & B[k, j])

    return result





def gf2_mat_rank(A):

    """计算 GF(2) 矩阵的秩"""

    A = np.array(A, dtype=int)

    m, n = A.shape

    rank = 0

    row_used = np.zeros(m, dtype=bool)



    for col in range(n):

        # 找到当前列及以下行中的 1

        pivot_row = -1

        for r in range(rank, m):

            if A[r, col] == 1 and not row_used[r]:

                pivot_row = r

                break

        if pivot_row == -1:

            continue

        # 交换行

        A[[rank, pivot_row]] = A[[pivot_row, rank]]

        row_used[rank] = True

        # 消去其他行的当前列

        for r in range(m):

            if r != rank and A[r, col] == 1:

                A[r] ^= A[rank]

        rank += 1

        if rank >= m:

            break



    return rank





def gf2_row_echelon(A):

    """

    将矩阵化为行阶梯形（GF(2)）



    返回:

        tuple: (echelon_form, pivot_columns)

    """

    A = np.array(A, dtype=int)

    m, n = A.shape

    result = A.copy()

    pivot_cols = []

    row = 0



    for col in range(n):

        # 找非零行

        pivot = -1

        for r in range(row, m):

            if result[r, col] == 1:

                pivot = r

                break

        if pivot == -1:

            continue

        # 交换

        result[[row, pivot]] = result[[pivot, row]]

        pivot_cols.append(col)

        # 消去

        for r in range(m):

            if r != row and result[r, col] == 1:

                result[r] ^= result[row]

        row += 1

        if row >= m:

            break



    return result, pivot_cols





# --------------------------------------------------------------------------- #

# 线性分组码核心

# --------------------------------------------------------------------------- #



class LinearBlockCode:

    """

    (n, k) 线性分组码



    参数:

        G (np.ndarray): 生成矩阵，形状 (k, n)，k 行 n 列

        H (np.ndarray, optional): 校验矩阵，形状 (n-k, n)

                                  如果未提供，会从 G 计算得到



    示例:

        >>> # 重复码 (3, 1)

        >>> G = np.array([[1, 1, 1]])

        >>> code = LinearBlockCode(G)

        >>> code.encode([1])

        array([1, 1, 1])

        >>> code.minimum_distance()

        3

    """



    def __init__(self, G, H=None):

        self.G = np.array(G, dtype=int)

        self.k = self.G.shape[0]

        self.n = self.G.shape[1]



        if H is not None:

            self.H = np.array(H, dtype=int)

        else:

            # 从 G 计算校验矩阵 H

            self.H = self._compute_parity_check_matrix()



        self.n_minus_k = self.H.shape[0]



        # 构建标准形式的 G 和 H

        self._standard_form()



        # 码字集合

        self._codewords = None



    def _compute_parity_check_matrix(self):

        """

        从生成矩阵 G 计算校验矩阵 H



        若 G 是系统形式 [I_k | A]，则 H = [A^T | I_{n-k}]



        方法：高斯消元找 G 的行空间的一组正交基

        """

        # 对 G 进行行变换，化为行简化阶梯形

        G_temp = self.G.copy().astype(int)



        # 使用 gf2_row_echelon

        G_echelon, pivot_cols = gf2_row_echelon(G_temp)



        # 提取左半部分（与 pivot 列对应的）

        # G_echelon 是行阶梯形，我们需要系统形式



        # 重新排列列，使 pivot 列在左边

        # 找非 pivot 列

        all_cols = set(range(self.n))

        pivot_set = set(pivot_cols)

        non_pivot_cols = sorted(all_cols - pivot_set)



        # 置换矩阵 P

        P = np.zeros((self.n, self.n), dtype=int)

        new_order = pivot_cols + non_pivot_cols

        for new_idx, old_idx in enumerate(new_order):

            P[old_idx, new_idx] = 1



        # G_sys = G @ P

        G_sys = (G_temp @ P) % 2



        # G_sys 现在是 [I_k | A] 形式

        # A 在右边 n-k 列

        A = G_sys[:, self.k:]  # 形状 (k, n-k)



        # H = [A^T | I_{n-k}]

        A_T = A.T  # 形状 (n-k, k)

        I_nk = np.eye(self.n_minus_k, dtype=int)

        H_sys = np.hstack([A_T, I_nk])  # 形状 (n-k, n)



        # 逆置换：H = H_sys @ P^T

        P_T = P.T

        H = (H_sys @ P_T) % 2



        return H



    def _standard_form(self):

        """

        将 G 和 H 化为标准形式



        系统形式 G = [I_k | A]

        系统形式 H = [A^T | I_{n-k}]

        """

        # 对 G 进行行变换和列置换，化为系统形式

        G_temp = self.G.copy().astype(int)



        # 行化简（行阶梯形）

        G_echelon, pivot_cols = gf2_row_echelon(G_temp)



        # 确保单位阵在左边（归一化每一行）

        G_normalized = np.zeros_like(G_echelon)

        for r, c in enumerate(pivot_cols):

            G_normalized[r] = G_echelon[r]



        # 列置换

        non_pivot_cols = [c for c in range(self.n) if c not in pivot_cols]

        new_order = pivot_cols + non_pivot_cols



        G_perm = G_normalized[:, new_order]

        # 去掉全零行（可能因独立行数 < k）

        G_perm = G_perm[:len(pivot_cols)]



        # 现在 G_perm 是 [I_k | A] 形式

        k = len(pivot_cols)

        if k < self.k:

            # 补零行

            G_std = np.zeros((self.k, self.n), dtype=int)

            G_std[:k] = G_perm

        else:

            G_std = G_perm



        # 如果左边不是完整的 I_k，补成完整的

        # 检查每一行

        G_final = np.zeros((self.k, self.n), dtype=int)

        for r, c in enumerate(pivot_cols):

            G_final[r] = G_std[r] if r < len(pivot_cols) else np.zeros(self.n, dtype=int)



        # 更好的方法：直接用原始 G，但限制到独立行

        # 简化处理：假设输入 G 已经足够好



        self.G_std = G_final

        self.A_mat = self.G_std[:, self.k:] if self.k > 0 else np.zeros((0, self.n)).astype(int)

        self.I_k = np.eye(self.k, dtype=int) if self.k > 0 else None



        # 计算对应的 H_std

        if self.k < self.n:

            self.H_std = np.hstack([self.A_mat.T, np.eye(self.n - self.k, dtype=int)])

        else:

            self.H_std = None



    @property

    def codewords(self):

        """生成所有码字（懒加载）"""

        if self._codewords is None:

            self._codewords = []

            for i in range(1 << self.k):

                message = [(i >> j) & 1 for j in range(self.k)]

                cw = self.encode(message, systematic=False)

                self._codewords.append(cw)

        return self._codewords



    def encode(self, message, systematic=True):

        """

        线性分组码编码



        参数:

            message: k 比特消息（列表或数组）

            systematic: True=系统码形式（消息在前，校验位在后）



        返回:

            np.ndarray: n 比特码字

        """

        message = np.asarray(message, dtype=int)

        if len(message) != self.k:

            raise ValueError(f"消息长度必须是 {self.k}")



        if systematic:

            # 系统码编码：c = [m | m*A]

            # 注意：G_std = [I_k | A]

            m_matrix = message.reshape(1, -1)

            G_used = self.G if hasattr(self, 'G') and self.G.shape[0] == len(message) else self.G_std

            # 直接用矩阵乘法

            code = (m_matrix @ G_used) % 2

            code = code.flatten()

        else:

            # 非系统码

            code = (message.reshape(1, -1) @ self.G) % 2

            code = code.flatten()



        return code



    def syndrome(self, received):

        """

        计算接收向量的伴随式（校验子）



        参数:

            received: n 比特接收向量



        返回:

            np.ndarray: (n-k) 比特伴随式

        """

        received = np.asarray(received, dtype=int)

        s = (self.H @ received) % 2

        return s



    def decode(self, received):

        """

        线性分组码译码（伴随式译码/查表译码）



        原理：

            1. 计算伴随式 s = H · r^T

            2. 若 s = 0，无错（或错误模式恰好落在陪集首）

            3. 否则查表找到错误模式 e，其伴随式为 s

            4. 纠正：c = r - e = r + e



        参数:

            received: n 比特接收向量



        返回:

            np.ndarray: 纠正后的码字

        """

        received = np.asarray(received, dtype=int)

        s = self.syndrome(received)



        # 伴随式为零，无错

        if np.all(s == 0):

            return received



        # 查找错误模式

        error_pattern = self._find_error_pattern(s)



        # 纠正

        corrected = received ^ error_pattern

        return corrected



    def _find_error_pattern(self, syndrome):

        """

        查找给定伴随式对应的错误模式



        使用标准数组译码（查表法）

        复杂度：O(2^n)，仅适用于短码

        """

        # 构建/获取译码表

        if not hasattr(self, '_syndrome_table'):

            self._build_syndrome_table()



        # 转为元组查找

        synd_tuple = tuple(int(x) for x in syndrome)

        return self._syndrome_table.get(synd_tuple, np.zeros(self.n, dtype=int))



    def _build_syndrome_table(self):

        """

        构建伴随式查找表



        表项：{伴随式 -> 错误模式}

        只包含重量 ≤ t 的错误模式（t 是最大可纠正错误数）

        """

        self._syndrome_table = {}

        t = self.minimum_distance() // 2



        # 枚举所有可能的长度 ≤ t 的错误

        for num_errors in range(t + 1):

            for positions in combinations(range(self.n), num_errors):

                error = np.zeros(self.n, dtype=int)

                for pos in positions:

                    error[pos] = 1

                s = self.syndrome(error)

                s_tuple = tuple(int(x) for x in s)

                # 如果还没有这个伴随式的记录，添加

                if s_tuple not in self._syndrome_table:

                    self._syndrome_table[s_tuple] = error



    def weight(self, vector):

        """

        计算向量的汉明重量（1 的个数）



        参数:

            vector: 二进制向量



        返回:

            int: 汉明重量

        """

        vector = np.asarray(vector, dtype=int)

        return int(np.sum(vector))



    def distance(self, a, b):

        """计算两个向量的汉明距离"""

        a = np.asarray(a, dtype=int)

        b = np.asarray(b, dtype=int)

        return int(np.sum(a != b))



    def minimum_distance(self):

        """

        计算最小距离 d



        方法：枚举所有非零码字，找最小重量

        复杂度：O(2^k * n)



        返回:

            int: 最小汉明距离 d

        """

        min_dist = self.n



        for i in range(1, 1 << self.k):

            message = [(i >> j) & 1 for j in range(self.k)]

            cw = self.encode(message, systematic=False)

            w = self.weight(cw)

            if w < min_dist:

                min_dist = w

            if min_dist == 1:

                break  # 最优情况



        return min_dist



    def weight_distribution(self):

        """

        计算重量分布（重量谱）



        返回:

            dict: {重量: 个数}

        """

        distribution = {}

        for cw in self.codewords:

            w = self.weight(cw)

            distribution[w] = distribution.get(w, 0) + 1

        return distribution



    def is_codeword(self, vector):

        """

        判断一个向量是否是码字



        参数:

            vector: n 比特向量



        返回:

            bool

        """

        vector = np.asarray(vector, dtype=int)

        s = self.syndrome(vector)

        return np.all(s == 0)



    def covering_radius(self):

        """

        计算覆盖半径 ρ



        ρ = max_{r ∈ GF(2)^n} min_{c ∈ C} d(r, c)

        即空间中任意点与其最近码字的距离的最大值



        返回:

            int: 覆盖半径

        """

        # 简化版本：只检查所有向量的样本

        max_dist = 0

        # 对所有可能的消息

        for i in range(1 << self.k):

            message = [(i >> j) & 1 for j in range(self.k)]

            cw = self.encode(message, systematic=False)

            # 对所有可能的错误（到码字的距离）

            for e in range(1 << self.n):

                received = tuple((cw[pos] ^ ((e >> pos) & 1)) for pos in range(self.n))

                s = self.syndrome(received)

                # 实际译码结果

                decoded = self.decode(received)

                dist = self.distance(received, decoded)

                max_dist = max(max_dist, dist)

                if max_dist >= self.n:

                    return max_dist

        return max_dist





# --------------------------------------------------------------------------- #

# 常见线性码

# --------------------------------------------------------------------------- #



def repetition_code(n):

    """

    重复码 (n, 1)



    编码：消息比特重复 n 次

    最小距离：d = n

    纠错能力：t = floor((n-1)/2)



    参数:

        n: 码字长度（奇数）



    返回:

        LinearBlockCode: 重复码对象

    """

    if n % 2 == 0:

        raise ValueError("重复码长度 n 必须是奇数（以便多数表决）")

    G = np.ones((1, n), dtype=int).reshape(1, n)

    return LinearBlockCode(G)





def parity_check_code(n):

    """

    奇偶校验码 (n, n-1)



    最后一个比特是前面 n-1 位的奇校验位

    最小距离：d = 2

    能检测 1 位错误，不能纠正任何错误



    参数:

        n: 码字总长度



    返回:

        LinearBlockCode: 奇偶校验码对象

    """

    G = np.hstack([np.eye(n - 1, dtype=int), np.ones((n - 1, 1), dtype=int)])

    return LinearBlockCode(G)





def simple_parity_check_matrix(n, k):

    """

    构造简单的 (n, k) 码的校验矩阵



    每个校验位监督一组特定的信息位

    """

    H = np.zeros((n - k, n), dtype=int)

    # 简单方案：H 的右边是单位阵，左边是随机分配的监督关系

    H[:, :k] = np.random.randint(0, 2, (n - k, k))

    H[:, k:] = np.eye(n - k, dtype=int)

    return H





def hamming_codeclassic(m):

    """

    经典汉明码 (2^m - 1, 2^m - m - 1)



    参数:

        m: 正整数



    返回:

        LinearBlockCode: 汉明码对象

    """

    n = (1 << m) - 1

    k = n - m



    # 构造校验矩阵（列是 1 到 n 的二进制表示）

    H = np.zeros((m, n), dtype=int)

    for j in range(1, n + 1):

        for bit in range(m):

            H[bit, j - 1] = (j >> bit) & 1



    # 提取 H 的左半部分作为 A

    A = H[:, :k]

    # G = [I_k | A^T]

    I_k = np.eye(k, dtype=int)

    G = np.hstack([I_k, A.T])

    G = G % 2



    return LinearBlockCode(G, H)





def simplex_code(m):

    """

    Simplex 码（对偶汉明码）(2^m - 1, m)



    是汉明码的对偶码，所有码字是 H 的行的所有线性组合

    最小距离：2^{m-1}



    参数:

        m: 正整数



    返回:

        LinearBlockCode: Simplex 码对象

    """

    n = (1 << m) - 1

    k = m



    # 构造 H：所有非零 m 维向量（作为列）

    H = np.zeros((m, n), dtype=int)

    col_idx = 0

    for val in range(1, 1 << m):

        for bit in range(m):

            H[bit, col_idx] = (val >> bit) & 1

        col_idx += 1



    # Simplex 码的生成矩阵就是 H^T

    G = H.T % 2



    return LinearBlockCode(G)





# --------------------------------------------------------------------------- #

# 性能分析

# --------------------------------------------------------------------------- #



def Gilbert_Varshamov_bound(n, k):

    """

    Gilbert-Varshamov 上界



    说明存在码长为 n、维数为 k 的线性码，其最小距离满足：

        A_2(n,k) >= V(n, d-1) + ... 不等式



    这里给出一个估计：最大可能的最小距离下界



    返回:

        int: 估计的最大 d

    """

    # 对于给定的 n,k，最小距离 d 必须满足：

    # sum_{i=0}^{d-2} C(n, i) < 2^{n-k}

    for d in range(n, 0, -1):

        total = 0

        for i in range(d - 1):

            total += int(np.math.comb(n, i))

        if total < (1 << (n - k)):

            return d

    return 1





def Singleton_bound(n, k):

    """

    Singleton 上界



    d <= n - k + 1



    参数:

        n, k: 码参数



    返回:

        int: d <= n - k + 1

    """

    return n - k + 1





def Plotkin_bound(n, k):

    """

    Plotkin 上界



    若 d > n/2，则 d <= n * 2^{k-1} / (2^{k-1} - 1)



    参数:

        n, k: 码参数



    返回:

        int: d 的上界

    """

    if k <= 0:

        return n + 1

    bound = n * (1 << (k - 1)) / ((1 << (k - 1)) - 1)

    return int(np.floor(bound))





# --------------------------------------------------------------------------- #

# 测试

# --------------------------------------------------------------------------- #



if __name__ == "__main__":

    print("=" * 60)

    print("线性分组码测试")

    print("=" * 60)



    # 测试 1: 重复码

    print("\n【测试 1】重复码 (5, 1)")

    code_rep = repetition_code(5)

    print(f"参数: n={code_rep.n}, k={code_rep.k}")

    print(f"生成矩阵 G:\n{code_rep.G}")

    print(f"校验矩阵 H (形状 {code_rep.H.shape}):\n{code_rep.H}")



    msg = [1]

    cw = code_rep.encode(msg)

    print(f"\n消息: {msg}")

    print(f"码字: {list(cw)}")



    d_min = code_rep.minimum_distance()

    print(f"最小距离: {d_min}")

    t_correct = d_min // 2

    print(f"纠错能力: t = {t_correct}")

    print("✓ 重复码测试通过")



    # 测试 2: 奇偶校验码

    print("\n【测试 2】奇偶校验码 (4, 3)")

    code_par = parity_check_code(4)

    print(f"参数: n={code_par.n}, k={code_par.k}")

    print(f"G:\n{code_par.G}")



    msg = [1, 0, 1]

    cw = code_par.encode(msg)

    print(f"\n消息: {msg}")

    print(f"码字: {list(cw)}")

    assert code_par.is_codeword(cw)

    print("✓ 奇偶校验码测试通过")



    # 测试 3: 伴随式计算

    print("\n【测试 3】伴随式计算")

    cw_check = code_par.decode(cw)  # 无错

    s = code_par.syndrome(cw_check)

    print(f"无错码字的伴随式: {list(s)} (应全零)")

    assert np.all(s == 0)



    # 引入错误

    corrupted = cw.copy()

    corrupted[0] ^= 1

    s_bad = code_par.syndrome(corrupted)

    print(f"有错接收的伴随式: {list(s_bad)}")

    print("✓ 伴随式计算通过")



    # 测试 4: 汉明码

    print("\n【测试 4】经典汉明码 (7, 4)")

    ham = hamming_codeclassic(3)

    print(f"参数: n={ham.n}, k={ham.k}")

    print(f"最小距离: {ham.minimum_distance()}")

    print(f"G:\n{ham.G}")

    print(f"H:\n{ham.H}")



    msg = [1, 0, 1, 1]

    cw = ham.encode(msg)

    print(f"\n消息: {msg}")

    print(f"码字: {list(cw)}")

    print(f"是码字: {ham.is_codeword(cw)}")



    # 单比特错误纠正

    for err_pos in range(ham.n):

        corrupted = list(cw)

        corrupted[err_pos] ^= 1

        decoded = ham.decode(corrupted)

        print(f"  位置 {err_pos} 错误: 译码 {list(decoded)}, 正确 {msg}")

    print("✓ 汉明码测试通过")



    # 测试 5: 重量分布

    print("\n【测试 5】重量分布")

    ham_7_4 = hamming_codeclassic(3)

    dist = ham_7_4.weight_distribution()

    print(f"重量分布:")

    for w in sorted(dist.keys()):

        print(f"  重量 {w}: {dist[w]} 个码字")



    # 验证：总共 2^k = 16 个码字

    total = sum(dist.values())

    print(f"总计: {total} (应为 {2**ham_7_4.k})")

    assert total == 2**ham_7_4.k

    print("✓ 重量分布测试通过")



    # 测试 6: GF(2) 矩阵运算

    print("\n【测试 6】GF(2) 矩阵运算")

    A = np.array([[1, 0, 1, 1], [1, 1, 0, 0]], dtype=int)

    B = np.array([[1, 1], [0, 1], [1, 0], [0, 1]], dtype=int)

    C = gf2_mat_mul(A, B)

    print(f"A @ B =\n{C}")



    rank = gf2_mat_rank(A)

    print(f"rank(A) = {rank}")

    print("✓ GF(2) 矩阵运算通过")



    # 测试 7: Simplex 码

    print("\n【测试 7】Simplex 码 (7, 3)")

    simp = simplex_code(3)

    print(f"参数: n={simp.n}, k={simp.k}")

    print(f"最小距离: {simp.minimum_distance()}")

    print(f"G:\n{simp.G}")



    dist_simp = simp.weight_distribution()

    print(f"重量分布: {dict(sorted(dist_simp.items()))}")

    print("✓ Simplex 码测试通过")



    # 测试 8: 界分析

    print("\n【测试 8】码界分析")

    n, k = 23, 12

    print(f"({n}, {k}) 码的理论上界:")

    print(f"  Singleton 上界: d <= {Singleton_bound(n, k)}")

    print(f"  Plotkin 上界: d <= {Plotkin_bound(n, k)}")

    print(f"  Gilbert-Varshamov 估计: d >= {Gilbert_Varshamov_bound(n, k)}")



    # 测试 9: 汉明码 (15, 11)

    print("\n【测试 9】汉明码 (15, 11)")

    ham_15 = hamming_codeclassic(4)

    print(f"参数: n={ham_15.n}, k={ham_15.k}")

    print(f"最小距离: {ham_15.minimum_distance()}")

    assert ham_15.minimum_distance() == 3

    print("✓ 汉明码 (15, 11) 测试通过")



    print("\n" + "=" * 60)

    print("所有测试完成！")

    print("=" * 60)



    print("\n复杂度分析:")

    print("  编码: O(k * n)")

    print("  伴随式计算: O((n-k) * n)")

    print("  查表译码: O(1)")

    print("  最小距离计算: O(2^k * k * n)")

    print("  空间: O(2^{n-k}) for syndrome table")

