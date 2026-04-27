# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / dtw_algorithm



本文件实现 dtw_algorithm 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Optional, List

from scipy.spatial.distance import euclidean





def dtw_distance(x: np.ndarray, y: np.ndarray, 

                 window: Optional[int] = None,

                 metric: str = 'euclidean') -> Tuple[float, List, List]:

    """

    计算两个时间序列之间的DTW距离

    

    参数:

        x: 第一个时间序列

        y: 第二个时间序列

        window: 约束窗口大小（用于加速）

        metric: 距离度量 ('euclidean', 'manhattan')

    

    返回:

        (DTW距离, 对齐路径1, 对齐路径2)

    """

    n = len(x)

    m = len(y)

    

    # 窗口约束

    if window is None:

        window = max(n, m)

    

    # 初始化距离矩阵

    dtw_matrix = np.full((n + 1, m + 1), np.inf)

    dtw_matrix[0, 0] = 0

    

    # 路径记录

    path_i = []

    path_j = []

    

    # 填充DTW矩阵

    for i in range(1, n + 1):

        for j in range(max(1, i - window), min(m + 1, i + window + 1)):

            # 计算距离

            if metric == 'euclidean':

                cost = (x[i - 1] - y[j - 1]) ** 2

            elif metric == 'manhattan':

                cost = abs(x[i - 1] - y[j - 1])

            else:

                cost = euclidean([x[i - 1]], [y[j - 1]])[0] ** 2

            

            # 动态规划转移

            dtw_matrix[i, j] = cost + min(

                dtw_matrix[i - 1, j],      # 插入

                dtw_matrix[i, j - 1],      # 删除

                dtw_matrix[i - 1, j - 1]   # 匹配

            )

    

    # 回溯找到最短路径

    i, j = n, m

    while i > 0 or j > 0:

        path_i.append(i - 1)

        path_j.append(j - 1)

        

        if i == 0:

            j -= 1

        elif j == 0:

            i -= 1

        else:

            # 选择最小方向回退

            candidates = [

                (dtw_matrix[i - 1, j - 1], i - 1, j - 1),

                (dtw_matrix[i - 1, j], i - 1, j),

                (dtw_matrix[i, j - 1], i, j - 1)

            ]

            _, i, j = min(candidates, key=lambda x: x[0])

    

    path_i.reverse()

    path_j.reverse()

    

    return np.sqrt(dtw_matrix[n, m]), path_i, path_j





def dtw_matrix(x: np.ndarray, y: np.ndarray, 

               metric: str = 'euclidean') -> np.ndarray:

    """

    计算点对点距离矩阵

    

    参数:

        x: 第一个时间序列

        y: 第二个时间序列

    

    返回:

        距离矩阵

    """

    n = len(x)

    m = len(y)

    

    dist_matrix = np.zeros((n, m))

    

    for i in range(n):

        for j in range(m):

            if metric == 'euclidean':

                dist_matrix[i, j] = (x[i] - y[j]) ** 2

            elif metric == 'manhattan':

                dist_matrix[i, j] = abs(x[i] - y[j])

            else:

                dist_matrix[i, j] = euclidean([x[i]], [y[j]]) ** 2

    

    return dist_matrix





def fast_dtw(x: np.ndarray, y: np.ndarray, 

             radius: int = 1) -> Tuple[float, List, List]:

    """

    FastDTW - 加速版本的DTW

    

    先在粗粒度上计算，再逐层细化

    

    参数:

        x: 第一个时间序列

        y: 第二个时间序列

        radius: 搜索半径

    

    返回:

        (DTW距离, 对齐路径)

    """

    n = len(x)

    m = len(y)

    

    # 如果序列足够短，直接计算

    if max(n, m) <= radius * 2:

        return dtw_distance(x, y)

    

    # 下采样

    x_shrunk = np.array([(x[2 * i] + x[2 * i + 1]) / 2 

                        for i in range(n // 2)])

    y_shrunk = np.array([(y[2 * i] + y[2 * i + 1]) / 2 

                        for i in range(m // 2)])

    

    # 递归计算

    _, path_i_shrunk, path_j_shrunk = fast_dtw(x_shrunk, y_shrunk, radius)

    

    # 在原始分辨率上细化路径

    window = max(radius, abs(n - m))

    

    # 构建粗粒度路径的约束窗口

    path_i = []

    path_j = []

    

    i = 0

    for j in range(len(path_i_shrunk) - 1):

        ci = path_i_shrunk[j] * 2

        cj = path_j_shrunk[j] * 2

        

        for k in range(2):

            path_i.append(min(ci + k, n - 1))

            path_j.append(min(cj + k, m - 1))

    

    return dtw_distance(x, y, window=window)





class DTWClustering:

    """

    基于DTW的距离的层次聚类

    

    参数:

        linkage: 连接方式 ('average', 'single', 'complete')

    """

    

    def __init__(self, linkage: str = 'average'):

        self.linkage = linkage

        self.labels = None

        self.distances = None

    

    def fit(self, series_list: List[np.ndarray]) -> np.ndarray:

        """

        对时间序列列表进行聚类

        

        参数:

            series_list: 时间序列列表

        

        返回:

            聚类标签

        """

        n = len(series_list)

        

        # 计算成对DTW距离矩阵

        dist_matrix = np.zeros((n, n))

        for i in range(n):

            for j in range(i + 1, n):

                d, _, _ = dtw_distance(series_list[i], series_list[j])

                dist_matrix[i, j] = d

                dist_matrix[j, i] = d

        

        self.distances = dist_matrix

        

        # 层次聚类（简化版）

        labels = np.arange(n)

        

        # 迭代合并

        for _ in range(n - 1):

            # 找到最小距离的对

            min_dist = np.inf

            merge_i, merge_j = -1, -1

            

            for i in range(n):

                for j in range(i + 1, n):

                    if labels[i] != labels[j] and dist_matrix[i, j] < min_dist:

                        min_dist = dist_matrix[i, j]

                        merge_i, merge_j = i, j

            

            if merge_i == -1:

                break

            

            # 合并：将merge_j的标签改为merge_i的标签

            labels[labels == labels[merge_j]] = labels[merge_i]

        

        # 重新编号

        unique_labels = np.unique(labels)

        label_map = {old: new for new, old in enumerate(unique_labels)}

        self.labels = np.array([label_map[l] for l in labels])

        

        return self.labels

    

    def predict(self, x: np.ndarray, series_list: List[np.ndarray]) -> int:

        """预测新序列的类别（找最近的聚类中心）"""

        if self.labels is None:

            raise ValueError("模型未拟合")

        

        min_dist = np.inf

        pred_label = 0

        

        for i, series in enumerate(series_list):

            d, _, _ = dtw_distance(x, series)

            if d < min_dist:

                min_dist = d

                pred_label = self.labels[i]

        

        return pred_label





def shape_dtw(x: np.ndarray, y: np.ndarray) -> float:

    """

    ShapeDTW - 基于形状的DTW变体

    

    使用局部形状描述符增强DTW

    

    参数:

        x: 时间序列1

        y: 时间序列2

    

    返回:

        ShapeDTW距离

    """

    n = len(x)

    m = len(y)

    

    # 提取局部描述符（使用差分）

    desc_x = np.diff(x)

    desc_y = np.diff(y)

    

    # 距离矩阵

    dist_matrix = np.zeros((n, m))

    

    for i in range(n):

        for j in range(m):

            # 综合原始值距离和描述符距离

            dist_matrix[i, j] = (x[i] - y[j]) ** 2 + 0.5 * (desc_x[i] - desc_y[j]) ** 2

    

    # 标准DTW

    dtw_matrix = np.full((n + 1, m + 1), np.inf)

    dtw_matrix[0, 0] = 0

    

    for i in range(1, n + 1):

        for j in range(1, m + 1):

            dtw_matrix[i, j] = dist_matrix[i - 1, j - 1] + min(

                dtw_matrix[i - 1, j],

                dtw_matrix[i, j - 1],

                dtw_matrix[i - 1, j - 1]

            )

    

    return np.sqrt(dtw_matrix[n, m])





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("动态时间规整（DTW）算法测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 生成两个相似的序列（有位移和拉伸）

    t = np.linspace(0, 2 * np.pi, 50)

    x = np.sin(t) + np.random.randn(50) * 0.1

    

    # y是x的拉伸版本

    y = np.sin(t * 0.8 + 0.5) + np.random.randn(50) * 0.1

    

    print(f"\n序列长度: x={len(x)}, y={len(y)}")

    

    # DTW距离

    print("\n--- 标准DTW ---")

    dtw_dist, path_i, path_j = dtw_distance(x, y)

    print(f"DTW距离: {dtw_dist:.4f}")

    print(f"对齐长度: {len(path_i)}")

    print(f"路径前5点: ({path_i[:5]}, {path_j[:5]})")

    

    # FastDTW

    print("\n--- FastDTW ---")

    dtw_fast, path_i_fast, path_j_fast = fast_dtw(x, y, radius=5)

    print(f"FastDTW距离: {dtw_fast:.4f}")

    

    # 欧氏距离对比

    print("\n--- 欧氏距离对比 ---")

    euclid_dist = np.sqrt(np.sum((x[:len(y)] - y) ** 2))

    print(f"欧氏距离: {euclid_dist:.4f}")

    print(f"DTW比欧氏{'更小' if dtw_dist < euclid_dist else '更大'}（DTW允许对齐）")

    

    # ShapeDTW

    print("\n--- ShapeDTW ---")

    shape_dist = shape_dtw(x, y)

    print(f"ShapeDTW距离: {shape_dist:.4f}")

    

    # DTW聚类

    print("\n--- DTW层次聚类 ---")

    np.random.seed(42)

    

    # 生成三组相似序列

    series_list = []

    for _ in range(5):

        base = np.sin(np.linspace(0, 2 * np.pi, 30))

        noise = np.random.randn(30) * 0.1

        series_list.append(base + noise)

    

    for _ in range(5):

        base = np.cos(np.linspace(0, 2 * np.pi, 30))

        noise = np.random.randn(30) * 0.1

        series_list.append(base + noise)

    

    for _ in range(5):

        base = np.sin(np.linspace(0, 4 * np.pi, 30))

        noise = np.random.randn(30) * 0.1

        series_list.append(base + noise)

    

    clusterer = DTWClustering(linkage='average')

    labels = clusterer.fit(series_list)

    print(f"聚类标签: {labels}")

    

    print("\n" + "=" * 50)

    print("测试完成")

