# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / anomaly_detection



本文件实现 anomaly_detection 相关的算法功能。

"""



import numpy as np



# mahalanobis_distance 算法

def mahalanobis_distance(x, mean, cov):

    diff = x - mean

    return np.sqrt(diff @ np.linalg.inv(cov) @ diff)



# isolation_forest_scores 算法

def isolation_forest_scores(data, n_trees=100, max_depth=10):

    n = len(data)

    scores = np.zeros(n)

    for _ in range(n_trees):

        indices = np.random.choice(n, n, replace=True)

        tree_data = data[indices]

        for i in range(n):

            path = 0

            for d in range(max_depth):

                if len(tree_data) <= 1: break

                split_val = np.random.uniform(tree_data.min(), tree_data.max())

                left = tree_data < split_val

                if np.sum(left) == 0 or np.sum(~left) == 0:

                    break

                tree_data = tree_data[left] if data[i] < split_val else tree_data[~left]

                path += 1

            scores[i] += path

    return scores / n_trees



# oc_svm_scores 算法

def oc_svm_scores(data, nu=0.1):

    """One-class SVM简化版"""

    center = np.mean(data, axis=0)

    distances = np.array([np.linalg.norm(x-center) for x in data])

    threshold = np.percentile(distances, (1-nu)*100)

    scores = np.where(distances > threshold, 1, -1)

    return scores



if __name__ == "__main__":

    np.random.seed(42)

    normal = np.random.randn(100,2) + [5,5]

    anomaly = np.random.randn(10,2) + [15,15]

    data = np.vstack([normal, anomaly])

    scores = isolation_forest_scores(data)

    print(f"Anomaly scores: min={np.min(scores):.2f}, max={np.max(scores):.2f}")

    print("\n异常检测测试完成!")

