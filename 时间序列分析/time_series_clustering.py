# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / time_series_clustering

本文件实现 time_series_clustering 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import euclidean


class FeatureExtractor:
    """时间序列特征提取器"""
    
    @staticmethod
    def extract_statistical_features(y: np.ndarray) -> dict:
        """
        提取统计特征
        
        参数:
            y: 时间序列
        
        返回:
            特征字典
        """
        n = len(y)
        
        # 基础统计
        mean = np.mean(y)
        std = np.std(y)
        median = np.median(y)
        min_val = np.min(y)
        max_val = np.max(y)
        
        # 趋势特征
        t = np.arange(n)
        slope = np.polyfit(t, y, 1)[0] if n > 1 else 0
        
        # 波动率特征
        returns = np.diff(y) / (y[:-1] + 1e-10)
        volatility = np.std(returns)
        
        # 峰度和偏度
        from scipy import stats
        skewness = stats.skew(y)
        kurtosis = stats.kurtosis(y)
        
        # 自相关特征
        acf1 = np.corrcoef(y[:-1], y[1:])[0, 1] if n > 1 else 0
        
        # 能量（频域）
        fft_magnitude = np.abs(np.fft.fft(y))
        energy = np.sum(fft_magnitude[:n // 2] ** 2)
        
        return {
            'mean': mean,
            'std': std,
            'median': median,
            'min': min_val,
            'max': max_val,
            'range': max_val - min_val,
            'slope': slope,
            'volatility': volatility,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'acf1': acf1,
            'energy': energy
        }
    
    @staticmethod
    def extract_shape_features(y: np.ndarray, n_segments: int = 5) -> np.ndarray:
        """
        提取形状特征（分段聚合近似）
        
        参数:
            y: 时间序列
            n_segments: 分段数
        
        返回:
            形状特征向量
        """
        n = len(y)
        segment_size = n / n_segments
        
        features = []
        for i in range(n_segments):
            start = int(i * segment_size)
            end = int((i + 1) * segment_size)
            segment = y[start:end]
            
            features.append(np.mean(segment))
            features.append(np.std(segment))
        
        return np.array(features)
    
    @staticmethod
    def extract_all(y: np.ndarray) -> np.ndarray:
        """提取所有特征并展平为向量"""
        stats_features = FeatureExtractor.extract_statistical_features(y)
        shape_features = FeatureExtractor.extract_shape_features(y)
        
        # 合并
        all_features = list(stats_features.values()) + list(shape_features)
        return np.array(all_features)


class TimeSeriesKMeans:
    """
    基于特征的时间序列K-means聚类
    
    参数:
        n_clusters: 聚类数
        max_iter: 最大迭代次数
    """
    
    def __init__(self, n_clusters: int = 3, max_iter: int = 100):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.centers = None
        self.labels = None
        self.scaler = StandardScaler()
    
    def fit(self, series_list: List[np.ndarray]) -> np.ndarray:
        """
        聚类
        
        参数:
            series_list: 时间序列列表
        
        返回:
            聚类标签
        """
        # 提取特征
        features = np.array([FeatureExtractor.extract_all(s) for s in series_list])
        
        # 标准化
        features_scaled = self.scaler.fit_transform(features)
        
        # K-means聚类
        kmeans = KMeans(n_clusters=self.n_clusters, max_iter=self.max_iter, random_state=42)
        self.labels = kmeans.fit_predict(features_scaled)
        
        # 保存聚类中心
        self.centers = kmeans.cluster_centers_
        
        return self.labels
    
    def predict(self, y: np.ndarray) -> int:
        """预测新序列的类别"""
        features = FeatureExtractor.extract_all(y)
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        # 找最近的聚类中心
        distances = np.array([euclidean(features_scaled[0], center) for center in self.centers])
        return np.argmin(distances)


class DTWKMeans:
    """
    基于DTW距离的K-means聚类（形状感知）
    
    参数:
        n_clusters: 聚类数
        max_iter: 最大迭代次数
        subsample_size: 下采样大小（加速）
    """
    
    def __init__(self, n_clusters: int = 3, max_iter: int = 100, subsample_size: int = 50):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.subsample_size = subsample_size
        self.centers = None  # 聚类中心（时序）
        self.labels = None
    
    def _subsample(self, y: np.ndarray) -> np.ndarray:
        """下采样到固定长度"""
        n = len(y)
        if n <= self.subsample_size:
            return y
        
        indices = np.linspace(0, n - 1, self.subsample_size).astype(int)
        return y[indices]
    
    def _dtw_distance(self, x: np.ndarray, y: np.ndarray) -> float:
        """计算DTW距离（简化版，使用下采样）"""
        x_sub = self._subsample(x)
        y_sub = self._subsample(y)
        
        n, m = len(x_sub), len(y_sub)
        
        # 距离矩阵
        dtw = np.full((n + 1, m + 1), np.inf)
        dtw[0, 0] = 0
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = (x_sub[i-1] - y_sub[j-1]) ** 2
                dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
        
        return np.sqrt(dtw[n, m])
    
    def fit(self, series_list: List[np.ndarray]) -> np.ndarray:
        """
        聚类
        
        参数:
            series_list: 时间序列列表
        """
        n = len(series_list)
        
        # 初始化：随机选K个中心
        indices = np.random.choice(n, self.n_clusters, replace=False)
        self.centers = [series_list[i] for i in indices]
        
        self.labels = np.zeros(n, dtype=int)
        
        for iteration in range(self.max_iter):
            # 分配
            new_labels = np.zeros(n, dtype=int)
            
            for i, series in enumerate(series_list):
                min_dist = np.inf
                best_cluster = 0
                
                for k, center in enumerate(self.centers):
                    dist = self._dtw_distance(series, center)
                    if dist < min_dist:
                        min_dist = dist
                        best_cluster = k
                
                new_labels[i] = best_cluster
            
            # 检查收敛
            if np.array_equal(new_labels, self.labels):
                break
            
            self.labels = new_labels
            
            # 更新中心
            for k in range(self.n_clusters):
                cluster_series = [series_list[i] for i in range(n) if self.labels[i] == k]
                
                if len(cluster_series) == 0:
                    continue
                
                # 找离所有成员最近的序列作为新中心
                min_total_dist = np.inf
                best_center = cluster_series[0]
                
                for candidate in cluster_series:
                    total_dist = sum(self._dtw_distance(candidate, s) for s in cluster_series)
                    if total_dist < min_total_dist:
                        min_total_dist = total_dist
                        best_center = candidate
                
                self.centers[k] = best_center
        
        return self.labels
    
    def predict(self, y: np.ndarray) -> int:
        """预测类别"""
        min_dist = np.inf
        pred = 0
        
        for k, center in enumerate(self.centers):
            dist = self._dtw_distance(y, center)
            if dist < min_dist:
                min_dist = dist
                pred = k
        
        return pred


class HierarchicalTSClustering:
    """
    时间序列层次聚类（使用DTW距离）
    
    参数:
        linkage: 连接方式 ('average', 'single', 'complete')
    """
    
    def __init__(self, linkage: str = 'average'):
        self.linkage = linkage
        self.labels = None
        self.n_clusters = None
    
    def _compute_distance_matrix(self, series_list: List[np.ndarray]) -> np.ndarray:
        """计算DTW距离矩阵"""
        n = len(series_list)
        dist_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                # 简化DTW
                x_sub = series_list[i][::len(series_list[i]) // 20][:20]
                y_sub = series_list[j][::len(series_list[j]) // 20][:20]
                
                n1, n2 = len(x_sub), len(y_sub)
                dtw = np.full((n1 + 1, n2 + 1), np.inf)
                dtw[0, 0] = 0
                
                for ii in range(1, n1 + 1):
                    for jj in range(1, n2 + 1):
                        cost = (x_sub[ii-1] - y_sub[jj-1]) ** 2
                        dtw[ii, jj] = cost + min(dtw[ii-1, jj], dtw[ii, jj-1], dtw[ii-1, jj-1])
                
                dist = np.sqrt(dtw[n1, n2])
                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist
        
        return dist_matrix
    
    def fit(self, series_list: List[np.ndarray], n_clusters: int = 3) -> np.ndarray:
        """
        聚类
        
        参数:
            series_list: 时间序列列表
            n_clusters: 目标聚类数
        
        返回:
            标签数组
        """
        n = len(series_list)
        
        # 计算距离矩阵
        dist_matrix = self._compute_distance_matrix(series_list)
        
        # 简化的层次聚类
        clusters = [[i] for i in range(n)]
        
        while len(clusters) > n_clusters:
            # 找最近的两个簇
            min_dist = np.inf
            merge_i, merge_j = 0, 1
            
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # 计算簇间距离
                    dists = []
                    for ci in clusters[i]:
                        for cj in clusters[j]:
                            dists.append(dist_matrix[ci][cj])
                    
                    avg_dist = np.mean(dists)
                    
                    if avg_dist < min_dist:
                        min_dist = avg_dist
                        merge_i, merge_j = i, j
            
            # 合并
            clusters[merge_i].extend(clusters[merge_j])
            clusters.pop(merge_j)
        
        # 分配标签
        self.labels = np.zeros(n, dtype=int)
        for k, cluster in enumerate(clusters):
            for idx in cluster:
                self.labels[idx] = k
        
        self.n_clusters = n_clusters
        return self.labels


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("时间序列聚类测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 生成三类时间序列
    n_per_class = 20
    length = 100
    
    series_list = []
    labels_true = []
    
    # 类1：正弦波
    for i in range(n_per_class):
        t = np.linspace(0, 2 * np.pi, length)
        series = 5 + 2 * np.sin(t + np.random.rand() * 0.5) + np.random.randn(length) * 0.3
        series_list.append(series)
        labels_true.append(0)
    
    # 类2：线性趋势
    for i in range(n_per_class):
        slope = np.random.rand() * 0.2 + 0.1
        series = 2 + slope * np.arange(length) + np.random.randn(length) * 0.5
        series_list.append(series)
        labels_true.append(1)
    
    # 类3：随机游走
    for i in range(n_per_class):
        walk = np.cumsum(np.random.randn(length) * 0.5)
        series = walk + np.random.rand() * 10
        series_list.append(series)
        labels_true.append(2)
    
    print(f"\n数据生成: {len(series_list)} 条序列，每条 {length} 点")
    print(f"真实类别分布: {[labels_true.count(i) for i in range(3)]}")
    
    # 特征提取测试
    print("\n--- 特征提取 ---")
    features = FeatureExtractor.extract_all(series_list[0])
    print(f"特征维度: {len(features)}")
    print(f"前5个特征值: {features[:5]}")
    
    # K-means聚类
    print("\n--- K-means聚类（基于特征）---")
    kmeans = TimeSeriesKMeans(n_clusters=3)
    labels_kmeans = kmeans.fit(series_list)
    
    # 计算准确率（匈牙利匹配）
    from scipy.optimize import linear_sum_assignment
    
    def cluster_accuracy(true_labels, pred_labels):
        n_clusters = max(true_labels) + 1
        confusion = np.zeros((n_clusters, n_clusters))
        
        for t, p in zip(true_labels, pred_labels):
            confusion[t, p] += 1
        
        row_ind, col_ind = linear_sum_assignment(-confusion)
        return confusion[row_ind, col_ind].sum() / len(true_labels)
    
    acc_kmeans = cluster_accuracy(labels_true, labels_kmeans)
    print(f"聚类准确率: {acc_kmeans:.2%}")
    
    # DTW K-means
    print("\n--- DTW K-means聚类 ---")
    dtw_kmeans = DTWKMeans(n_clusters=3, max_iter=50, subsample_size=30)
    labels_dtw = dtw_kmeans.fit(series_list)
    
    acc_dtw = cluster_accuracy(labels_true, labels_dtw)
    print(f"聚类准确率: {acc_dtw:.2%}")
    
    # 层次聚类
    print("\n--- 层次聚类 ---")
    hier = HierarchicalTSClustering(linkage='average')
    labels_hier = hier.fit(series_list, n_clusters=3)
    
    acc_hier = cluster_accuracy(labels_true, labels_hier)
    print(f"聚类准确率: {acc_hier:.2%}")
    
    print("\n" + "=" * 50)
    print("测试完成")
