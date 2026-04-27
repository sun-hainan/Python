# -*- coding: utf-8 -*-

"""

算法实现：局部可解码码 / reed_muller_ldc



本文件实现 reed_muller_ldc 相关的算法功能。

"""



import random





class ReedMullerCode:

    """

    二元 Reed-Muller 码 RM(m, r)。



    参数:

        m: 变量数

        r: 多项式次数



    码字长度: 2^m

    维度: C(m+r, r)

    距离: 2^{m-r}

    """



    def __init__(self, m, r):

        self.m = m

        self.r = r

        self.n = 2 ** m  # 码字长度

        # 生成所有 m 比特向量的列表

        self.points = self._generate_all_points()



    def _generate_all_points(self):

        """生成所有 2^m 个 m 维二元点。"""

        points = []

        for i in range(self.n):

            # 将 i 转为 m 位二进制

            point = []

            x = i

            for _ in range(self.m):

                point.append(x & 1)

                x >>= 1

            # 补齐到 m 位

            while len(point) < self.m:

                point.append(0)

            points.append(tuple(point))

        return points



    def encode(self, coefficients):

        """

        编码：评估多项式在所有 2^m 个点上。



        参数:

            coefficients: 多项式系数（字典或列表）

            对于 RM(m,1)，系数包括：常数项 + m 个一次项



        返回:

            codeword: 长度为 2^m 的码字

        """

        codeword = []

        for point in self.points:

            value = self._evaluate_polynomial(coefficients, point)

            codeword.append(value % 2)

        return codeword



    def _evaluate_polynomial(self, coeffs, point):

        """

        在一个点上评估多项式。



        对于 RM(m,1): f(x1,...,xm) = a0 + a1*x1 + ... + am*xm

        """

        if isinstance(coeffs, dict):

            # 系数字典：key 是单项式的索引

            result = coeffs.get((), 0)  # 常数项

            for i, xi in enumerate(point):

                key = (i,)  # 第 i 个变量

                result += coeffs.get(key, 0) * xi

        else:

            # 系数列表：[a0, a1, a2, ..., a_m]

            result = coeffs[0]  # 常数项

            for i, xi in enumerate(point):

                if i + 1 < len(coeffs):

                    result += coeffs[i + 1] * xi

        return result % 2



    def decode_bit(self, received_word, index, errors):

        """

        局部解码：恢复码字中第 index 个比特。



        使用 Walsh-Hadamard 码的解码技术（对于 RM(1,m)）。



        参数:

            received_word: 接收到的（有噪声的）码字

            index: 要恢复的比特位置

            errors: 假设的错误数



        返回:

            恢复的比特值

        """

        m = self.m

        n = self.n



        # 对于 RM(m,1)，每个比特位置对应一个点

        # 恢复该点的函数值



        # 方法1：检查附近点的值，通过多数投票

        # 方法2：使用导数（偏导）来隔离每个变量



        # 这里用简化方法：随机查询若干位置，用投票恢复

        num_queries = 3 * (errors + 1)  # 查询复杂度 O(errors)



        votes = []

        for _ in range(num_queries):

            # 随机选一个点

            query_idx = random.randint(0, n - 1)

            query_point = self.points[query_idx]



            # 构造导数查询

            # f(x) + f(x + e_i) 可以消除第 i 个变量的贡献

            derivative_point = list(query_point)

            derivative_point[index % m] ^= 1

            derivative_point = tuple(derivative_point)



            # 找到这两个点的索引

            idx1 = self.points.index(query_point)

            idx2 = self.points.index(derivative_point)



            # 计算 f(x) + f(x + e_i)

            val = (received_word[idx1] + received_word[idx2]) % 2

            votes.append(val)



        # 多数投票

        return 1 if sum(votes) > len(votes) // 2 else 0





def rm_1_m_encoder(m, coefficients):

    """

    RM(1,m) 编码器的便捷封装。



    参数:

        m: 变量数

        coefficients: 长度 m+1 的列表 [a0, a1, ..., am]

    """

    rm = ReedMullerCode(m, 1)

    return rm.encode(coefficients)





def rm_1_m_local_decode(m, received_word, index, errors=0):

    """

    RM(1,m) 的局部解码器。



    参数:

        m: 变量数

        received_word: 接收字

        index: 要恢复的比特位置

        errors: 容忍的错误数



    返回:

        恢复的比特

    """

    rm = ReedMullerCode(m, 1)

    return rm.decode_bit(received_word, index, errors)





if __name__ == "__main__":

    print("=== Reed-Muller 码 LDC 测试 ===")



    # RM(3,1) 码：3 个变量，一次多项式

    m = 3

    rm = ReedMullerCode(m, 1)



    print(f"RM({m}, 1) 码:")

    print(f"  码字长度: {rm.n}")

    print(f"  变量数: {rm.m}")



    # 编码：f(x,y,z) = 1 + x + y + z

    coefficients = [1, 1, 1, 1]  # [a0, ax, ay, az]



    codeword = rm.encode(coefficients)

    print(f"\n编码多项式 f(x,y,z) = 1 + x + y + z")

    print(f"码字: {codeword}")

    print(f"码字长度: {len(codeword)}")



    # 模拟噪声

    noisy = codeword[:]

    num_errors = 1

    error_positions = random.sample(range(len(noisy)), num_errors)

    for pos in error_positions:

        noisy[pos] ^= 1



    print(f"\n注入 {num_errors} 个错误后的接收字:")

    print(f"  错误位置: {error_positions}")

    print(f"  接收字: {noisy}")



    # 局部解码：恢复几个比特

    print(f"\n=== 局部解码测试 ===")

    for test_idx in [0, 3, 5, 7]:

        recovered = rm.decode_bit(noisy, test_idx, errors=1)

        original = codeword[test_idx]

        print(f"  恢复 bit[{test_idx}]: {recovered} (原始: {original}) {'✓' if recovered == original else '✗'}")



    print(f"\nRM 码的 LDC 特性:")

    print(f"  查询复杂度: O(errors) = O(1)")

    print(f"  码字长度: 2^m（指数级）")

    print(f"  距离: 2^{m-1}")

    print(f"  局部解码：从任意位置恢复单个比特")

