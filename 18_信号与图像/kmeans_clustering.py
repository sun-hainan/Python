# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / kmeans_clustering



本文件实现 kmeans_clustering 相关的算法功能。

"""



if __name__ == "__main__":

    np.random.seed(42)

    c1 = np.random.randn(50,2)+[3,3]

    c2 = np.random.randn(50,2)+[-3,-3]

    data = np.vstack([c1,c2])

    labels, centers = kmeans(data, k=2)

    print(f"Cluster sizes: {np.bincount(labels)}")

    print("\nK-Means测试完成!")

