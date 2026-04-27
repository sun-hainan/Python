# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / causal_representation



本文件实现 causal_representation 相关的算法功能。

"""



from typing import List, Dict, Optional, Tuple

from dataclasses import dataclass, field

import numpy as np

import random





# =============================================================================

# 基础组件

# =============================================================================



@dataclass

class CausalFactor:

    """因果因子：表示一个独立的因果变量"""

    name: str  # 因子名称

    dim: int  # 维度

    value: float  # 当前值

    parents: List[str] = field(default_factory=list)  # 父因子列表



    def __repr__(self):

        return f"CausalFactor({self.name}={self.value:.3f})"





class StructuralMechanism:

    """

    结构因果机制



    描述因果因子之间的生成关系

    """



    def __init__(self, output_name: str, parent_names: List[str],

                 mechanism_func: callable):

        self.output_name = output_name

        self.parent_names = parent_names

        self.mechanism_func = mechanism_func



    def generate(self, parent_values: Dict[str, float]) -> float:

        """根据父因子的值生成当前因子的值"""

        if not self.parent_names:

            # 外生因子

            return self.mechanism_func()

        else:

            parent_vals = [parent_values[p] for p in self.parent_names]

            return self.mechanism_func(*parent_vals)





# =============================================================================

# 因果自编码器

# =============================================================================



class CausalRepresentationEncoder:

    """

    因果表示编码器



    将观测数据编码为因果因子表示

    """



    def __init__(self, input_dim: int, latent_dim: int):

        self.input_dim = input_dim

        self.latent_dim = latent_dim



        # 简化的编码器参数（使用随机初始化）

        self.weights_encoder = np.random.randn(latent_dim, input_dim) * 0.1

        self.bias_encoder = np.zeros(latent_dim)



    def encode(self, x: np.ndarray) -> np.ndarray:

        """

        编码：观测 -> 因果因子



        参数:

            x: 观测数据 (input_dim,)



        返回:

            因果因子表示 (latent_dim,)

        """

        # 线性编码 + 非线性激活（简化版本）

        z = np.dot(self.weights_encoder, x) + self.bias_encoder

        z = np.tanh(z)  # 激活函数

        return z





class CausalRepresentationDecoder:

    """

    因果表示解码器



    将因果因子解码为观测数据

    """



    def __init__(self, latent_dim: int, output_dim: int):

        self.latent_dim = latent_dim

        self.output_dim = output_dim



        # 简化解码器参数

        self.weights_decoder = np.random.randn(output_dim, latent_dim) * 0.1

        self.bias_decoder = np.zeros(output_dim)



    def decode(self, z: np.ndarray) -> np.ndarray:

        """

        解码：因果因子 -> 观测



        参数:

            z: 因果因子表示 (latent_dim,)



        返回:

            观测数据 (output_dim,)

        """

        x_reconstructed = np.dot(self.weights_decoder, z) + self.bias_decoder

        return x_reconstructed





class CausalVAE:

    """

    因果变分自编码器（Causal-VAE）



    结合因果结构和变分推断，学习解耦的因果表示



    核心思想：

        1. 潜在空间中的因果因子应该具有稀疏的依赖关系

        2. 干预一个因子应该只影响相关的结果变量

        3. 表示应该对因果干预具有不变性

    """



    def __init__(self, input_dim: int, latent_dim: int,

                 causal_graph: Optional[Dict[str, List[str]]] = None):

        self.input_dim = input_dim

        self.latent_dim = latent_dim

        self.causal_graph = causal_graph  # 因果图结构



        self.encoder = CausalRepresentationEncoder(input_dim, latent_dim)

        self.decoder = CausalRepresentationDecoder(latent_dim, input_dim)



        # 因果机制列表

        self.causal_mechanisms: Dict[str, StructuralMechanism] = {}



    def infer_causal_factors(self, x: np.ndarray) -> np.ndarray:

        """

        推断因果因子



        参数:

            x: 观测数据



        返回:

            因果因子值

        """

        return self.encoder.encode(x)



    def reconstruct(self, z: np.ndarray) -> np.ndarray:

        """

        从因果因子重建观测



        参数:

            z: 因果因子



        返回:

            重建的观测

        """

        return self.decoder.decode(z)



    def intervene(self, z: np.ndarray, intervention_factor: str,

                  intervention_value: float) -> np.ndarray:

        """

        对因果因子进行干预



        do(Z_i = z_i*) 只影响Z_i及其后代因子



        参数:

            z: 原始因果因子

            intervention_factor: 干预的因子索引

            intervention_value: 干预的值



        返回:

            干预后的因果因子

        """

        z_intervened = z.copy()

        z_intervened[int(intervention_factor.split('_')[1])] = intervention_value



        # 如果有因果图，还需要传播到后代

        if self.causal_graph:

            self._propagate_intervention(z_intervened, intervention_factor)



        return z_intervened



    def _propagate_intervention(self, z: np.ndarray, intervened_factor: str):

        """根据因果图传播干预效果"""

        if intervened_factor not in self.causal_graph:

            return



        # 简化版本：只更新直接子节点

        children = self.causal_graph.get(intervenved_factor, [])

        for child in children:

            child_idx = int(child.split('_')[1])

            # 假设子节点是由父节点线性组合得到

            if child in self.causal_mechanisms:

                mechanism = self.causal_mechanisms[child]

                parent_vals = {p: z[int(p.split('_')[1])] for p in mechanism.parent_names}

                z[child_idx] = mechanism.generate(parent_vals)





# =============================================================================

# 因果一致性损失

# =============================================================================



class CausalConsistencyLoss:

    """

    因果一致性损失函数



    确保学习到的表示满足因果性质：

        1. 干预不变性：干预一个因子不应影响不相关的因子

        2. 稀疏性：因果图应该是稀疏的

        3. 重构一致性：因果因子应能重建观测

    """



    @staticmethod

    def intervention_invariance_loss(z1: np.ndarray, z2: np.ndarray,

                                   intervened_dims: List[int]) -> float:

        """

        干预不变性损失



        干预某些维度后，未干预的维度应该保持不变



        参数:

            z1: 干预前的表示

            z2: 干预后的表示

            intervened_dims: 被干预的维度索引



        返回:

            不变损失值

        """

        unchanged_dims = [i for i in range(len(z1)) if i not in intervened_dims]

        invariance_loss = np.mean((z1[unchanged_dims] - z2[unchanged_dims]) ** 2)

        return invariance_loss



    @staticmethod

    def reconstruction_loss(x_orig: np.ndarray, x_reconstructed: np.ndarray) -> float:

        """重构损失"""

        return np.mean((x_orig - x_reconstructed) ** 2)



    @staticmethod

    def sparsity_loss(causal_graph: Dict[str, List[str]], beta: float = 0.01) -> float:

        """

        稀疏性损失



        参数:

            causal_graph: 因果图

            beta: 正则化系数



        返回:

            稀疏性损失值

        """

        num_edges = sum(len(children) for children in causal_graph.values())

        return beta * num_edges





# =============================================================================

# 因果图学习

# =============================================================================



class CausalGraphLearner:

    """

    因果图学习器



    从数据中学习因果图结构



    方法：

        1. PC算法：基于条件独立性测试

        2. GES算法：基于分数的贪婪搜索

        3. NOTEARS：基于连续优化的方法

    """



    def __init__(self, variables: List[str]):

        self.variables = variables

        self.n_vars = len(variables)

        self.var_to_idx = {v: i for i, v in enumerate(variables)}



        # 估计的因果图（邻接矩阵）

        self.graph: np.ndarray = np.zeros((self.n_vars, self.n_vars))



    def learn_pc(self, data: np.ndarray, alpha: float = 0.05) -> Dict[str, List[str]]:

        """

        PC算法学习因果图



        参数:

            data: 数据矩阵 (n_samples, n_vars)

            alpha: 显著性水平



        返回:

            因果图 {变量名: [子节点列表]}

        """

        print(f"[PC算法] 使用 {data.shape[0]} 个样本学习因果图")



        # 初始化：完全无向图

        adj_matrix = np.ones((self.n_vars, self.n_vars)) - np.eye(self.n_vars)



        # 逐步移除边（基于条件独立性测试）

        # 简化版本：使用相关系数作为条件独立性测试

        for i in range(self.n_vars):

            for j in range(i + 1, self.n_vars):

                if adj_matrix[i, j] == 0:

                    continue



                # 简化的条件独立性测试

                # 实际应该使用偏相关系数或统计测试

                corr = np.abs(np.corrcoef(data[:, i], data[:, j])[0, 1])

                if corr < alpha:

                    adj_matrix[i, j] = 0

                    adj_matrix[j, i] = 0



        # 定向边（简化版本：使用时间顺序或领域知识）

        # 这里使用启发式方法

        self._orient_edges(adj_matrix)



        # 转换为字典格式

        graph_dict = {v: [] for v in self.variables}

        for i in range(self.n_vars):

            for j in range(self.n_vars):

                if self.graph[i, j] == 1:

                    graph_dict[self.variables[i]].append(self.variables[j])



        return graph_dict



    def _orient_edges(self, adj_matrix: np.ndarray):

        """定向边（简化实现）"""

        # 简化的定向规则：假设索引较小的变量是原因

        for i in range(self.n_vars):

            for j in range(i + 1, self.n_vars):

                if adj_matrix[i, j] == 1:

                    # i -> j

                    self.graph[i, j] = 1

                elif adj_matrix[j, i] == 1:

                    # j -> i

                    self.graph[j, i] = 1



    def learn_notears(self, data: np.ndarray, lambda_param: float = 0.1) -> np.ndarray:

        """

        NOTEARS算法（MOU-Continuous Optimization）



        通过优化问题学习因果图：

            min 0.5 * ||X - XW||^2 + lambda * ||W||_1

            s.t. diag(W) = 0, W >= 0 (如果需要)



        参数:

            data: 数据矩阵

            lambda_param: L1正则化参数



        返回:

            因果邻接矩阵

        """

        n, d = data.shape



        # 简化的NOTEARS实现

        # 实际应该使用连续优化算法



        # 初始化W为单位矩阵

        W = np.eye(d)



        # 简化的迭代优化

        learning_rate = 0.01

        for iteration in range(100):

            # 计算残差

            residual = data - data @ W

            gradient = -data.T @ residual + lambda_param * np.sign(W)

            W = W - learning_rate * gradient



            # 确保无自环

            np.fill_diagonal(W, 0)



            # 阈值化

            W[np.abs(W) < 0.1] = 0



        self.graph = (np.abs(W) > 0.1).astype(float)

        return self.graph





# =============================================================================

# 测试代码

# =============================================================================



if __name__ == "__main__":

    print("=" * 60)

    print("因果表示学习测试")

    print("=" * 60)



    # 测试1：因果因子和结构机制

    print("\n【测试1：因果因子生成】")

    # 创建因果机制：Z = X + Y, X -> Z, Y -> Z

    mechanisms = {

        "X": StructuralMechanism("X", [], lambda: random.gauss(0, 1)),

        "Y": StructuralMechanism("Y", [], lambda: random.gauss(0, 1)),

        "Z": StructuralMechanism("Z", ["X", "Y"], lambda x, y: x + y + random.gauss(0, 0.1))

    }



    values = {}

    values["X"] = mechanisms["X"].generate({})

    values["Y"] = mechanisms["Y"].generate({})

    values["Z"] = mechanisms["Z"].generate(values)



    print(f"生成的因子值: X={values['X']:.3f}, Y={values['Y']:.3f}, Z={values['Z']:.3f}")



    # 测试2：因果VAE

    print("\n【测试2：因果变分自编码器】")

    input_dim = 10

    latent_dim = 4



    vae = CausalVAE(input_dim, latent_dim)



    # 生成随机数据

    np.random.seed(42)

    x_data = np.random.randn(100, input_dim)



    # 推断因果因子

    z_sample = vae.infer_causal_factors(x_data[0])

    print(f"原始观测维度: {input_dim}")

    print(f"因果因子维度: {len(z_sample)}")

    print(f"推断的因果因子: {z_sample}")



    # 重建

    x_reconstructed = vae.reconstruct(z_sample)

    recon_error = np.mean((x_data[0] - x_reconstructed) ** 2)

    print(f"重构误差: {recon_error:.4f}")



    # 测试3：干预

    print("\n【测试3：因果干预】")

    z_intervened = vae.intervene(z_sample, "factor_0", 10.0)

    print(f"原始因子: {z_sample}")

    print(f"干预后因子: {z_intervened}")



    # 测试4：因果一致性损失

    print("\n【测试4：因果一致性损失】")

    z1 = np.array([1.0, 2.0, 3.0, 4.0])

    z2 = np.array([10.0, 2.0, 3.0, 4.0])  # 只有第0维被干预

    intervened_dims = [0]



    invariance_loss = CausalConsistencyLoss.intervention_invariance_loss(z1, z2, intervened_dims)

    print(f"干预不变性损失: {invariance_loss:.6f} (应该接近0)")



    # 测试5：因果图学习

    print("\n【测试5：因果图学习（PC算法）】")

    variables = ["X", "Y", "Z"]

    learner = CausalGraphLearner(variables)



    # 生成具有因果关系的数据

    np.random.seed(42)

    n_samples = 500

    x = np.random.randn(n_samples)

    y = 2 * x + np.random.randn(n_samples) * 0.1

    z = x + y + np.random.randn(n_samples) * 0.1



    data = np.column_stack([x, y, z])

    learned_graph = learner.learn_pc(data, alpha=0.05)



    print("学习到的因果图:")

    for var, children in learned_graph.items():

        if children:

            print(f"  {var} -> {children}")

