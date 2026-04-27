# -*- coding: utf-8 -*-

"""

算法实现：21_量子计算 / qram



本文件实现 qram 相关的算法功能。

"""



import numpy as np

from collections import defaultdict





class BucketBrigadeQRAM:

    """

    Bucket Brigade QRAM 模型

    

    结构：

    - 完全二叉树

    - 叶节点存储经典数据

    - 内部节点作为路由

    - 路径上的qubit处于相干叠加态

    

    操作：

    1. 准备地址叠加态 Σ_n α_n |n⟩

    2. 对每个层级，应用路由操作

    3. 到达叶节点后加载数据

    4. 逆向操作恢复

    

    复杂度：

    - 深度：O(log N)

    - 门数：O(N log N) 总体

    """

    

    def __init__(self, data):

        """

        参数：

            data: 长度为 N = 2^n 的经典数据向量

        """

        self.data = np.array(data)

        self.n = int(np.log2(len(data)))

        self.N = len(data)

        

        if 2 ** self.n != self.N:

            raise ValueError(f"数据长度必须是 2 的幂，当前 {self.N}")

    

    def memory_access(self, address_qubits):

        """

        模拟 QRAM 内存访问

        

        参数：

            address_qubits: 地址量子比特数

        

        返回：加载的数据概率分布

        """

        # 准备地址叠加态

        n_addr = len(address_qubits)

        dim = 2 ** n_addr

        

        # 振幅：均匀叠加

        amplitudes = np.ones(dim, dtype=complex) / np.sqrt(dim)

        

        # 模拟路由过程

        # 每层：应用路由门

        for level in range(n_addr):

            # 第 level 层有 2^level 个路由节点

            n_nodes = 2 ** level

            

            # 更新振幅（简化模拟）

            new_amplitudes = np.zeros(dim, dtype=complex)

            

            for addr in range(dim):

                # 路由决策（叠加）

                if (addr >> (n_addr - 1 - level)) & 1 == 0:

                    # 向左

                    new_amplitudes[addr] += amplitudes[addr] / np.sqrt(2)

                else:

                    # 向右

                    new_amplitudes[addr] += amplitudes[addr] / np.sqrt(2)

            

            amplitudes = new_amplitudes

        

        # 计算测量结果概率

        probs = np.abs(amplitudes) ** 2

        

        # 数据加载后的结果

        result_probs = np.zeros(self.N)

        

        for addr in range(dim):

            result_probs[addr] = probs[addr] * (abs(self.data[addr]) ** 2)

        

        return result_probs

    

    def parallel_query(self, n_queries):

        """

        模拟并行查询

        

        量子优势：

        - 经典：O(N) 查询

        - 量子：O(sqrt(N)) 使用 Grover

        """

        # 经典随机查询

        classical_cost = self.N

        

        # 量子查询（Grover）

        quantum_cost = int(np.sqrt(self.N))

        

        return classical_cost, quantum_cost

    

    def circuit_depth(self):

        """

        电路深度

        

        树深度 = n = log₂(N)

        加上逆操作 = 2n

        """

        return 2 * self.n

    

    def gate_count(self):

        """

        门数量估计

        

        每个路由节点需要：

        - 1 个控制门

        - 2 个单比特门

        """

        # 内部节点数 = N - 1

        n_internal = self.N - 1

        # 每节点约 3 个门

        return n_internal * 3





class QuantumAddressingMode:

    """

    量子寻址模式

    

    三种模式：

    1. Sum（相加模式）：|a⟩|b⟩ -> |a⟩|a+b⟩

    2. Multiply（相乘模式）：|a⟩|b⟩ -> |a⟩|a*b⟩  

    3. Compare（比较模式）：|a⟩|b⟩ -> |a⟩|a>b⟩

    """

    

    def __init__(self, n_bits):

        self.n = n_bits

        self.dim = 2 ** n_bits

    

    def sum_mode(self, vector_a, vector_b):

        """

        量子相加模式

        

        Σ_a α_a |a⟩ -> Σ_a α_a |a⟩ ⊕ Σ_b β_b |b⟩

        """

        result = np.zeros(self.dim, dtype=complex)

        

        for a in range(self.dim):

            for b in range(self.dim):

                c = (a + b) % self.dim

                result[c] += np.abs(vector_a[a]) * np.abs(vector_b[b])

        

        result = result / np.linalg.norm(result)

        return result

    

    def multiply_mode(self, vector_a, vector_b):

        """

        量子相乘模式（模 2^n）

        """

        result = np.zeros(self.dim, dtype=complex)

        

        for a in range(self.dim):

            for b in range(self.dim):

                c = (a * b) % self.dim

                result[c] += np.abs(vector_a[a]) * np.abs(vector_b[b])

        

        result = result / np.linalg.norm(result)

        return result

    

    def superposition_preparation(self, probs):

        """

        基于概率分布制备叠加态

        

        输入：概率分布 p(x)

        输出：叠加态 Σ_x sqrt(p(x)) |x⟩

        

        方法：量子幅度编码

        """

        n_qubits = int(np.ceil(np.log2(len(probs))))

        

        # 归一化概率

        probs = np.array(probs) / sum(probs)

        

        # 振幅 = sqrt(概率)

        amplitudes = np.sqrt(probs)

        

        # 填充到 2^n

        dim = 2 ** n_qubits

        padded = np.zeros(dim, dtype=complex)

        padded[:len(amplitudes)] = amplitudes

        

        # 归一化

        padded = padded / np.linalg.norm(padded)

        

        return padded





def fidelity(state1, state2):

    """计算两个量子态的保真度"""

    return np.abs(np.conj(state1) @ state2) ** 2





if __name__ == "__main__":

    print("=" * 55)

    print("量子随机存取存储器（QRAM）")

    print("=" * 55)

    

    # Bucket Brigade 示例

    print("\n1. Bucket Brigade QRAM")

    print("-" * 40)

    

    N = 8

    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])

    

    qram = BucketBrigadeQRAM(data)

    

    print(f"数据大小: {qram.N} = 2^{qram.n}")

    print(f"数据: {data}")

    

    n_addr_bits = 3

    print(f"\n地址量子比特数: {n_addr_bits}")

    

    result_probs = qram.memory_access(list(range(n_addr_bits)))

    

    print(f"\n内存访问结果概率:\n{result_probs.round(4)}")

    

    print(f"\n电路深度: {qram.circuit_depth()}")

    print(f"门数量估计: {qram.gate_count()}")

    

    c_cost, q_cost = qram.parallel_query(1)

    print(f"\n并行查询成本：经典 O({c_cost}), 量子 O({q_cost})")

    

    # 寻址模式

    print("\n2. 量子寻址模式")

    print("-" * 40)

    

    mode = QuantumAddressingMode(4)

    

    vec_a = np.ones(16) / 4

    vec_b = np.ones(16) / 4

    

    sum_result = mode.sum_mode(vec_a, vec_b)

    mul_result = mode.multiply_mode(vec_a, vec_b)

    

    print(f"输入 A (均匀叠加): {vec_a[:4]}...")

    print(f"输入 B (均匀叠加): {vec_b[:4]}...")

    print(f"求和结果 (叠加): {sum_result[:4].round(3)}...")

    print(f"相乘结果 (叠加): {mul_result[:4].round(3)}...")

    

    # 振幅编码

    print("\n3. 量子幅度编码")

    print("-" * 40)

    

    probs = [0.5, 0.3, 0.1, 0.1]

    superposition = mode.superposition_preparation(probs)

    

    print(f"概率分布: {probs}")

    print(f"叠加态振幅: {superposition.round(4)}")

    print(f"验证（振幅平方和）: {np.sum(np.abs(superposition)**2):.4f}")

