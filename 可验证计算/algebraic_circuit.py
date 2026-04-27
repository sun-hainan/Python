# -*- coding: utf-8 -*-

"""

算法实现：可验证计算 / algebraic_circuit



本文件实现 algebraic_circuit 相关的算法功能。

"""



import random





class ArithmeticCircuit:

    """

    算术电路：表示为加法和乘法门的有向无环图。

    """



    def __init__(self):

        self.inputs = []      # 输入变量名

        self.outputs = []     # 输出变量名

        self.gates = []       # 门列表：('add', left, right, out) 或 ('mul', left, right, out)

        self.num_constraints = 0



    def add_input(self, name):

        """添加输入变量。"""

        self.inputs.append(name)



    def add_gate(self, op, left, right, out):

        """添加一个门。"""

        self.gates.append((op, left, right, out))

        self.num_constraints += 1



    def r1cs_matrices(self):

        """

        转换为 R1CS 矩阵形式。



        R1CS: (A * x) * (B * x) = C * x

        其中 x 是所有变量的连接向量

        """

        all_vars = self.inputs + [g[3] for g in self.gates]

        var_idx = {v: i for i, v in enumerate(all_vars)}



        n = len(all_vars)

        A, B, C = [], [], []



        for op, left, right, out in self.gates:

            a_vec = [0] * n

            b_vec = [0] * n

            c_vec = [0] * n



            if op == 'input':

                a_vec[var_idx[left]] = 1

                b_vec[0] = 1          # 乘以常数1

                c_vec[var_idx[out]] = 1

            elif op == 'add':

                a_vec[var_idx[left]] = 1

                b_vec[0] = 1

                c_vec[var_idx[out]] = 1

                # 额外的 equal 约束

                A.append(a_vec)

                B.append(b_vec)

                C.append(c_vec)

                # 第二组：left = out

                a_vec2 = [0] * n

                a_vec2[var_idx[left]] = 1

                b_vec2 = [0] * n

                b_vec2[0] = 1

                c_vec2 = [0] * n

                c_vec2[var_idx[out]] = 1

                A.append(a_vec2)

                B.append(b_vec2)

                C.append(c_vec2)

            elif op == 'mul':

                a_vec[var_idx[left]] = 1

                b_vec[var_idx[right]] = 1

                c_vec[var_idx[out]] = 1



            A.append(a_vec)

            B.append(b_vec)

            C.append(c_vec)



        return A, B, C, var_idx





def build_multiplication_circuit(a_var, b_var, c_var):

    """

    构造乘法电路：验证 c = a * b



    变量: a, b, c, one

    约束: a * b = c

    """

    circ = ArithmeticCircuit()

    circ.add_input(a_var)

    circ.add_input(b_var)

    circ.add_input(c_var)

    circ.add_gate('input', 'one', None, 'one')  # 常量1



    # a * b = c

    circ.add_gate('mul', a_var, b_var, c_var)



    return circ





def witness_assignment(circuit, input_values):

    """

    根据输入值计算电路的完整见证。

    """

    # 变量名到值的映射

    values = {'one': 1}

    values.update(input_values)



    # 按拓扑顺序计算

    for op, left, right, out in circuit.gates:

        if op == 'input':

            continue

        elif op == 'mul':

            values[out] = values[left] * values[right]

        elif op == 'add':

            values[out] = values[left] + values[right]



    all_vars = circuit.inputs + [g[3] for g in circuit.gates]

    return [values.get(v, 0) for v in all_vars]





def r1cs_verify(A, B, C, witness):

    """

    验证 R1CS 约束：对于每个约束 i，

    (A_i · x) * (B_i · x) = C_i · x

    """

    for a_vec, b_vec, c_vec in zip(A, B, C):

        left = sum(a * x for a, x in zip(a_vec, witness)) % 13

        right = sum(b * x for b, x in zip(b_vec, witness)) % 13

        result = sum(c * x for c, x in zip(c_vec, witness)) % 13



        if (left * right) % 13 != result % 13:

            return False

    return True





if __name__ == "__main__":

    print("=== 算术电路 R1CS 证明测试 ===")



    # 构造电路: 验证 c = a * b

    circ = build_multiplication_circuit('a', 'b', 'c')

    print(f"电路门数: {circ.num_constraints}")

    print(f"输入变量: {circ.inputs}")



    # 获取 R1CS 矩阵

    A, B, C, var_idx = circ.r1cs_matrices()

    print(f"\nR1CS 约束数: {len(A)}")

    print(f"变量数: {len(var_idx)}")



    # 正确赋值测试

    input_values = {'a': 3, 'b': 4, 'c': 12}

    witness = witness_assignment(circ, input_values)

    print(f"\n输入: a=3, b=4, c=12")

    print(f"见证向量: {witness}")



    valid = r1cs_verify(A, B, C, witness)

    print(f"R1CS 验证: {valid}")



    # 错误赋值测试

    print("\n=== 错误赋值测试 ===")

    wrong_input = {'a': 3, 'b': 4, 'c': 10}  # 3*4 != 10

    wrong_witness = witness_assignment(circ, wrong_input)

    valid_wrong = r1cs_verify(A, B, C, wrong_witness)

    print(f"输入: a=3, b=4, c=10")

    print(f"R1CS 验证: {valid_wrong}")



    print("\n电路可满足性证明:")

    print("  将计算表达为电路 -> R1CS -> 证明/验证")

    print("  约束数 = 电路门数 = O(n)")

    print("  验证时间 = O(n)")

