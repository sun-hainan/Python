# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / regression

本文件实现 regression 相关的算法功能。
"""

import numpy as np

def linear_regression(X, y):
    X_b = np.column_stack([np.ones(X.shape[0]), X])
    theta = np.linalg.lstsq(X_b, y, rcond=None)[0]
    return theta

def ridge_regression(X, y, alpha=1.0):
    n = X.shape[1]
    X_b = np.column_stack([np.ones(X.shape[0]), X])
    I = np.eye(n+1)
    I[0,0] = 0
    H = np.linalg.inv(X_b.T @ X_b + alpha * I) @ X_b.T @ y
    return H

def logistic_regression(X, y, lr=0.1, max_iter=1000):
    w = np.zeros(X.shape[1])
    for _ in range(max_iter):
        p = 1/(1+np.exp(-X @ w))
        w += lr * X.T @ (y - p)
    return w

def theil_sen_estimator(x, y):
    n = len(x)
    slopes = []
    for i in range(n):
        for j in range(i+1,n):
            if x[i] != x[j]:
                slopes.append((y[j]-y[i])/(x[j]-x[i]))
    slopes = np.array(slopes)
    median_slope = np.median(slopes)
    median_intercept = np.median(y - median_slope*x)
    return median_slope, median_intercept

if __name__ == "__main__":
    np.random.seed(42)
    X = np.random.randn(100,2)
    y = 3*X[:,0] + 2*X[:,1] + 1 + np.random.randn(100)*0.1
    theta = linear_regression(X, y)
    print(f"Linear regression: {theta.round(3)}")
    print("\n回归分析测试完成!")
