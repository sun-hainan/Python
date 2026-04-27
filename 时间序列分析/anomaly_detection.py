# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / anomaly_detection

本文件实现 anomaly_detection 相关的算法功能。
"""

import numpy as np
from scipy import stats
from collections import defaultdict


def grubbs_test(series, alpha=0.05):
    """
    Grubbs ESD（Extreme Studentized Deviate）异常检测
    适用于单变量数据，检测是否存在一个异常值
    
    参数:
        series: 时间序列（一维numpy数组）
        alpha: 显著性水平（默认0.05，即95%置信区间）
    
    返回:
        outliers: 异常点索引列表
        grubbs_stat: Grubbs统计量
        critical_value: 临界值
    """
    n = len(series)
    
    if n < 3:
        return [], 0, 0
    
    mean_val = np.mean(series)
    std_val = np.std(series, ddof=1)  # 样本标准差
    
    if std_val < 1e-10:
        return [], 0, 0
    
    # 计算每个点与均值的偏差
    deviations = np.abs(series - mean_val)
    
    # 找到偏差最大的点
    max_idx = np.argmax(deviations)
    max_deviation = deviations[max_idx]
    
    # 计算Grubbs统计量
    # G = max(|x_i - mean|) / s
    grubbs_stat = max_deviation / std_val
    
    # 计算临界值（t分布）
    # G_critical = ((n-1) / sqrt(n)) * sqrt(t_{alpha/(2n), n-2}^2 / (n-2 + t_{alpha/(2n), n-2}^2))
    t_critical = stats.t.ppf(1 - alpha / (2 * n), n - 2)
    grubbs_critical = ((n - 1) / np.sqrt(n)) * np.sqrt(
        t_critical ** 2 / (n - 2 + t_critical ** 2)
    )
    
    # 判断是否为异常
    outliers = []
    if grubbs_stat > grubbs_critical:
        outliers.append(max_idx)
    
    return outliers, grubbs_stat, grubbs_critical


def esd_test(series, max_outliers=3, alpha=0.05):
    """
    多次迭代的ESD检验（Extreme Studentized Deviate Test）
    逐步检测多个异常值，每次移除已检测到的异常后重复检验
    
    参数:
        series: 时间序列
        max_outliers: 最多检测的异常个数
        alpha: 显著性水平
    
    返回:
        outlier_indices: 所有异常点的索引列表
        all_stats: 每次迭代的统计量
    """
    n = len(series)
    data = series.copy()
    outlier_indices = []
    all_stats = []
    
    for iteration in range(min(max_outliers, n // 2)):
        if len(data) < 3:
            break
        
        mean_val = np.mean(data)
        std_val = np.std(data, ddof=1)
        
        if std_val < 1e-10:
            break
        
        # 找到偏差最大的点
        deviations = np.abs(data - mean_val)
        max_idx = np.argmax(deviations)
        max_deviation = deviations[max_idx]
        
        # 计算ESD统计量
        esd_stat = max_deviation / std_val
        
        # 计算临界值
        current_n = len(data)
        t_critical = stats.t.ppf(1 - alpha / (2 * current_n), current_n - 2)
        critical_val = ((current_n - 1) / np.sqrt(current_n)) * np.sqrt(
            t_critical ** 2 / (current_n - 2 + t_critical ** 2)
        )
        
        all_stats.append({'iteration': iteration + 1, 'stat': esd_stat, 'critical': critical_val})
        
        # 判断并移除异常
        if esd_stat > critical_val:
            # 记录原始索引
            original_idx = np.where(series == data[max_idx])[0][0]
            outlier_indices.append(original_idx)
            # 移除该异常值
            data = np.delete(data, max_idx)
        else:
            break
    
    return outlier_indices, all_stats


class IsolationTreeNode:
    """隔离树的节点结构"""
    def __init__(self, left=None, right=None, feature=None, threshold=None, size=None):
        self.left = left
        self.right = right
        self.feature = feature  # 切分特征索引
        self.threshold = threshold  # 切分阈值
        self.size = size  # 该节点包含的样本数


def build_isolation_tree(data, current_height, limit_height):
    """
    构建一棵隔离树
    递归随机选择特征和切分点，直到所有样本被隔离或达到高度限制
    
    参数:
        data: 数据矩阵（n_samples, n_features）
        current_height: 当前节点深度
        limit_height: 高度限制（一般取log2(n_samples)）
    
    返回:
        root: 隔离树的根节点
    """
    n_samples, n_features = data.shape
    
    # 终止条件：数据只有1个样本或达到高度限制
    if n_samples <= 1 or current_height >= limit_height:
        return IsolationTreeNode(size=n_samples)
    
    # 随机选择切分特征和切分点
    feature_idx = np.random.randint(0, n_features)
    feature_values = data[:, feature_idx]
    
    min_val = np.min(feature_values)
    max_val = np.max(feature_values)
    
    if min_val == max_val:
        return IsolationTreeNode(size=n_samples)
    
    # 随机选择切分阈值
    threshold = np.random.uniform(min_val, max_val)
    
    # 根据阈值分割数据
    left_mask = feature_values < threshold
    right_mask = ~left_mask
    
    left_data = data[left_mask]
    right_data = data[right_mask]
    
    # 递归构建子树
    left_child = build_isolation_tree(left_data, current_height + 1, limit_height)
    right_child = build_isolation_tree(right_data, current_height + 1, limit_height)
    
    return IsolationTreeNode(left=left_child, right=right_child,
                             feature=feature_idx, threshold=threshold, size=n_samples)


def path_length(instance, tree, current_height):
    """
    计算一个实例在隔离树中的路径长度
    路径越短，越可能是异常
    
    参数:
        instance: 单个数据点
        tree: 隔离树节点
        current_height: 当前高度
    
    返回:
        path_len: 从根节点到叶节点的路径长度
    """
    # 如果到达叶节点或节点大小为1，返回路径长度
    if tree.left is None or tree.right is None or tree.size == 1:
        return current_height
    
    feature_idx = tree.feature
    threshold = tree.threshold
    
    if instance[feature_idx] < threshold:
        return path_length(instance, tree.left, current_height + 1)
    else:
        return path_length(instance, tree.right, current_height + 1)


class IsolationForest:
    """
    隔离森林异常检测
    原理：异常点只需少量随机切分即可被隔离，正常点需要更多切分
    """
    def __init__(self, n_trees=100, sample_size=None, height_limit=None, random_seed=42):
        self.n_trees = n_trees
        self.sample_size = sample_size
        self.height_limit = height_limit
        self.random_seed = random_seed
        self.trees = []
    
    def fit(self, data):
        """
        训练隔离森林
        参数:
            data: 数据矩阵（n_samples, n_features）
        """
        np.random.seed(self.random_seed)
        
        n_samples = len(data)
        
        # 如果样本数小于指定采样大小，使用全部数据
        if self.sample_size is None or self.sample_size >= n_samples:
            self.sample_size = n_samples
        
        # 计算高度限制：log2(sample_size)
        if self.height_limit is None:
            self.height_limit = int(np.ceil(np.log2(self.sample_size)))
        
        # 构建多棵隔离树
        self.trees = []
        for _ in range(self.n_trees):
            # 随机采样子集
            indices = np.random.choice(n_samples, min(self.sample_size, n_samples), replace=False)
            sample_data = data[indices]
            
            # 构建一棵隔离树
            tree = build_isolation_tree(sample_data, 0, self.height_limit)
            self.trees.append(tree)
    
    def anomaly_score(self, instance):
        """
        计算单个实例的异常分数
        分数越高，越可能是异常
        
        参数:
            instance: 单个数据点
        
        返回:
            score: 异常分数（0-1之间）
        """
        avg_path_len = 0.0
        n_trees = len(self.trees)
        
        for tree in self.trees:
            path_len = path_length(instance, tree, 0)
            avg_path_len += path_len
        
        avg_path_len /= n_trees
        
        # 计算异常分数
        # c(n) = 2 * H(n-1) - 2 * (n-1)/n，其中H(k)为谐波数
        n = self.sample_size
        if n > 2:
            harmonic_num = np.log(n - 1) + 0.5772156649  # 欧拉-马歇罗尼常数近似
            c_n = 2 * harmonic_num - 2 * (n - 1) / n
        else:
            c_n = 1
        
        # 标准化路径长度到[0,1]区间
        score = 2 ** (-avg_path_len / c_n)
        
        return score
    
    def predict(self, data, threshold=0.5):
        """
        预测数据中的异常点
        
        参数:
            data: 数据矩阵
            threshold: 异常分数阈值，超过此值判定为异常
        
        返回:
            outliers: 异常点索引数组
            scores: 每个点的异常分数数组
        """
        scores = np.array([self.anomaly_score(instance) for instance in data])
        outliers = np.where(scores > threshold)[0]
        
        return outliers, scores


def local_outlier_factor(data, k=5):
    """
    LOF（Local Outlier Factor）异常检测
    原理：一个点的LOF值接近1表示密度与邻域相当；LOF >> 1表示密度明显低于邻域，
    即该点为异常
    
    参数:
        data: 数据矩阵（n_samples, n_features）
        k: 邻域点数
    
    返回:
        lof_scores: 每个点的LOF分数
        outliers: 异常点索引（LOF > threshold）
    """
    n_samples = data.shape[0]
    
    # 计算欧氏距离矩阵
    distances = np.zeros((n_samples, n_samples))
    for i in range(n_samples):
        for j in range(i + 1, n_samples):
            dist = np.linalg.norm(data[i] - data[j])
            distances[i, j] = dist
            distances[j, i] = dist
    
    # 对每个点找k个最近邻
    k_distances = np.zeros(n_samples)  # k距离
    neighbors = np.zeros((n_samples, k), dtype=int)  # k近邻索引
    
    for i in range(n_samples):
        sorted_indices = np.argsort(distances[i])
        k_distances[i] = distances[i, sorted_indices[k]]  # k距离
        neighbors[i] = sorted_indices[1:k+1]  # 排除自身后取k个最近邻
    
    # 计算可达距离
    def reach_dist(i, j):
        """点j到点i的可达距离"""
        return max(k_distances[j], distances[i, j])
    
    # 计算局部可达密度
    lrd = np.zeros(n_samples)
    for i in range(n_samples):
        neighbor_list = neighbors[i]
        reach_sum = sum(reach_dist(i, j) for j in neighbor_list)
        if reach_sum > 0:
            lrd[i] = k / reach_sum
    
    # 计算LOF
    lof_scores = np.zeros(n_samples)
    for i in range(n_samples):
        neighbor_list = neighbors[i]
        lrd_sum = sum(lrd[j] for j in neighbor_list)
        if lrd[i] > 0:
            lof_scores[i] = lrd_sum / (k * lrd[i])
    
    # 判定异常：LOF > 1.5 通常视为异常
    threshold = 1.5
    outliers = np.where(lof_scores > threshold)[0]
    
    return lof_scores, outliers


if __name__ == "__main__":
    # 测试代码
    np.random.seed(42)
    
    # 生成正常数据：均值0标准差1的正态分布
    normal_data = np.random.normal(0, 1, 200)
    
    # 注入异常值
    anomalies = np.array([8.5, -7.2, 9.0, 10.0])
    all_data = np.concatenate([normal_data, anomalies])
    
    print(f"总数据量: {len(all_data)}, 异常值注入: {len(anomalies)}个")
    print(f"数据范围: [{np.min(all_data):.2f}, {np.max(all_data):.2f}]")
    
    # 1. Grubbs ESD检验
    print("\n=== Grubbs ESD 检测 ===")
    outliers_grubbs, stat, critical = grubbs_test(all_data)
    print(f"检测到的异常: {outliers_grubbs}")
    print(f"Grubbs统计量: {stat:.4f}, 临界值: {critical:.4f}")
    
    # 2. 多次迭代ESD
    print("\n=== 多次迭代ESD 检测 ===")
    outliers_esd, stats_list = esd_test(all_data, max_outliers=5)
    print(f"检测到的异常: {outliers_esd}")
    for s in stats_list:
        print(f"  迭代{s['iteration']}: 统计量={s['stat']:.4f}, 临界={s['critical']:.4f}")
    
    # 3. 隔离森林
    print("\n=== 隔离森林 检测 ===")
    data_matrix = all_data.reshape(-1, 1)  # 一维时序转为二维特征矩阵
    forest = IsolationForest(n_trees=50, sample_size=64, random_seed=42)
    forest.fit(data_matrix)
    
    outlier_indices, scores = forest.predict(data_matrix, threshold=0.6)
    print(f"检测到的异常: {outlier_indices}")
    print(f"异常分数（前10个）: {scores[:10]}")
    
    # 4. LOF
    print("\n=== LOF 检测 ===")
    lof_scores, lof_outliers = local_outlier_factor(data_matrix, k=5)
    print(f"检测到的异常: {lof_outliers}")
    print(f"LOF分数（前10个）: {lof_scores[:10]}")
