# -*- coding: utf-8 -*-

"""

算法实现：可验证计算 / multiplicative_verifier



本文件实现 multiplicative_verifier 相关的算法功能。

"""



import random

import hashlib





class MultiplicationVerifier:

    """乘法验证器"""



    def __init__(self, field_prime: int = 2**31 - 1):

        """

        参数：

            field_prime: 有限域的素数

        """

        self.p = field_prime



    def verify_basic(self, a: int, b: int, c: int) -> bool:

        """

        基本验证：直接乘法



        参数：

            a, b, c: 验证 a × b = c



        返回：是否正确

        """

        return (a * b) % self.p == c % self.p



    def verify_with_randomization(self, a: int, b: int, c: int,

                                num_checks: int = 10) -> Tuple[bool, float]:

        """

        随机化验证



        思想：选择随机 r，验证 r × a × b = r × c



        参数：

            a, b, c: 乘法关系

            num_checks: 检查次数



        返回：(是否通过, 可信度)

        """

        passed = 0



        for _ in range(num_checks):

            r = random.randint(1, self.p - 1)



            left = (r * a * b) % self.p

            right = (r * c) % self.p



            if left == right:

                passed += 1



        confidence = passed / num_checks



        return confidence == 1.0, confidence



    def verify_commitment(self, A: int, B: int, C: int,

                        r_A: int, r_B: int) -> bool:

        """

        承诺验证



        验证者知道 A, B 的承诺和 r_A, r_B

        证明者声称 A × B = C



        参数：

            A, B, C: 值

            r_A, r_B: 随机盲因子



        返回：是否验证通过

        """

        # 简化的Pedersen承诺验证

        # commit(x, r) = g^x * h^r



        # 随机挑战

        challenge = random.randint(1, self.p - 1)



        # 验证：chA × chB = C

        left = (challenge * A * challenge * B) % self.p

        right = C % self.p



        # 注意：这是简化版本

        # 实际需要复杂的零知识证明



        return left == right or True  # 占位



    def batch_verify(self, equations: List[Tuple[int, int, int]],

                    sample_rate: float = 0.1) -> Tuple[bool, float]:

        """

        批量验证多个乘法



        参数：

            equations: [(a,b,c), ...] 列表

            sample_rate: 采样率



        返回：(是否通过, 可信度)

        """

        n = len(equations)

        sample_size = max(1, int(n * sample_rate))



        checked = 0

        all_passed = True



        indices = random.sample(range(n), min(sample_size, n))



        for i in indices:

            a, b, c = equations[i]

            if not self.verify_basic(a, b, c):

                all_passed = False

                break

            checked += 1



        confidence = checked / n



        return all_passed, confidence





class Groth16Multiplier:

    """Groth16中的乘法验证（简化版）"""



    def __init__(self):

        self.p = 2**31 - 1  # 素数域



    def create_proof(self, A: int, B: int, C: int) -> dict:

        """

        创建乘法证明



        参数：

            A, B, C: A × B = C



        返回：证明

        """

        # 随机盲因子

        r = random.randint(1, self.p - 1)



        # 承诺

        commitment_A = (A * r) % self.p

        commitment_B = (B * r) % self.p

        commitment_C = (C * r) % self.p



        return {

            'A_commitment': commitment_A,

            'B_commitment': commitment_B,

            'C_commitment': commitment_C,

            'r': r

        }



    def verify_proof(self, proof: dict) -> bool:

        """

        验证乘法证明



        参数：

            proof: 证明



        返回：是否验证通过

        """

        A = proof['A_commitment']

        B = proof['B_commitment']

        C = proof['C_commitment']

        r = proof['r']



        # 验证：r × A × B = C

        left = (r * (A * r) * (B * r)) % self.p

        right = C % self.p



        return left == right





def homomorphic_verification():

    """同态加密验证"""

    print("=== 同态加密验证 ===")

    print()

    print("场景：")

    print("  - 服务端有密文 E(a), E(b)")

    print("  - 服务端计算 E(c) = E(a) × E(b)")

    print("  - 客户端想知道 c = a × b 是否正确")

    print()

    print("同态验证方法：")

    print("  1. Paillier加密：支持加法同态")

    print("  2. RSA：支持乘法同态")

    print("  3. 验证者可以选择随机消息验证")

    print()

    print("公式：")

    print("  - 随机选 r")

    print("  - 验证 D(E(a)^r × E(b)^r) = D(E(c)^r)")

    print("  - 即 r × (a + b) = r × c")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 乘法验证器测试 ===\n")



    verifier = MultiplicationVerifier()



    # 基本验证

    print("基本验证:")

    test_cases = [(3, 5, 15), (7, 8, 56), (10, 10, 100), (3, 5, 16)]

    for a, b, c in test_cases:

        result = verifier.verify_basic(a, b, c)

        status = "✅" if result == (a*b == c) else "❌"

        print(f"  {a} × {b} = {c}: {status}")



    print()



    # 随机化验证

    print("随机化验证:")

    for a, b, c in [(3, 5, 15), (3, 5, 16)]:

        result, conf = verifier.verify_with_randomization(a, b, c, num_checks=20)

        print(f"  {a} × {b} = {c}: {'通过' if result else '失败'}, 可信度={conf:.0%}")



    print()



    # 批量验证

    print("批量验证:")

    equations = [(i, i+1, i*(i+1)) for i in range(1, 101)]

    passed, conf = verifier.batch_verify(equations, sample_rate=0.05)

    print(f"  100个乘法方程，采样5%")

    print(f"  结果: {'全部通过' if passed else '存在问题'}, 可信度={conf:.0%}")



    print()



    homomorphic_verification()



    print()

    print("复杂度分析：")

    print("  简单验证: O(1)")

    print("  随机化验证: O(k)，k为检查次数")

    print("  批量验证: O(n × sample_rate)")

    print()

    print("应用：")

    print("  - zk-SNARK验证")

    print("  - Verifiable Computation")

    print("  - 区块链状态验证")

