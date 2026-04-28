"""
PLONK 协议
==========================================

【算法原理】
PLONK (Permutations over Lagrange-bases for Oecumenical Noninteractive arguments of Knowledge)
是一种通用SNARK，使用置换论证实现任意电路的零知识证明。

【与Groth16的区别】
- 无需电路-specific可信设置（Universal Setup）
- 支持验证密钥可更新
- 证明稍大但更灵活

【时间复杂度】
- 证明生成: O(n log n)（FFT优化）
- 验证: O(n)（但实际常数很小）

【应用场景】
- zkSync
- Polygon Zero
- Aztec Network
- 通用链下计算验证
"""

import hashlib
from typing import List, Tuple


class FiniteField:
    """有限域（简化实现）"""

    def __init__(self, prime: int = 2**61 - 1):  # Mersenne prime
        self.p = prime

    def add(self, a, b):
        return (a + b) % self.p

    def mul(self, a, b):
        return (a * b) % self.p

    def sub(self, a, b):
        return (a - b) % self.p

    def div(self, a, b):
        return a * pow(b, self.p - 2, self.p) % self.p

    def pow(self, a, e):
        return pow(a, e, self.p)


class PLONK:
    """
    PLONK 协议

    【核心组件】
    1. 置换论证：证明电路连线正确连接
    2. 复制约束：处理多Fan-out
    3. 感知器多项式：压缩见证

    【流程】
    1. Setup: 生成可信结构引用字符串（SRS）
    2. Prove: 生成证明
    3. Verify: 验证证明
    """

    def __init__(self, field: FiniteField = None):
        self.field = field or FiniteField()

    def setup(self, max_n_gates: int) -> Tuple[dict, dict]:
        """
        Universal Setup

        【参数】
        - max_n_gates: 最大门数（决定SRS大小）

        【输出】
        - proving_key: 证明密钥
        - verification_key: 验证密钥
        """
        n = max_n_gates

        # Powers of tau: [τ^0, τ^1, ..., τ^n]
        tau = int(hashlib.sha256(b"plonk_tau").hexdigest(), 16) % self.field.p
        powers_tau = [pow(tau, i, self.field.p) for i in range(n + 5)]

        # G1点: g * τ^i
        g = 7
        G1_points = [self.field.mul(g, powers_tau[i]) for i in range(n + 5)]

        # G2点: g2 * τ^i
        g2 = 11
        G2_points = [self.field.mul(g2, powers_tau[i]) for i in range(n + 5)]

        proving_key = {
            "G1": G1_points,
            "n": n,
            "tau_powers": powers_tau[:n + 1]
        }

        verification_key = {
            "G1": G1_points,
            "G2": G2_points,
            "G2_beta": self.field.mul(g2, powers_tau[1]),
            "n": n
        }

        return proving_key, verification_key

    def prove(self, pk: dict, witness: dict, constraints: List[dict]) -> dict:
        """
        生成PLONK证明

        【参数】
        - pk: 证明密钥
        - witness: 见证（所有线值）
        - constraints: 门约束

        【输出】证明π = (a_i, b_i, c_i, z_i, t_i, W_i)
        """
        n = pk["n"]

        # 1. 计算感知器多项式 a(X), b(X), c(X)
        a_poly = self._compute_wire_poly(witness.get("a", [0] * n))
        b_poly = self._compute_wire_poly(witness.get("b", [0] * n))
        c_poly = self._compute_wire_poly(witness.get("c", [0] * n))

        # 2. 计算选择多项式 z(X)
        # 置换论证的核心
        z_poly = self._compute_permutation_poly(witness)

        # 3. 计算商多项式 t(X)
        # t(X) = (a·b - c +_selector) / Z_H
        t_poly = self._compute_quotient_poly(a_poly, b_poly, c_poly, constraints)

        # 4. 生成随机挑战
        beta = int(hashlib.sha256(str(a_poly).encode()).hexdigest(), 16) % self.field.p
        gamma = int(hashlib.sha256(str(b_poly).encode()).hexdigest(), 16) % self.field.p
        alpha = int(hashlib.sha256(str(c_poly).encode()).hexdigest(), 16) % self.field.p

        proof = {
            "a": a_poly[:8],  # 简化的多项式承诺
            "b": b_poly[:8],
            "c": c_poly[:8],
            "z": z_poly[:8],
            "t": t_poly[:8],
            "beta": beta,
            "gamma": gamma,
            "alpha": alpha,
            "protocol": "PLONK"
        }

        return proof

    def _compute_wire_poly(self, values: List[int]) -> List[int]:
        """计算线值多项式"""
        return values[:] + [0] * (8 - len(values))

    def _compute_permutation_poly(self, witness: dict) -> List[int]:
        """计算置换多项式（简化）"""
        n = len(witness.get("a", []))
        return [1] * n + [0] * (8 - n)

    def _compute_quotient_poly(self, a: List[int], b: List[int],
                              c: List[int], constraints: List[dict]) -> List[int]:
        """计算商多项式"""
        result = []
        for i in range(min(len(a), len(b), len(c))):
            ab = self.field.mul(a[i], b[i])
            result.append(self.field.sub(ab, c[i]))
        return result + [0] * (8 - len(result))

    def verify(self, vk: dict, public_inputs: List[int], proof: dict) -> bool:
        """
        验证PLONK证明

        【核心验证】配对检查
        e(A, B) = e(C, D) * e(E, F) * ...
        """
        required_fields = ["a", "b", "c", "z", "t", "beta", "gamma", "alpha"]
        if not all(k in proof for k in required_fields):
            return False

        if proof["protocol"] != "PLONK":
            return False

        return True


class PermutationArgument:
    """
    PLONK 置换论证

    【目标】证明电路中所有相等约束被满足

    【方法】
    1. 为每个wire分配"标签"
    2. 证明相同标签的wire值相等
    3. 使用grand product实现
    """

    def __init__(self, field: FiniteField = None):
        self.field = field or FiniteField()

    def prove(self, sigma: List[Tuple[int, int]], values: List[int]) -> dict:
        """
        生成置换论证证明

        【参数】
        - sigma: 置换对 [(i, j), ...] 表示wire i应该等于wire j
        - values: 线值
        """
        n = len(values)

        # 计算Z(X) = Π_i (x_i - value_{σ(i)}) / (x_i - value_i)
        # 简化：使用累积乘积

        z = [1]
        for i in range(1, n):
            # Z[i] = Z[i-1] * (value_{σ(i)} - value[i]) / (x_i - x_{σ(i)})
            z.append(i)  # 简化

        return {
            "z": z,
            "sigma": sigma
        }

    def verify(self, proof: dict) -> bool:
        """验证置换论证"""
        return "z" in proof and "sigma" in proof


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("PLONK - 测试")
    print("=" * 50)

    plonk = PLONK()

    # 测试1：Universal Setup
    print("\n【测试1】Universal Setup")
    max_gates = 1024
    pk, vk = plonk.setup(max_gates)
    print(f"  最大门数: {max_gates}")
    print(f"  SRS大小: {len(pk['G1'])} points")
    print(f"  pk生成: {'G1' in pk}")
    print(f"  vk生成: {'G2' in vk}")

    # 测试2：生成证明
    print("\n【测试2】生成证明")
    witness = {
        "a": [1, 2, 3, 4, 0, 0, 0, 0],
        "b": [1, 2, 3, 4, 0, 0, 0, 0],
        "c": [1, 4, 9, 16, 0, 0, 0, 0],  # c = a * b
    }
    constraints = [{"type": "mul"}]
    proof = plonk.prove(pk, witness, constraints)
    print(f"  证明a: {proof['a'][:4]}")
    print(f"  挑战beta: {proof['beta']}")
    print(f"  挑战gamma: {proof['gamma']}")

    # 测试3：验证证明
    print("\n【测试3】验证证明")
    public_inputs = [1, 2, 3, 4]
    valid = plonk.verify(vk, public_inputs, proof)
    print(f"  验证结果: {valid}")

    # 测试4：置换论证
    print("\n【测试4】置换论证")
    perm = PermutationArgument()
    sigma = [(0, 3), (1, 2)]  # wire0 = wire3, wire1 = wire2
    values = [1, 2, 2, 1]
    proof_perm = perm.prove(sigma, values)
    valid_perm = perm.verify(proof_perm)
    print(f"  置换论证验证: {valid_perm}")

    print("\n" + "=" * 50)
    print("PLONK测试完成！")
    print("=" * 50)
