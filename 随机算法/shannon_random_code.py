# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / shannon_random_code



本文件实现 shannon_random_code 相关的算法功能。

"""



import random

import numpy as np

from typing import List, Tuple





class ShannonRandomCode:

    """Shannon随机编码"""



    def __init__(self, n: int, k: int, channel_capacity: float):

        """

        参数：

            n: 码字长度

            k: 信息位数

            channel_capacity: 信道容量（比特/信道使用）

        """

        self.n = n

        self.k = k

        self.capacity = channel_capacity



        # 生成随机码书

        self.codebook = self._generate_random_codebook()

        self.rate = k / n



    def _generate_random_codebook(self) -> List[np.ndarray]:

        """生成随机码书"""

        codebook = []



        n_codes = 2 ** self.k



        for _ in range(n_codes):

            # 随机生成码字（0/1）

            codeword = np.random.randint(0, 2, self.n)

            codebook.append(codeword)



        return codebook



    def encode(self, message_bits: List[int]) -> np.ndarray:

        """

        编码



        参数：

            message_bits: 信息位



        返回：码字

        """

        # 将位转换为索引

        index = 0

        for i, bit in enumerate(message_bits):

            index = index * 2 + bit



        return self.codebook[index % len(self.codebook)]



    def decode(self, received: np.ndarray) -> List[int]:

        """

        最佳译码（MAP）



        参数：

            received: 接收向量



        返回：信息位

        """

        # 寻找最可能的码字（简化：最小汉明距离）

        min_distance = self.n + 1

        best_codeword = self.codebook[0]



        for codeword in self.codebook:

            distance = np.sum(codeword != received)

            if distance < min_distance:

                min_distance = distance

                best_codeword = codeword



        # 找到对应的消息

        for i, codeword in enumerate(self.codebook):

            if np.array_equal(codeword, best_codeword):

                # 转换为位

                message = []

                idx = i

                for _ in range(self.k):

                    message.insert(0, idx % 2)

                    idx //= 2

                return message



        return [0] * self.k



    def simulate_channel(self, codeword: np.ndarray,

                        error_prob: float) -> np.ndarray:

        """

        模拟 BSC 信道



        参数：

            codeword: 发送码字

            error_prob: 错误概率



        返回：接收向量

        """

        # 二面对称信道（BSC）

        noise = np.random.random(self.n) < error_prob

        received = codeword.copy()

        received[noise] ^= 1



        return received





def shannon_capacity():

    """Shannon容量"""

    print("=== Shannon容量定理 ===")

    print()

    print("信道编码定理：")

    print("  - 存在码率达到容量C且错误概率任意小")

    print("  - 需要随机编码")

    print("  - 需要最佳译码")

    print()

    print("BSC信道容量：")

    print("  - C = 1 - H(p)")

    print("  - 其中p是错误概率")

    print()

    print("实际限制：")

    print("  - 随机码分析容易但构建困难")

    print("  - 需要短码长时的实际编码")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Shannon随机编码测试 ===\n")



    random.seed(42)



    # 参数

    n = 20  # 码字长度

    k = 5   # 信息长度

    error_prob = 0.1



    capacity = 1 - (-error_prob * np.log2(error_prob) - (1-error_prob) * np.log2(1-error_prob))

    print(f"码字长度: {n}, 信息长度: {k}")

    print(f"码率: {k/n:.2f}")

    print(f"信道容量: {capacity:.4f} bits/channel use")

    print()



    # 创建编码器

    encoder = ShannonRandomCode(n, k, capacity)



    # 发送消息

    message = [0, 1, 0, 1, 1]

    print(f"消息: {message}")



    # 编码

    codeword = encoder.encode(message)

    print(f"码字: {codeword}")



    # 模拟信道

    received = encoder.simulate_channel(codeword, error_prob)

    errors = np.sum(codeword != received)

    print(f"接收: {received}, 错误位数: {errors}")



    # 译码

    decoded = encoder.decode(received)

    print(f"译码: {decoded}")

    print(f"正确: {'✅' if decoded == message else '❌'}")



    print()

    shannon_capacity()



    print()

    print("说明：")

    print("  - Shannon证明了容量的可达性")

    print("  - 随机码性能好但编译码复杂")

    print("  - 现代编码（LDPC,Turbo）接近容量")

