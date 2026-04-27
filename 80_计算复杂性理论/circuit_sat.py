# -*- coding: utf-8 -*-

"""

算法实现：计算复杂性理论 / circuit_sat



本文件实现 circuit_sat 相关的算法功能。

"""



from typing import List, Tuple, Set, Optional, Dict

from enum import Enum





# ==================== 电路基本结构 ====================



class GateType(Enum):

    """门类型"""

    AND = "AND"

    OR = "OR"

    NOT = "NOT"

    INPUT = "INPUT"

    OUTPUT = "OUTPUT"





class Wire:

    """电路中的线（连接）"""

    def __init__(self, wire_id: int):

        self.id = wire_id

        self.value: Optional[int] = None  # 0或1

        self.source: Optional[int] = None  # 源门ID

        self.sinks: List[int] = []  # 目标门ID列表





class Gate:

    """电路门"""

    def __init__(self, gate_id: int, gate_type: GateType):

        self.id = gate_id

        self.type = gate_type

        self.inputs: List[int] = []  # 输入线ID列表

        self.output: Optional[int] = None  # 输出线ID





class Circuit:

    """布尔电路"""



    def __init__(self):

        self.gates: Dict[int, Gate] = {}

        self.wires: Dict[int, Wire] = {}

        self.input_count: int = 0

        self.output_gate: Optional[int] = None



    def add_gate(self, gate_type: GateType, inputs: List[int]) -> int:

        """添加门"""

        gate_id = len(self.gates)

        gate = Gate(gate_id, gate_type)

        gate.inputs = inputs

        self.gates[gate_id] = gate

        return gate_id



    def add_input(self) -> int:

        """添加输入"""

        self.input_count += 1

        return self.input_count - 1



    def set_output_gate(self, gate_id: int):

        """设置输出门"""

        self.output_gate = gate_id



    def evaluate(self, input_values: List[int]) -> Optional[int]:

        """

        评估电路



        参数：

            input_values: 输入位列表



        返回：输出（0或1）或None（如果无法评估）

        """

        if len(input_values) != self.input_count:

            return None



        # 设置输入值

        for i, val in enumerate(input_values):

            self.wires[i].value = val



        # 评估每个门

        for gate_id in sorted(self.gates.keys()):

            gate = self.gates[gate_id]



            if gate.type == GateType.INPUT:

                gate.output = self.wires[gate.inputs[0]].value if gate.inputs else input_values[gate.id]



            elif gate.type == GateType.AND:

                inputs = [self.wires[w].value for w in gate.inputs]

                gate.output = 1 if all(v == 1 for v in inputs) else 0



            elif gate.type == GateType.OR:

                inputs = [self.wires[w].value for w in gate.inputs]

                gate.output = 1 if any(v == 1 for v in inputs) else 0



            elif gate.type == GateType.NOT:

                if gate.inputs:

                    gate.output = 1 - self.wires[gate.inputs[0]].value

                else:

                    gate.output = None



        return self.gates[self.output_gate].output if self.output_gate else None





# ==================== 电路SAT验证 ====================



def verify_circuit_sat(circuit: Circuit, assignment: List[int]) -> bool:

    """

    验证电路是否可满足



    参数：

        circuit: 布尔电路

        assignment: 输入赋值



    返回：True如果赋值使输出为1

    """

    result = circuit.evaluate(assignment)

    return result == 1





def circuit_sat_backtracking(circuit: Circuit) -> Optional[List[int]]:

    """

    使用回溯法找电路可满足赋值



    复杂度：O(2^n * n)

    """

    n = circuit.input_count



    def backtrack(assignment: List[int]) -> Optional[List[int]]:

        if len(assignment) == n:

            if verify_circuit_sat(circuit, assignment):

                return assignment

            return None



        # 尝试0

        assignment.append(0)

        result = backtrack(assignment)

        if result:

            return result

        assignment.pop()



        # 尝试1

        assignment.append(1)

        result = backtrack(assignment)

        if result:

            return result

        assignment.pop()



        return None



    return backtrack([])





# ==================== NP完全性证明 ====================



def prove_circuit_sat_np():

    """

    证明Circuit SAT ∈ NP



    验证器V(C, a)：

    1. 检查a是长度为n的二进制串

    2. 计算C(a)

    3. 检查C(a) = 1



    复杂度：O(|C|)

    """

    print("【步骤1：证明Circuit SAT ∈ NP】")

    print()

    print("验证器V(C, a):")

    print("  1. 验证|a| = n（输入位数）")

    print("  2. 评估电路C(a)")

    print("  3. 检查输出 = 1")

    print()

    print("评估时间：O(|C|) = 多项式时间")

    print("因此Circuit SAT ∈ NP")

    print()





def prove_circuit_sat_nphard():

    """

    证明Circuit SAT是NP难的



    归约：TM判定问题 ≤_p Circuit SAT



    对于任意NP语言L：

    1. 存在多项式时间TM M判定L

    2. 将M展开为布尔电路（每个时间步一个门）

    3. 电路可满足 ⟺ TM接受



    复杂度：O(n * T(n))，T是时间复杂度

    """

    print("【步骤2：证明Circuit SAT是NP难的】")

    print()

    print("归约：TM判定 ≤_p Circuit SAT")

    print()

    print("对于任意语言L ∈ NP：")

    print("  - 存在多项式时间TM M使得：")

    print("    x ∈ L ⟺ M(x) accepts")

    print()

    print("归约步骤：")

    print("  1. 将M的每个计算步骤展开为布尔门")

    print("  2. 电路输入 = TM的输入 + 工作带")

    print("  3. 电路输出 = TM的接受状态")

    print()

    print("正确性：")

    print("  - 如果M接受x，存在赋值使电路输出1")

    print("  - 如果M拒绝x，任何赋值都使电路输出0")

    print()

    print("归约时间：O(|x| * T(|x|)) = 多项式时间")

    print()





def circuit_to_sat(circuit: Circuit) -> List[List[str]]:

    """

    将电路转换为SAT公式（CNF）



    每个门产生若干子句：

    - AND门：输出=输入1∧输入2

    - OR门：输出=输入1∨输入2

    - NOT门：输出=¬输入



    复杂度：O(|C|)

    """

    clauses = []

    n = circuit.input_count



    # 为每个门的输出创建变量

    gate_vars = {}

    for gate_id, gate in circuit.gates.items():

        gate_vars[gate_id] = f"g{gate_id}"



    # 处理每个门

    for gate_id, gate in circuit.gates.items():

        g = gate_vars[gate_id]



        if gate.type == GateType.AND:

            # g = i1 ∧ i2 ⟺ (¬g ∨ i1) ∧ (¬g ∨ i2) ∧ (¬i1 ∨ ¬i2 ∨ g)

            i1_var = gate_vars[gate.inputs[0]] if gate.inputs else f"x{gate.inputs[0]}"

            i2_var = gate_vars[gate.inputs[1]] if len(gate.inputs) > 1 else f"x{gate.inputs[1]}"



            clauses.append([f"!{g}", i1_var])

            clauses.append([f"!{g}", i2_var])

            clauses.append([f"!{i1_var}", f"!{i2_var}", g])



        elif gate.type == GateType.OR:

            # g = i1 ∨ i2 ⟺ (¬g ∨ i1 ∨ i2) ∧ (¬i1 ∨ g) ∧ (¬i2 ∨ g)

            i1_var = gate_vars.get(gate.inputs[0], f"x{gate.inputs[0]}")

            i2_var = gate_vars.get(gate.inputs[1], f"x{gate.inputs[1]}")



            clauses.append([f"!{g}", i1_var, i2_var])

            clauses.append([f"!{i1_var}", g])

            clauses.append([f"!{i2_var}", g])



        elif gate.type == GateType.NOT:

            # g = ¬i ⟺ (¬i ∨ ¬g) ∧ (i ∨ g)

            i_var = gate_vars.get(gate.inputs[0], f"x{gate.inputs[0]}")

            clauses.append([f"!{i_var}", f"!{g}"])

            clauses.append([i_var, g])



    return clauses





# ==================== SAT到电路 ====================



def sat_to_circuit(formula: List[List[str]]) -> Circuit:

    """

    将SAT公式转换为电路



    每个子句对应一个OR门

    所有子句的OR门连接到最终AND门



    复杂度：O(m * k)，m是子句数，k是子句长度

    """

    circuit = Circuit()



    # 添加输入变量

    var_set = set()

    for clause in formula:

        for lit in clause:

            var = lit.replace('!', '')

            var_set.add(var)



    for _ in var_set:

        circuit.add_input()



    # 为每个子句创建OR门

    clause_gates = []

    for clause in formula:

        input_vars = []

        for lit in clause:

            var = lit.replace('!', '')

            idx = list(var_set).index(var)

            input_vars.append(idx)



        clause_gate = circuit.add_gate(GateType.OR, input_vars)

        clause_gates.append(clause_gate)



    # 最终AND门

    if clause_gates:

        final_and = circuit.add_gate(GateType.AND, clause_gates)

        circuit.set_output_gate(final_and)



    return circuit





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 电路可满足性 ===\n")



    prove_circuit_sat_np()

    prove_circuit_sat_nphard()



    print()

    print("【结论】")

    print("Circuit SAT ∈ NP 且 Circuit SAT是NP难的")

    print("因此Circuit SAT是NP完全问题")

    print()



    print("【示例】")

    # 构建简单电路: (x1 AND x2) OR x3

    circuit = Circuit()



    # 添加输入

    x1 = 0

    x2 = 1

    x3 = 2

    circuit.input_count = 3



    # AND门

    and_gate = circuit.add_gate(GateType.AND, [x1, x2])



    # OR门

    or_gate = circuit.add_gate(GateType.OR, [and_gate, x3])

    circuit.set_output_gate(or_gate)



    # 测试

    print("电路：(x1 AND x2) OR x3")

    print()



    test_cases = [

        [0, 0, 0],

        [0, 0, 1],

        [1, 1, 0],

        [1, 0, 1],

        [1, 1, 1],

    ]



    for inputs in test_cases:

        result = circuit.evaluate(inputs)

        print(f"  输入{inputs} → 输出{result}")



    print()

    print("【复杂度分析】")

    print("验证：O(|C|)")

    print("搜索：O(2^n)")

    print("SAT归约：O(m * k)")

    print()

    print("【应用】")

    print("  - 硬件验证")

    print("  - 程序验证")

    print("  - SAT求解器基础")

