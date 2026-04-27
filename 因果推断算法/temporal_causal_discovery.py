# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / temporal_causal_discovery



本文件实现 temporal_causal_discovery 相关的算法功能。

"""



from typing import List, Dict, Optional, Tuple, Set

from dataclasses import dataclass, field

import numpy as np

import random





# =============================================================================

# 数据结构定义

# =============================================================================



@dataclass

class TimeSeries:

    """时间序列数据"""

    name: str  # 变量名

    values: np.ndarray  # 时间序列值

    timestamps: Optional[np.ndarray] = None  # 时间戳



    def __post_init__(self):

        if self.timestamps is None:

            self.timestamps = np.arange(len(self.values))



    def lag(self, k: int) -> 'TimeSeries':

        """返回滞后k个时间点的序列"""

        return TimeSeries(

            name=f"{self.name}_lag{k}",

            values=self.values[k:] if k > 0 else self.values,

            timestamps=self.timestamps[k:] if k > 0 else self.timestamps

        )



    def get_window(self, start: int, end: int) -> np.ndarray:

        """获取指定窗口的数据"""

        return self.values[start:end]





@dataclass

class CausalRelation:

    """因果关系"""

    cause: str  # 原因变量

    effect: str  # 结果变量

    lag: int  # 延迟（原因在effect之前lag个时间步）

    strength: float  # 因果强度（0-1）

    confidence: float  # 置信度



    def __repr__(self):

        return f"{self.cause} --({self.lag})--> {self.effect} (strength={self.strength:.3f})"





# =============================================================================

# 时序因果发现算法

# =============================================================================



class TemporalCausalDiscovery:

    """

    时序因果发现框架



    支持多种时序因果发现方法

    """



    def __init__(self, variables: List[str], max_lag: int = 5):

        self.variables = variables

        self.max_lag = max_lag

        self.n_vars = len(variables)

        self.var_to_idx = {v: i for i, v in enumerate(variables)}



        # 存储时间序列数据

        self.time_series_data: Dict[str, np.ndarray] = {}



        # 发现的因果关系

        self.causal_relations: List[CausalRelation] = []



    def add_time_series(self, name: str, values: np.ndarray):

        """添加时间序列数据"""

        self.time_series_data[name] = values



    def discover_granger(self, alpha: float = 0.05) -> List[CausalRelation]:

        """

        Granger因果检验



        如果X有助于预测Y（在包含Y的过去后），

        则称X Granger-cause Y



        参数:

            alpha: 显著性水平



        返回:

            发现的因果关系列表

        """

        print(f"[Granger因果检验] max_lag={self.max_lag}")



        relations = []

        for target_var in self.variables:

            y = self.time_series_data[target_var]



            for cause_var in self.variables:

                if cause_var == target_var:

                    continue



                x = self.time_series_data[cause_var]



                # 检验X是否改善Y的预测

                # 简化版本：使用相关系数

                for lag in range(1, self.max_lag + 1):

                    # 计算滞后相关性

                    y_lagged = y[lag:]

                    x_lagged = x[:len(x) - lag]



                    if len(x_lagged) < 10:

                        continue



                    corr = np.corrcoef(x_lagged, y_lagged)[0, 1]



                    # 使用F检验的简化版本

                    # 实际应该比较受限和非受限模型的残差

                    f_stat = corr ** 2 / (1 - corr ** 2) * (len(x_lagged) - 2)



                    # 临界值（简化）

                    critical_value = 3.84  # chi-square(1) at 0.05



                    if f_stat > critical_value:

                        strength = min(abs(corr), 1.0)

                        relations.append(CausalRelation(

                            cause=cause_var,

                            effect=target_var,

                            lag=lag,

                            strength=strength,

                            confidence=1.0 - alpha

                        ))



        self.causal_relations = relations

        return relations



    def discover_pcmci(self, data: np.ndarray, alpha: float = 0.05) -> np.ndarray:

        """

        PCMCI算法（Peter-Clark-MCI）



        因果发现的条件独立性方法



        参数:

            data: 时间序列数据 (n_times, n_vars)

            alpha: 显著性水平



        返回:

            因果图邻接矩阵

        """

        print(f"[PCMCI] 数据形状: {data.shape}")



        n_times, n_vars = data.shape

        graph = np.zeros((n_vars, n_vars))



        # 步骤1：PC阶段 - 学习骨架（无向因果图）

        # 简化版本：使用条件独立性测试

        for i in range(n_vars):

            for j in range(i + 1, n_vars):

                # 简化：只测试无条件独立

                corr = np.corrcoef(data[:, i], data[:, j])[0, 1]



                # 如果相关性显著，认为存在边

                if abs(corr) > 0.1:

                    # 在时间序列中，j是i的后继

                    # 检查滞后相关性

                    for lag in range(1, min(self.max_lag, n_times // 2)):

                        x_lagged = data[:-lag, i]

                        y_current = data[lag:, j]



                        if len(x_lagged) > 10:

                            corr_lag = np.corrcoef(x_lagged, y_current)[0, 1]

                            if abs(corr_lag) > 0.2:

                                graph[i, j] = 1

                                break



        return graph



    def discover_ccm(self, target_var: str, cause_var: str,

                    lag: int = 1, embedding_dim: int = 3) -> float:

        """

        收敛交叉映射（Convergent Cross Mapping）



        用于检测非线性因果关系



        参数:

            target_var: 目标变量

            cause_var: 原因变量

            lag: 滞后时间步

            embedding_dim: 嵌入维度



        返回:

            CCM相关性（因果强度估计）

        """

        # 提取时间序列

        y = self.time_series_data[target_var]

        x = self.time_series_data[cause_var]



        n = len(y)

        if n < embedding_dim * 2:

            return 0.0



        # 构建影子流形（时间序列的滞后坐标嵌入）

        def build_shadowmanifold(series: np.ndarray, dim: int) -> np.ndarray:

            """构建影子流形"""

            n = len(series)

            max_delay = dim - 1

            manifold = []

            for i in range(max_delay, n):

                # 滞后坐标嵌入

                point = [series[i - d] for d in range(max_delay, -1, -1)]

                manifold.append(point)

            return np.array(manifold)



        # 构建两个流形

        M_y = build_shadowmanifold(y, embedding_dim)

        M_x = build_shadowmanifold(x, embedding_dim)



        # 计算交叉映射

        # M_y 应该能够预测 X（如果 X 导致 Y）

        def cross_mapping(M_source, M_target) -> float:

            """交叉映射"""

            n_m = len(M_target)

            predictions = []



            for i in range(len(M_source)):

                # 找到M_target中最接近M_source[i]的点

                distances = np.linalg.norm(M_target - M_source[i], axis=1)

                nearest_indices = np.argsort(distances)[:embedding_dim]



                # 加权平均来预测当前值

                weights = 1.0 / (distances[nearest_indices] + 1e-10)

                weights = weights / weights.sum()



                # 简化：用最近邻的当前值加权预测

                if i < len(M_target):

                    prediction = M_target[i, 0]  # 简化的预测值

                    predictions.append(prediction)



            if len(predictions) < 10:

                return 0.0



            # 计算预测能力

            return np.mean(predictions)



        # 计算因果强度

        # 如果X导致Y，那么从Y的过去应该能预测X的当前

        ccm_y_to_x = cross_mapping(M_y[:-lag], M_x[lag:]) if lag < len(M_y) else 0.0

        ccm_x_to_y = cross_mapping(M_x[:-lag], M_y[lag:]) if lag < len(M_x) else 0.0



        # CCM相关：使用预测误差的比值

        strength = abs(ccm_x_to_y - ccm_y_to_x) if ccm_x_to_y > 0 else 0.0



        return min(strength, 1.0)





# =============================================================================

# TCDF算法实现

# =============================================================================



class TCDF(TemporalCausalDiscovery):

    """

    时序因果发现网络（Temporal Causal Discovery Framework）



    使用注意力机制的深度学习方法发现时序因果关系



    核心思想：

        1. 使用1D卷积提取时序特征

        2. 使用注意力机制识别因果滞后

        3. 自动选择最优滞后

    """



    def __init__(self, variables: List[str], max_lag: int = 5):

        super().__init__(variables, max_lag)

        self.attention_weights: Dict[Tuple[str, str], np.ndarray] = {}



    def discover_with_attention(self, data: np.ndarray,

                               learning_rate: float = 0.01,

                               n_iterations: int = 100) -> List[CausalRelation]:

        """

        使用注意力机制发现时序因果



        参数:

            data: 时间序列数据 (n_times, n_vars)

            learning_rate: 学习率

            n_iterations: 迭代次数



        返回:

            因果关系列表

        """

        print(f"[TCDF注意力机制] 发现时序因果关系")



        n_times, n_vars = data.shape

        relations = []



        # 简化的注意力权重学习

        # 实际应该使用神经网络

        attention_scores = np.random.rand(n_vars, n_vars, self.max_lag) * 0.1



        # 简化的梯度下降

        for iteration in range(n_iterations):

            # 计算当前注意力分数

            for i in range(n_vars):

                for j in range(n_vars):

                    if i == j:

                        continue



                    # 计算j对i的注意力（考虑滞后）

                    for lag in range(1, self.max_lag + 1):

                        if lag < n_times:

                            x_lagged = data[:-lag, i]

                            y_current = data[lag:, j]



                            if len(x_lagged) > 10:

                                corr = np.corrcoef(x_lagged, y_current)[0, 1]

                                # 更新注意力分数

                                attention_scores[i, j, lag - 1] += learning_rate * corr



        # 从注意力权重提取因果关系

        for i in range(n_vars):

            for j in range(n_vars):

                if i == j:

                    continue



                # 找到最大注意力对应的滞后

                max_lag_idx = np.argmax(attention_scores[i, j])

                max_score = attention_scores[i, j, max_lag_idx]



                if max_score > 0.3:  # 阈值

                    relations.append(CausalRelation(

                        cause=self.variables[i],

                        effect=self.variables[j],

                        lag=max_lag_idx + 1,

                        strength=max_score,

                        confidence=max_score

                    ))



                    self.attention_weights[(self.variables[i], self.variables[j])] = \

                        attention_scores[i, j]



        self.causal_relations = relations

        return relations





# =============================================================================

# 因果滞后网络

# =============================================================================



class CausalLagNetwork:

    """

    因果滞后网络



    表示变量之间的时序因果关系

    """



    def __init__(self):

        self.nodes: List[str] = []  # 变量名

        self.lag_edges: Dict[Tuple[str, str], List[int]] = {}  # (原因, 结果) -> 滞后列表



    def add_relation(self, cause: str, effect: str, lag: int):

        """添加因果滞后边"""

        if cause not in self.nodes:

            self.nodes.append(cause)

        if effect not in self.nodes:

            self.nodes.append(effect)



        key = (cause, effect)

        if key not in self.lag_edges:

            self.lag_edges[key] = []



        if lag not in self.lag_edges[key]:

            self.lag_edges[key].append(lag)

            self.lag_edges[key].sort()



    def get_max_lag(self, cause: str, effect: str) -> int:

        """获取从cause到effect的最大滞后"""

        key = (cause, effect)

        if key not in self.lag_edges:

            return 0

        return max(self.lag_edges[key])



    def get_total_effect(self, cause: str) -> Set[str]:

        """获取cause能影响的所有变量（通过任意滞后）"""

        effects = set()

        for (c, e), lags in self.lag_edges.items():

            if c == cause:

                effects.add(e)

        return effects





# =============================================================================

# 测试代码

# =============================================================================



if __name__ == "__main__":

    print("=" * 60)

    print("时序因果发现测试")

    print("=" * 60)



    np.random.seed(42)



    # 创建示例时间序列数据

    # X -> Y (滞后2), Y -> Z (滞后1)

    n_times = 500

    t = np.arange(n_times)



    # 生成时间序列

    x = np.sin(0.1 * t) + np.random.randn(n_times) * 0.1  # X

    y = np.zeros(n_times)

    for i in range(2, n_times):

        y[i] = 0.8 * x[i - 2] + 0.2 * y[i - 1] + np.random.randn() * 0.1  # Y = f(X_{t-2})

    z = np.zeros(n_times)

    for i in range(1, n_times):

        z[i] = 0.7 * y[i - 1] + 0.3 * z[i - 1] + np.random.randn() * 0.1  # Z = f(Y_{t-1})



    print("\n【测试1：Granger因果检验】")

    tcd = TemporalCausalDiscovery(["X", "Y", "Z"], max_lag=5)

    tcd.add_time_series("X", x)

    tcd.add_time_series("Y", y)

    tcd.add_time_series("Z", z)



    relations = tcd.discover_granger(alpha=0.05)

    print("发现的因果关系:")

    for rel in relations:

        print(f"  {rel}")



    print("\n【测试2：TCDF注意力机制】")

    data = np.column_stack([x, y, z])

    tcdf = TCDF(["X", "Y", "Z"], max_lag=5)

    tcdf.add_time_series("X", x)

    tcdf.add_time_series("Y", y)

    tcdf.add_time_series("Z", z)



    relations_tcdf = tcdf.discover_with_attention(data, n_iterations=50)

    print("TCDF发现的因果关系:")

    for rel in relations_tcdf:

        print(f"  {rel}")



    print("\n【测试3：因果滞后网络】")

    lag_network = CausalLagNetwork()



    for rel in relations:

        lag_network.add_relation(rel.cause, rel.effect, rel.lag)



    print(f"节点: {lag_network.nodes}")

    print(f"滞后边:")

    for (cause, effect), lags in lag_network.lag_edges.items():

        print(f"  {cause} -> {effect}: 滞后{lags}")



    print("\n【测试4：收敛交叉映射（CCM）】")

    tcd2 = TemporalCausalDiscovery(["X", "Y"], max_lag=3)

    tcd2.add_time_series("X", x)

    tcd2.add_time_series("Y", y)



    ccm_strength = tcd2.discover_ccm("Y", "X", lag=2)

    print(f"CCM因果强度 (X -> Y, lag=2): {ccm_strength:.4f}")



    ccm_strength_back = tcd2.discover_ccm("X", "Y", lag=2)

    print(f"CCM因果强度 (Y -> X, lag=2): {ccm_strength_back:.4f}")

