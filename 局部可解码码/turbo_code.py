# -*- coding: utf-8 -*-

"""

算法实现：局部可解码码 / turbo_code



本文件实现 turbo_code 相关的算法功能。

"""



import random

from typing import List, Tuple





class TurboCode:

    """Turbo码"""



    def __init__(self, n: int, k: int, interleaver_size: int = 1000):

        """

        参数：

            n: 码字长度

            k: 信息长度

            interleaver_size: 交织器大小

        """

        self.n = n

        self.k = k

        self.interleaver_size = interleaver_size



        # 创建两个卷积编码器

        self.encoder1 = ConvolutionalEncoder(rate=1)

        self.encoder2 = ConvolutionalEncoder(rate=1)



        # 交织器

        self.interleaver = list(range(interleaver_size))

        random.shuffle(self.interleaver)



    def encode(self, message: List[int]) -> List[int]:

        """

        Turbo编码



        参数：

            message: 信息位



        返回：码字（信息位 + 两个校验位）

        """

        # 编码器1输出

        parity1 = self.encoder1.encode(message)



        # 交织

        interleaved = [message[self.interleaver[i % len(self.interleaver)]] for i in range(len(message))]



        # 编码器2输出

        parity2 = self.encoder2.encode(interleaved)



        # 串联：信息位 + 校验位1 + 校验位2

        codeword = []

        for i in range(len(message)):

            codeword.append(message[i])

            if i < len(parity1):

                codeword.append(parity1[i])

            if i < len(parity2):

                codeword.append(parity2[i])



        return codeword



    def decode_iterative(self, received: List[float],

                       max_iter: int = 10) -> List[int]:

        """

        迭代译码（简化版）



        参数：

            received: 接收的软信息

            max_iter: 最大迭代次数



        返回：译码信息

        """

        # 简化的迭代译码

        decoded = []



        # 硬判决

        for val in received[:self.k]:

            decoded.append(0 if val < 0 else 1)



        return decoded





class ConvolutionalEncoder:

    """卷积编码器"""



    def __init__(self, rate: int = 1, memory: int = 2):

        """

        参数：

            rate: 码率

            memory: 记忆长度

        """

        self.rate = rate

        self.memory = memory

        self.register = [0] * memory



    def encode(self, bits: List[int]) -> List[int]:

        """卷积编码"""

        output = []



        for bit in bits:

            # 移位

            self.register.pop(0)

            self.register.append(bit)



            # 计算校验位（简化：异或所有位）

            parity = sum(self.register) % 2

            output.append(parity)



        return output





def turbo_performance():

    """Turbo码性能"""

    print("=== Turbo码性能 ===")

    print()

    print("性能：")

    print("  - 在AWGN信道上，0.5 dB可达到10^-5误码率")

    print("  - 离香农极限只有约0.5 dB")

    print()

    print("迭代译码：")

    print("  - 每次迭代更新两个软信息")

    print("  - 通常5-10次迭代收敛")

    print()

    print("应用：")

    print("  - 3G/4G/5G移动通信")

    print("  - 卫星通信")

    print("  - 深空通信")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Turbo码测试 ===\n")



    random.seed(42)



    # 创建Turbo码

    turbo = TurboCode(n=100, k=50)



    # 信息

    message = [random.randint(0, 1) for _ in range(50)]



    print(f"信息长度: {len(message)}")

    print()



    # 编码

    codeword = turbo.encode(message)



    print(f"码字长度: {len(codeword)}")

    print(f"码率: {len(message)/len(codeword):.2f}")



    # 模拟噪声

    noisy = [b + 0.5 * random.gauss(0, 1) for b in codeword[:len(message)]]



    # 译码

    decoded = turbo.decode_iterative(noisy)



    print(f"译码结果前10位: {decoded[:10]}")

    print(f"原始信息前10位: {message[:10]}")



    print()

    turbo_performance()



    print()

    print("说明：")

    print("  - Turbo码是3G到5G的核心技术")

    print("  - 迭代译码是成功的关键")

    print("  - 与LDPC是竞争关系")

