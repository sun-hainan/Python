# -*- coding: utf-8 -*-

"""

算法实现：隐私计算 / 11_garbled_circuit



本文件实现 11_garbled_circuit 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional

from enum import Enum





class WireValue(Enum):

    """线值类型"""

    ZERO = 0

    ONE = 1

    ENC_0 = 2  # 加密的0

    ENC_1 = 3  # 加密的1





class GarbledGate:

    """

    混淆门



    存储混淆后的真值表

    """



    def __init__(self, gate_type: str):

        """

        初始化混淆门



        Args:

            gate_type: 门类型 "AND", "OR", "XOR", "NOT"

        """

        self.gate_type = gate_type

        self.garbled_table = []

        self.keys = {}  # wire_id -> {0: key0, 1: key1}



    def set_keys(self, wire_id: str, key0: int, key1: int):

        """

        设置线的密钥对



        Args:

            wire_id: 线ID

            key0: 值为0时的密钥

            key1: 值为1时的密钥

        """

        self.keys[wire_id] = {"0": key0, "1": key1}



    def get_key(self, wire_id: str, bit: int) -> int:

        """

        获取特定位的密钥



        Args:

            wire_id: 线ID

            bit: 位值(0或1)



        Returns:

            密钥

        """

        return self.keys.get(wire_id, {}).get(str(bit), 0)



    def garble(self):

        """

        混淆真值表



        生成打乱后的密文表

        """

        if self.gate_type == "AND":

            self._garble_and()

        elif self.gate_type == "OR":

            self._garble_or()

        elif self.gate_type == "XOR":

            self._garble_xor()

        elif self.gate_type == "NOT":

            self._garble_not()



    def _garble_and(self):

        """

        AND门混淆表



        输入: (a, b), 输出: a AND b

        """

        a0 = self.get_key("a", 0)

        a1 = self.get_key("a", 1)

        b0 = self.get_key("b", 0)

        b1 = self.get_key("b", 1)

        out0 = self.get_key("out", 0)

        out1 = self.get_key("out", 1)



        # 简化的加密: 异或操作符

        # 实际应使用PRG或块密码

        self.garbled_table = [

            (a0 ^ b0, out0),  # 0 AND 0 = 0

            (a0 ^ b1, out0),  # 0 AND 1 = 0

            (a1 ^ b0, out0),  # 1 AND 0 = 0

            (a1 ^ b1, out1),  # 1 AND 1 = 1

        ]

        np.random.shuffle(self.garbled_table)



    def _garble_or(self):

        """OR门混淆"""

        a0 = self.get_key("a", 0)

        a1 = self.get_key("a", 1)

        b0 = self.get_key("b", 0)

        b1 = self.get_key("b", 1)

        out0 = self.get_key("out", 0)

        out1 = self.get_key("out", 1)



        self.garbled_table = [

            (a0 ^ b0, out0),  # 0 OR 0 = 0

            (a0 ^ b1, out1),  # 0 OR 1 = 1

            (a1 ^ b0, out1),  # 1 OR 0 = 1

            (a1 ^ b1, out1),  # 1 OR 1 = 1

        ]

        np.random.shuffle(self.garbled_table)



    def _garble_xor(self):

        """XOR门混淆"""

        a0 = self.get_key("a", 0)

        a1 = self.get_key("a", 1)

        b0 = self.get_key("b", 0)

        b1 = self.get_key("b", 1)

        out0 = self.get_key("out", 0)

        out1 = self.get_key("out", 1)



        self.garbled_table = [

            (a0 ^ b0, out0),  # 0 XOR 0 = 0

            (a0 ^ b1, out1),  # 0 XOR 1 = 1

            (a1 ^ b0, out1),  # 1 XOR 0 = 1

            (a1 ^ b1, out0),  # 1 XOR 1 = 0

        ]



    def _garble_not(self):

        """NOT门混淆"""

        in0 = self.get_key("in", 0)

        in1 = self.get_key("in", 1)

        out0 = self.get_key("out", 0)

        out1 = self.get_key("out", 1)



        self.garbled_table = [

            (in0, out1),  # NOT 0 = 1

            (in1, out0),  # NOT 1 = 0

        ]



    def evaluate(self, key_a: int, key_b: int) -> int:

        """

        求值混淆门



        Args:

            key_a: 输入线A的密钥

            key_b: 输入线B的密钥



        Returns:

            输出线的密钥

        """

        for table_entry in self.garbled_table:

            if table_entry[0] == (key_a ^ key_b):

                return table_entry[1]

        return 0





class GarbledCircuit:

    """

    混淆电路



    由多个混淆门组成的完整电路

    """



    def __init__(self):

        """初始化混淆电路"""

        self.gates = []

        self.input_wires = []

        self.output_wires = []

        self.wire_keys = {}  # wire_id -> {0: key0, 1: key1}



    def add_wire(self, wire_id: str):

        """

        添加线



        Args:

            wire_id: 线ID

        """

        if wire_id not in self.wire_keys:

            # 生成密钥对

            key0 = np.random.randint(1, 2**31)

            key1 = np.random.randint(1, 2**31)

            self.wire_keys[wire_id] = {"0": key0, "1": key1}



    def add_input_wire(self, wire_id: str, owner: str):

        """

        添加输入线



        Args:

            wire_id: 线ID

            owner: 输入方 "garbler" 或 "evaluator"

        """

        self.add_wire(wire_id)

        self.input_wires.append({

            "wire_id": wire_id,

            "owner": owner

        })



    def add_output_wire(self, wire_id: str):

        """

        添加输出线



        Args:

            wire_id: 线ID

        """

        self.add_wire(wire_id)

        self.output_wires.append(wire_id)



    def add_gate(

        self,

        gate_type: str,

        input_wire1: str,

        input_wire2: str,

        output_wire: str

    ) -> GarbledGate:

        """

        添加门



        Args:

            gate_type: 门类型

            input_wire1: 输入线1

            input_wire2: 输入线2

            output_wire: 输出线



        Returns:

            混淆门对象

        """

        self.add_wire(output_wire)



        gate = GarbledGate(gate_type)



        # 设置密钥

        gate.set_keys("a", self.wire_keys[input_wire1]["0"], self.wire_keys[input_wire1]["1"])

        gate.set_keys("b", self.wire_keys[input_wire2]["0"], self.wire_keys[input_wire2]["1"])

        gate.set_keys("out", self.wire_keys[output_wire]["0"], self.wire_keys[output_wire]["1"])



        # 混淆

        gate.garble()



        self.gates.append({

            "gate": gate,

            "inputs": [input_wire1, input_wire2],

            "output": output_wire

        })



        return gate



    def add_not_gate(self, input_wire: str, output_wire: str) -> GarbledGate:

        """添加NOT门"""

        self.add_wire(output_wire)



        gate = GarbledGate("NOT")

        gate.set_keys("in", self.wire_keys[input_wire]["0"], self.wire_keys[input_wire]["1"])

        gate.set_keys("out", self.wire_keys[output_wire]["0"], self.wire_keys[output_wire]["1"])

        gate.garble()



        self.gates.append({

            "gate": gate,

            "inputs": [input_wire],

            "output": output_wire

        })



        return gate



    def get_public_info(self) -> Dict:

        """

        获取公共信息(发送给evaluator)



        Returns:

            公共信息字典

        """

        return {

            "gates": self.gates,

            "output_wires": self.output_wires,

            "garbler_inputs": [w for w in self.input_wires if w["owner"] == "garbler"],

            "evaluator_inputs": [w for w in self.input_wires if w["owner"] == "evaluator"]

        }



    def get_output_mapping(self) -> Dict[str, int]:

        """

        获取输出线的真实值映射



        用于最终解密



        Returns:

            wire_id -> 真实值的映射

        """

        mapping = {}

        for wire_id in self.output_wires:

            mapping[wire_id] = {

                self.wire_keys[wire_id]["0"]: 0,

                self.wire_keys[wire_id]["1"]: 1

            }

        return mapping





class Garbler:

    """

    混淆方(Garbler)



    负责生成混淆电路

    """



    def __init__(self):

        """初始化混淆方"""

        self.circuit = None

        self.input_bits = {}



    def create_circuit(self) -> GarbledCircuit:

        """

        创建混淆电路



        Returns:

            混淆电路对象

        """

        self.circuit = GarbledCircuit()

        return self.circuit



    def set_input(self, wire_id: str, bit: int):

        """

        设置本方输入



        Args:

            wire_id: 线ID

            bit: 输入位

        """

        self.input_bits[wire_id] = bit



    def get_encrypted_input_keys(self) -> Dict[str, int]:

        """

        获取本方输入对应的加密密钥



        用于发送给evaluator



        Returns:

            wire_id -> 密钥的映射

        """

        keys = {}

        for wire_info in self.circuit.input_wires:

            if wire_info["owner"] == "garbler":

                wire_id = wire_info["wire_id"]

                bit = self.input_bits.get(wire_id, 0)

                key = self.circuit.wire_keys[wire_id][str(bit)]

                keys[wire_id] = key

        return keys





class Evaluator:

    """

    求值方(Evaluator)



    负责执行混淆电路

    """



    def __init__(self, public_info: Dict):

        """

        初始化求值方



        Args:

            public_info: 公共信息

        """

        self.gates = public_info["gates"]

        self.output_wires = public_info["output_wires"]

        self.evaluator_input_wires = public_info["evaluator_inputs"]



        self.wire_values = {}  # wire_id -> 值(密钥)

        self.input_bits = {}



    def set_input(self, wire_id: str, bit: int):

        """

        设置本方输入



        Args:

            wire_id: 线ID

            bit: 输入位

        """

        self.input_bits[wire_id] = bit



    def set_garbler_keys(self, keys: Dict[str, int]):

        """

        设置混淆方输入的密钥



        Args:

            keys: wire_id -> 密钥

        """

        for wire_id, key in keys.items():

            self.wire_values[wire_id] = key



    def evaluate(self) -> Dict[str, int]:

        """

        求值电路



        Returns:

            output_wire_id -> 输出值(0或1)

        """

        # 设置本方输入

        for wire_info in self.evaluator_input_wires:

            wire_id = wire_info["wire_id"]

            bit = self.input_bits.get(wire_id, 0)

            # evaluator也需要知道对应密钥

            # 实际通过OT协议获取,这里简化

            self.wire_values[wire_id] = bit  # 简化:直接存储位



        # 逐门求值

        for gate_info in self.gates:

            gate = gate_info["gate"]

            inputs = gate_info["inputs"]

            output = gate_info["output"]



            # 获取输入值

            in_vals = [self.wire_values.get(w, 0) for w in inputs]



            # 求值

            if gate.gate_type == "NOT":

                out_val = 1 - in_vals[0]

            elif gate.gate_type == "XOR":

                out_val = in_vals[0] ^ in_vals[1]

            elif gate.gate_type == "AND":

                out_val = in_vals[0] & in_vals[1]

            elif gate.gate_type == "OR":

                out_val = in_vals[0] | in_vals[1]

            else:

                out_val = 0



            self.wire_values[output] = out_val



        # 提取输出

        outputs = {}

        for wire_id in self.output_wires:

            outputs[wire_id] = self.wire_values.get(wire_id, 0)



        return outputs





class ObliviousTransfer:

    """

    不经意传输(OT)



    允许evaluator从garbler获取特定输入的密钥,

    而garbler不知道evaluator选择了哪个输入

    """



    def __init__(self):

        """初始化OT"""

        np.random.seed(42)



    def execute(

        self,

        key0: int,

        key1: int,

        choice_bit: int,

        public_key: Tuple[int, int] = None

    ) -> int:

        """

        执行OT



        Args:

            key0: 选项0对应的密钥

            key1: 选项1对应的密钥

            choice_bit: 选择位

            public_key: 公钥(可选)



        Returns:

            选择的密钥

        """

        # 简化版本: 直接返回选择项

        # 实际需要密码学协议

        return key0 if choice_bit == 0 else key1





def create_majority_circuit(circuit: GarbledCircuit) -> GarbledCircuit:

    """

    创建多数投票电路



    判断三个输入中多数是0还是1



    Args:

        circuit: 混淆电路对象



    Returns:

        配置好的电路

    """

    # 添加输入线

    circuit.add_input_wire("a", "garbler")

    circuit.add_input_wire("b", "garbler")

    circuit.add_input_wire("c", "evaluator")



    # 中间线

    circuit.add_wire("ab_and")

    circuit.add_wire("bc_and")

    circuit.add_wire("ac_and")

    circuit.add_wire("ab_or_bc")

    circuit.add_wire("not_ab_or_bc")

    circuit.add_wire("temp_or")



    # 输出线

    circuit.add_output_wire("result")



    # 计算 majority = (a AND b) OR (a AND c) OR (b AND c)

    circuit.add_gate("AND", "a", "b", "ab_and")

    circuit.add_gate("AND", "a", "c", "ac_and")

    circuit.add_gate("AND", "b", "c", "bc_and")



    # (ab AND ac) OR bc

    circuit.add_gate("AND", "ab_and", "ac_and", "temp_and")

    circuit.add_gate("OR", "temp_and", "bc_and", "result")



    return circuit





def garbled_circuit_demo():

    """

    混淆电路演示

    """



    print("混淆电路 - 两方安全计算演示")

    print("=" * 60)



    # 1. 创建混淆电路

    print("\n1. 创建混淆电路")

    garbler = Garbler()

    circuit = garbler.create_circuit()



    # 创建3输入多数电路

    circuit = create_majority_circuit(circuit)



    print(f"   输入线: {len(circuit.input_wires)}")

    print(f"   门数: {len(circuit.gates)}")

    print(f"   输出线: {len(circuit.output_wires)}")



    # 2. Garbler设置输入

    print("\n2. Garbler设置输入")

    garbler.set_input("a", 1)  # 输入a=1

    garbler.set_input("b", 0)  # 输入b=0

    garbler_keys = garbler.get_encrypted_input_keys()

    print(f"   Garbler输入: a=1, b=0")

    print(f"   加密密钥: a->{garbler_keys.get('a', 0)}, b->{garbler_keys.get('b', 0)}")



    # 3. Evaluator设置输入

    print("\n3. Evaluator设置输入")

    evaluator = Evaluator(circuit.get_public_info())

    evaluator.set_input("c", 1)  # 输入c=1

    evaluator.set_garbler_keys(garbler_keys)

    print(f"   Evaluator输入: c=1")



    # 4. 求值

    print("\n4. 求值电路")

    outputs = evaluator.evaluate()

    print(f"   电路输出: {outputs}")



    # 5. 结果验证

    print("\n5. 结果验证")

    a, b, c = 1, 0, 1

    expected = 1 if (a + b + c) >= 2 else 0

    actual = outputs.get("result", 0)

    print(f"   输入: a={a}, b={b}, c={c}")

    print(f"   期望输出: {expected} (多数为1)")

    print(f"   实际输出: {actual}")

    print(f"   验证: {'通过 ✓' if expected == actual else '失败 ✗'}")



    # 6. 更多测试用例

    print("\n6. 更多测试用例")



    test_cases = [

        (0, 0, 0),

        (1, 1, 1),

        (1, 0, 0),

        (0, 1, 1),

    ]



    for a, b, c in test_cases:

        # 重新创建电路

        garbler = Garbler()

        circuit = garbler.create_circuit()

        circuit = create_majority_circuit(circuit)



        garbler.set_input("a", a)

        garbler.set_input("b", b)

        garbler_keys = garbler.get_encrypted_input_keys()



        evaluator = Evaluator(circuit.get_public_info())

        evaluator.set_input("c", c)

        evaluator.set_garbler_keys(garbler_keys)



        outputs = evaluator.evaluate()

        expected = 1 if (a + b + c) >= 2 else 0

        actual = outputs.get("result", 0)



        status = "✓" if expected == actual else "✗"

        print(f"   ({a},{b},{c}) -> {actual} (期望:{expected}) {status}")



    # 7. 安全性说明

    print("\n7. 安全性说明")

    print("   混淆电路的安全性保证:")

    print("   - Garbler不知道Evaluator的输入")

    print("   - Evaluator只知道输出,不知道Garbler的输入")

    print("   - 实际需要OT协议传递Evaluator的输入密钥")

    print("   - 电路表示需要合适以防信息泄露")





if __name__ == "__main__":

    garbled_circuit_demo()



    print("\n" + "=" * 60)

    print("混淆电路演示完成!")

    print("实际系统需要: 安全的OT协议 + 认证通道 + 恶意模型防护")

    print("=" * 60)

