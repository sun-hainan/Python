# -*- coding: utf-8 -*-

"""

算法实现：编码理论 / convolutional_code



本文件实现 convolutional_code 相关的算法功能。

"""



from typing import List, Tuple, Optional

import random





class ConvolutionalCode:

    """

    卷积码编码器

    """

    

    def __init__(self, n: int, k: int, generator_polynomials: List[List[int]]):

        """

        初始化

        

        Args:

            n: 输出位数

            k: 状态位数

            generator_polynomials: 生成多项式(每个是系数的列表)

        """

        self.n = n

        self.k = k

        self.num_states = 2 ** k

        self.generators = generator_polynomials

        self.state = 0

    

    def encode(self, data: List[int]) -> List[int]:

        """

        卷积编码

        

        Args:

            data: 输入数据位

        

        Returns:

            编码输出

        """

        self.state = 0

        output = []

        

        for bit in data:

            # 移入新数据

            self.state = ((self.state << 1) | bit) & ((1 << self.k) - 1)

            

            # 计算输出

            for gen in self.generators:

                out_bit = 0

                state_copy = self.state

                for coef in gen:

                    out_bit ^= (state_copy & 1) * coef

                    state_copy >>= 1

                output.append(out_bit & 1)

        

        return output

    

    def reset(self):

        """重置状态"""

        self.state = 0





class ViterbiDecoder:

    """

    Viterbi译码器

    使用动态规划找最可能的路径

    """

    

    def __init__(self, n: int, k: int, generator_polynomials: List[List[int]]):

        """

        初始化

        

        Args:

            n: 输出位数

            k: 状态位数

            generator_polynomials: 生成多项式

        """

        self.n = n

        self.k = k

        self.num_states = 2 ** k

        self.generators = generator_polynomials

        

        # 预计算状态转移

        self._build_transitions()

    

    def _build_transitions(self):

        """预计算所有状态转移"""

        self.next_state = [[0, 0] for _ in range(self.num_states)]  # [输入0时的下一状态, 输入1时的下一状态]

        self.output = [[0, 0] for _ in range(self.num_states)]  # 对应的输出

        

        for state in range(self.num_states):

            for input_bit in [0, 1]:

                # 下一状态

                next_state = ((state << 1) | input_bit) & ((1 << self.k) - 1)

                self.next_state[state][input_bit] = next_state

                

                # 输出

                out_bits = 0

                state_copy = self.next_state[state][input_bit]

                for gen in self.generators:

                    out_bit = 0

                    for coef in gen:

                        out_bit ^= (state_copy & 1) * coef

                        state_copy >>= 1

                    out_bits = (out_bits << 1) | (out_bit & 1)

                

                self.output[state][input_bit] = out_bits

    

    def decode(self, received: List[int]) -> List[int]:

        """

        Viterbi译码

        

        Args:

            received: 接收序列(硬判决)

        

        Returns:

            译码后的数据位

        """

        if len(received) < self.n:

            return []

        

        num_bits = len(received) // self.n

        

        # 路径度量 [状态] = 累计汉明距离

        path_metrics = [float('inf')] * self.num_states

        path_metrics[0] = 0

        

        # 存储路径 [时间步][状态] = 前一个状态

        paths = [[-1] * self.num_states for _ in range(num_bits + 1)]

        

        # 逐时间步处理

        for t in range(num_bits):

            # 提取t时刻的接收符号

            recv_bits = received[t * self.n:(t + 1) * self.n]

            recv_val = 0

            for bit in recv_bits:

                recv_val = (recv_val << 1) | bit

            

            # 新路径度量

            new_metrics = [float('inf')] * self.num_states

            

            for state in range(self.num_states):

                if path_metrics[state] == float('inf'):

                    continue

                

                for input_bit in [0, 1]:

                    next_state = self.next_state[state][input_bit]

                    out_val = self.output[state][input_bit]

                    

                    # 汉明距离

                    hamming_dist = bin(recv_val ^ out_val).count('1')

                    

                    new_metric = path_metrics[state] + hamming_dist

                    

                    if new_metric < new_metrics[next_state]:

                        new_metrics[next_state] = new_metric

                        paths[t + 1][next_state] = state

            

            path_metrics = new_metrics

        

        # 找到最终最佳状态

        best_state = min(range(self.num_states), key=lambda s: path_metrics[s])

        

        # 回溯

        decoded = []

        state = best_state

        for t in range(num_bits, 0, -1):

            prev_state = paths[t][state]

            # 输入位是状态的最低位

            input_bit = state & 1

            decoded.append(input_bit)

            state = prev_state

        

        decoded.reverse()

        return decoded

    

    def decode_soft(self, received: List[float], threshold: float = 0) -> List[int]:

        """

        软判决Viterbi译码

        

        Args:

            received: 接收的软值(概率或对数似然比)

            threshold: 判决阈值

        

        Returns:

            译码后的数据位

        """

        # 简化为硬判决

        hard = [1 if r > threshold else 0 for r in received]

        return self.decode(hard)





def encode_conv(data: List[int], generator_polys: List[List[int]] = None) -> List[int]:

    """

    卷积编码便捷函数

    

    Args:

        data: 输入数据

        generator_polys: 生成多项式

    

    Returns:

        编码序列

    """

    if generator_polys is None:

        # (2, 1, 2) 卷积码: [133, 171] 八进制

        generator_polys = [[1, 1, 1], [1, 1, 1]]  # 简化

    

    encoder = ConvolutionalCode(n=2, k=2, generator_polynomials=generator_polys)

    return encoder.encode(data)





def decode_viterbi(received: List[int], generator_polys: List[List[int]] = None) -> List[int]:

    """

    Viterbi译码便捷函数

    

    Args:

        received: 接收序列

        generator_polys: 生成多项式

    

    Returns:

        译码数据

    """

    if generator_polys is None:

        generator_polys = [[1, 1, 1], [1, 1, 1]]

    

    decoder = ViterbiDecoder(n=2, k=2, generator_polynomials=generator_polys)

    return decoder.decode(received)





# 测试代码

if __name__ == "__main__":

    # 测试1: 基本编码译码

    print("测试1 - 基本卷积码:")

    

    # (2, 1, 2) 卷积码

    # 生成多项式: g1 = [1, 1, 1], g2 = [1, 1, 1]

    generators = [[1, 1, 1], [1, 1, 1]]

    

    encoder = ConvolutionalCode(n=2, k=2, generator_polynomials=generators)

    decoder = ViterbiDecoder(n=2, k=2, generator_polynomials=generators)

    

    data = [1, 0, 1, 1, 0, 0, 1]

    print(f"  原始数据: {data}")

    

    encoded = encoder.encode(data)

    print(f"  编码后: {encoded}")

    print(f"  编码长度: {len(data)} -> {len(encoded)}")

    

    # 译码

    decoded = decoder.decode(encoded)

    print(f"  译码后: {decoded}")

    print(f"  正确: {data == decoded}")

    

    # 测试2: 错误注入

    print("\n测试2 - 错误注入:")

    data = [1, 0, 1, 1, 0, 0, 1]

    encoded = encoder.encode(data)

    

    # 注入单比特错误

    for error_pos in range(len(encoded)):

        corrupted = encoded.copy()

        corrupted[error_pos] ^= 1

        

        decoded = decoder.decode(corrupted)

        correct = (decoded == data)

        print(f"  位置{error_pos:2d}错误: 正确={correct}")

    

    # 测试3: 多比特错误

    print("\n测试3 - 多比特错误:")

    errors = [(1, 5), (3, 7), (2, 4, 8)]

    

    for error_positions in errors:

        corrupted = encoded.copy()

        for pos in error_positions:

            if pos < len(corrupted):

                corrupted[pos] ^= 1

        

        decoded = decoder.decode(corrupted)

        print(f"  位置{error_positions}: 正确={decoded == data}")

    

    # 测试4: 批量测试

    print("\n测试4 - 随机测试:")

    import random

    random.seed(42)

    

    correct = 0

    total = 100

    

    for _ in range(total):

        data = [random.randint(0, 1) for _ in range(20)]

        encoder.state = 0

        encoded = encoder.encode(data)

        

        # 随机错误(1-2%)

        corrupted = encoded.copy()

        for i in range(len(corrupted)):

            if random.random() < 0.015:

                corrupted[i] ^= 1

        

        decoded = decoder.decode(corrupted)

        

        if decoded == data:

            correct += 1

    

    print(f"  正确率: {correct}/{total} = {correct/total:.2%}")

    

    # 测试5: 便捷函数

    print("\n测试5 - 便捷函数:")

    data = [1, 1, 0, 1, 0, 1]

    encoded = encode_conv(data)

    decoded = decode_viterbi(encoded)

    print(f"  数据: {data}")

    print(f"  编码: {encoded}")

    print(f"  译码: {decoded}")

    

    print("\n所有测试完成!")

