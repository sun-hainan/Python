# -*- coding: utf-8 -*-
"""
算法实现：可验证计算 / verifiable_computation

本文件实现 verifiable_computation 相关的算法功能。
"""

import random
import hashlib
from typing import Tuple, Any


class VerifiableComputation:
    """可验证计算服务"""

    def __init__(self, security_bits: int = 256):
        """
        参数：
            security_bits: 安全参数
        """
        self.security = security_bits

    def compute_offload(self, function_id: int, input_data: Any) -> dict:
        """
        外包计算

        参数：
            function_id: 函数标识
            input_data: 输入数据

        返回：结果和证明
        """
        # 简化：模拟计算
        result = f"computed_{input_data}_{function_id}"

        # 生成简化证明
        proof = hashlib.sha256(f"{result}_proof".encode()).hexdigest()

        return {
            'result': result,
            'proof': proof,
            'function_id': function_id
        }

    def verify_proof(self, computation_result: dict) -> bool:
        """
        验证证明

        返回：是否有效
        """
        proof = computation_result['proof']

        # 简化验证
        return len(proof) == self.security // 4

    def generate_challenge(self, result: str) -> str:
        """
        生成挑战

        返回：挑战字符串
        """
        return hashlib.sha256(f"challenge_{result}".encode()).hexdigest()

    def check_response(self, challenge: str, response: str) -> bool:
        """
        检查响应

        返回：是否正确
        """
        # 简化：检查格式
        return len(response) > 0


def verifiable_computation_applications():
    """可验证计算应用"""
    print("=== 可验证计算应用 ===")
    print()
    print("1. 云服务器")
    print("   - 外包计算到云")
    print("   - 验证结果正确")
    print()
    print("2. 区块链")
    print("   - 轻客户端验证全节点")
    print("   - 无需重新计算")
    print()
    print("3. 委托计算")
    print("   - 手机委托到服务器")
    print("   - 结果可验证")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 可验证计算测试 ===\n")

    vc = VerifiableComputation()

    # 外包计算
    function_id = 42
    input_data = "some input data"

    print(f"函数ID: {function_id}")
    print(f"输入: {input_data}")
    print()

    result = vc.compute_offload(function_id, input_data)

    print(f"计算结果: {result['result']}")
    print(f"证明: {result['proof'][:32]}...")
    print()

    # 验证
    is_valid = vc.verify_proof(result)
    print(f"验证: {'✅ 有效' if is_valid else '❌ 无效'}")
    print()

    # 挑战-响应
    challenge = vc.generate_challenge(result['result'])
    print(f"挑战: {challenge[:32]}...")

    response = "response_from_worker"
    is_correct = vc.check_response(challenge, response)
    print(f"响应正确: {'是' if is_correct else '否'}")

    print()
    verifiable_computation_applications()

    print()
    print("说明：")
    print("  - 可验证计算保护外包计算完整性")
    print("  - SNARK/STARK是主要技术")
    print("  - 区块链应用广泛")
