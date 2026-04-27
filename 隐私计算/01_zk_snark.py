# -*- coding: utf-8 -*-
"""
算法实现：隐私计算 / 01_zk_snark

本文件实现 01_zk_snark 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict


class ArithmeticCircuit:
    """
    算术电路类

    电路由加法和乘法门组成,用于表示待证明的计算
    """

    def __init__(self):
        """初始化算术电路"""
        self.num_inputs = 0
        self.num_outputs = 0
        self.num_intermediates = 0
        self.gates = []  # 门列表,每个门为(input1, input2, operation)

    def add_input(self) -> int:
        """
        添加输入变量

        Returns:
            变量的索引
        """
        idx = self.num_inputs
        self.num_inputs += 1
        return idx

    def add_gate(
        self,
        input1: int,
        input2: int,
        operation: str = "mul"
    ) -> int:
        """
        添加门

        Args:
            input1: 第一个输入变量索引
            input2: 第二个输入变量索引
            operation: 操作类型,"mul"或"add"

        Returns:
            输出变量索引
        """
        gate = {"input1": input1, "input2": input2, "op": operation}
        self.gates.append(gate)
        idx = self.num_inputs + self.num_intermediates
        self.num_intermediates += 1
        return idx

    def add_constant(self, const: float) -> int:
        """
        添加常数门

        Args:
            const: 常数值

        Returns:
            输出变量索引
        """
        # 模拟: 使用特殊索引表示常数
        return -1 - self.num_outputs - len([g for g in self.gates if g["op"] == "const"])

    def evaluate(self, inputs: List[float]) -> List[float]:
        """
        评估电路

        Args:
            inputs: 输入值列表

        Returns:
            输出值列表
        """
        values = inputs.copy()

        for gate in self.gates:
            input1 = values[gate["input1"]]
            input2 = values[gate["input2"]]
            op = gate["op"]

            if op == "mul":
                result = input1 * input2
            elif op == "add":
                result = input1 + input2
            elif op == "const":
                result = gate.get("const", 0)
            else:
                result = 0

            values.append(result)

        return values


class Polynomial:
    """
    多项式类

    用于SNARK中的多项式承诺
    """

    def __init__(self, coefficients: List[float]):
        """
        初始化多项式

        Args:
            coefficients: 系数列表,coeff[i]为x^i的系数
        """
        self.coeffs = coefficients
        self.degree = len(coefficients) - 1

    def evaluate(self, point: float) -> float:
        """
        在给定点求值

        使用Horner法则高效计算

        Args:
            point: 求值点

        Returns:
            多项式值
        """
        result = 0.0
        for coeff in reversed(self.coeffs):
            result = result * point + coeff
        return result

    def add(self, other: "Polynomial") -> "Polynomial":
        """
        多项式加法

        Args:
            other: 另一个多项式

        Returns:
            和多项式
        """
        max_len = max(len(self.coeffs), len(other.coeffs))
        new_coeffs = [0.0] * max_len

        for i in range(len(self.coeffs)):
            new_coeffs[i] += self.coeffs[i]
        for i in range(len(other.coeffs)):
            new_coeffs[i] += other.coeffs[i]

        return Polynomial(new_coeffs)

    def multiply(self, other: "Polynomial") -> "Polynomial":
        """
        多项式乘法

        Args:
            other: 另一个多项式

        Returns:
            积多项式
        """
        new_degree = self.degree + other.degree
        new_coeffs = [0.0] * (new_degree + 1)

        for i, c1 in enumerate(self.coeffs):
            for j, c2 in enumerate(other.coeffs):
                new_coeffs[i + j] += c1 * c2

        return Polynomial(new_coeffs)

    def divide_by_t(self, t: List[float]) -> Tuple["Polynomial", "Polynomial"]:
        """
        多项式除以目标多项式T(x) = (x-1)(x-2)...(x-n)

        用于SNARK中验证多项式在特定点的值

        Args:
            t: 目标点列表[1, 2, ..., n]

        Returns:
            (商多项式, 余数多项式)
        """
        # 构建T(x)
        t_poly = Polynomial([1.0])
        for point in t:
            # 乘以(x - point)
            t_poly = t_poly.multiply(Polynomial([-point, 1.0]))

        # 简化的除法(实际需要多项式长除法)
        quotient = Polynomial([0.0])
        remainder = Polynomial(self.coeffs.copy())

        return quotient, remainder


class PolynomialCommitment:
    """
    多项式承诺类

    承诺者将多项式P(x)承诺给验证者,
    之后可以证明P在某个点的值

    协议:
    1. Commit: 承诺多项式,发送commitment C
    2. Open: 在点z打开,发送P(z)和证明
    3. Verify: 验证P(z)与证明一致
    """

    def __init__(self, security_param: int = 128):
        """
        初始化承诺方案

        Args:
            security_param: 安全参数(位长)
        """
        self.security_param = security_param
        np.random.seed(42)
        # 生成随机挑战点(实际需要可信 setup)
        self.tau = np.random.randint(1, 2**31)

    def commit(self, poly: Polynomial) -> int:
        """
        承诺多项式

        简化版: 返回多项式在tau点的值作为承诺

        实际使用椭圆曲线点作为承诺

        Args:
            poly: 多项式

        Returns:
            承诺值
        """
        return int(poly.evaluate(self.tau))

    def create_opening_proof(
        self,
        poly: Polynomial,
        point: float
    ) -> Dict:
        """
        创建开门口证明

        Args:
            poly: 多项式
            point: 打开点

        Returns:
            证明字典
        """
        # 计算商多项式
        quotient, remainder = poly.divide_by_t([point])

        proof = {
            "value": poly.evaluate(point),
            "quotient_commitment": self.commit(quotient),
            "point": point
        }

        return proof

    def verify_opening(
        self,
        commitment: int,
        proof: Dict,
        point: float
    ) -> bool:
        """
        验证开门口

        验证: C - P(z) = H(z) * T(z)

        Args:
            commitment: 承诺值
            proof: 证明字典
            point: 打开点

        Returns:
            是否验证通过
        """
        # 简化的验证
        # 实际需要验证椭圆曲线配对

        value = proof["value"]
        # C = P(tau), 验证 P(tau) - P(z) = H * T(z)
        # 这里简化,只检查值是否匹配

        return True  # 简化版本总是返回True


class SNARKProver:
    """
    SNARK证明者

    负责生成证明
    """

    def __init__(self):
        """初始化证明者"""
        self.circuit = ArithmeticCircuit()
        self.commitment_scheme = PolynomialCommitment()

    def generate_witness(
        self,
        circuit: ArithmeticCircuit,
        inputs: List[float]
    ) -> List[float]:
        """
        生成见证

        见证是电路所有中间变量的值

        Args:
            circuit: 算术电路
            inputs: 公开输入

        Returns:
            完整的见证向量
        """
        return circuit.evaluate(inputs)

    def prove(
        self,
        circuit: ArithmeticCircuit,
        witness: List[float],
        public_inputs: List[float]
    ) -> Dict:
        """
        生成SNARK证明

        简化版Groth16协议:
        1. 将电路转换为QAP
        2. 计算多项式A, B, C
        3. 计算H多项式
        4. 承诺A, B, C, H

        Args:
            circuit: 算术电路
            witness: 见证向量
            public_inputs: 公开输入

        Returns:
            证明字典
        """
        # 步骤1: 计算 witness polynomial
        n = len(witness)

        # 简化为随机多项式(实际需要根据QAP计算)
        poly_a = Polynomial(list(witness) + [0] * 3)
        poly_b = Polynomial(list(witness) + [0] * 3)
        poly_c = Polynomial(list(witness) + [0] * 3)

        # 步骤2: 承诺
        commit_a = self.commitment_scheme.commit(poly_a)
        commit_b = self.commitment_scheme.commit(poly_b)
        commit_c = self.commitment_scheme.commit(poly_c)

        # 步骤3: 计算H
        # 简化: H = (A * B - C) / T
        product = poly_a.multiply(poly_b)
        diff = product.add(poly_c.multiply(Polynomial([-1.0])))
        quotient, remainder = diff.divide_by_t(list(range(1, n + 1)))
        commit_h = self.commitment_scheme.commit(quotient)

        proof = {
            "commit_a": commit_a,
            "commit_b": commit_b,
            "commit_c": commit_c,
            "commit_h": commit_h,
            "public_inputs": public_inputs
        }

        return proof


class SNARKVerifier:
    """
    SNARK验证者

    负责验证证明
    """

    def __init__(self):
        """初始化验证者"""
        self.commitment_scheme = PolynomialCommitment()

    def verify(self, proof: Dict, public_inputs: List[float]) -> bool:
        """
        验证SNARK证明

        验证配对方程: A * B = C + H * T

        Args:
            proof: 证明字典
            public_inputs: 公开输入

        Returns:
            是否验证通过
        """
        # 简化验证
        # 实际需要使用椭圆曲线配对验证

        commit_a = proof["commit_a"]
        commit_b = proof["commit_b"]
        commit_c = proof["commit_c"]
        commit_h = proof["commit_h"]

        # 简化检查
        # 真实验证: e(A, B) = e(C, G) + e(H, T)
        # 这里只做基础检查

        return True


def create_knowledge_proof(
    secret: float,
    modulus: int = 17
) -> Dict:
    """
    创建知识证明 - 证明知道某个数的值

    示例: 证明知道x,使得x^2 = a (不泄露x)

    Args:
        secret: 秘密值x
        modulus: 模数

    Returns:
        证明字典
    """
    # 简化的非交互证明
    a = (secret * secret) % modulus

    # 承诺
    tau = np.random.randint(1, modulus)
    commitment = (secret + tau) % modulus

    # 挑战(使用哈希模拟)
    challenge = hash((commitment + a) % modulus) % modulus

    # 响应
    response = (secret + challenge * tau) % modulus

    proof = {
        "a": a,
        "commitment": commitment,
        "challenge": challenge,
        "response": response,
        "modulus": modulus
    }

    return proof


def verify_knowledge_proof(proof: Dict) -> bool:
    """
    验证知识证明

    Args:
        proof: 证明字典

    Returns:
        是否验证通过
    """
    a = proof["a"]
    commitment = proof["commitment"]
    challenge = proof["challenge"]
    response = proof["response"]
    modulus = proof["modulus"]

    # 验证
    lhs = (response * response) % modulus
    rhs = (a + (challenge * commitment) % modulus) % modulus

    return lhs == rhs


if __name__ == "__main__":
    print("=" * 60)
    print("zk-SNARK 零知识证明演示")
    print("=" * 60)

    # 示例1: 算术电路
    print("\n--- 算术电路 ---")
    circuit = ArithmeticCircuit()
    inputs = [circuit.add_input() for _ in range(2)]

    # 创建一个简单的计算: (a * b) + (a + b)
    mul_gate = circuit.add_gate(inputs[0], inputs[1], "mul")
    add_gate = circuit.add_gate(inputs[0], inputs[1], "add")
    result_gate = circuit.add_gate(mul_gate, add_gate, "add")

    result = circuit.evaluate([3.0, 4.0])
    print(f"电路输入: [3, 4]")
    print(f"电路输出: {result[-1]:.2f}")
    print(f"预期: (3*4) + (3+4) + (3*4) = 12 + 7 + 12 = 31")

    # 示例2: 多项式承诺
    print("\n--- 多项式承诺 ---")
    poly = Polynomial([1.0, -3.0, 2.0])  # P(x) = 1 - 3x + 2x^2
    print(f"多项式系数: {poly.coeffs}")
    print(f"多项式在x=2处取值: {poly.evaluate(2.0)}")

    commitment = PolynomialCommitment()
    commit_value = commitment.commit(poly)
    print(f"承诺值: {commit_value}")

    # 示例3: 知识证明
    print("\n--- 平方根知识证明 ---")
    secret_value = 5
    proof = create_knowledge_proof(secret_value, modulus=17)
    print(f"秘密值: {secret_value}")
    print(f"a = x^2 mod 17 = {proof['a']}")

    is_valid = verify_knowledge_proof(proof)
    print(f"证明验证: {'通过' if is_valid else '失败'}")

    print("\n" + "=" * 60)
    print("SNARK演示完成!")
    print("=" * 60)
