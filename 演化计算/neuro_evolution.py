"""
神经进化 (NEAT)
==========================================

【原理】
同时进化神经网络的拓扑结构和权重。
使用种系历史标记追踪基因 innovation。

【时间复杂度】O(generations × population)
【空间复杂度】O(population × connections)
"""

import random
from typing import List


class Node:
    """神经网络节点"""
    def __init__(self, node_id, node_type='hidden'):
        self.id = node_id
        self.type = node_type  # input, hidden, output


class Connection:
    """连接基因"""
    def __init__(self, in_node, out_node, weight, enabled=True, innovation=0):
        self.in_node = in_node
        self.out_node = out_node
        self.weight = weight
        self.enabled = enabled
        self.innovation = innovation  # 全局唯一ID


class NEATGenome:
    """
    NEAT基因组

    【基因类型】
    - 节点基因：定义网络结构
    - 连接基因：定义连接权重
    """

    def __init__(self, n_input, n_output):
        self.n_input = n_input
        self.n_output = n_output
        self.nodes = []
        self.connections = []
        self.next_node_id = 0
        self.next_innovation = 0

        # 添加输入输出节点
        for i in range(n_input):
            self.nodes.append(Node(i, 'input'))
        for i in range(n_output):
            self.nodes.append(Node(self.next_node_id, 'output'))
            self.next_node_id += 1

    def add_connection(self, in_node, out_node):
        """添加连接"""
        # 检查是否已存在
        for c in self.connections:
            if c.in_node == in_node and c.out_node == out_node:
                return

        conn = Connection(in_node, out_node, random.uniform(-1, 1),
                        innovation=self.next_innovation)
        self.connections.append(conn)
        self.next_innovation += 1

    def add_node(self, conn_index):
        """添加节点（分裂连接）"""
        conn = self.connections[conn_index]
        conn.enabled = False

        node_id = self.next_node_id
        self.nodes.append(Node(node_id, 'hidden'))
        self.next_node_id += 1

        # 新输入连接
        self.add_connection(conn.in_node, node_id)
        # 新输出连接
        self.add_connection(node_id, conn.out_node)

    def mutate(self):
        """变异操作"""
        if random.random() < 0.8:
            # 权重突变
            for c in self.connections:
                if random.random() < 0.9:
                    c.weight += random.gauss(0, 0.1)
                    c.weight = max(-1, min(1, c.weight))

        if random.random() < 0.05:
            # 添加连接
            nodes = [n.id for n in self.nodes if n.type != 'output']
            outputs = [n.id for n in self.nodes if n.type != 'input']
            if nodes and outputs:
                self.add_connection(random.choice(nodes),
                                  random.choice(outputs))

        if random.random() < 0.03:
            # 添加节点
            if self.connections:
                self.add_node(random.randint(0, len(self.connections) - 1))


class NEAT:
    """NEAT算法"""

    def __init__(self, n_input, n_output, pop_size=100):
        self.n_input = n_input
        self.n_output = n_output
        self.pop_size = pop_size
        self.population = [NEATGenome(n_input, n_output) for _ in range(pop_size)]

    def evaluate(self, genome, fitness_func):
        """评估基因组"""
        return fitness_func(genome)

    def evolve(self, fitness_func, generations=100):
        """进化"""
        for gen in range(generations):
            # 评估
            fitnesses = [self.evaluate(g, fitness_func) for g in self.population]

            # 排序
            sorted_pop = sorted(zip(fitnesses, self.population),
                             key=lambda x: x[0], reverse=True)

            # 保留精英
            new_pop = [sorted_pop[0][1]]

            # 交叉和变异
            while len(new_pop) < self.pop_size:
                parent1, parent2 = random.choices(
                    [g for _, g in sorted_pop[:20]],
                    weights=range(20, 0, -1)
                )[0], random.choice([g for _, g in sorted_pop[:20]])[1]

                # 简化交叉
                child = parent1 if random.random() < 0.5 else parent2
                child = NEATGenome(self.n_input, self.n_output)
                child.nodes = parent1.nodes[:]
                child.connections = parent1.connections[:]

                child.mutate()
                new_pop.append(child)

            self.population = new_pop

            if gen % 20 == 0:
                print(f"Gen {gen}: best_fitness={max(fitnesses):.4f}")

        return max(zip(fitnesses, self.population), key=lambda x: x[0])


if __name__ == "__main__":
    print("NEAT测试")

    def simple_fitness(genome):
        """简化适应度函数"""
        return len(genome.connections) * 0.01

    neat = NEAT(n_input=2, n_output=1)
    best_fit, best = neat.evolve(simple_fitness, generations=50)
    print(f"最优适应度: {best_fit:.4f}, 连接数: {len(best.connections)}")
