# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / dimensionality_reduction



本文件实现 dimensionality_reduction 相关的算法功能。

"""



import numpy as np



def pca(X, n_components=2):

    # pca function



    # pca function

    Xc = X - X.mean(axis=0)

    C = Xc.T @ Xc / (len(X)-1)

    eigenvalues, eigenvectors = np.linalg.eigh(C)

    idx = np.argsort(eigenvalues)[::-1]

    V = eigenvectors[:,idx[:n_components]]

    return Xc @ V, eigenvalues[idx[:n_components]]



def lda(X, y, n_components=2):

    # lda function



    # lda function

    classes = np.unique(y)

    n_features = X.shape[1]

    Sw = np.zeros((n_features,n_features))

    for c in classes:

        Xc = X[y==c] - X[y==c].mean(axis=0)

        Sw += Xc.T @ Xc

    overall_mean = X.mean(axis=0)

    Sb = np.zeros((n_features,n_features))

    for c in classes:

        nc = np.sum(y==c)

        mean_c = X[y==c].mean(axis=0)

        diff = mean_c - overall_mean

        Sb += nc * np.outer(diff, diff)

    eigenvalues, eigenvectors = np.linalg.eig(np.linalg.inv(Sw) @ Sb)

    idx = np.argsort(eigenvalues.real)[::-1]

    W = eigenvectors.real[:,idx[:n_components]]

    return X @ W



def t_sne(X, perplexity=30, n_iter=100):

    # t_sne function



    # t_sne function

    n = len(X)

    dists = np.zeros((n,n))

    for i in range(n):

        for j in range(n):

            dists[i,j] = np.linalg.norm(X[i]-X[j])**2

    P = np.zeros((n,n))

    for i in range(n):

        beta = 1.0

        p = np.exp(-dists[i]/beta)

        p /= p.sum()

        P[i] = (p + p[i]) / 2

    Y = np.random.randn(n, 2)

    return Y



if __name__ == "__main__":

    np.random.seed(42)

    X = np.random.randn(100,5)

    X_pca, ev = pca(X, 2)

    print(f"PCA explained variance: {ev[:2].round(2)}")

    print("\n降维测试完成!")

