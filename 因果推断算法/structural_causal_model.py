# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / structural_causal_model



本文件实现 structural_causal_model 相关的算法功能。

"""



from typing import Dict, List, Optional, Set, Tuple, Any

from dataclasses import dataclass, field

from enum import Enum

import numpy as np

import random





# =============================================================================

# 数据结构定义

# =============================================================================



@dataclass

class StructuralEquation:

    """

    结构方程：定义变量如何由其父变量决定



    例如：X = f(parents_X) + noise

    """

    variable: str  # 变量名

    parents: List[str]  # 父变量列表

    function: callable  # 结构方程函数

    noise_std: float = 0.0  # 噪声标准差



    def evaluate(self, values: Dict[str, float]) -> float:

        """计算当前变量的值"""

        parent_values = [values[p] for p in self.parents]

        result = self.function(*parent_values)

        if self.noise_std > 0:

            result += random.gauss(0, self.noise_std)

        return result





@dataclass

class CausalGraph:

    """因果图：表示变量之间的因果关系"""

    nodes: List[str]  # 节点列表

    edges: List[Tuple[str, str]]  # 有向边列表 (父节点, 子节点)

    adjacencies: Dict[str, List[str]] = field(default_factory=dict)  # 邻接表：节点 -> 子节点

    reverse_adj: Dict[str, List[str]] = field(default_factory=dict)  # 逆邻接表：节点 -> 父节点



    def __post_init__(self):

        # 构建邻接表

        self.adjacencies = {n: [] for n in self.nodes}

        self.reverse_adj = {n: [] for n in self.nodes}

        for parent, child in self.edges:

            self.adjacencies[parent].append(child)

            self.reverse_adj[child].append(parent)



    def get_parents(self, node: str) -> List[str]:

        """获取节点的父节点"""

        return self.reverse_adj.get(node, [])



    def get_children(self, node: str) -> List[str]:

        """获取节点的子节点"""

        return self.adjacencies.get(node, [])



    def get_descendants(self, node: str) -> Set[str]:

        """获取节点的所有后代"""

        descendants = set()

        queue = list(self.adjacencies.get(node, []))

        while queue:

            n = queue.pop(0)

            if n not in descendants:

                descendants.add(n)

                queue.extend(self.adjacencies.get(n, []))

        return descendants



    def get_ancestors(self, node: str) -> Set[str]:

        """获取节点的所有祖先"""

        ancestors = set()

        queue = list(self.reverse_adj.get(node, []))

        while queue:

            n = queue.pop(0)

            if n not in ancestors:

                ancestors.add(n)

                queue.extend(self.reverse_adj.get(n, []))

        return ancestors



    def is_d_separated(self, x: str, y: str, z: Set[str]) -> bool:

        """

        检查x和y在给定条件集z下是否d-分离



        d-分离是两个节点之间不存在有效路径的条件



        参数:

            x: 节点1

            y: 节点2

            z: 条件集（观测变量）



        返回:

            True= d-分离（无因果关系）, False= d-连接

        """

        # 简化的d-分离检查（完整实现需要考虑链式、叉式、反叉式结构）

        ancestors_z = set()

        for node in z:

            ancestors_z |= self.get_ancestors(node)

        ancestors_z |= set(z)



        # 检查x到y的路径是否被z阻断

        return y not in self.get_descendants(x) and y not in ancestors_z





# =============================================================================

# 结构因果模型

# =============================================================================



class SCM:

    """

    结构因果模型（SCM）



    SCM由以下部分组成：

        1. 外生变量（ exogenous variables）：没有父节点的变量

        2. 内生变量（endogenous variables）：有父节点的变量

        3. 结构方程：定义每个内生变量如何由其父变量决定

        4. 因果图：可视化表示



    SCM示例：

        X <- u_x (外生，无父节点)

        Y <- 2*X + u_y (内生，父节点为X)

        Z <- Y + X + u_z (内生，父节点为X和Y)

    """



    def __init__(self, name: str = "SCM"):

        self.name = name

        self.graph: Optional[CausalGraph] = None  # 因果图

        self.structural_equations: Dict[str, StructuralEquation] = {}  # 结构方程

        self.exogenous_variables: Set[str] = set()  # 外生变量（无父节点）

        self.endogenous_variables: Set[str] = set()  # 内生变量（有父节点）



    def add_variable(self, name: str, parents: Optional[List[str]] = None,

                    equation_func: Optional[callable] = None, noise_std: float = 0.0):

        """

        添加变量及其结构方程



        参数:

            name: 变量名

            parents: 父变量列表（None表示外生变量）

            equation_func: 结构方程函数

            noise_std: 噪声标准差

        """

        if parents is None or len(parents) == 0:

            # 外生变量

            self.exogenous_variables.add(name)

            if equation_func is not None:

                self.structural_equations[name] = StructuralEquation(

                    variable=name,

                    parents=[],

                    function=equation_func,

                    noise_std=noise_std

                )

        else:

            # 内生变量

            self.endogenous_variables.add(name)

            if equation_func is None:

                raise ValueError(f"内生变量 {name} 必须提供结构方程")

            self.structural_equations[name] = StructuralEquation(

                variable=name,

                parents=parents,

                function=equation_func,

                noise_std=noise_std

            )



    def build_graph(self):

        """从变量和结构方程构建因果图"""

        all_nodes = self.exogenous_variables | self.endogenous_variables

        edges = []

        for var_name, eq in self.structural_equations.items():

            for parent in eq.parents:

                edges.append((parent, var_name))



        self.graph = CausalGraph(nodes=list(all_nodes), edges=edges)



    def sample(self, n_samples: int = 1) -> List[Dict[str, float]]:

        """

        从SCM中采样



        使用顺序蒙特卡洛：先计算外生变量，再依次计算内生变量



        参数:

            n_samples: 样本数量



        返回:

            样本列表，每个样本是一个 {变量名: 值} 的字典

        """

        if self.graph is None:

            self.build_graph()



        samples = []



        # 拓扑排序确定计算顺序

        # 外生变量先计算，然后按依赖顺序计算内生变量

        topo_order = list(self.exogenous_variables)

        remaining = set(self.endogenous_variables)



        while remaining:

            for var in list(remaining):

                eq = self.structural_equations[var]

                if all(p in topo_order for p in eq.parents):

                    topo_order.append(var)

                    remaining.remove(var)

                    break



        for _ in range(n_samples):

            values = {}

            for var_name in topo_order:

                if var_name in self.exogenous_variables:

                    # 外生变量：从分布采样或使用固定值

                    if var_name in self.structural_equations:

                        values[var_name] = self.structural_equations[var_name].evaluate({})

                    else:

                        values[var_name] = random.gauss(0, 1)

                else:

                    # 内生变量：使用结构方程计算

                    values[var_name] = self.structural_equations[var_name].evaluate(values)



            samples.append(values)



        return samples



    def do_intervention(self, intervention: Dict[str, float]) -> 'SCM':

        """

        执行do干预，返回新的SCM



        do(X=x0) 表示将变量X固定为值x0，移除X的所有入边



        参数:

            intervention: 干预字典 {变量名: 固定值}



        返回:

            干预后的新SCM

        """

        new_scm = SCM(name=f"{self.name}_do({intervention})")



        # 复制原图的边（但移除被干预变量的入边）

        new_edges = []

        for parent, child in self.graph.edges:

            if child not in intervention:

                new_edges.append((parent, child))



        # 重建变量

        new_nodes = list(self.graph.nodes)

        new_scm.graph = CausalGraph(nodes=new_nodes, edges=new_edges)



        # 复制结构方程，但移除被干预变量

        for var_name, eq in self.structural_equations.items():

            if var_name not in intervention:

                new_eq = StructuralEquation(

                    variable=var_name,

                    parents=[p for p in eq.parents if p not in intervention],

                    function=eq.function,

                    noise_std=eq.noise_std

                )

                new_scm.structural_equations[var_name] = new_eq

                if len(new_eq.parents) == 0:

                    new_scm.exogenous_variables.add(var_name)

                else:

                    new_scm.endogenous_variables.add(var_name)



        # 添加被干预变量为外生变量（固定值）

        for var_name, value in intervention.items():

            new_scm.exogenous_variables.add(var_name)

            new_scm.structural_equations[var_name] = StructuralEquation(

                variable=var_name,

                parents=[],

                function=lambda: value,

                noise_std=0.0

            )



        return new_scm



    def counterfactual(self, observation: Dict[str, float],

                      intervention: Dict[str, float]) -> Dict[str, float]:

        """

        反事实推理



        给定观察到的结果，计算在另一种干预下的结果



        参数:

            observation: 观察到的变量值

            intervention: 假设的干预



        返回:

            反事实结果

        """

        # 第一步：给定观察，计算外生变量的值

        # 这需要"反演"结构方程（简化版本使用迭代求解）



        # 第二步：在干预下计算结果

        intervened_scm = self.do_intervention(intervention)



        # 使用观察初始化外生变量

        init_values = dict(observation)



        # 计算干预后的结果

        result = {}

        for var_name in intervened_scm.exogenous_variables:

            if var_name in observation:

                result[var_name] = observation[var_name]

            elif var_name in intervened_scm.structural_equations:

                result[var_name] = intervened_scm.structural_equations[var_name].evaluate({})



        # 计算内生变量

        for var_name in intervened_scm.endogenous_variables:

            if var_name not in intervention:

                result[var_name] = intervened_scm.structural_equations[var_name].evaluate(result)



        return result





# =============================================================================

# 因果效应计算

# =============================================================================



class CausalEffect:

    """因果效应计算工具"""



    @staticmethod

    def compute_average_treatment_effect(scm: SCM, treatment: str, outcome: str,

                                        n_samples: int = 1000) -> float:

        """

        计算平均处理效应（ATE）



        ATE = E[Y|do(T=1)] - E[Y|do(T=0)]



        参数:

            scm: 因果模型

            treatment: 处理变量

            outcome: 结果变量

            n_samples: 样本数



        返回:

            平均处理效应估计值

        """

        # E[Y|do(T=1)]

        scm_do_1 = scm.do_intervention({treatment: 1.0})

        samples_1 = scm_do_1.sample(n_samples)

        y_do_1 = np.mean([s.get(outcome, 0) for s in samples_1])



        # E[Y|do(T=0)]

        scm_do_0 = scm.do_intervention({treatment: 0.0})

        samples_0 = scm_do_0.sample(n_samples)

        y_do_0 = np.mean([s.get(outcome, 0) for s in samples_0])



        return y_do_1 - y_do_0



    @staticmethod

    def identify_causal_effect(graph: CausalGraph, treatment: str, outcome: str) -> bool:

        """

        检查因果效应是否可识别（使用后门准则）



        参数:

            graph: 因果图

            treatment: 处理变量

            outcome: 结果变量



        返回:

            True=可识别，False=不可识别

        """

        # 后门准则：存在一组节点Z，使得：

        # 1. Z阻断了所有从T到Y的后门路径

        # 2. Z不包含T的后代



        # 简化的可识别性检查

        ancestors_t = graph.get_ancestors(treatment)



        # 检查是否存在后门路径

        # 如果T和Y在图中d-分离（给定祖先），则可识别

        return graph.is_d_separated(treatment, outcome, ancestors_t)





# =============================================================================

# 测试代码

# =============================================================================



if __name__ == "__main__":

    print("=" * 60)

    print("结构因果模型（SCM）测试")

    print("=" * 60)



    # 创建示例SCM：X -> Y -> Z, X -> Z

    # 这是一个经典的混淆结构，X是混淆变量

    scm = SCM("confounding_example")



    # 添加变量

    scm.add_variable("X", parents=None, equation_func=lambda: random.gauss(0, 1))

    scm.add_variable("Y", parents=["X"],

                    equation_func=lambda x: 2 * x + random.gauss(0, 0.1))

    scm.add_variable("Z", parents=["X", "Y"],

                    equation_func=lambda x, y: x + y + random.gauss(0, 0.1))



    # 构建因果图

    scm.build_graph()



    print("\n【测试1：因果图结构】")

    print(f"节点: {scm.graph.nodes}")

    print(f"边: {scm.graph.edges}")

    print(f"X的子节点: {scm.graph.get_children('X')}")

    print(f"Z的父节点: {scm.graph.get_parents('Z')}")

    print(f"Z的后代: {scm.graph.get_descendants('Z')}")



    print("\n【测试2：采样】")

    samples = scm.sample(n_samples=5)

    for i, s in enumerate(samples):

        print(f"  样本{i+1}: X={s['X']:.3f}, Y={s['Y']:.3f}, Z={s['Z']:.3f}")



    print("\n【测试3：do干预】")

    scm_do_x1 = scm.do_intervention({"X": 1.0})

    print(f"干预后的图边: {scm_do_x1.graph.edges}")

    samples_intervened = scm_do_x1.sample(n_samples=3)

    for i, s in enumerate(samples_intervened):

        print(f"  do(X=1) 样本{i+1}: X={s['X']:.3f}, Y={s['Y']:.3f}, Z={s['Z']:.3f}")



    print("\n【测试4：平均处理效应】")

    ate = CausalEffect.compute_average_treatment_effect(scm, "Y", "Z", n_samples=500)

    print(f"ATE(Y -> Z) = {ate:.4f}")

    print(f"理论值（因为Y=2X）≈ 2.0")



    print("\n【测试5：反事实推理】")

    # 观察：X=1, Y=3, Z=5

    observation = {"X": 1.0, "Y": 3.0, "Z": 5.0}

    # 假设：do(X=2)

    counterfactual = scm.counterfactual(observation, {"X": 2.0})

    print(f"观察: {observation}")

    print(f"反事实 do(X=2): {counterfactual}")

