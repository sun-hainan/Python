# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / do_calculus



本文件实现 do_calculus 相关的算法功能。

"""



import numpy as np

from typing import List, Dict, Set, Optional, Tuple

from collections import defaultdict

import math





class CausalGraph:

    """

    因果图（DAG）

    """

    

    def __init__(self):

        self.nodes: List[str] = []

        self.parents: Dict[str, Set[str]] = defaultdict(set)

        self.children: Dict[str, Set[str]] = defaultdict(set)

        self.descendants: Dict[str, Set[str]] = defaultdict(set)

        self.ancestors: Dict[str, Set[str]] = defaultdict(set)

    

    def add_edge(self, parent: str, child: str):

        """添加有向边 parent -> child"""

        if parent not in self.nodes:

            self.nodes.append(parent)

        if child not in self.nodes:

            self.nodes.append(child)

        

        self.parents[child].add(parent)

        self.children[parent].add(child)

        

        # 更新祖先/后代

        self._update_ancestors(child, parent)

        self._update_descendants(parent, child)

    

    def _update_ancestors(self, node: str, new_ancestor: str):

        """更新祖先关系"""

        self.ancestors[node].add(new_ancestor)

        for parent in self.parents[node]:

            self.ancestors[node].add(parent)

            self._update_ancestors(parent, new_ancestor)

    

    def _update_descendants(self, node: str, new_descendant: str):

        """更新后代关系"""

        self.descendants[node].add(new_descendant)

        for child in self.children[node]:

            self.descendants[node].add(child)

            self._update_descendants(child, new_descendant)

    

    def get_ancestors(self, node: str) -> Set[str]:

        """获取节点的祖先"""

        return self.ancestors[node]

    

    def get_descendants(self, node: str) -> Set[str]:

        """获取节点的后代"""

        return self.descendants[node]

    

    def is_d_separated(self, x: str, y: str, z: Set[str]) -> bool:

        """

        判断x和y在给定z下是否d-分离

        

        Args:

            x: 节点x

            y: 节点y

            z: 条件集

        

        Returns:

            True表示d-分离

        """

        # 简化的d-分离检查

        # 构建阻断路径的集合

        

        def blocked(path, observed):

            """判断路径是否被阻断"""

            if len(path) < 2:

                return True

            

            for i in range(1, len(path)):

                prev = path[i-1]

                curr = path[i]

                next_node = path[i+1] if i+1 < len(path) else None

                

                # 检查是否是碰撞器

                if curr not in observed and prev != x and curr != y:

                    # 碰撞器节点未被观察

                    return False

                

                # 检查是否是中介

                if next_node and curr in observed:

                    if prev in self.parents.get(curr, set()) and next_node in self.children.get(curr, set()):

                        return True

            

            return True

        

        return True  # 简化





class DoCalculus:

    """

    Do-Calculus规则实现

    

    用于识别因果效应和进行因果推理

    """

    

    def __init__(self, graph: CausalGraph):

        self.graph = graph

    

    def rule_1(self, y: str, x: str, z: Set[str], w: Set[str]) -> bool:

        """

        规则1: 插入/删除观测

        

        P(Y | do(X), Z, W) = P(Y | do(X), W) 如果 Y ⊥ Z | X, W, 非X的后代

        

        Returns:

            True表示可以简化

        """

        # 检查Z是否与Y在给定X,W下d-分离

        non_descendants_x = self.graph.nodes - self.graph.get_descendants(x)

        

        return y in non_descendants_x

    

    def rule_2(self, y: str, x: str, z: Set[str]) -> bool:

        """

        规则2: 行动/观察交换

        

        P(Y | do(X), do(Z), W) = P(Y | do(X), Z, W) 

        如果 Z ⊥ 非Z后代 | X, 非Z的祖先

        

        Returns:

            True表示可以交换

        """

        return True  # 简化

    

    def rule_3(self, y: str, x: str, z: str) -> bool:

        """

        规则3: 伪干预

        

        P(Y | do(X), do(Z), W) = P(Y | do(X), W)

        如果 Z 是 X 的后代且 Z 与 Y 在 X 的干预下无直接连接

        

        Returns:

            True表示可以简化

        """

        if z not in self.graph.get_descendants(x):

            return False

        

        return True





class CausalEffectIdentifier:

    """

    因果效应识别器

    

    使用do-calculus识别P(Y|do(X))

    """

    

    def __init__(self, graph: CausalGraph):

        self.graph = graph

    

    def identify(self, x: str, y: str) -> Optional[str]:

        """

        识别P(Y|do(X))

        

        Args:

            x: 处理变量

            y: 结果变量

        

        Returns:

            识别的表达式，或None如果不可识别

        """

        # 前门准则检查

        front_door = self._check_front_door(x, y)

        if front_door:

            return front_door

        

        # 后门准则检查

        back_door = self._check_back_door(x, y)

        if back_door:

            return back_door

        

        return None

    

    def _check_front_door(self, x: str, y: str) -> Optional[str]:

        """

        前门准则

        

        条件：

        1. X到Y的所有路径都经过M（中介）

        2. X到M没有直接边（除非另有约定）

        3. M阻塞了所有从X到Y的伪路径

        4. 没有从X到M的隐藏混杂

        """

        # 简化实现

        return f"P(Y|do(X)) = Σ_m P(M=m|do(X)) * P(Y|do(M=m))"

    

    def _check_back_door(self, x: str, y: str) -> Optional[str]:

        """

        后门准则

        

        找到阻塞X和Y之间所有后门路径的集合Z

        

        Returns:

            后门调整公式

        """

        # 简化

        return f"P(Y|do(X)) = Σ_z P(Y|X, Z=z) * P(Z=z)"





class BackdoorAdjustment:

    """

    后门调整公式计算

    """

    

    def __init__(self, graph: CausalGraph):

        self.graph = graph

    

    def compute(self, data: Dict[str, np.ndarray], 

                x: str, y: str, z_vars: List[str]) -> np.ndarray:

        """

        计算后门调整

        

        P(Y|do(X)) = Σ_z P(Y|X, Z=z) * P(Z=z)

        

        Args:

            data: 数据

            x: 处理变量

            y: 结果变量

            z_vars: 调整变量

        

        Returns:

            因果效应估计

        """

        # 获取数据

        X = data[x]

        Y = data[y]

        Z = np.column_stack([data[z] for z in z_vars])

        

        n = len(X)

        

        # 计算P(Z=z)

        Z_unique = np.unique(Z, axis=0)

        p_z = {}

        for z_val in Z_unique:

            mask = np.all(Z == z_val, axis=1)

            p_z[tuple(z_val)] = mask.sum() / n

        

        # 计算因果效应

        effect = 0.0

        

        for z_val, p_z_val in p_z.items():

            # P(Y|X, Z=z)

            mask = np.all(Z == np.array(z_val), axis=1)

            

            if mask.sum() > 0:

                # 分层估计

                p_y_given_xz = []

                

                for x_val in np.unique(X):

                    x_mask = mask & (X == x_val)

                    if x_mask.sum() > 0:

                        p_y_given_xz.append((x_val, Y[x_mask].mean()))

                

                # 加权求和

                for x_val, mean_y in p_y_given_xz:

                    p_x_given_z = (X == x_val).sum() / n / p_z_val

                    effect += p_z_val * p_x_given_z * mean_y

        

        return np.array([effect])





def demo_do_calculus():

    """演示do-calculus"""

    print("=== Do-Calculus演示 ===\n")

    

    print("Do-Calculus三个规则:")

    print()

    

    print("规则1 - 插入/删除观测:")

    print("  P(Y | do(X), Z, W) = P(Y | do(X), W)")

    print("  如果 Y ⊥ Z | X, W, 非X的后代")

    

    print("\n规则2 - 行动/观察交换:")

    print("  P(Y | do(X), do(Z), W) = P(Y | do(X), Z, W)")

    print("  如果 Z ⊥ 非Z后代 | X, 非Z的祖先")

    

    print("\n规则3 - 伪干预:")

    print("  P(Y | do(X), do(Z), W) = P(Y | do(X), W)")

    print("  如果 Z 是 X 的后代")





def demo_front_door():

    """演示前门准则"""

    print("\n=== 前门准则演示 ===\n")

    

    print("问题设置:")

    print("  X -> M -> Y")

    print("  Z -> X")

    print("  Z -> Y (混杂)")

    print()

    

    print("前门准则:")

    print("  条件1: M阻塞所有X到Y的直接路径")

    print("  条件2: 没有从X到M的直接箭头")

    print("  条件3: 所有从X到Y的伪路径都经过M")

    print()

    

    print("识别公式:")

    print("  P(Y|do(X)) = Σ_m P(M=m|do(X)) * Σ_x' P(Y|M=m, X=x') * P(X=x')")

    print()

    

    print("解释:")

    print("  - 首先计算通过中介M的因果效应")

    print("  - 然后对X求和（边缘化）")





def demo_back_door():

    """演示后门准则"""

    print("\n=== 后门准则演示 ===\n")

    

    print("问题设置:")

    print("  Z -> X -> Y")

    print("  Z -> Y (后门路径)")

    print()

    

    print("后门准则:")

    print("  找到阻塞Z到Y后门路径的集合")

    print()

    

    print("调整公式:")

    print("  P(Y|do(X)) = Σ_z P(Y|X, Z=z) * P(Z=z)")

    print()

    

    print("解释:")

    print("  - 对混杂变量Z进行分层")

    print("  - 在每层中计算处理效应")

    print("  - 加权求和")





def demo_causal_effect():

    """演示因果效应计算"""

    print("\n=== 因果效应计算演示 ===\n")

    

    np.random.seed(42)

    

    # 生成数据

    n = 1000

    

    # Z -> X -> Y

    Z = np.random.randn(n)

    X = 0.5 * Z + 0.3 * np.random.randn(n)

    Y = 0.4 * X + 0.2 * Z + 0.1 * np.random.randn(n)

    

    data = {'X': X, 'Y': Y, 'Z': Z}

    

    print("数据:")

    print("  Z -> X -> Y")

    print("  Z -> Y (混杂)")

    

    print("\n观察相关:")

    corr_xy = np.corrcoef(X, Y)[0, 1]

    print(f"  Corr(X, Y) = {corr_xy:.4f}")

    

    print("\n后门调整后:")

    print("  P(Y|do(X)) = Σ_z P(Y|X, Z=z) * P(Z=z)")

    

    # 计算后门调整

    ba = BackdoorAdjustment(CausalGraph())

    effect = ba.compute(data, 'X', 'Y', ['Z'])

    print(f"  估计因果效应: {effect[0]:.4f}")





def demo_intervention():

    """演示干预"""

    print("\n=== 干预 vs 观察 ===\n")

    

    print("观察:")

    print("  P(Y | X=1) = 干预后看到X=1的概率")

    print("  可能受混杂影响")

    

    print("\n干预:")

    print("  P(Y | do(X=1)) = 强制设置X=1后的Y的概率")

    print("  不受X<-Z->Y混杂影响")

    print()

    

    print("例子:")

    print("  观察: 冰淇凌销量高时溺水多")

    print("  干预: 强制增加冰淇凌销量")

    print("  干预后溺水不会增加（除非有直接因果）")





if __name__ == "__main__":

    print("=" * 60)

    print("Do-Calculus 因果推断")

    print("=" * 60)

    

    # do-calculus

    demo_do_calculus()

    

    # 前门准则

    demo_front_door()

    

    # 后门准则

    demo_back_door()

    

    # 因果效应计算

    demo_causal_effect()

    

    # 干预vs观察

    demo_intervention()

    

    print("\n" + "=" * 60)

    print("Do-Calculus核心:")

    print("=" * 60)

    print("""

1. 干预分布 P(Y|do(X)):

   - 不同于条件分布 P(Y|X)

   - 表示强制设置X后的Y分布

   - 是因果推断的核心



2. 三个规则:

   - 规则1: 可删除无关观测

   - 规则2: 可交换干预和观察

   - 规则3: 可移除伪干预



3. 识别策略:

   - 前门准则: 通过中介

   - 后门准则: 调整混杂



4. 不可识别情况:

   - 没有可识别的因果效应

   - 需要额外假设或实验

""")

