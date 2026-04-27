# -*- coding: utf-8 -*-
"""
算法实现：密码学协议 / garbled_circuit

本文件实现 garbled_circuit 相关的算法功能。
"""

import random
import hashlib


def is_prime(n):
    """素性测试。"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def generate_prime(bits=12):
    """生成素数。"""
    while True:
        p = random.randrange(2**(bits-1), 2**bits, 2)
        if is_prime(p):
            return p


def int_to_bytes(x, length=4):
    """整数转字节串。"""
    return x.to_bytes(length, 'big')


def bytes_to_int(b):
    """字节串转整数。"""
    return int.from_bytes(b, 'big')


class GarbledCircuit:
    """Yao 混淆电路。"""

    def __init__(self, num_wires):
        self.num_wires = num_wires
        self.tables = {}  # 混淆真值表
        self.labels = {}  # 线标签（每条线的两个可能的标签）
        self.garbled_table = {}  # 混淆表

    def generate_labels(self, wire):
        """为每条线生成两个标签（0标签和1标签）。"""
        label0 = random.randint(1, 2**32)
        label1 = random.randint(1, 2**32)
        self.labels[wire] = {0: label0, 1: label1}
        return label0, label1

    def garble_gate(self, gate_id, gate_type, wire_a, wire_b, wire_out):
        """
        混淆一个门。

        参数:
            gate_id: 门 ID
            gate_type: 'AND', 'OR', 'XOR', 'NOT'
            wire_a, wire_b: 输入线
            wire_out: 输出线
        """
        labels_a = self.labels[wire_a]
        labels_b = self.labels[wire_b]
        labels_out = self.labels[wire_out]

        # 混淆表条目
        entries = {}

        # 遍历所有输入组合
        for val_a in [0, 1]:
            for val_b in [0, 1]:
                # 计算输出值
                if gate_type == 'AND':
                    val_out = val_a & val_b
                elif gate_type == 'OR':
                    val_out = val_a | val_b
                elif gate_type == 'XOR':
                    val_out = val_a ^ val_b
                elif gate_type == 'NOT':
                    val_out = 1 - val_a
                    val_b = 0  # NOT 门忽略第二个输入
                    val_b = 0
                else:
                    val_out = 0

                # 标签
                label_a = labels_a[val_a]
                label_b = labels_b[val_b]
                label_out = labels_out[val_out]

                # 混淆：Enc(label_out, label_a, label_b)
                key = hashlib.sha256(int_to_bytes(label_a) + int_to_bytes(label_b)).digest()
                entry = bytes_to_int(key) ^ label_out
                entries[(val_a, val_b)] = entry

        # 打乱表顺序（混淆关键步骤）
        entry_list = list(entries.values())
        random.shuffle(entry_list)
        self.garbled_table[gate_id] = entry_list

        return entry_list

    def garble_circuit(self, circuit):
        """
        混淆整个电路。

        参数:
            circuit: 电路描述 [(gate_type, input_a, input_b, output), ...]
        """
        # 为所有线生成标签
        for wire in range(self.num_wires):
            self.generate_labels(wire)

        # 混淆每个门
        for gate_id, (gate_type, wire_a, wire_b, wire_out) in enumerate(circuit):
            self.garble_gate(gate_id, gate_type, wire_a, wire_b, wire_out)

        return self.garbled_table, self.labels


class Evaluator:
    """混淆电路评估器。"""

    def __init__(self, garbled_table, labels):
        self.garbled_table = garbled_table
        self.labels = labels
        self.wire_values = {}  # 线上的值（标签形式）

    def set_input_labels(self, input_labels):
        """
        设置输入标签。

        参数:
            input_labels: {wire: label} 字典
        """
        self.wire_values.update(input_labels)

    def evaluate_gate(self, gate_id, gate_type, wire_a, wire_b, wire_out):
        """评估一个门。"""
        label_a = self.wire_values.get(wire_a)
        label_b = self.wire_values.get(wire_b)

        if label_a is None or label_b is None:
            return None

        # 解密表条目
        key = hashlib.sha256(int_to_bytes(label_a) + int_to_bytes(label_b)).digest()
        key_int = bytes_to_int(key)

        # 尝试所有表条目
        for entry in self.garbled_table[gate_id]:
            output_label = entry ^ key_int
            # 检查这个标签是否是有效的输出标签
            if wire_out in self.labels:
                if output_label in self.labels[wire_out].values():
                    self.wire_values[wire_out] = output_label
                    return output_label

        return None

    def evaluate_circuit(self, circuit):
        """
        评估整个电路。

        参数:
            circuit: 电路描述
        """
        for gate_id, (gate_type, wire_a, wire_b, wire_out) in enumerate(circuit):
            self.evaluate_gate(gate_id, gate_type, wire_a, wire_b, wire_out)

        return self.wire_values


def build_and_circuit(num_inputs):
    """
    构建 AND 电路。

    电路: (a AND b) XOR (c AND d)
    """
    circuit = []

    # 门1: a AND b
    circuit.append(('AND', 0, 1, num_inputs))  # wire 4 = a AND b

    # 门2: c AND d
    circuit.append(('AND', 2, 3, num_inputs + 1))  # wire 5 = c AND d

    # 门3: XOR
    circuit.append(('XOR', num_inputs, num_inputs + 1, num_inputs + 2))  # wire 6 = result

    return circuit


if __name__ == "__main__":
    print("=== 混淆电路测试 ===")

    # 示例：计算 (a AND b) XOR (c AND d)
    # 4 个输入: a=1, b=1, c=0, d=1
    # 期望结果: (1 AND 1) XOR (0 AND 1) = 1 XOR 0 = 1

    num_wires = 7  # 4 输入 + 2 中间 + 1 输出
    circuit = build_and_circuit(4)

    print("电路描述:")
    for i, (gt, wa, wb, wo) in enumerate(circuit):
        print(f"  门 {i}: {gt}(wire {wa}, wire {wb}) -> wire {wo}")

    # 混淆方
    gc = GarbledCircuit(num_wires)
    garbled_table, labels = gc.garble_circuit(circuit)

    print(f"\n混淆后表数量: {len(garbled_table)}")
    print(f"线数量: {len(labels)}")

    # 评估方
    ev = Evaluator(garbled_table, labels)

    # 设置输入（a=1, b=1, c=0, d=1）
    inputs = {0: labels[0][1], 1: labels[1][1], 2: labels[2][0], 3: labels[3][1]}
    ev.set_input_labels(inputs)

    # 评估
    results = ev.evaluate_circuit(circuit)

    # 获取输出值
    output_wire = 6
    output_label = results.get(output_wire)

    # 解码输出
    output_value = None
    if output_label == labels[output_wire][0]:
        output_value = 0
    elif output_label == labels[output_wire][1]:
        output_value = 1

    print(f"\n输入: a=1, b=1, c=0, d=1")
    print(f"期望输出: 1")
    print(f"实际输出: {output_value}")

    # 另一个测试
    print("\n=== 另一个测试 ===")
    inputs2 = {0: labels[0][1], 1: labels[1][0], 2: labels[2][1], 3: labels[3][1]}
    ev2 = Evaluator(garbled_table, labels)
    ev2.set_input_labels(inputs2)
    results2 = ev2.evaluate_circuit(circuit)
    output_label2 = results2.get(6)
    output_value2 = 1 if output_label2 == labels[6][1] else 0
    print(f"输入: a=1, b=0, c=1, d=1")
    print(f"期望: (1 AND 0) XOR (1 AND 1) = 0 XOR 1 = 1")
    print(f"实际输出: {output_value2}")

    print("\n混淆电路特性:")
    print("  混淆方（Garbler）：生成混淆电路和输入标签")
    print("  评估方（Evaluator）：获得混淆表和输出标签")
    print("  混淆表打乱：评估方无法区分哪个条目对应哪个输入组合")
    print("  应用：安全两方计算（Yao's Millionaires' Problem）")
