# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / anomaly_detection_ts



本文件实现 anomaly_detection_ts 相关的算法功能。

"""



import numpy as np

from scipy import stats

from typing import Tuple, Optional, List





def grubbs_test(y: np.ndarray, alpha: float = 0.05) -> Tuple[int, float, float]:

    """

    格拉布斯检验（单异常值检测）

    

    H0: 数据中不存在异常值

    H1: 数据中存在至少一个异常值

    

    参数:

        y: 数据数组

        alpha: 显著性水平

    

    返回:

        (异常值索引, G统计量, 临界值)

    """

    n = len(y)

    if n < 3:

        return -1, 0.0, 0.0

    

    y_mean = np.mean(y)

    y_std = np.std(y, ddof=1)

    

    if y_std < 1e-10:

        return -1, 0.0, 0.0

    

    # 计算每个点的格拉布斯统计量

    abs_deviations = np.abs(y - y_mean)

    max_idx = np.argmax(abs_deviations)

    G = abs_deviations[max_idx] / y_std

    

    # 计算临界值（t分布）

    t_critical = stats.t.ppf(1 - alpha / (2 * n), n - 2)

    G_critical = (n - 1) / np.sqrt(n) * np.sqrt(t_critical ** 2 / (n - 2 + t_critical ** 2))

    

    return max_idx, G, G_critical





def esd_test(y: np.ndarray, max_outliers: int = 10, alpha: float = 0.05) -> dict:

    """

    广义极端学生化偏差检验（ESD）

    

    迭代检测多个异常值，每次移除检测到的异常值后重新检验

    

    参数:

        y: 时间序列数据

        max_outliers: 最大检测异常值个数

        alpha: 显著性水平

    

    返回:

        检测结果字典

    """

    n = len(y)

    y_copy = y.copy().astype(float)

    

    outliers_indices = []

    G_values = []

    critical_values = []

    

    for k in range(1, min(max_outliers + 1, n // 2 + 1)):

        # 格拉布斯检验

        idx, G, G_crit = grubbs_test(y_copy[:n - k + 1], alpha)

        

        G_values.append(G)

        critical_values.append(G_crit)

        

        if G > G_crit:

            # 找到异常值，移除它（用剩余数据的均值替代）

            outliers_indices.append(idx)

            y_copy[idx] = np.mean(y_copy[:n - k + 1])

        else:

            # 无更多异常值，停止

            break

    

    return {

        'outliers_indices': outliers_indices,

        'G_statistics': G_values,

        'critical_values': critical_values,

        'n_outliers': len(outliers_indices)

    }





class IsolationAnomalyDetector:

    """

    基于隔离森林思想的异常检测（简化版）

    

    核心思想：异常点更容易被随机隔离

    使用递归分割构建二叉树，异常点深度较浅

    

    参数:

        window_size: 滑动窗口大小

        threshold: 异常分数阈值

        n_trees: 树的数量

    """

    

    def __init__(self, window_size: int = 50, threshold: float = 0.8, n_trees: int = 100):

        self.window_size = window_size

        self.threshold = threshold

        self.n_trees = n_trees

        self.trees = []

    

    def _build_tree(self, data: np.ndarray, depth: int = 0, max_depth: int = 10) -> dict:

        """递归构建隔离树"""

        n = len(data)

        

        # 终止条件

        if depth >= max_depth or n <= 1:

            return {'type': 'leaf', 'size': n}

        

        # 随机选择分割维度（这里用一维，所以总是选择第一个）

        # 随机选择分割值

        min_val = np.min(data)

        max_val = np.max(data)

        

        if min_val == max_val:

            return {'type': 'leaf', 'size': n}

        

        split_val = np.random.uniform(min_val, max_val)

        

        # 分割数据

        left_mask = data <= split_val

        right_mask = ~left_mask

        

        left_data = data[left_mask]

        right_data = data[right_mask]

        

        return {

            'type': 'node',

            'split_val': split_val,

            'left': self._build_tree(left_data, depth + 1, max_depth),

            'right': self._build_tree(right_data, depth + 1, max_depth)

        }

    

    def _path_length(self, tree: dict, data: float, depth: int = 0) -> float:

        """计算数据点在树中的路径长度"""

        if tree['type'] == 'leaf':

            # 叶子节点的路径长度（考虑小样本调整）

            if tree['size'] <= 1:

                return depth

            return depth + np.log(tree['size']) / np.log(2)

        

        if data <= tree['split_val']:

            return self._path_length(tree['left'], data, depth + 1)

        else:

            return self._path_length(tree['right'], data, depth + 1)

    

    def fit(self, y: np.ndarray):

        """构建隔离森林"""

        n = len(y)

        

        self.trees = []

        for _ in range(self.n_trees):

            # 随机采样构建树

            indices = np.random.choice(n, size=min(self.window_size, n), replace=False)

            sample = y[indices]

            

            tree = self._build_tree(sample)

            self.trees.append(tree)

        

        return self

    

    def score(self, y: np.ndarray) -> np.ndarray:

        """

        计算异常分数

        

        参数:

            y: 时间序列

        

        返回:

            异常分数数组（0-1，越接近1越异常）

        """

        n = len(y)

        scores = np.zeros(n)

        

        # 计算平均路径长度

        for i in range(n):

            path_lengths = []

            for tree in self.trees:

                pl = self._path_length(tree, y[i])

                path_lengths.append(pl)

            

            # 异常分数 = 2^(-平均路径长度 / c(n))

            c_n = 2 * (np.log(self.window_size - 1) + 0.57721566) - \

                  2 * (self.window_size - 1) / self.window_size if self.window_size > 1 else 1

            

            avg_pl = np.mean(path_lengths)

            scores[i] = 2 ** (-avg_pl / c_n) if c_n > 0 else 0

        

        return scores

    

    def predict(self, y: np.ndarray) -> np.ndarray:

        """预测二分类（正常/异常）"""

        scores = self.score(y)

        return (scores > self.threshold).astype(int)





class MovingZScoreDetector:

    """

    滑动Z分数异常检测

    

    计算滑动窗口内的Z分数，检测偏离程度

    

    参数:

        window_size: 滑动窗口大小

        threshold: Z分数阈值

        min_periods: 最小观测数

    """

    

    def __init__(self, window_size: int = 50, threshold: float = 3.0, min_periods: int = 10):

        self.window_size = window_size

        self.threshold = threshold

        self.min_periods = min_periods

    

    def detect(self, y: np.ndarray) -> dict:

        """检测异常值"""

        n = len(y)

        z_scores = np.zeros(n)

        is_anomaly = np.zeros(n, dtype=bool)

        

        for i in range(n):

            start = max(0, i - self.window_size + 1)

            window = y[start:i + 1]

            

            if len(window) >= self.min_periods:

                mean = np.mean(window)

                std = np.std(window)

                

                if std > 1e-10:

                    z_scores[i] = (y[i] - mean) / std

                    is_anomaly[i] = abs(z_scores[i]) > self.threshold

        

        return {

            'z_scores': z_scores,

            'is_anomaly': is_anomaly,

            'anomaly_indices': np.where(is_anomaly)[0].tolist()

        }





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("时间序列异常检测 - ESD格拉布斯检验")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 生成正常数据 + 注入异常

    n = 200

    normal = np.random.randn(n) * 0.5

    

    # 注入异常值

    anomalous_indices = [20, 80, 150]

    anomalous_values = [4.5, -3.8, 5.2]

    

    y = normal.copy()

    for idx, val in zip(anomalous_indices, anomalous_values):

        y[idx] = val

    

    print(f"\n数据生成: n={n}, 注入异常位置={anomalous_indices}")

    

    # ESD检验

    print("\n--- ESD格拉布斯检验 ---")

    result_esd = esd_test(y, max_outliers=10, alpha=0.05)

    print(f"检测到的异常索引: {result_esd['outliers_indices']}")

    print(f"G统计量: {[f'{g:.3f}' for g in result_esd['G_statistics']]}")

    print(f"临界值: {[f'{c:.3f}' for c in result_esd['critical_values']]}")

    

    # 移动Z分数检测

    print("\n--- 移动Z分数检测 ---")

    zscore_detector = MovingZScoreDetector(window_size=50, threshold=3.0)

    result_zscore = zscore_detector.detect(y)

    print(f"检测到的异常索引: {result_zscore['anomaly_indices']}")

    

    # 隔离森林检测

    print("\n--- 隔离森林异常检测 ---")

    iso_forest = IsolationAnomalyDetector(window_size=50, threshold=0.7, n_trees=50)

    iso_forest.fit(y)

    anomaly_scores = iso_forest.score(y)

    predictions = iso_forest.predict(y)

    

    anomaly_idx = np.where(predictions == 1)[0]

    print(f"检测到的异常索引: {list(anomaly_idx)}")

    print(f"异常分数范围: [{np.min(anomaly_scores):.3f}, {np.max(anomaly_scores):.3f}]")

    

    print("\n" + "=" * 50)

    print("测试完成")

