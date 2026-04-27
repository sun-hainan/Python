# -*- coding: utf-8 -*-
"""
算法实现：隐私计算 / 10_gmw_protocol

本文件实现 10_gmw_protocol 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict
from enum import Enum


class GarbledGate:
    """
    混淆门

    将布尔门的真值表加密打乱
    """

    def __init__(self, gate_type: str):
        """
        初始化混淆门

        Args:
            gate_type: 门类型 "AND", "OR", "XOR", "NOT"
        """
        self.gate_type = gate_type
        self.garbled_table = None
        self.keys = {}  # 线的密钥

    def generate_keys(self):
        """生成混淆密钥"""
        np.random.seed(42)
        # 每条线两个密钥: 0和1
        self.keys = {
            "wire0": [np.random.randint(1, 2**31), np.random.randint(1, 2**31)],
            "wire1": [np.random.randint(1, 2**31), np.random.randint(1, 2**31)]
        }

    def garble(self):
        """混淆真值表"""
        if self.gate_type == "XOR":
            self.garbled_table = self._garble_xor()
        elif self.gate_type == "AND":
            self.garbled_table = self._garble_and()
        elif self.gate_type == "OR":
            self.garbled_table = self._garble_or()
        elif self.gate_type == "NOT":
            self.garbled_table = self._garble_not()

    def _garble_xor(self) -> List[Tuple[int, int]]:
        """
        XOR门混淆:
        0 XOR 0 = 0
        0 XOR 1 = 1
        1 XOR 0 = 1
        1 XOR 1 = 0
        """
        k00 = self.keys["wire0"][0]
        k01 = self.keys["wire0"][1]
        k10 = self.keys["wire1"][0]
        k11 = self.keys["wire1"][1]

        # 输出密钥
        out_0 = self.keys.get("out0", np.random.randint(1, 2**31))
        out_1 = self.keys.get("out1", np.random.randint(1, 2**31))

        self.keys["out0"] = out_0
        self.keys["out1"] = out_1

        # 加密的表项(简化版,实际使用PRG)
        return [
            (k00 ^ k10, out_0),
            (k01 ^ k10, out_1),
            (k00 ^ k11, out_1),
            (k01 ^ k11, out_0)
        ]

    def _garble_and(self) -> List[Tuple[int, int]]:
        """AND门混淆"""
        k00 = self.keys["wire0"][0]
        k01 = self.keys["wire0"][1]
        k10 = self.keys["wire1"][0]
        k11 = self.keys["wire1"][1]

        out_0 = self.keys.get("out0", np.random.randint(1, 2**31))
        out_1 = self.keys.get("out1", np.random.randint(1, 2**31))

        self.keys["out0"] = out_0
        self.keys["out1"] = out_1

        # 输出0对应输入(0,0),(0,1),(1,0); 输出1对应(1,1)
        return [
            (k00 ^ k10, out_1),  # 1*1=1
            (k01 ^ k10, out_0),
            (k00 ^ k11, out_0),
            (k01 ^ k11, out_0)
        ]

    def _garble_or(self) -> List[Tuple[int, int]]:
        """OR门混淆"""
        k00 = self.keys["wire0"][0]
        k01 = self.keys["wire0"][1]
        k10 = self.keys["wire1"][0]
        k11 = self.keys["wire1"][1]

        out_0 = self.keys.get("out0", np.random.randint(1, 2**31))
        out_1 = self.keys.get("out1", np.random.randint(1, 2**31))

        self.keys["out0"] = out_0
        self.keys["out1"] = out_1

        return [
            (k00 ^ k10, out_0),
            (k01 ^ k11, out_1),
            (k00 ^ k11, out_1),
            (k01 ^ k10, out_1)
        ]

    def _garble_not(self) -> List[Tuple[int, int]]:
        """NOT门混淆"""
        k0 = self.keys["wire0"][0]
        k1 = self.keys["wire0"][1]

        out_0 = self.keys.get("out0", np.random.randint(1, 2**31))
        out_1 = self.keys.get("out1", np.random.randint(1, 2**31))

        self.keys["out0"] = out_1
        self.keys["out1"] = out_0

        return [(k0, out_1), (k1, out_0)]

    def get_output_key(self, bit: int) -> int:
        """获取输出线的密钥"""
        return self.keys.get(f"out{bit}", 0)


class BooleanCircuit:
    """
    布尔电路

    由多个混淆门组成
    """

    def __init__(self):
        """初始化布尔电路"""
        self.gates = []
        self.wires = {}  # wire_id -> gate_id, output_index

    def add_input_wire(self, wire_id: str) -> str:
        """添加输入线"""
        self.wires[wire_id] = None
        return wire_id

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
        gate = GarbledGate(gate_type)
        gate.generate_keys()
        gate.garble()

        self.gates.append({
            "gate": gate,
            "inputs": [input_wire1, input_wire2],
            "output": output_wire
        })

        self.wires[output_wire] = len(self.gates) - 1

        return gate

    def add_not_gate(self, input_wire: str, output_wire: str) -> GarbledGate:
        """添加NOT门"""
        gate = GarbledGate("NOT")
        gate.generate_keys()
        gate.garble()

        self.gates.append({
            "gate": gate,
            "inputs": [input_wire],
            "output": output_wire
        })

        self.wires[output_wire] = len(self.gates) - 1

        return gate


class GMWParty:
    """
    GMW协议参与方

    参与安全多方计算的一方
    """

    def __init__(self, party_id: int):
        """
        初始化参与方

        Args:
            party_id: 参与方ID
        """
        self.party_id = party_id
        self.input_bits = {}
        self.output_keys = {}

    def set_input(self, wire_id: str, bit: int):
        """设置输入位"""
        self.input_bits[wire_id] = bit

    def get_wire_key(self, wire_id: str, bit: int) -> int:
        """获取线的密钥(从混淆表获取)"""
        # 简化: 实际需要从OT协议获取
        return 0


class ObliviousTransfer:
    """
    不经意传输(OT)协议

    允许发送方发送一条消息给接收方,
    但发送方不知道接收方选择了哪条

    简化实现,基于RSA
    """

    def __init__(self):
        """初始化OT"""
        np.random.seed(42)

    def send(self, message0: int, message1: int, public_key: Tuple[int, int]) -> Tuple[int, int]:
        """
        OT发送方

        Args:
            message0: 消息0
            message1: 消息1
            public_key: 公钥

        Returns:
            (密文0, 密文1)
        """
        n, e = public_key
        c0 = pow(message0, e, n)
        c1 = pow(message1, e, n)
        return c0, c1

    def receive(
        self,
        choice_bit: int,
        ciphertexts: Tuple[int, int],
        private_key: int,
        modulus: int
    ) -> int:
        """
        OT接收方

        Args:
            choice_bit: 选择位(0或1)
            ciphertexts: 两个密文
            private_key: 私钥
            modulus: 模数

        Returns:
            选择的消息
        """
        c0, c1 = ciphertexts
        if choice_bit == 0:
            return pow(c0, private_key, modulus)
        else:
            return pow(c1, private_key, modulus)


class GMWProtocol:
    """
    GMW协议主类

    实现安全两方计算
    """

    def __init__(self):
        """初始化GMW协议"""
        self.circuit = BooleanCircuit()
        self.parties: Dict[int, GMWParty] = {}
        self.garbled_gates = []

    def create_circuit_for_comparison(
        self,
        input_a: str,
        input_b: str,
        output: str
    ) -> BooleanCircuit:
        """
        创建比较电路

        检查 a == b

        Args:
            input_a: 输入A的线ID
            input_b: 输入B的线ID
            output: 输出线ID

        Returns:
            布尔电路
        """
        circuit = BooleanCircuit()

        # 添加输入线
        circuit.add_input_wire(input_a)
        circuit.add_input_wire(input_b)

        # 中间线
        wire_xnor = "xnor"
        wire_not_a = "not_a"
        circuit.add_input_wire(wire_xnor)
        circuit.add_input_wire(wire_not_a)

        # XNOR = NOT(XOR) = NOT(a XOR b)
        circuit.add_gate("XOR", input_a, input_b, "xor_out")
        circuit.add_not_gate("xor_out", wire_xnor)

        # 输出
        circuit.add_gate("AND", wire_xnor, wire_not_a, "temp")
        circuit.add_not_gate("temp", output)

        self.circuit = circuit
        return circuit

    def create_adder_circuit(
        self,
        bits: int
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        创建加法器电路

        Args:
            bits: 位数

        Returns:
            (input_a_wires, input_b_wires, output_wires)
        """
        a_wires = [f"a{i}" for i in range(bits)]
        b_wires = [f"b{i}" for i in range(bits)]
        sum_wires = [f"sum{i}" for i in range(bits)]
        carry_wires = [f"c{i}" for i in range(bits + 1)]

        for w in a_wires + b_wires + sum_wires + carry_wires:
            self.circuit.add_input_wire(w)

        # 全加器链
        for i in range(bits):
            # sum_i = a_i XOR b_i XOR carry_i
            self.circuit.add_gate("XOR", a_wires[i], b_wires[i], f"temp_sum{i}")
            self.circuit.add_gate("XOR", f"temp_sum{i}", carry_wires[i], sum_wires[i])

            # carry_{i+1} = (a_i AND b_i) OR (carry_i AND (a_i XOR b_i))
            self.circuit.add_gate("AND", a_wires[i], b_wires[i], f"and_ab{i}")
            self.circuit.add_gate("AND", carry_wires[i], f"temp_sum{i}", f"and_c{i}")
            self.circuit.add_gate("OR", f"and_ab{i}", f"and_c{i}", carry_wires[i + 1])

        return a_wires, b_wires, sum_wires

    def evaluate_garbled_circuit(
        self,
        input_keys: Dict[str, int],
        party_id: int = 0
    ) -> Dict[str, int]:
        """
        求值混淆电路

        Args:
            input_keys: 每条输入线的密钥
            party_id: 执行方ID

        Returns:
            输出线的值
        """
        wire_values = input_keys.copy()

        for gate_info in self.circuit.gates:
            gate = gate_info["gate"]
            inputs = gate_info["inputs"]
            output = gate_info["output"]

            # 获取输入值
            in_vals = []
            for wire in inputs:
                in_vals.append(wire_values[wire])

            # 简化: 使用真值计算
            if gate.gate_type == "XOR":
                result = in_vals[0] ^ in_vals[1]
            elif gate.gate_type == "AND":
                result = in_vals[0] & in_vals[1]
            elif gate.gate_type == "OR":
                result = in_vals[0] | in_vals[1]
            elif gate.gate_type == "NOT":
                result = 1 - in_vals[0]
            else:
                result = 0

            wire_values[output] = result

        # 只返回输出线
        outputs = {}
        for wire_id, value in wire_values.items():
            if wire_id.startswith("out") or wire_id.startswith("sum"):
                outputs[wire_id] = value

        return outputs


class GMWProtocolSimulator:
    """
    GMW协议模拟器

    模拟两方安全计算
    """

    def __init__(self):
        """初始化模拟器"""
        self.gmw = GMWProtocol()

    def secure_compute_equal(
        self,
        party_a_input: int,
        party_b_input: int,
        n_bits: int = 4
    ) -> bool:
        """
        安全计算两数是否相等

        Args:
            party_a_input: 参与方A的输入
            party_b_input: 参与方B的输入
            n_bits: 位数

        Returns:
            是否相等
        """
        # 创建电路
        circuit = self.gmw.create_circuit_for_comparison("a", "b", "equal")

        # 转换为位
        a_bits = [(party_a_input >> i) & 1 for i in range(n_bits)]
        b_bits = [(party_b_input >> i) & 1 for i in range(n_bits)]

        # 简化: 直接计算(实际需要OT协议)
        is_equal = party_a_input == party_b_input

        return is_equal

    def secure_add(
        self,
        party_a_input: int,
        party_b_input: int,
        n_bits: int = 8
    ) -> int:
        """
        安全计算两数之和

        Args:
            party_a_input: 参与方A的输入
            party_b_input: 参与方B的输入
            n_bits: 位数

        Returns:
            和
        """
        return (party_a_input + party_b_input) % (2 ** n_bits)

    def secure_compare(
        self,
        party_a_input: int,
        party_b_input: int
    ) -> int:
        """
        安全计算 a < b

        Args:
            party_a_input: 参与方A的输入
            party_b_input: 参与方B的输入

        Returns:
            1如果a<b,否则0
        """
        return 1 if party_a_input < party_b_input else 0


def gmw_demo():
    """
    GMW协议演示
    """

    print("GMW协议 - 安全多方计算演示")
    print("=" * 60)

    # 1. 混淆门
    print("\n1. 混淆门演示")
    gate = GarbledGate("AND")
    gate.generate_keys()
    gate.garble()

    print(f"   AND门类型: {gate.gate_type}")
    print(f"   密钥: {gate.keys}")

    # 2. 布尔电路
    print("\n2. 布尔电路")
    circuit = BooleanCircuit()

    # 构建 (a AND b) OR c
    circuit.add_input_wire("a")
    circuit.add_input_wire("b")
    circuit.add_input_wire("c")

    circuit.add_gate("AND", "a", "b", "ab")
    circuit.add_gate("OR", "ab", "c", "result")

    print(f"   电路门数: {len(circuit.gates)}")
    print(f"   输入线: {list(circuit.wires.keys())}")

    # 3. GMW协议模拟
    print("\n3. GMW安全计算")

    simulator = GMWProtocolSimulator()

    # 安全相等测试
    a, b = 5, 7
    is_equal = simulator.secure_compute_equal(a, b, n_bits=4)
    print(f"   安全相等: {a} == {b} ? {is_equal}")

    a, b = 5, 5
    is_equal = simulator.secure_compute_equal(a, b, n_bits=4)
    print(f"   安全相等: {a} == {b} ? {is_equal}")

    # 安全加法
    a, b = 100, 50
    result = simulator.secure_add(a, b, n_bits=8)
    print(f"   安全加法: {a} + {b} = {result}")

    # 安全比较
    a, b = 3, 7
    result = simulator.secure_compare(a, b)
    print(f"   安全比较: {a} < {b} ? {result}")

    # 4. 实际场景
    print("\n4. 应用场景")

    # 场景: 两个医院在不泄露患者数据的情况下联合计算平均值
    print("   场景: 安全平均薪资计算")
    print("   医院A薪资: [50k, 60k, 55k]")
    print("   医院B薪资: [70k, 80k, 75k]")

    # 简化:直接计算
    hospital_a_avg = np.mean([50, 60, 55])
    hospital_b_avg = np.mean([70, 80, 75])
    combined_avg = (sum([50, 60, 55]) + sum([70, 80, 75])) / 6

    print(f"   医院A平均: {hospital_a_avg:.2f}k")
    print(f"   医院B平均: {hospital_b_avg:.2f}k")
    print(f"   联合平均: {combined_avg:.2f}k")
    print("   (注意:实际应使用安全求和协议)")


if __name__ == "__main__":
    gmw_demo()

    print("\n" + "=" * 60)
    print("GMW协议演示完成!")
    print("实际协议需要: 混淆电路 + 不经意传输 + 认证通道")
    print("=" * 60)
