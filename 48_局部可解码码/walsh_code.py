# -*- coding: utf-8 -*-

"""

算法实现：局部可解码码 / walsh_code



本文件实现 walsh_code 相关的算法功能。

"""



import numpy as np

from typing import List





class WalshCode:

    """Walsh码"""



    def __init__(self, n: int):

        """

        参数：

            n: Walsh矩阵大小（2的幂）

        """

        self.n = n

        self.matrix = self._build_walsh_matrix()



    def _build_walsh_matrix(self) -> np.ndarray:

        """

        构建Walsh矩阵



        返回：Walsh矩阵

        """

        # 基础矩阵

        H0 = np.array([[1]])



        # 迭代构造

        while H0.shape[0] < self.n:

            size = H0.shape[0]

            top = np.hstack([H0, H0])

            bottom = np.hstack([H0, -H0])

            H0 = np.vstack([top, bottom])



        return H0



    def get_code(self, index: int) -> List[int]:

        """

        获取指定索引的码



        参数：

            index: 码索引



        返回：码序列

        """

        if index >= self.n:

            index = index % self.n



        return self.matrix[index].tolist()



    def encode_data(self, data_bits: List[int], code_index: int) -> List[int]:

        """

        用Walsh码编码数据



        参数：

            data_bits: 数据位

            code_index: 码索引



        返回：编码后的信号

        """

        code = self.get_code(code_index)



        # 扩展调制

        encoded = []

        for bit in data_bits:

            if bit == 1:

                encoded.extend(code)

            else:

                encoded.extend([-c for c in code])



        return encoded



    def decode_signal(self, signal: List[int], code_index: int) -> List[int]:

        """

        解码信号



        参数：

            signal: 接收信号

            code_index: 码索引



        返回：数据位

        """

        code = self.get_code(code_index)

        code_len = len(code)



        decoded = []

        for i in range(0, len(signal) - code_len + 1, code_len):

            segment = signal[i:i + code_len]



            # 相关解码

            correlation = sum(s * c for s, c in zip(segment, code))



            # 判决

            bit = 1 if correlation > 0 else 0

            decoded.append(bit)



        return decoded



    def orthogonality_check(self) -> bool:

        """

        检查正交性



        返回：是否正交

        """

        for i in range(self.n):

            for j in range(i + 1, self.n):

                dot = sum(self.matrix[i] * self.matrix[j])

                if dot != 0:

                    return False

        return True





def walsh_applications():

    """Walsh码应用"""

    print("=== Walsh码应用 ===")

    print()

    print("1. CDMA移动通信")

    print("   - 每个用户分配唯一Walsh码")

    print("   - 同时传输不互相干扰")

    print()

    print("2. 同步多路复用")

    print("   - 正交多路复用")

    print("   - 减少干扰")

    print()

    print("3. 误码控制")

    print("   - Walsh-Hadamard码")

    print("   - 可纠正部分错误")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Walsh码测试 ===\n")



    # 创建Walsh矩阵

    n = 8

    walsh = WalshCode(n)



    print(f"Walsh矩阵大小: {n}×{n}")

    print(f"矩阵:\n{walsh.matrix}")

    print()



    # 检查正交性

    is_orthogonal = walsh.orthogonality_check()

    print(f"正交性检查: {'✅ 通过' if is_orthogonal else '❌ 失败'}")

    print()



    # 编码和解码

    data = [1, 0, 1, 1]

    code_idx = 3



    print(f"原始数据: {data}")

    print(f"使用的码: {walsh.get_code(code_idx)}")

    print()



    # 编码

    encoded = walsh.encode_data(data, code_idx)

    print(f"编码后: {encoded[:32]}...")  # 显示部分



    # 解码

    decoded = walsh.decode_signal(encoded, code_idx)

    print(f"解码后: {decoded}")

    print(f"正确: {'✅' if decoded == data else '❌'}")



    print()

    walsh_applications()



    print()

    print("说明：")

    print("  - Walsh码是重要的正交码")

    print("  - 用于CDMA等通信系统")

    print("  - 构造简单，正交性好")

