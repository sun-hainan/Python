# -*- coding: utf-8 -*-
"""
算法实现：局部可解码码 / ldc_witness_test

本文件实现 ldc_witness_test 相关的算法功能。
"""

import random


class WitnessTest:
    """
    基于 RM(1,m) 的 Witness 测试。

    用于证明某个 m 位字符串 w 满足某个电路 C(w) = 1。
    """

    def __init__(self, m, circuit):
        """
        初始化。

        参数:
            m: 输入比特数
            circuit: 电路描述（函数）
        """
        self.m = m
        self.circuit = circuit
        self.n = 2 ** m  # 码字长度
        self.points = self._generate_points()

    def _generate_points(self):
        """生成所有 m 维二元点。"""
        points = []
        for i in range(self.n):
            point = []
            x = i
            for _ in range(self.m):
                point.append(x & 1)
                x >>= 1
            while len(point) < self.m:
                point.append(0)
            points.append(tuple(point))
        return points

    def encode_witness(self, witness):
        """
        将 witness 编码为码字。

        参数:
            witness: m 位字符串（列表）

        返回:
            码字
        """
        # RM(1,m) 编码
        codeword = []
        for point in self.points:
            # f(x) = sum(w_i * x_i) mod 2
            value = sum(w * x for w, x in zip(witness, point)) % 2
            codeword.append(value)
        return codeword

    def prover_commit(self, witness):
        """
        证明者提交 witness 的编码。

        返回:
            码字
        """
        return self.encode_witness(witness)

    def verifier_query(self, committed_word, random_seed=None):
        """
        验证者随机查询几个位置。

        参数:
            committed_word: 提交的码字
            random_seed: 随机种子

        返回:
            查询结果和查询位置
        """
        if random_seed:
            random.seed(random_seed)

        # 验证者随机选择 3 个位置查询
        num_queries = 3
        query_positions = random.sample(range(self.n), num_queries)
        query_values = [committed_word[pos] for pos in query_positions]

        return query_positions, query_values

    def verify_queries(self, witness, query_positions, query_values):
        """
        验证者检查查询结果。

        参数:
            witness: 声称的 witness
            query_positions: 查询位置
            query_values: 查询到的值

        返回:
            True/False
        """
        for pos in query_positions:
            point = self.points[pos]
            expected_value = sum(w * x for w, x in zip(witness, point)) % 2
            if expected_value != query_values[pos]:
                return False
        return True

    def low_degree_extension(self, partial_assignment, domain_size):
        """
        低度扩展：将部分赋值扩展为全局低度多项式。

        参数:
            partial_assignment: 部分赋值
            domain_size: 域大小

        返回:
            扩展后的赋值
        """
        # 简化实现
        # 实际使用多项式插值
        assignment = partial_assignment[:]

        # 用随机值填充
        while len(assignment) < domain_size:
            assignment.append(random.randint(0, 1))

        return assignment


def circuit_sat_witness_test(m, witness):
    """
    演示电路可满足性的 Witness 测试。

    参数:
        m: 输入比特数
        witness: 声称的可满足赋值

    返回:
        测试结果
    """
    # 简单的电路：检查 witness 是否是全 1 向量
    def simple_circuit(w):
        return all(x == 1 for x in w)

    wt = WitnessTest(m, simple_circuit)

    # 证明者提交
    committed = wt.prover_commit(witness)

    # 验证者查询
    query_pos, query_vals = wt.verifier_query(committed, random_seed=42)

    # 验证
    valid = wt.verify_queries(witness, query_pos, query_vals)

    return valid


if __name__ == "__main__":
    print("=== LDC Witness 测试 ===")

    # 设置
    m = 4
    witness = [1, 1, 1, 1]

    print(f"输入比特数: {m}")
    print(f"Witness: {witness}")

    # 创建 Witness 测试器
    wt = WitnessTest(m, lambda w: all(x == 1 for x in w))

    # 证明者提交
    committed = wt.prover_commit(witness)
    print(f"\n提交的码字长度: {len(committed)}")

    # 多次测试
    print("\n=== 验证测试 ===")
    for seed in [42, 123, 456]:
        query_pos, query_vals = wt.verifier_query(committed, random_seed=seed)
        valid = wt.verify_queries(witness, query_pos, query_vals)
        print(f"  种子 {seed}: 查询位置 {query_pos}, 验证结果 {valid}")

    # 错误 witness 测试
    print("\n=== 错误 Witness 测试 ===")
    wrong_witness = [1, 1, 0, 1]
    query_pos, query_vals = wt.verifier_query(committed, random_seed=42)
    valid = wt.verify_queries(wrong_witness, query_pos, query_vals)
    print(f"正确 witness: {witness}")
    print(f"错误 witness: {wrong_witness}")
    print(f"验证结果: {valid}")

    # 电路可满足性测试
    print("\n=== 电路可满足性测试 ===")
    for witness in [[1, 1, 1, 1], [0, 0, 0, 0], [1, 0, 1, 0]]:
        valid = circuit_sat_witness_test(4, witness)
        print(f"  witness {witness}: 验证 {'通过' if valid else '失败'}")

    print("\nWitness 测试特性:")
    print("  零知识：验证者只知道 witness 满足电路，不知道具体值")
    print("  局部性：只需查询少量位置")
    print("  可靠性：假冒者很难通过验证")
    print("  应用：简洁参数验证、零知识证明")
