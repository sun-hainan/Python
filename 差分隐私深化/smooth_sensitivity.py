# -*- coding: utf-8 -*-
"""
平滑敏感度方法模块

本模块实现平滑敏感度（Smooth Sensitivity）计算方法。
平滑敏感度是局部敏感度的加权上界，比全局敏感度更紧。

适用于：复杂查询、自适应查询、迭代算法。

作者：算法实现
版本：1.0
"""

import numpy as np
from typing import Callable, List


def local_sensitivity(dataset: np.ndarray, query: Callable) -> float:
    """计算数据集的局部敏感度"""
    d = len(dataset)
    max_sens = 0.0
    for i in range(d):
        neighbor = dataset.copy()
        neighbor[i] = 1 - neighbor[i]
        diff = abs(query(dataset) - query(neighbor))
        max_sens = max(max_sens, diff)
    return max_sens


def smooth_sensitivity(dataset: np.ndarray, query: Callable,
                       beta: float = 0.5, max_dist: int = 10) -> float:
    """
    计算平滑敏感度

    SS_β(f, D) = max_{t≥0} { LS(f, D_t) * exp(-β*t) }

    参数:
        dataset: 输入数据集
        query: 查询函数
        beta: 平滑参数（0 < β < 1）
        max_dist: 最大考虑距离

    返回:
        平滑敏感度值
    """
    d = len(dataset)
    base_ls = local_sensitivity(dataset, query)
    smooth_sens = base_ls

    for t in range(1, max_dist + 1):
        neighbors_t = get_neighbors_at_distance(dataset, t)
        for neighbor in neighbors_t:
            ls_neighbor = local_sensitivity(neighbor, query)
            weighted = ls_neighbor * np.exp(-beta * t)
            smooth_sens = max(smooth_sens, weighted)

    return smooth_sens


def get_neighbors_at_distance(dataset: np.ndarray, dist: int) -> List[np.ndarray]:
    """生成距离为dist的邻居"""
    d = len(dataset)
    neighbors = []

    def generate(idx, remaining, mask):
        if remaining == 0:
            neighbor = dataset.copy()
            for i in range(d):
                if mask[i]:
                    neighbor[i] = 1 - neighbor[i]
            neighbors.append(neighbor)
        else:
            for i in range(idx, d - remaining + 1):
                mask[i] = True
                generate(i + 1, remaining - 1, mask)
                mask[i] = False

    actual_dist = min(dist, d)
    if actual_dist > 0:
        generate(0, actual_dist, [False] * d)
    return neighbors


def adaptive_smooth_sensitivity(dataset: np.ndarray, query: Callable,
                                  delta: float = 1e-5) -> float:
    """
    自适应平滑敏感度

    根据数据集特性自动选择β。

    参数:
        dataset: 数据集
        query: 查询函数
        delta: 隐私参数

    返回:
        自适应平滑敏感度
    """
    ls = local_sensitivity(dataset, query)
    d = len(dataset)
    beta = np.log(d / delta) / d
    return smooth_sensitivity(dataset, query, beta=beta)


if __name__ == "__main__":
    print("=" * 60)
    print("平滑敏感度测试")
    print("=" * 60)

    print("\n【测试1】基本平滑敏感度")
    count_query = lambda x: np.sum(x)
    data = np.array([1, 0, 1, 0, 1, 0, 0, 1, 0, 1])

    ls = local_sensitivity(data, count_query)
    ss = smooth_sensitivity(data, count_query, beta=0.5, max_dist=5)

    print(f"  数据: {data}")
    print(f"  局部敏感度: {ls}")
    print(f"  平滑敏感度(β=0.5): {ss:.4f}")

    print("\n【测试2】不同β的影响")
    for beta in [0.1, 0.3, 0.5, 0.7, 1.0]:
        ss = smooth_sensitivity(data, count_query, beta=beta, max_dist=5)
        print(f"  β={beta}: SS={ss:.4f}")

    print("\n【测试3】不同数据集")
    datasets = [
        np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0]),
        np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0]),
        np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),
    ]
    print(f"  {'数据集':<25} {'LS':<8} {'SS':<8}")
    print(f"  {'-'*40}")
    for ds in datasets:
        ls = local_sensitivity(ds, count_query)
        ss = smooth_sensitivity(ds, count_query, beta=0.5, max_dist=5)
        print(f"  {str(ds):<25} {ls:<8.1f} {ss:<8.4f}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
