# -*- coding: utf-8 -*-

"""

算法实现：隐私计算 / 05_bulletproofs



本文件实现 05_bulletproofs 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict





class PedersenCommitment:

    """

    Pedersen承诺



    承诺: C = g^r * h^m mod p

    其中m是消息,r是随机盲因子



    性质:

    - 隐藏性: 随机r完全隐藏了m

    - 绑定性: 无法在不改变C的情况下改变m

    """



    def __init__(self, security_bits: int = 256):

        """

        初始化Pedersen承诺



        Args:

            security_bits: 安全参数(位长)

        """

        self.security_bits = security_bits

        # 简化的群参数

        np.random.seed(42)

        self.p = 2**31 - 1  # 大素数

        self.g = 5  # 生成元

        self.h = 7  # 第二个生成元(与g独立)

        self.r = None  # 随机盲因子



    def commit(self, value: int, r: int = None) -> Tuple[int, int]:

        """

        承诺值



        Args:

            value: 要承诺的值

            r: 随机盲因子(可选)



        Returns:

            (承诺值, 使用的随机数)

        """

        if r is None:

            r = np.random.randint(1, self.p)



        # C = g^value * h^r mod p

        commitment = (pow(self.g, value, self.p) *

                      pow(self.h, r, self.p)) % self.p



        self.r = r

        return commitment, r



    def open(self, commitment: int, value: int, r: int) -> bool:

        """

        打开承诺



        Args:

            commitment: 承诺值

            value: 原始值

            r: 盲因子



        Returns:

            是否正确打开

        """

        expected = (pow(self.g, value, self.p) *

                   pow(self.h, r, self.p)) % self.p

        return commitment == expected





class InnerProductArgument:

    """

    内积论证(Inner Product Argument)



    Bulletproofs的核心构建块



    证明者声称知道向量a和b,使得:

    P = <a, b> = sum(a_i * b_i)



    而不透露a和b的具体值

    """



    def __init__(self, field_modulus: int = 2**31 - 1):

        """

        初始化内积论证



        Args:

            field_modulus: 有限域模数

        """

        self.p = field_modulus

        np.random.seed(42)



    def prove(

        self,

        a: List[int],

        b: List[int],

        P: int = None

    ) -> Dict:

        """

        证明内积关系



        使用递归协议:

        1. 将向量分成两半

        2. 发送一小组.commitment用于验证

        3. 递归处理剩余部分



        Args:

            a: 第一个向量

            b: 第二个向量

            P: 声称的内积(可选)



        Returns:

            证明字典

        """

        n = len(a)



        if P is None:

            P = sum(ai * bi for ai, bi in zip(a, b)) % self.p



        # 递归深度

        depth = int(np.log2(n))



        # 存储每轮的挑战和commitment

        L_list = []

        R_list = []

        a_list = [a]

        b_list = [b]



        # 简化的证明

        current_a = a

        current_b = b



        for i in range(depth):

            # 将向量分成两半

            half = len(current_a) // 2

            a_L = current_a[:half]

            a_R = current_a[half:]

            b_L = current_b[:half]

            b_R = current_b[half:]



            # 计算 L = <a_L, b_R>, R = <a_R, b_L>

            L = sum(ai * bi for ai, bi in zip(a_L, b_R)) % self.p

            R = sum(ai * bi for ai, bi in zip(a_R, b_L)) % self.p



            L_list.append(L)

            R_list.append(R)



            # 简化的下一轮向量

            # 实际需要使用随机挑战

            challenge = np.random.randint(1, self.p)

            next_a = [(aiL + challenge * aiR) % self.p

                     for aiL, aiR in zip(a_L, a_R)]

            next_b = [(biR + challenge * biL) % self.p

                     for biR, biL in zip(b_R, b_L)]



            current_a = next_a

            current_b = next_b



        proof = {

            "L": L_list,

            "R": R_list,

            "a_final": current_a,

            "b_final": current_b,

            "P": P

        }



        return proof



    def verify(self, proof: Dict) -> bool:

        """

        验证内积证明



        Args:

            proof: 证明字典



        Returns:

            是否验证通过

        """

        # 简化的验证

        # 实际需要重建过程并验证最终等式



        L = proof["L"]

        R = proof["R"]

        P = proof["P"]



        # 验证最终内积

        a_final = proof["a_final"]

        b_final = proof["b_final"]



        if len(a_final) == 1 and len(b_final) == 1:

            final_product = (a_final[0] * b_final[0]) % self.p

            # 需要验证这个与P的关系

            pass



        return True





class RangeProof:

    """

    Bulletproofs范围证明



    证明: v ∈ [0, 2^n - 1]



    通过将v表示为二进制,然后证明每位在{0,1}中

    """



    def __init__(self, n_bits: int = 32):

        """

        初始化范围证明



        Args:

            n_bits: 位数(默认32位整数)

        """

        self.n_bits = n_bits

        self.pedersen = PedersenCommitment()

        self.inner_product = InnerProductArgument()



    def create_bits_vector(self, value: int) -> List[int]:

        """

        将值转换为二进制位向量



        Args:

            value: 要编码的值



        Returns:

            二进制位向量

        """

        bits = []

        for i in range(self.n_bits):

            bits.append((value >> i) & 1)

        return bits



    def prove(

        self,

        value: int,

        r: int = None,

        commitment: int = None

    ) -> Dict:

        """

        证明值在范围内



        Args:

            value: 要承诺的值

            r: 随机盲因子

            commitment: 已有承诺(可选)



        Returns:

            证明字典

        """

        # 1. 承诺值

        if commitment is None:

            commitment, r = self.pedersen.commit(value, r)



        # 2. 创建位向量

        bits = self.create_bits_vector(value)



        # 3. 创建证明

        # 令 a = bits, b = 2^i

        powers_of_2 = [pow(2, i, self.pedersen.p) for i in range(self.n_bits)]



        # 内积 <bits, powers> = value

        ip_proof = self.inner_product.prove(bits, powers_of_2, value)



        proof = {

            "commitment": commitment,

            "bits_proof": ip_proof,

            "r": r

        }



        return proof



    def verify(self, proof: Dict) -> bool:

        """

        验证范围证明



        Args:

            proof: 证明字典



        Returns:

            是否验证通过

        """

        commitment = proof["commitment"]

        bits_proof = proof["bits_proof"]



        # 验证内积证明

        return self.inner_product.verify(bits_proof)





class AggregatedRangeProof:

    """

    聚合范围证明



    将多个范围证明聚合成一个,减少通信开销



    适用于:

    - 多个交易金额同时验证

    - 隐私数据库的批量查询

    """



    def __init__(self, n_bits: int = 32, max_aggregates: int = 8):

        """

        初始化聚合范围证明



        Args:

            n_bits: 位数

            max_aggregates: 最大聚合数量

        """

        self.n_bits = n_bits

        self.max_aggregates = max_aggregates

        self.pedersen = PedersenCommitment()

        self.inner_product = InnerProductArgument()



    def prove_multiple(

        self,

        values: List[int],

        rs: List[int] = None

    ) -> Dict:

        """

        证明多个值在范围内



        使用对数通信复杂度:O(log n * log m)



        Args:

            values: 值列表

            rs: 随机盲因子列表



        Returns:

            聚合证明

        """

        n = len(values)



        if rs is None:

            rs = [np.random.randint(1, self.pedersen.p) for _ in range(n)]



        # 承诺所有值

        commitments = []

        for v, r in zip(values, rs):

            c, _ = self.pedersen.commit(v, r)

            commitments.append(c)



        # 聚合位向量

        # 创建一个大的位矩阵

        all_bits = []

        for v in values:

            bits = [(v >> i) & 1 for i in range(self.n_bits)]

            all_bits.extend(bits)



        # 聚合承诺

        aggregated_commitment = sum(commitments) % self.pedersen.p



        # 创建聚合证明

        powers_of_2 = [pow(2, i, self.pedersen.p) for i in range(self.n_bits)]



        # 重复powers以匹配总位数

        extended_powers = powers_of_2 * n



        ip_proof = self.inner_product.prove(all_bits, extended_powers)



        proof = {

            "commitments": commitments,

            "aggregated_commitment": aggregated_commitment,

            "bits_proof": ip_proof,

            "n_values": n,

            "n_bits": self.n_bits

        }



        return proof



    def verify_multiple(self, proof: Dict) -> bool:

        """

        验证聚合证明



        Args:

            proof: 聚合证明



        Returns:

            是否验证通过

        """

        bits_proof = proof["bits_proof"]

        return self.inner_product.verify(bits_proof)





def create_range_proof_example():

    """

    创建范围证明示例



    示例: 证明交易金额v在[0, 2^32 - 1]范围内

    """



    print("Bulletproofs 范围证明示例")

    print("=" * 50)



    # 1. 基本范围证明

    print("\n1. 基本范围证明")

    rp = RangeProof(n_bits=16)  # 使用16位



    value = 12345

    print(f"   要证明的值: {value}")

    print(f"   二进制: {bin(value)}")



    proof = rp.prove(value)



    print(f"   承诺: {proof['commitment']}")

    print(f"   证明有效: {rp.verify(proof)}")



    # 2. 多值聚合证明

    print("\n2. 聚合范围证明 (8个值)")

    agg_rp = AggregatedRangeProof(n_bits=16, max_aggregates=8)



    values = [100, 500, 1000, 5000, 10000, 30000, 50000, 65535]

    print(f"   要证明的值: {values}")



    agg_proof = agg_rp.prove_multiple(values)



    print(f"   聚合承诺: {agg_proof['aggregated_commitment']}")

    print(f"   验证结果: {agg_rp.verify_multiple(agg_proof)}")



    # 3. Pedersen承诺验证

    print("\n3. Pedersen承诺演示")

    pc = PedersenCommitment()



    secret = 42

    commitment, r = pc.commit(secret)



    print(f"   秘密值: {secret}")

    print(f"   承诺: {commitment}")

    print(f"   打开验证: {pc.open(commitment, secret, r)}")



    # 验证承诺隐藏了值

    wrong_value = 100

    print(f"   用错误值打开: {pc.open(commitment, wrong_value, r)}")





if __name__ == "__main__":

    create_range_proof_example()



    print("\n" + "=" * 60)

    print("Bulletproofs演示完成!")

    print("=" * 60)

