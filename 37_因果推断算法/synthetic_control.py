# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / synthetic_control



本文件实现 synthetic_control 相关的算法功能。

"""



import numpy as np

import pandas as pd

from typing import List, Dict, Tuple, Optional

from scipy.optimize import minimize





class SyntheticControl:

    """

    合成控制法

    """

    

    def __init__(self, treatment_unit: int, control_units: List[int]):

        """

        初始化

        

        Args:

            treatment_unit: 处理单元索引

            control_units: 对照单元索引列表

        """

        self.treatment_unit = treatment_unit

        self.control_units = control_units

        self.weights = None

        

        # 拟合结果

        self.pre_treatment_fit = None

        self.effect = None

    

    def fit(self, data: np.ndarray, treatment_time: int) -> np.ndarray:

        """

        拟合合成控制

        

        Args:

            data: 面板数据 shape: (n_units, n_periods)

            treatment_time: 干预时间点

        

        Returns:

            权重向量

        """

        n_units, n_periods = data.shape

        

        # 干预前数据

        pre_data = data[:, :treatment_time]

        post_data = data[:, treatment_time:]

        

        # 处理单元的干预前值

        treated_pre = pre_data[self.treatment_unit]

        

        # 对照单元的干预前值

        control_pre = pre_data[self.control_units]

        

        # 优化：最小化处理单元与合成对照的差异

        def objective(w):

            synthetic = control_pre.T @ w

            return np.sum((treated_pre - synthetic) ** 2)

        

        # 约束：权重非负，和为1

        n_control = len(self.control_units)

        constraints = [

            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # 和为1

        ]

        bounds = [(0, 1)] * n_control  # 非负

        

        # 初始权重

        w0 = np.ones(n_control) / n_control

        

        # 优化

        result = minimize(objective, w0, method='SLSQP',

                         bounds=bounds, constraints=constraints)

        

        self.weights = result.x

        

        # 计算干预效应

        self._compute_effect(pre_data, post_data)

        

        return self.weights

    

    def _compute_effect(self, pre_data: np.ndarray, post_data: np.ndarray):

        """计算干预效应"""

        # 合成对照的干预前值

        treated_pre = pre_data[self.treatment_unit]

        control_pre = pre_data[self.control_units]

        synthetic_pre = control_pre.T @ self.weights

        

        # 干预前拟合质量

        self.pre_treatment_fit = np.sum((treated_pre - synthetic_pre) ** 2)

        

        # 合成对照的干预后值（反事实）

        synthetic_post = post_data[self.control_units].T @ self.weights

        

        # 干预后实际值

        treated_post = post_data[self.treatment_unit]

        

        # 干预效应

        self.effect = treated_post - synthetic_post





class SyntheticControlWithCovariates:

    """

    带协变量的合成控制

    """

    

    def __init__(self):

        self.weights = None

        self.covariate_weights = None

    

    def fit(self, data: np.ndarray, covariates: np.ndarray, 

            treatment_time: int) -> np.ndarray:

        """

        拟合

        

        Args:

            data: 面板数据

            covariates: 协变量

            treatment_time: 干预时间

        """

        # 简化的实现

        sc = SyntheticControl(0, list(range(1, data.shape[0])))

        return sc.fit(data, treatment_time)





class MultipleTreatmentSyntheticControl:

    """

    多处理单元的合成控制

    """

    

    def __init__(self, treatment_units: List[int], control_units: List[int]):

        self.treatment_units = treatment_units

        self.control_units = control_units

        self.weights = {}

    

    def fit(self, data: np.ndarray, treatment_time: int):

        """拟合"""

        for unit in self.treatment_units:

            remaining_units = [u for u in range(data.shape[0]) 

                              if u not in self.treatment_units or u == unit]

            

            sc = SyntheticControl(unit, remaining_units)

            sc.fit(data, treatment_time)

            

            self.weights[unit] = sc.weights





def demo_basic_synthetic_control():

    """演示合成控制法"""

    print("=== 合成控制法演示 ===\n")

    

    np.random.seed(42)

    

    # 面板数据

    n_units = 5

    n_periods = 30

    treatment_time = 20

    

    # 生成数据

    # 处理单元: Y = trend + treatment_effect

    # 对照单元: Y = trend + noise

    

    data = np.zeros((n_units, n_periods))

    

    # 共同趋势

    trend = np.linspace(1, 3, n_periods)

    

    # 处理单元

    treated_unit = 0

    data[treated_unit, :treatment_time] = trend[:treatment_time] + np.random.randn(treatment_time) * 0.2

    # 干预后

    treatment_effect = 1.0

    data[treated_unit, treatment_time:] = trend[treatment_time:] + treatment_effect + np.random.randn(n_periods - treatment_time) * 0.2

    

    # 对照单元

    for i in range(1, n_units):

        data[i] = trend + np.random.randn(n_periods) * 0.3

    

    print(f"数据: {n_units}个单元, {n_periods}个时间点")

    print(f"干预时间: 第{treatment_time}期")

    print(f"真实干预效应: {treatment_effect}")

    

    # 拟合合成控制

    sc = SyntheticControl(treated_unit, list(range(1, n_units)))

    weights = sc.fit(data, treatment_time)

    

    print(f"\n合成控制权重:")

    for i, w in enumerate(weights):

        print(f"  单元{i+1}: {w:.4f}")

    

    print(f"\n干预效应 (每期):")

    for t in range(treatment_time, min(treatment_time + 5, n_periods)):

        effect_idx = t - treatment_time

        if effect_idx < len(sc.effect):

            print(f"  t={t}: {sc.effect[effect_idx]:.4f}")

    

    print(f"\n平均干预效应: {np.mean(sc.effect):.4f}")





def demo_synthetic_control_with_covariates():

    """演示带协变量的合成控制"""

    print("\n=== 带协变量合成控制 ===\n")

    

    print("协变量的作用:")

    print("  - 帮助更好地预测反事实")

    print("  - 提高估计精度")

    print()

    

    print("常用协变量:")

    print("  - 人口统计特征")

    print("  - 经济指标")

    print("  - 地理特征")





def demo_placebo_test():

    """演示安慰剂检验"""

    print("\n=== 安慰剂检验 ===\n")

    

    print("安慰剂检验:")

    print("  - 对照单元应用同样的方法")

    print("  - 应该没有显著效应")

    print("  - 用于检验合成控制的可靠性")

    print()

    

    print("处理:")

    print("  - 删除处理单元")

    print("  - 用合成对照替代")

    print("  - 检查是否有类似效应")





def demo_visualization():

    """演示结果可视化"""

    print("\n=== 结果可视化 ===\n")

    

    print("合成控制结果图:")

    print()

    print("  Y轴: 结果变量")

    print("  X轴: 时间")

    print()

    print("  两条线:")

    print("    - 实线: 处理单元实际值")

    print("    - 虚线: 合成对照（反事实）")

    print()

    print("  垂直线: 干预时间点")

    print()

    print("  差距: 因果效应")





if __name__ == "__main__":

    print("=" * 60)

    print("合成控制法")

    print("=" * 60)

    

    # 基本演示

    demo_basic_synthetic_control()

    

    # 带协变量

    demo_synthetic_control_with_covariates()

    

    # 安慰剂检验

    demo_placebo_test()

    

    # 可视化

    demo_visualization()

    

    print("\n" + "=" * 60)

    print("合成控制法核心:")

    print("=" * 60)

    print("""

1. 方法:

   - 优化找到对照组权重

   - 最小化干预前预测误差

   - 干预后比较实际与反事实



2. 假设:

   - 平行趋势假设

   - 不存在交互效应

   - 对照组无污染



3. 优点:

   - 可用于面板数据

   - 无需对照组完全匹配

   - 提供个案效应估计



4. 局限:

   - 需要干预前数据

   - 无法处理多个处理单元（除非改进）

   - 依赖平行趋势假设

""")

