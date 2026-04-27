# -*- coding: utf-8 -*-

"""

算法实现：编码理论 / bch_code



本文件实现 bch_code 相关的算法功能。

"""



from typing import List, Tuple, Optional

import random





class BCHCode:

    """

    BCH码编码器/解码器(简化版)

    支持二进制BCH码

    """

    

    def __init__(self, m: int, t: int):

        """

        初始化

        

        Args:

            m: 域GF(2^m)的阶

            t: 纠错能力

        """

        self.m = m

        self.t = t

        self.n = 2 ** m - 1  # 码长

        self.k = self.n - m * t  # 信息位长度(近似)

        

        # 构建本原多项式和域

        self._build_field()

        self._build_generator()

    

    def _build_field(self):

        """构建GF(2^m)域"""

        # 使用本原多项式 x^m + x + 1 (简化)

        self.field_size = 2 ** self.m

        self.alpha_powers = [1] * self.field_size  # alpha^i

        

        # 生成域元素(简化表示)

        for i in range(1, self.field_size - 1):

            self.alpha_powers[i] = (1 << i) % self.field_size

    

    def _build_generator(self):

        """构建生成多项式"""

        # 对于t-纠错BCH,生成多项式是最小多项式的最小公倍式

        # 简化:使用已知的生成多项式

        

        # 对于(15, 7) BCH码(t=2)

        if self.m == 4 and self.t == 2:

            # 生成多项式系数(从最高次到常数项)

            self.generator = [1, 0, 0, 1, 1, 0, 1, 0, 1]  # g(x) = x^8 + x^7 + x^6 + x^4 + 1

            self.k = 7

        else:

            # 通用简化

            self.generator = [1] + [0] * (self.m * self.t) + [1]

            self.k = self.n - len(self.generator) + 1

    

    def encode(self, data: List[int]) -> List[int]:

        """

        BCH编码

        

        Args:

            data: 信息位

        

        Returns:

            编码后的码字

        """

        if len(data) != self.k:

            data = data[:self.k] + [0] * (self.k - len(data))

        

        # 信息多项式乘以x^{n-k}

        padded = data + [0] * (len(self.generator) - 1)

        

        # 除以生成多项式

        remainder = self._polynomial_divide(padded, self.generator)

        

        # 码字 = 信息 + 余式

        code = data + remainder

        

        return code

    

    def _polynomial_divide(self, dividend: List[int], divisor: List[int]) -> List[int]:

        """

        多项式除法

        

        Args:

            dividend: 被除多项式系数

            divisor: 除多项式系数

        

        Returns:

            余式

        """

        dividend = dividend.copy()

        divisor_degree = len(divisor) - 1

        

        for i in range(len(dividend) - divisor_degree):

            if dividend[i]:

                for j in range(1, len(divisor)):

                    dividend[i + j] ^= divisor[j]

        

        # 返回余式(最后 divisor_degree 位)

        return dividend[len(dividend) - divisor_degree:]

    

    def decode(self, received: List[int]) -> Tuple[List[int], int]:

        """

        BCH解码(简化版,只检测错误)

        

        Args:

            received: 接收序列

        

        Returns:

            (解码后的信息位, 错误数估计)

        """

        # 计算伴随式

        syndrome = self._compute_syndrome(received)

        

        # 错误位置和数量估计

        error_count = sum(syndrome)

        

        # 简化:假设无错误或可纠正

        # 实际需要复杂的译码算法(Chien搜索等)

        

        # 返回信息位

        return received[:self.k], error_count

    

    def _compute_syndrome(self, code: List[int]) -> List[int]:

        """计算伴随式"""

        syndrome = []

        for i in range(self.t):

            s = 0

            for j in range(len(code)):

                s ^= (code[j] * self.alpha_powers[(j * (i + 1)) % self.field_size])

            syndrome.append(s)

        return syndrome





def encode_bch_15_7(data: int) -> int:

    """

    (15, 7) BCH码编码

    

    Args:

        data: 7位数据

    

    Returns:

        15位码字

    """

    if data < 0 or data >= 128:

        raise ValueError("数据必须是7位")

    

    # 生成多项式 g(x) = x^8 + x^7 + x^6 + x^4 + 1

    generator = [1, 0, 0, 1, 1, 0, 1, 0, 1]

    

    # 信息多项式系数

    info_bits = [(data >> i) & 1 for i in range(7)]

    

    # 乘以x^8

    padded = info_bits + [0] * 8

    

    # 除以g(x)

    remainder = polynomial_divide(padded, generator)

    

    # 码字

    code = info_bits + remainder

    

    return sum(code[i] << i for i in range(15))





def polynomial_divide(dividend: List[int], divisor: List[int]) -> List[int]:

    """多项式除法"""

    dividend = dividend.copy()

    divisor_degree = len(divisor) - 1

    

    for i in range(len(dividend) - divisor_degree):

        if dividend[i]:

            for j in range(1, len(divisor)):

                dividend[i + j] ^= divisor[j]

    

    return dividend[len(dividend) - divisor_degree:]





def decode_bch_15_7(code: int) -> Tuple[int, int]:

    """

    (15, 7) BCH码解码

    

    Args:

        code: 15位码字

    

    Returns:

        (解码后的7位数据, 错误数)

    """

    # 提取码字位

    bits = [(code >> i) & 1 for i in range(15)]

    

    # 校验多项式

    g = [1, 0, 0, 1, 1, 0, 1, 0, 1]  # 生成多项式

    

    # 计算余式

    remainder = polynomial_divide(bits.copy(), g)

    

    # 错误数

    errors = sum(remainder)

    

    # 提取信息位

    info_bits = bits[:7]

    data = sum(info_bits[i] << i for i in range(7))

    

    return data, errors





def chien_search(error_locator: List[int], n: int) -> List[int]:

    """

    Chien搜索找错误位置

    

    Args:

        error_locator: 错误位置多项式系数

        n: 码长

    

    Returns:

        错误位置列表

    """

    errors = []

    

    for i in range(n):

        # 计算错误值多项式在alpha^{-i}处的值

        val = 0

        for j, coeff in enumerate(error_locator):

            val ^= coeff * (1 << (j * i % n))  # 简化

        if val == 0:

            errors.append(n - 1 - i)

    

    return errors





# 测试代码

if __name__ == "__main__":

    # 测试1: 基本功能

    print("测试1 - (15, 7) BCH码:")

    

    for data in [0, 1, 42, 127]:

        code = encode_bch_15_7(data)

        decoded, errors = decode_bch_15_7(code)

        

        print(f"  数据: {data:07b}, 码字: {code:015b}")

        print(f"    解码: {decoded:07b}, 错误数: {errors}")

    

    # 测试2: 单比特错误

    print("\n测试2 - 单比特错误:")

    data = 42

    code = encode_bch_15_7(data)

    

    for error_pos in range(15):

        corrupted = code ^ (1 << error_pos)

        decoded, errors = decode_bch_15_7(corrupted)

        print(f"  位置{error_pos:2d}翻转: 解码={decoded:07b}, 错误={errors}, 正确={decoded==data}")

    

    # 测试3: 双比特错误

    print("\n测试3 - 双比特错误:")

    data = 42

    code = encode_bch_15_7(data)

    

    for pos1, pos2 in [(0, 1), (5, 10), (7, 14)]:

        corrupted = code ^ (1 << pos1) ^ (1 << pos2)

        decoded, errors = decode_bch_15_7(corrupted)

        print(f"  位置{pos1},{pos2}翻转: 解码={decoded:07b}, 错误={errors}, 正确={decoded==data}")

    

    # 测试4: 汉明距离

    print("\n测试4 - 距离验证:")

    codes = [encode_bch_15_7(d) for d in range(128)]

    

    min_dist = 15

    for i in range(128):

        for j in range(i + 1, 128):

            dist = bin(codes[i] ^ codes[j]).count('1')

            if dist > 0:

                min_dist = min(min_dist, dist)

    

    print(f"  最小距离: {min_dist}")

    

    # 测试5: 批量测试

    print("\n测试5 - 随机测试:")

    import random

    random.seed(42)

    

    correct = 0

    total = 500

    

    for _ in range(total):

        data = random.randint(0, 127)

        code = encode_bch_15_7(data)

        

        # 随机单比特翻转

        if random.random() > 0.3:

            error_pos = random.randint(0, 14)

            code ^= (1 << error_pos)

        

        decoded, _ = decode_bch_15_7(code)

        

        if decoded == data:

            correct += 1

    

    print(f"  正确率: {correct}/{total} = {correct/total:.2%}")

    

    print("\n所有测试完成!")

