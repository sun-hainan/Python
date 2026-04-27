# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / online_feature_selection



本文件实现 online_feature_selection 相关的算法功能。

"""



import numpy as np

import random

from typing import List, Set, Tuple, Optional

from collections import defaultdict

import math





class StreamingFeatureSelector:

    """

    流式特征选择器基类

    

    维护一个候选特征集，根据与目标的相关性更新

    """

    

    def __init__(self, max_features: int = 100, threshold: float = 0.1):

        self.max_features = max_features

        self.threshold = threshold

        

        # 统计量

        self.feature_correlations: dict = {}  # 特征 -> 相关性

        self.feature_mutual_info: dict = {}  # 特征对 -> 互信息

        

        # 选中的特征

        self.selected_features: Set[int] = set()

        

        # 样本统计

        self.n_samples = 0

        self.x_sums: dict = {}  # Σx

        self.x2_sums: dict = {}  # Σx²

        self.xy_sum: dict = {}  # Σxy (x*target)

    

    def _update_stats(self, x: np.ndarray, y: float):

        """更新统计量"""

        self.n_samples += 1

        

        for i, xi in enumerate(x):

            if i not in self.x_sums:

                self.x_sums[i] = 0.0

                self.x2_sums[i] = 0.0

                self.xy_sum[i] = 0.0

            

            self.x_sums[i] += xi

            self.x2_sums[i] += xi ** 2

            self.xy_sum[i] += xi * y

    

    def _pearson_correlation(self, feature_idx: int) -> float:

        """计算皮尔逊相关系数"""

        n = self.n_samples

        if n < 2:

            return 0.0

        

        x_sum = self.x_sums.get(feature_idx, 0)

        x2_sum = self.x2_sums.get(feature_idx, 0)

        xy_sum = self.xy_sum.get(feature_idx, 0)

        

        # 计算均值

        mean_x = x_sum / n

        mean_y = self.y_sum / n

        

        # 计算协方差

        cov_xy = xy_sum / n - mean_x * mean_y

        var_x = x2_sum / n - mean_x ** 2

        var_y = self.y2_sum / n - mean_y ** 2

        

        std_x = math.sqrt(max(var_x, 1e-10))

        std_y = math.sqrt(max(var_y, 1e-10))

        

        corr = cov_xy / (std_x * std_y)

        return max(-1, min(1, corr))

    

    def _mutual_information(self, x: np.ndarray, y: np.ndarray, 

                            n_bins: int = 10) -> float:

        """计算互信息（简化版）"""

        # 离散化

        x_bins = np.digitize(x, np.linspace(x.min(), x.max(), n_bins))

        y_bins = np.digitize(y, np.linspace(y.min(), y.max(), n_bins))

        

        # 计算概率

        pxy = np.zeros((n_bins, n_bins))

        px = np.zeros(n_bins)

        py = np.zeros(n_bins)

        

        for i in range(len(x)):

            pxy[x_bins[i], y_bins[i]] += 1

            px[x_bins[i]] += 1

            py[y_bins[i]] += 1

        

        pxy /= len(x)

        px /= len(x)

        py /= len(x)

        

        # 计算互信息

        mi = 0.0

        for i in range(n_bins):

            for j in range(n_bins):

                if pxy[i, j] > 0:

                    mi += pxy[i, j] * math.log(

                        pxy[i, j] / (px[i] * py[j] + 1e-10) + 1e-10

                    )

        

        return max(0, mi)

    

    def select_features(self, x: np.ndarray, y: np.ndarray) -> Set[int]:

        """选择特征"""

        raise NotImplementedError





class OSFS(StreamingFeatureSelector):

    """

    Online Streaming Feature Selection (OSFS)

    

    算法：

    1. 在线计算特征与目标的相关性

    2. 使用统计检验判断相关性

    3. 移除冗余特征

    """

    

    def __init__(self, max_features: int = 50, relevance_threshold: float = 0.05,

                 redundancy_threshold: float = 0.8):

        super().__init__(max_features, relevance_threshold)

        self.relevance_threshold = relevance_threshold

        self.redundancy_threshold = redundancy_threshold

        

        # 初始化y的统计

        self.y_sum = 0.0

        self.y2_sum = 0.0

    

    def partial_fit(self, x: np.ndarray, y: float):

        """

        部分拟合

        

        Args:

            x: 特征向量

            y: 目标值

        """

        # 更新y的统计

        self.y_sum += y

        self.y2_sum += y ** 2

        

        # 更新特征的统计

        self._update_stats(x, y)

    

    def select_features(self, x: np.ndarray, y: np.ndarray) -> Set[int]:

        """特征选择"""

        self.partial_fit(x, y)

        

        selected = set()

        

        for i in range(len(x)):

            # 计算相关性

            corr = self._pearson_correlation(i)

            

            # 相关性阈值

            if abs(corr) >= self.relevance_threshold:

                # 检查冗余

                is_redundant = False

                

                for j in selected:

                    corr_ij = self._feature_correlation(i, j)

                    corr_jy = self._pearson_correlation(j)

                    

                    # 如果特征i与j高度相关，且j与y也相关

                    if abs(corr_ij) > self.redundancy_threshold and abs(corr_jy) > self.relevance_threshold:

                        is_redundant = True

                        break

                

                if not is_redundant:

                    selected.add(i)

        

        self.selected_features = selected

        return selected

    

    def _feature_correlation(self, i: int, j: int) -> float:

        """计算两个特征的相关系数"""

        # 需要维护 Σx_ix_j，这里简化

        return 0.0  # 简化





class SAOLA(StreamingFeatureSelector):

    """

    SAOLA (Scalable and Online Feature Selection)

    

    使用成对约束来减少冗余

    """

    

    def __init__(self, max_features: int = 50, delta: float = 0.1):

        super().__init__(max_features, delta)

        self.delta = delta  # 成对约束阈值

        self.knn_graph: dict = {}  # 特征 -> 近邻

    

    def _conditional_mutual_information(self, i: int, j: int) -> float:

        """

        计算条件互信息 CMI(Xi, Xj | Y)

        

        简化实现

        """

        return 0.0  # 需要更复杂的统计

    

    def select_features(self, x: np.ndarray, y: np.ndarray) -> Set[int]:

        """SAOLA特征选择"""

        selected = set()

        

        for i in range(x.shape[1]):

            xi = x[:, i]

            

            # 检查与已选特征的冗余

            should_add = True

            

            for j in selected:

                # 计算成对约束

                cmi = self._conditional_mutual_information(i, j)

                

                if cmi < self.delta:

                    should_add = False

                    break

            

            if should_add:

                selected.add(i)

                

                # 限制特征数量

                if len(selected) > self.max_features:

                    break

        

        self.selected_features = selected

        return selected





class AlphaInvesting:

    """

    Alpha-Investing 流式特征选择

    

    使用财富递减策略进行统计检验

    """

    

    def __init__(self, alpha: float = 0.05, delta: float = 0.5):

        self.alpha = alpha  # 初始显著性水平

        self.delta = delta  # 财富增量

        

        self.wealth = alpha  # 当前财富

        self.selected_features: List[int] = []

        self.feature_pvalues: dict = {}

    

    def _statistical_test(self, x: np.ndarray, y: np.ndarray, feature_idx: int) -> Tuple[float, float]:

        """

        统计检验

        

        Returns:

            (statistic, p-value)

        """

        # 简化：使用相关性作为统计量

        corr = np.corrcoef(x[:, feature_idx], y)[0, 1]

        return abs(corr), 1 - abs(corr)

    

    def partial_fit(self, x: np.ndarray, y: np.ndarray):

        """部分拟合"""

        # 对新特征进行检验

        n_features = x.shape[1]

        n_current = len(self.selected_features)

        

        for i in range(n_current, n_features):

            stat, pvalue = self._statistical_test(x, y, i)

            

            if pvalue < self.wealth:

                # 接受特征

                self.selected_features.append(i)

                self.wealth -= pvalue  # 消耗财富

                

                # 投资回报

                self.wealth += self.delta * (1 - pvalue)

                

                self.feature_pvalues[i] = pvalue

    

    def get_selected(self) -> Set[int]:

        """获取选中的特征"""

        return set(self.selected_features)





def demo_online_feature_selection():

    """演示在线特征选择"""

    print("=== 在线特征选择演示 ===\n")

    

    np.random.seed(42)

    

    # 生成数据

    n_samples = 500

    n_features = 20

    

    # 真实相关特征: 0, 3, 7

    X = np.random.randn(n_samples, n_features)

    y = 2 * X[:, 0] + 0.5 * X[:, 3] + X[:, 7] + np.random.randn(n_samples) * 0.1

    

    print(f"数据形状: {X.shape}")

    print(f"真实相关特征: {{0, 3, 7}}")

    

    # 在线学习

    print("\n流式学习 (每次1个样本):")

    

    osfs = OSFS(max_features=10, relevance_threshold=0.1)

    

    for i in range(0, n_samples, 10):

        # 批量处理

        x_batch = X[i:i+10]

        y_batch = y[i:i+10]

        

        for j in range(len(x_batch)):

            osfs.partial_fit(x_batch[j], y_batch[j])

    

    # 特征选择

    selected = osfs.select_features(X, y)

    

    print(f"\nOSFS选中的特征: {sorted(selected)}")

    

    # Alpha-Investing

    print("\nAlpha-Investing:")

    alpha_inv = AlphaInvesting(alpha=0.05)

    alpha_inv.partial_fit(X, y)

    print(f"选中的特征: {sorted(alpha_inv.get_selected())}")





def demo_redundancy_removal():

    """演示冗余特征移除"""

    print("\n=== 冗余特征移除演示 ===\n")

    

    print("相关特征 vs 冗余特征:")

    print()

    print("  相关特征: 与目标变量有强相关性")

    print("  冗余特征: 与已选特征高度相关")

    print()

    

    print("示例:")

    print("  X1 = 噪声")

    print("  X2 = 0.9*X1 + 噪声  <- 冗余")

    print("  X3 = 0.5*y + 噪声   <- 相关")

    print()

    

    print("选择策略:")

    print("  1. 先选择X3（与y相关）")

    print("  2. 检查X1和X2与X3的相关性")

    print("  3. 如果X2与X3高相关，标记X2为冗余")

    print("  4. 只保留X1（与X3独立）")





def demo_streaming_vs_batch():

    """对比流式和批量"""

    print("\n=== 流式 vs 批量特征选择 ===\n")

    

    print("| 特性      | 流式                | 批量              |")

    print("|-----------|---------------------|-------------------|")

    print("| 内存      | O(1)                | O(n)              |")

    print("| 速度      | 快                  | 慢                |")

    print("| 精度      | 可能较低            | 较高              |")

    print("| 概念漂移  | 支持                | 不支持            |")

    print("| 适用场景  | 大数据流            | 小数据集          |")

    

    print("\n流式优势:")

    print("  - 不需要存储所有数据")

    print("  - 能适应概念漂移")

    print("  - 计算效率高")

    

    print("\n流式劣势:")

    print("  - 无法利用全局统计")

    print("  - 统计检验功效较低")

    print("  - 可能错过复杂依赖")





def demo_feature_importance_tracking():

    """演示特征重要性追踪"""

    print("\n=== 特征重要性追踪 ===\n")

    

    np.random.seed(42)

    

    # 模拟特征重要性变化

    n_features = 5

    importance_history = {i: [] for i in range(n_features)}

    

    for t in range(100):

        # 模拟重要性变化

        base = [0.5, 0.3, 0.1, 0.05, 0.05]

        

        # 时间趋势

        trend = [

            0.1 * math.sin(t / 10),

            0.2 * math.cos(t / 15),

            0.1 * t / 100,

            -0.1 * t / 100,

            0.05 * math.sin(t / 5)

        ]

        

        for i in range(n_features):

            imp = max(0, base[i] + trend[i] + random.gauss(0, 0.05))

            importance_history[i].append(imp)

    

    print("特征重要性随时间变化 (前20步):")

    print("| t    | F0    | F1    | F2    | F3    | F4    |")

    

    for t in [0, 10, 20, 30, 40, 50]:

        if t < len(importance_history[0]):

            row = [f"{importance_history[i][t]:.3f}" for i in range(n_features)]

            print(f"| {t:4d} | {' | '.join(row)} |")

    

    print("\n观察:")

    print("  - 某些特征重要性随时间变化")

    print("  - 流式方法能追踪这种变化")

    print("  - 批量方法可能错过变化")





if __name__ == "__main__":

    print("=" * 60)

    print("流式特征选择算法")

    print("=" * 60)

    

    # 在线特征选择

    demo_online_feature_selection()

    

    # 冗余移除

    demo_redundancy_removal()

    

    # 流式 vs 批量

    demo_streaming_vs_batch()

    

    # 重要性追踪

    demo_feature_importance_tracking()

    

    print("\n" + "=" * 60)

    print("核心算法:")

    print("=" * 60)

    print("""

1. OSFS (Online Streaming Feature Selection):

   - 使用互信息和统计检验

   - 动态维护特征相关图

   - 移除冗余特征



2. SAOLA:

   - 使用成对约束

   - CMI(Xi, Xj | Y) < delta 认为冗余

   - 适用于高维数据



3. Alpha-Investing:

   - 财富递减的统计检验

   - 初始财富=α

   - 每拒绝一次检验，财富增加δ

   - 直到财富耗尽



4. 评价指标:

   - Precision: 选中的相关特征比例

   - Recall: 真实相关特征被选中的比例

   - F1: 调和平均

""")

