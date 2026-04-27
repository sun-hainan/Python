# -*- coding: utf-8 -*-

"""

算法实现：安全多方计算 / garbled_circuits



本文件实现 garbled_circuits 相关的算法功能。

"""



import random

from typing import List, Tuple, Dict





class GarbledCircuit:

    """混淆电路"""



    def __init__(self, n_inputs: int):

        """

        参数：

            n_inputs: 输入数量

        """

        self.n_inputs = n_inputs

        self.gates = []



    def _generate_labels(self) -> Tuple[str, str]:

        """

        生成0和1的标签（混淆密钥）



        返回：(label_0, label_1)

        """

        label_0 = str(random.randint(0, 2**128))

        label_1 = str(random.randint(0, 2**128))

        return label_0, label_1



    def garble_gate(self, gate_type: str, input_labels: List[Tuple[str, str]]) -> Dict:

        """

        混淆单个门



        参数：

            gate_type: 门类型（AND, XOR等）

            input_labels: 输入标签



        返回：混淆后的门

        """

        # 生成输出标签

        out_label_0, out_label_1 = self._generate_labels()



        # 简化：只用真值表

        garbled_table = {}



        for inputs in [(0, 0), (0, 1), (1, 0), (1, 1)]:

            # 计算输出

            if gate_type == "AND":

                output = inputs[0] and inputs[1]

            elif gate_type == "XOR":

                output = inputs[0] ^ inputs[1]

            elif gate_type == "OR":

                output = inputs[0] or inputs[1]

            else:

                output = inputs[0]



            # 加密输出

            out_label = out_label_0 if output == 0 else out_label_1

            garbled_table[inputs] = out_label



        return {

            'type': gate_type,

            'input_labels': input_labels,

            'output_labels': (out_label_0, out_label_1),

            'garbled_table': garbled_table

        }



    def build_circuit(self, circuit_description: List[str]) -> List[Dict]:

        """

        构建混淆电路



        参数：

            circuit_description: 电路描述



        返回：混淆后的电路

        """

        circuit = []



        for gate_desc in circuit_description:

            # 简化：解析描述并混淆

            gate_type = gate_desc.split('_')[0]

            labels = [self._generate_labels() for _ in range(2)]

            garbled_gate = self.garble_gate(gate_type, labels)

            circuit.append(garbled_gate)



        self.gates = circuit

        return circuit



    def evaluate_circuit(self, circuit: List[Dict],

                        garbled_inputs: List[str]) -> List[str]:

        """

        评估混淆电路



        参数：

            circuit: 混淆电路

            garbled_inputs: 混淆后的输入



        返回：混淆后的输出

        """

        # 简化：随机输出

        return [random.choice(['0', '1']) for _ in range(len(circuit))]





def yao_protocol_steps():

    """Yao协议步骤"""

    print("=== Yao协议步骤 ===")

    print()

    print("1. 电路生成")

    print("   - 将函数转化为布尔电路")

    print("   - 发送方混淆电路")

    print()

    print("2. 输入编码")

    print("   - 发送方输入用标签编码")

    print("   - 接收方通过OT获取标签")

    print()

    print("3. 评估")

    print("   - 接收方按顺序评估门")

    print("   - 解密输出标签得到结果")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 混淆电路测试 ===\n")



    # 创建电路

    circuit_desc = ["AND_gate", "XOR_gate", "OR_gate"]



    gc = GarbledCircuit(n_inputs=2)



    # 构建电路

    circuit = gc.build_circuit(circuit_desc)



    print(f"电路门数: {len(circuit)}")

    print()



    print("混淆后的电路：")

    for i, gate in enumerate(circuit):

        print(f"  门 {i+1}: {gate['type']}")

        print(f"    输入标签: {len(gate['input_labels'])} 对")

        print(f"    输出标签: {len(gate['output_labels'])} 个")



    print()



    # 评估

    garbled_inputs = ['label_0', 'label_1']

    outputs = gc.evaluate_circuit(circuit, garbled_inputs)



    print(f"输出: {outputs}")



    print()

    yao_protocol_steps()



    print()

    print("说明：")

    print("  - Yao的混淆电路是MPC的里程碑")

    print("  - 理论上可以计算任意函数")

    print("  - 但开销仍然较高")

