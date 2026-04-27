# -*- coding: utf-8 -*-

"""

算法实现：编码理论 / ldpc_code



本文件实现 ldpc_code 相关的算法功能。

"""



from typing import List, Tuple, Optional

import random

import math





class LDPCCode:

    """

    LDPC码编码器/译码器

    """

    

    def __init__(self, m: int, n: int):

        """

        初始化

        

        Args:

            m: 校验节点数

            n: 变量节点数

        """

        self.m = m  # 校验节点

        self.n = n  # 变量节点

        self.H = [[0] * n for _ in range(m)]  # 校验矩阵

        self._build_matrix()

    

    def _build_matrix(self):

        """构建LDPC校验矩阵(简化:规则LDPC)"""

        # 每个变量节点连接2个校验节点

        # 每个校验节点连接3个变量节点

        

        for j in range(self.n):

            # 第j个变量节点连接到校验节点j%2和(j+1)%2

            self.H[j % self.m][j] = 1

            self.H[(j + 1) % self.m][j] = 1

    

    def encode(self, data: List[int]) -> List[int]:

        """

        LDPC编码(简化)

        

        Args:

            data: 信息位

        

        Returns:

            编码位(需要满足H*c=0)

        """

        # 简化:使用生成矩阵编码

        # 实际应该使用高斯消元构建生成矩阵

        

        code = data.copy()

        

        # 迭代满足校验约束

        for _ in range(100):

            satisfied = True

            for i in range(self.m):

                # 计算校验约束

                nodes = [j for j in range(self.n) if self.H[i][j] == 1]

                parity = sum(code[j] for j in nodes) % 2

                

                if parity == 1:

                    satisfied = False

                    # 翻转一个位来满足约束

                    # 简化:翻转第一个

                    if nodes:

                        code[nodes[0]] ^= 1

            

            if satisfied:

                break

        

        return code

    

    def decode_bp(self, received: List[float], max_iter: int = 100) -> List[int]:

        """

        置信传播译码

        

        Args:

            received: 接收的软值(LLR)

            max_iter: 最大迭代次数

        

        Returns:

            译码位

        """

        n = len(received)

        

        # 初始化消息(从变量到校验)

        v_to_c = [[0.0] * self.m for _ in range(n)]

        

        for j in range(n):

            for i in range(self.m):

                if self.H[i][j] == 1:

                    v_to_c[j][i] = received[j]

        

        # 迭代

        for iteration in range(max_iter):

            # 步骤1: 校验节点更新(水平迭代)

            c_to_v = [[0.0] * self.n for _ in range(self.m)]

            

            for i in range(self.m):

                connected_vars = [j for j in range(n) if self.H[i][j] == 1]

                

                for j in connected_vars:

                    # 计算传递给变量节点j的消息

                    # tanh加法形式

                    product = 1.0

                    for k in connected_vars:

                        if k != j:

                            product *= math.tanh(v_to_c[k][i] / 2)

                    

                    if product == 0:

                        c_to_v[i][j] = 0

                    else:

                        c_to_v[i][j] = 2 * math.atanh(product)

            

            # 步骤2: 变量节点更新(垂直迭代)

            for j in range(n):

                for i in range(self.m):

                    if self.H[i][j] == 1:

                        connected_checks = [k for k in range(self.m) if self.H[k][j] == 1]

                        

                        # 消息 = 接收值 + 从其他校验节点收到的消息之和

                        total = received[j]

                        for k in connected_checks:

                            if k != i:

                                total += c_to_v[k][j]

                        

                        v_to_c[j][i] = total

            

            # 决策

            decoded = []

            for j in range(n):

                connected_checks = [i for i in range(self.m) if self.H[i][j] == 1]

                

                # 计算后验概率

                posterior = received[j]

                for i in connected_checks:

                    posterior += c_to_v[i][j]

                

                decoded.append(1 if posterior > 0 else 0)

            

            # 检查是否满足校验

            if self._check_codeword(decoded):

                return decoded

        

        return decoded

    

    def _check_codeword(self, code: List[int]) -> bool:

        """检查码字是否有效"""

        for i in range(self.m):

            parity = 0

            for j in range(self.n):

                if self.H[i][j] == 1:

                    parity ^= code[j]

            if parity == 1:

                return False

        return True

    

    def decode_hard(self, received: List[int], max_iter: int = 100) -> List[int]:

        """

        硬判决译码(比特翻转)

        

        Args:

            received: 接收的硬值

            max_iter: 最大迭代次数

        

        Returns:

            译码位

        """

        code = received.copy()

        

        for _ in range(max_iter):

            # 计算每个校验节点的不满足数

            unsatisfied = []

            for i in range(self.m):

                nodes = [j for j in range(self.n) if self.H[i][j] == 1]

                parity = sum(code[j] for j in nodes) % 2

                if parity == 1:

                    unsatisfied.append((i, nodes))

            

            if not unsatisfied:

                return code

            

            # 统计每个变量节点被多少个不满足的校验节点连接

            var_counts = {}

            for i, nodes in unsatisfied:

                for j in nodes:

                    var_counts[j] = var_counts.get(j, 0) + 1

            

            if not var_counts:

                return code

            

            # 翻转计数最多的变量

            max_count = max(var_counts.values())

            candidates = [j for j, c in var_counts.items() if c == max_count]

            j = candidates[0]

            code[j] ^= 1

        

        return code





def encode_ldpc(data: List[int], m: int = 6, n: int = 12) -> List[int]:

    """

    LDPC编码便捷函数

    

    Args:

        data: 信息位

        m: 校验节点数

        n: 变量节点数

    

    Returns:

        编码位

    """

    code = LDPCCode(m, n)

    return code.encode(data)





def decode_ldpc(received: List[float], m: int = 6, n: int = 12, 

                method: str = 'bp') -> List[int]:

    """

    LDPC译码便捷函数

    

    Args:

        received: 接收值

        m: 校验节点数

        n: 变量节点数

        method: 'bp' 或 'hard'

    

    Returns:

        译码位

    """

    code = LDPCCode(m, n)

    

    if method == 'bp':

        return code.decode_bp(received)

    else:

        hard = [1 if r > 0 else 0 for r in received]

        return code.decode_hard(hard)





# 测试代码

if __name__ == "__main__":

    # 测试1: 基本编码译码

    print("测试1 - 基本LDPC:")

    m, n = 6, 12

    ldpc = LDPCCode(m, n)

    

    data = [1, 0, 1, 1, 0, 0]  # 6位信息

    print(f"  信息: {data}")

    

    code = ldpc.encode(data)

    print(f"  编码: {code}")

    print(f"  校验: {ldpc._check_codeword(code)}")

    

    # 测试2: 硬判决译码

    print("\n测试2 - 硬判决译码:")

    # 引入错误

    corrupted = code.copy()

    corrupted[2] ^= 1  # 翻转一位

    print(f"  损坏: {corrupted}")

    

    decoded = ldpc.decode_hard(corrupted)

    print(f"  译码: {decoded}")

    print(f"  正确: {decoded == code}")

    

    # 测试3: 软判决译码

    print("\n测试3 - 软判决译码(置信传播):")

    # 创建软输入(添加噪声)

    received = []

    for i, bit in enumerate(code):

        # 简单模型:加噪声

        noise = random.gauss(0, 0.5)

        llr = 2 * bit - 1 + noise  # LLR近似

        received.append(llr)

    

    print(f"  接收LLR: {[f'{x:.2f}' for x in received]}")

    

    decoded_bp = ldpc.decode_bp(received)

    print(f"  BP译码: {decoded_bp}")

    print(f"  正确: {decoded_bp == code}")

    

    # 测试4: 多比特错误

    print("\n测试4 - 多比特错误:")

    for num_errors in [1, 2, 3]:

        corrupted = code.copy()

        error_positions = random.sample(range(n), num_errors)

        for pos in error_positions:

            corrupted[pos] ^= 1

        

        decoded = ldpc.decode_hard(corrupted)

        print(f"  {num_errors}位错误: 正确={decoded == code}")

    

    # 测试5: 批量测试

    print("\n测试5 - 批量测试:")

    import random

    random.seed(42)

    

    correct_hard = 0

    correct_bp = 0

    total = 50

    

    for _ in range(total):

        data = [random.randint(0, 1) for _ in range(6)]

        code = ldpc.encode(data)

        

        # 单比特错误

        corrupted = code.copy()

        error_pos = random.randint(0, n - 1)

        corrupted[error_pos] ^= 1

        

        # 硬判决

        decoded_hard = ldpc.decode_hard(corrupted)

        if decoded_hard == code:

            correct_hard += 1

        

        # 软判决

        received = []

        for bit in corrupted:

            llr = 2 * bit - 1 + random.gauss(0, 0.3)

            received.append(llr)

        

        decoded_bp = ldpc.decode_bp(received)

        if decoded_bp == code:

            correct_bp += 1

    

    print(f"  硬判决正确率: {correct_hard}/{total} = {correct_hard/total:.2%}")

    print(f"  BP正确率: {correct_bp}/{total} = {correct_bp/total:.2%}")

    

    print("\n所有测试完成!")

