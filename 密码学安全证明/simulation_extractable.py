"""
可模拟提取证明 (SE-ZK)
==========================================

【原理】
模拟器可以在不 knowledge witness 的情况下模拟证明。
Extractor可以提取出真正的证人。

【时间复杂度】O(n)
【应用场景】
- zk-SNARK
- 知识证明
- 通用零知识
"""

import random
import hashlib


class SimulatbleProof:
    """
    可模拟证明

    【两个算法】
    - Simulate(statement): 不需要witness，生成模拟证明
    - Extract(real_proof): 从真实证明中提取witness
    """

    def __init__(self, prime: int = 2**255 - 19):
        self.prime = prime

    def simulate(self, statement: str) -> dict:
        """
        模拟证明

        【与真实证明不可区分】
        """
        # 生成随机响应
        a = random.randint(1, self.prime - 1)
        challenge = int(hashlib.sha256(f"{statement}:{a}".encode()).hexdigest(), 16) % self.prime
        response = (a + challenge * 123) % self.prime  # 简化的模拟

        return {
            "statement": statement,
            "a": a,
            "challenge": challenge,
            "response": response,
            "simulated": True
        }

    def extract(self, proof: dict) -> int:
        """从证明中提取证人"""
        if proof.get("simulated"):
            raise ValueError("无法从模拟证明中提取")

        # 简化的提取逻辑
        return proof.get("witness", 0)


class NIZK:
    """
    非交互式零知识证明

    【使用Fiat-Shamir变换】
    - 挑战 = H(a || statement)
    """

    def __init__(self):
        self.prime = 2**255 - 19

    def prove(self, statement: str, witness: int) -> dict:
        """生成非交互式证明"""
        # 随机选择
        random_value = random.randint(1, self.prime - 1)

        # 计算commitment
        commitment = pow(2, random_value, self.prime)

        # Fiat-Shamir挑战
        h_input = f"{commitment}:{statement}".encode()
        challenge = int(hashlib.sha256(h_input).hexdigest(), 16) % self.prime

        # 计算响应
        response = (random_value + challenge * witness) % (self.prime - 1)

        return {
            "statement": statement,
            "commitment": commitment,
            "challenge": challenge,
            "response": response
        }

    def verify(self, proof: dict) -> bool:
        """验证证明"""
        statement = proof["statement"]
        commitment = proof["commitment"]
        challenge = proof["challenge"]
        response = proof["response"]

        # 重新计算挑战
        h_input = f"{commitment}:{statement}".encode()
        expected_challenge = int(hashlib.sha256(h_input).hexdigest(), 16) % self.prime

        # 验证挑战匹配
        if challenge != expected_challenge:
            return False

        # 验证等式
        left = pow(2, response, self.prime)
        right = (commitment * pow(2, challenge, self.prime)) % self.prime

        return left == right


if __name__ == "__main__":
    print("=" * 50)
    print("SE-ZK证明 - 测试")
    print("=" * 50)

    print("\n【测试1】可模拟证明")
    sp = SimulatbleProof()

    # 模拟
    sim_proof = sp.simulate("x = g^w")
    print(f"  模拟证明: {sim_proof['simulated']}")

    # 无法从模拟证明提取
    try:
        sp.extract(sim_proof)
        print("  错误：应该无法提取")
    except ValueError as e:
        print(f"  正确抛出异常: {type(e).__name__}")

    print("\n【测试2】NIZK")
    nizk = NIZK()
    witness = 42
    statement = "I know the discrete log"

    proof = nizk.prove(statement, witness)
    valid = nizk.verify(proof)
    print(f"  陈述: {statement}")
    print(f"  见证: {witness}")
    print(f"  验证结果: {valid}")

    print("\n" + "=" * 50)
