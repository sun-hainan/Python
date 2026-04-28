"""
直线式提取器
==========================================

【原理】
直线式提取器可以在收到证据后"提取"出证人。
用于证明knowledge extractor的straight-line属性。

【时间复杂度】O(n)
【应用场景】
- SNARK证明提取
- 知识证明
- 非交互式证明
"""

import random


class StraightLineExtractor:
    """
    直线式提取器

    【与退回式提取器的区别】
    - 退回式：在挑战处退回重试，可能永远无法提取
    - 直线式：按固定顺序执行，不需要退回

    【适用协议】
    - Groth16
    - Pinocchio
    - PCP类协议
    """

    def __init__(self, protocol):
        self.protocol = protocol

    def extract(self, challenges: list) -> dict:
        """
        直线式提取

        【方法】
        给定所有挑战，按顺序计算所有响应
        """
        witness = {}

        for i, challenge in enumerate(challenges):
            response = self._compute_response(i, challenge)
            witness[f"step_{i}"] = response

        return witness

    def _compute_response(self, step: int, challenge: int) -> int:
        """计算每个步骤的响应"""
        return step * challenge % self.protocol.get_prime()


class KnowledgeExtractor:
    """
    知识提取器

    【目标】
    从证明中提取出"知识"（证人）

    【协议】
    1. 运行证明协议
    2. 如果诚实验证者接受，提取器也成功
    """

    def __init__(self):
        self.prime = 2**255 - 19

    def extract_from_proof(self, proof: dict) -> int:
        """从证明中提取见证"""
        if "witness" in proof:
            return proof["witness"]
        return proof.get("commitment", 0)


class SpecialSoundnessVerifier:
    """
    特殊Soundness验证器

    【性质】
    从同一个声明的两个接受证明中，
    可以提取出有效证人

    【例子】
    Σ协议：(a, challenge, response)
    两个证明有相同的a和commitment，但不同challenge
    """

    def __init__(self):
        self.prime = 2**255 - 19

    def extract(self, proof1: dict, proof2: dict) -> int:
        """
        从两个证明提取证人

        【公式】
        witness = (response1 - response2) / (challenge1 - challenge2)
        """
        c1 = proof1.get("challenge", 0)
        c2 = proof2.get("challenge", 0)
        r1 = proof1.get("response", 0)
        r2 = proof2.get("response", 0)

        if c1 == c2:
            raise ValueError("挑战必须不同")

        # 计算差值
        diff_c = c1 - c2
        inv_diff_c = pow(diff_c, -1, self.prime)
        witness = ((r1 - r2) * inv_diff_c) % self.prime

        return witness


if __name__ == "__main__":
    print("=" * 50)
    print("直线式提取器 - 测试")
    print("=" * 50)

    print("\n【测试】特殊Soundness提取")
    verifier = SpecialSoundnessVerifier()

    # 模拟两个证明
    proof1 = {"challenge": 123, "response": 456}
    proof2 = {"challenge": 789, "response": 1234}

    witness = verifier.extract(proof1, proof2)
    print(f"  证明1挑战: {proof1['challenge']}")
    print(f"  证明2挑战: {proof2['challenge']}")
    print(f"  提取的证人: {witness}")

    print("\n" + "=" * 50)
