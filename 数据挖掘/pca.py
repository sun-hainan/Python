# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / pca

本文件实现 pca 相关的算法功能。
"""

import numpy as np


class PCA:
    """主成分分析（Principal Component Analysis）"""

    def __init__(self, n_components=None):
        """
        n_components: 保留的主成分数（维度）
            如果为 float，表示解释方差比例阈值
        """
        self.n_components = n_components
        self.components_ = None  # 主成分方向向量 (n_components, D)
        self.mean_ = None  # 数据均值
        self.explained_variance_ = None  # 各主成分解释的方差
        self.explained_variance_ratio_ = None  # 方差解释比例

    def fit(self, X):
        """拟合并计算主成分"""
        n_samples, n_features = X.shape

        # 中心化
        self.mean_ = X.mean(axis=0)
        X_centered = X - self.mean_

        # SVD 分解：X_centered = U * S * V^T
        # V 的行向量即主成分方向
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

        # 确定主成分数
        if self.n_components is None:
            self.n_components = min(n_samples, n_features)
        elif isinstance(self.n_components, float):
            # 按方差比例确定
            total_var = np.sum(S ** 2)
            cumsum = np.cumsum(S ** 2)
            var_threshold = self.n_components * total_var
            self.n_components = np.searchsorted(cumsum, var_threshold) + 1

        self.n_components = int(self.n_components)

        # 主成分方向（V 的前 n_components 行）
        self.components_ = Vt[:self.n_components]

        # 解释方差 = S^2 / (N-1)
        self.explained_variance_ = (S ** 2) / (n_samples - 1)
        self.explained_variance_ratio_ = self.explained_variance_ / self.explained_variance_.sum()

        return self

    def transform(self, X):
        """将数据投影到主成分空间"""
        X_centered = X - self.mean_
        return X_centered @ self.components_.T

    def fit_transform(self, X):
        """拟合并转换"""
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X_transformed):
        """从投影空间重建数据（近似）"""
        return X_transformed @ self.components_ + self.mean_

    def reconstruction_error(self, X):
        """计算重构误差（投影后重建的均方误差）"""
        X_transformed = self.transform(X)
        X_reconstructed = self.inverse_transform(X_transformed)
        return np.mean((X - X_reconstructed) ** 2)


def pca_svd(X):
    """使用 SVD 的简化 PCA"""
    n_samples, n_features = X.shape
    # 中心化
    mean = X.mean(axis=0)
    X_centered = X - mean
    # SVD
    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
    # 主成分
    components = Vt
    # 解释方差比例
    variance = S ** 2 / (n_samples - 1)
    variance_ratio = variance / variance.sum()
    return components, variance, variance_ratio, mean


def demo():
    """PCA 演示"""
    np.random.seed(42)

    # 生成高维低秩数据（存在隐结构）
    n_samples = 200
    n_features = 10

    # 真实隐变量（3个独立成分）
    latent = np.random.randn(n_samples, 3)

    # 加载矩阵
    W = np.random.randn(3, n_features)
    noise = np.random.randn(n_samples, n_features) * 0.1

    # 生成观测数据
    X = latent @ W + noise

    print("=== PCA 演示 ===")
    print(f"数据形状: {X.shape}（{n_samples} 样本, {n_features} 特征）")

    # PCA 分析
    pca = PCA(n_components=5)
    pca.fit(X)

    print(f"\n保留主成分数: {pca.n_components}")
    print(f"各主成分解释方差比例:")
    for i, ratio in enumerate(pca.explained_variance_ratio_):
        print(f"  PC{i + 1}: {ratio:.4f} ({ratio * 100:.2f}%)")
    print(f"累计解释方差: {pca.explained_variance_ratio_.sum():.4f}")

    # 降维
    X_transformed = pca.transform(X)
    print(f"\n降维后形状: {X_transformed.shape}")

    # 重构误差
    recon_err = pca.reconstruction_error(X)
    print(f"重构均方误差: {recon_err:.6f}")

    # 不同维度对比
    print("\n不同维度对累计解释方差的影响:")
    for n_comp in [1, 2, 3, 5, 7, 10]:
        pca_n = PCA(n_components=n_comp)
        pca_n.fit(X)
        cum_var = pca_n.explained_variance_ratio_.sum()
        print(f"  n_components={n_comp}: 累计方差={cum_var:.4f}")

    # 二维可视化示例
    pca2 = PCA(n_components=2)
    X_2d = pca2.fit_transform(X)
    print(f"\n2D 投影形状: {X_2d.shape}")


if __name__ == "__main__":
    demo()
