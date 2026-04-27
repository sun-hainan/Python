# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / feature_selection

本文件实现 feature_selection 相关的算法功能。
"""

import numpy as np
from typing import List

def variance_threshold(X, threshold=0.0):
    """Variance-based feature selection"""
    variances = np.var(X, axis=0)
    return np.where(variances > threshold)[0]

def correlation_filter(X, y, threshold=0.1):
    """Correlation-based feature selection"""
    correlations = []
    for i in range(X.shape[1]):
        corr = np.abs(np.corrcoef(X[:, i], y)[0, 1])
        correlations.append(corr if not np.isnan(corr) else 0)
    return np.where(np.array(correlations) > threshold)[0]

def mutual_info_filter(X, y, n_features=10):
    """Mutual information feature selection"""
    mi_scores = []
    for i in range(X.shape[1]):
        # Simplified mutual info
        mi = np.abs(np.corrcoef(X[:, i], y)[0, 1])
        mi_scores.append(mi if not np.isnan(mi) else 0)
    return np.argsort(mi_scores)[::-1][:n_features]

def lasso_feature_selection(X, y, alpha=1.0):
    """Lasso-based feature selection"""
    from sklearn.linear_model import Lasso
    lasso = Lasso(alpha=alpha, max_iter=10000)
    lasso.fit(X, y)
    return np.where(np.abs(lasso.coef_) > 1e-6)[0]

if __name__ == '__main__':
    print('=== Feature Selection test ===')
    np.random.seed(42)
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=200, n_features=20, n_informative=10, random_state=42)
    print(f'Data shape: {X.shape}')
    var_idx = variance_threshold(X, threshold=0.5)
    print(f'Variance filter: {len(var_idx)} features')
    corr_idx = correlation_filter(X, y, threshold=0.1)
    print(f'Correlation filter: {len(corr_idx)} features')
    mi_idx = mutual_info_filter(X, y, n_features=10)
    print(f'Mutual info top 10: {mi_idx}')
    lasso_idx = lasso_feature_selection(X, y, alpha=0.5)
    print(f'Lasso selected: {lasso_idx}')
