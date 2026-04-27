# -*- coding: utf-8 -*-

"""

算法实现：局部可解码码 / polar_code



本文件实现 polar_code 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class PolarCode:

    """Polar码"""



    def __init__(self, n: int, k: int):

        """

        参数：

            n: 码字长度（2的幂）

            k: 信息位数

        """

        self.n = n

        self.k = k

        self.r = n - k  # 冻结位数



        # 信道可靠性排序（简化）

        self.frozen_bits = list(range(self.r))



    def encode(self, message: List[int]) -> List[int]:

        """

        极化码编码



        参数：

            message: k位信息



        返回：n位码字

        """

        if len(message) != self.k:

            raise ValueError(f"消息长度必须是{self.k}")



        # 构造信息位和冻结位

        u = [0] * self.n



        # 放置信息位

        info_idx = 0

        for i in range(self.n):

            if i not in self.frozen_bits:

                u[i] = message[info_idx]

                info_idx += 1



        # 信道合并（XOR操作）

        codeword = self._channel_combination(u)



        return codeword



    def _channel_combination(self, u: List[int]) -> List[int]:

        """信道合并操作"""

        # 递归XOR树

        n = len(u)

        if n <= 1:

            return u



        mid = n // 2



        # 递归合并

        left = self._channel_combination(u[:mid])

        right = self._channel_combination(u[mid:])



        # XOR操作

        for i in range(mid):

            right[i] ^= left[i]



        return left + right



    def decode(self, received: List[int]) -> List[int]:

        """

        SC译码（_successive cancellation）



        参数：

            received: 接收向量



        返回：信息位

        """

        # 反向操作

        u_hat = self._channel_split(received)



        # 提取信息位

        message = []

        for i in range(self.n):

            if i not in self.frozen_bits:

                message.append(u_hat[i])



        return message



    def _channel_split(self, y: List[int]) -> List[int]:

        """信道分离（反向操作）"""

        n = len(y)

        if n <= 1:

            return y



        mid = n // 2

        left = y[:mid]

        right = y[mid:]



        # 反向XOR

        for i in range(mid):

            right[i] ^= left[i]



        # 递归

        left_decoded = self._channel_split(left)

        right_decoded = self._channel_split(right)



        return left_decoded + right_decoded





def polar_code_capacity():

    """极化码容量"""

    print("=== 极化码容量 ===")

    print()

    print("信道极化：")

    print("  - N 个独立信道 → N 个相关信道")

    print("  - 有些信道容量接近1（好信道）")

    print("  - 有些信道容量接近0（差信道）")

    print()

    print("编码定理：")

    print("  - 当 N → ∞，好信道比例 → 容量")

    print("  - 可以达到香农容量")

    print()

    print("5G标准：")

    print("  - Polar码成为5G控制信道编码标准")

    print("  - 用于eMBB场景")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Polar码测试 ===\n")



    # 创建极化码

    n = 8

    k = 4



    polar = PolarCode(n, k)



    # 信息

    message = [1, 0, 1, 1]



    print(f"信息位: {message}")

    print()



    # 编码

    codeword = polar.encode(message)

    print(f"码字: {codeword}")



    # 模拟噪声

    noisy = codeword.copy()

    noisy[2] ^= 1  # 翻转一位



    print(f"噪声接收: {noisy}")



    # 译码

    decoded = polar.decode(noisy)

    print(f"译码结果: {decoded}")

    print(f"验证: {'✅ 正确' if decoded == message else '❌ 错误'}")



    print()

    polar_code_capacity()



    print()

    print("说明：")

    print("  - Polar码是5G标准之一")

    print("  - 基于信道极化理论")

    print("  - 可以达到信道容量")

