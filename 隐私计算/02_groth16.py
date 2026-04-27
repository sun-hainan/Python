# -*- coding: utf-8 -*-
"""
算法实现：隐私计算 / 02_groth16

本文件实现 02_groth16 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict


class R1CS:
    """
    R1CS (Rank-1 Constraint System) 约束系统

    R1CS由一组约束组成,每个约束形式为:
    <A, X> * <B, X> = <C, X>

    其中A, B, C是系数向量, X是变量向量
    """

    def __init__(self):
        """初始化R1CS"""
        self.constraints = []
        self.num_variables = 0

    def add_variable(self) -> int:
        """
        添加变量

        Returns:
            变量索引
        """
        idx = self.num_variables
        self.num_variables += 1
        return idx

    def add_constraint(
        self,
        A: List[float],
        B: List[float],
        C: List[float]
    ):
        """
        添加R1CS约束

        Args:
            A: 第一个线性组合系数
            B: 第二个线性组合系数
            C: 输出线性组合系数
        """
        self.constraints.append({
            "A": A,
            "B": B,
            "C": C
        })

    def add_uniform_constraint(
        self,
        var_idx: int,
        value: float = 1.0
    ):
        """
        添加一致性约束,确保变量等于常数

        Args:
            var_idx: 变量索引
            value: 常数值
        """
        A = [0.0] * self.num_variables
        B = [0.0] * self.num_variables
        C = [0.0] * self.num_variables

        A[var_idx] = 1.0
        B[0] = value
        C[0] = value

        self.add_constraint(A, B, C)


class QAP:
    """
    QAP (Quadratic Arithmetic Program) 二次算术程序

    将R1CS转换为多项式形式:
    - A_i(x), B_i(x), C_i(x) 是多项式
    - 约束变为: sum(A_i(x) * z_i) * sum(B_i(x) * z_i) = sum(C_i(x) * z_i)

    满足条件: P(x) = H(x) * T(x)
    其中T(x)是目标多项式的根
    """

    def __init__(self, r1cs: R1CS):
        """
        从R1CS初始化QAP

        Args:
            r1cs: R1CS约束系统
        """
        self.r1cs = r1cs
        self.num_constraints = len(r1cs.constraints)
        self.degree = self.num_constraints

        # 插值得到多项式
        self.A_polys = self._interpolate_constraints("A")
        self.B_polys = self._interpolate_constraints("B")
        self.C_polys = self._interpolate_constraints("C")

        # 目标多项式 T(x) = (x-1)(x-2)...(x-n)
        self.target_poly = self._compute_target_poly()

    def _interpolate_constraints(self, component: str) -> List[List[float]]:
        """
        对约束的某个分量进行插值

        Args:
            component: "A", "B" 或 "C"

        Returns:
            每个变量的多项式系数
        """
        n_vars = self.r1cs.num_variables
        n_constraints = self.num_constraints

        # 点集: (1, A_i(1)), (2, A_i(2)), ...
        x_points = list(range(1, n_constraints + 1))

        result = []
        for var_idx in range(n_vars):
            y_points = []
            for constraint in self.r1cs.constraints:
                coeffs = constraint[component]
                if var_idx < len(coeffs):
                    y_points.append(coeffs[var_idx])
                else:
                    y_points.append(0.0)

            # 拉格朗日插值(简化为取均值)
            poly_coeffs = [np.mean(y_points)] * (self.degree + 1)
            result.append(poly_coeffs)

        return result

    def _compute_target_poly(self) -> List[float]:
        """
        计算目标多项式 T(x) = (x-1)(x-2)...(x-n)

        Returns:
            T(x)的系数
        """
        # T(x) = x^n - sum(x^i) + ... (简化)
        coeffs = [1.0] + [0.0] * self.degree
        for i in range(1, self.degree + 1):
            # 乘以(x - i)
            new_coeffs = [0.0] * (self.degree + 2)
            for j, c in enumerate(coeffs):
                new_coeffs[j] -= c * i
                new_coeffs[j + 1] += c
            coeffs = new_coeffs

        return coeffs


class Groth16Setup:
    """
    Groth16 Setup阶段

    生成证明密钥和验证密钥
    """

    def __init__(self, qap: QAP):
        """
        初始化Setup

        Args:
            qap: QAP程序
        """
        self.qap = qap
        np.random.seed(42)

        # 模拟椭圆曲线参数(实际使用BLS12-381)
        self.g1_generator = "BLS12_381_G1_generator"
        self.g2_generator = "BLS12_381_G2_generator"

        # 模拟有毒废物(toxic waste)采样
        self.alpha = np.random.randint(1, 2**31)
        self.beta = np.random.randint(1, 2**31)
        self.gamma = np.random.randint(1, 2**31)
        self.delta = np.random.randint(1, 2**31)
        self.tau = np.random.randint(1, 2**31)

    def generate_proving_key(self) -> Dict:
        """
        生成证明密钥

        Returns:
            证明密钥字典
        """
        proving_key = {
            "A": [],  # A多项式在tau点的值
            "B": [],  # B多项式在tau点的值
            "C": [],  # C多项式在tau点的值
            "H": [],  # H多项式在tau点的值
            "beta": self.beta,
            "alpha": self.alpha,
            "delta": self.delta
        }

        # 模拟计算
        for i in range(self.qap.r1cs.num_variables):
            proving_key["A"].append(self.alpha + i * self.tau)
            proving_key["B"].append(self.beta + i * self.tau)
            proving_key["C"].append(self.gamma + i * self.tau)

        return proving_key

    def generate_verification_key(self) -> Dict:
        """
        生成验证密钥

        Returns:
            验证密钥字典
        """
        verification_key = {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "delta": self.delta,
            "IC": []  # 公开输入的承诺
        }

        # 计算公开输入的承诺
        for i in range(self.qap.num_constraints + 1):
            verification_key["IC"].append(self.beta + i * self.gamma)

        return verification_key


class Groth16Prover:
    """
    Groth16证明者
    """

    def __init__(self, proving_key: Dict):
        """
        初始化证明者

        Args:
            proving_key: 证明密钥
        """
        self.proving_key = proving_key

    def prove(self, witness: List[float], public_inputs: List[float]) -> Tuple[int, int, int]:
        """
        生成证明

        Args:
            witness: 见证向量 [1, 公开输入..., 秘密输入...]
            public_inputs: 公开输入

        Returns:
            (A, B, C) 证明的三个群元素
        """
        n = len(witness)

        # 计算A
        A = self.proving_key["alpha"]
        for i in range(n):
            A += self.proving_key["A"][i] * witness[i]
        A = A % (2**31)

        # 计算B
        B = self.proving_key["beta"]
        for i in range(n):
            B += self.proving_key["B"][i] * witness[i]
        B = B % (2**31)

        # 计算C
        C = 0
        for i in range(n):
            C += self.proving_key["C"][i] * witness[i]
        C = C % (2**31)

        return A, B, C


class Groth16Verifier:
    """
    Groth16验证者
    """

    def __init__(self, verification_key: Dict):
        """
        初始化验证者

        Args:
            verification_key: 验证密钥
        """
        self.verification_key = verification_key

    def verify(
        self,
        proof: Tuple[int, int, int],
        public_inputs: List[float]
    ) -> bool:
        """
        验证证明

        验证方程: e(A, B) = e(alpha, beta) * e(IC, gamma) * e(C, delta)

        Args:
            proof: 证明元组(A, B, C)
            public_inputs: 公开输入

        Returns:
            是否验证通过
        """
        A, B, C = proof
        vk = self.verification_key

        # 计算IC * public_inputs
        ic_sum = 0
        for i, inp in enumerate(public_inputs):
            if i < len(vk["IC"]):
                ic_sum += vk["IC"][i] * inp

        # 简化的验证(实际需要配对验证)
        # 验证: A * B = alpha * beta + IC * gamma + C * delta
        lhs = (A * B) % (2**31)
        rhs = (vk["alpha"] * vk["beta"] + ic_sum * vk["gamma"] +
               C * vk["delta"]) % (2**31)

        return lhs == rhs


def create_groth16_proof_example():
    """
    创建Groth16证明示例

    示例: 证明知道x,使得 x^3 + x + 5 = 35

    电路:
    y1 = x * x
    y2 = y1 * x  # y2 = x^3
    y3 = y2 + x  # y3 = x^3 + x
    y4 = y3 + 5  # y4 = x^3 + x + 5
    """

    # 创建R1CS
    r1cs = R1CS()

    # 添加变量: x, y1, y2, y3, y4
    x = r1cs.add_variable()
    y1 = r1cs.add_variable()
    y2 = r1cs.add_variable()
    y3 = r1cs.add_variable()
    y4 = r1cs.add_variable()
    one = 0  # 常量1

    # 约束1: y1 = x * x
    r1cs.add_constraint(
        A=[1, 1, 0, 0, 0, 0],  # x + x
        B=[1, 1, 0, 0, 0, 0],  # x + x
        C=[0, 0, 1, 0, 0, 0]   # y1
    )

    # 约束2: y2 = y1 * x
    r1cs.add_constraint(
        A=[0, 0, 1, 1, 0, 0],  # y1 + x
        B=[0, 1, 0, 0, 0, 0],  # x
        C=[0, 0, 0, 1, 0, 0]   # y2
    )

    # 约束3: y3 = y2 + x
    r1cs.add_constraint(
        A=[0, 1, 0, 1, 1, 0],  # x + y1 + y2
        B=[1, 0, 0, 0, 0, 0],  # 1
        C=[0, 0, 0, 0, 1, 0]   # y3
    )

    # 约束4: y4 = y3 + 5
    r1cs.add_constraint(
        A=[5, 0, 0, 0, 1, 1],  # 5 + x + y1 + y2 + y3
        B=[1, 0, 0, 0, 0, 0],  # 1
        C=[0, 0, 0, 0, 0, 1]   # y4
    )

    # 创建QAP
    qap = QAP(r1cs)

    # Setup
    setup = Groth16Setup(qap)
    proving_key = setup.generate_proving_key()
    verification_key = setup.generate_verification_key()

    # 见证: x=3, y1=9, y2=27, y3=30, y4=35
    witness = [1, 3, 9, 27, 30, 35]
    public_inputs = [35]

    # 证明
    prover = Groth16Prover(proving_key)
    proof = prover.prove(witness, public_inputs)

    # 验证
    verifier = Groth16Verifier(verification_key)
    is_valid = verifier.verify(proof, public_inputs)

    return {
        "proof": proof,
        "is_valid": is_valid,
        "public_inputs": public_inputs
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Groth16 零知识证明协议演示")
    print("=" * 60)

    # 创建示例证明
    print("\n--- 示例: 证明 x^3 + x + 5 = 35 ---")
    print("证明知道x=3使得等式成立(不泄露x)")

    result = create_groth16_proof_example()

    print(f"\n公开输入: {result['public_inputs']}")
    print(f"证明 (A, B, C): {result['proof']}")
    print(f"验证结果: {'通过 ✓' if result['is_valid'] else '失败 ✗'}")

    print("\n" + "=" * 60)
    print("Groth16演示完成!")
    print("=" * 60)
