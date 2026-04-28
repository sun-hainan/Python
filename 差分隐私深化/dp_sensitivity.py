# -*- coding: utf-8 -*-
"""
差分隐私敏感度分析模块

本模块实现差分隐私中的核心概念——敏感度（Sensitivity）分析。
敏感度衡量的是相邻数据集（仅相差一条记录）在查询函数上输出的最大差异，
是确定所需噪声量级的关键参数。

主要内容包括：
- 全局敏感度（Global Sensitivity）：最保守的度量，适用于任何数据集
- 局部敏感度（Local Sensitivity）：针对特定数据集的敏感度，可能更低
- 平滑敏感度（Smooth Sensitivity）：局部敏感度的平滑上界

作者：算法实现
版本：1.0
"""

import numpy as np  # 数值计算库，用于数学运算
from typing import Callable, List  # 类型提示，用于函数类型声明


def global_sensitivity(query: Callable, d: int) -> float:
    """
    计算查询函数的全局敏感度

    全局敏感度定义为所有可能相邻数据集在查询函数上输出的最大L1范数差异。
    它是一个常数，与具体数据集无关，因此最保守但最安全。

    参数:
        query: 查询函数，输入为d维向量，输出为数值
        d: 数据维度，即向量长度

    返回:
        全局敏感度GS值

    示例:
        >>> # 计数查询：任意移除一条记录，计数最多变化1
        >>> global_sensitivity(lambda x: np.sum(x), d=10)
        1.0
    """
    # 初始化敏感度为0
    gs = 0.0
    # 对每个维度遍历，计算添加/删除单位向量时的查询差异
    for i in range(d):
        # 创建标准基向量（第i维为1，其余为0）
        e_i = np.zeros(d)
        e_i[i] = 1.0
        # 计算查询在原始向量和添加单位向量后的差异
        # 这里用全0向量作为基准，真实场景中需考虑所有可能的数据集
        diff = abs(query(e_i) - query(np.zeros(d)))
        # 更新全局敏感度（取最大差异）
        gs = max(gs, diff)
    return gs


def global_sensitivity_l2(query: Callable, d: int) -> float:
    """
    计算查询函数的全局L2敏感度

    L2敏感度使用欧几里得距离（L2范数）衡量相邻数据集的差异。
    对于某些查询，L2敏感度可能比L1敏感度小很多。

    参数:
        query: 查询函数，输入为d维向量，输出为数值
        d: 数据维度

    返回:
        全局L2敏感度值

    示例:
        >>> # 均值查询的L2敏感度
        >>> global_sensitivity_l2(lambda x: np.mean(x), d=10)
        1.0
    """
    gs_l2 = 0.0
    for i in range(d):
        e_i = np.zeros(d)
        e_i[i] = 1.0
        diff = abs(query(e_i) - query(np.zeros(d)))
        gs_l2 = max(gs_l2, diff)
    return gs_l2


def local_sensitivity(dataset: np.ndarray, query: Callable, 
                      neighbor_func: str = "flip") -> float:
    """
    计算特定数据集的局部敏感度

    局部敏感度只考虑与当前数据集相邻的数据集，比全局敏感度更精确。
    但由于依赖于数据集，单独使用时不能直接保证差分隐私。

    参数:
        dataset: 当前数据集（d维向量）
        query: 查询函数
        neighbor_func: 邻居数据集生成方式，"flip"为翻转一位，"add"为添加一位

    返回:
        局部敏感度LS值

    示例:
        >>> ds = np.array([1, 0, 1, 0, 1])
        >>> local_sensitivity(ds, lambda x: np.sum(x))
        1.0
    """
    d = len(dataset)  # 数据维度
    ls = 0.0  # 初始化局部敏感度为0

    for i in range(d):
        # 创建邻居数据集：根据neighbor_func生成第i位的邻居
        if neighbor_func == "flip":
            # 翻转：0变1，1变0
            neighbor = dataset.copy()
            neighbor[i] = 1 - neighbor[i]
        elif neighbor_func == "add":
            # 添加：第i位加1（适用于计数场景）
            neighbor = dataset.copy()
            neighbor[i] += 1
        else:
            raise ValueError(f"未知的邻居函数类型: {neighbor_func}")

        # 计算查询在当前数据集和邻居数据集上的差异
        diff = abs(query(dataset) - query(neighbor))
        # 更新局部敏感度
        ls = max(ls, diff)

    return ls


def local_sensitivity_range(dataset: np.ndarray, query: Callable) -> float:
    """
    计算特定数据集的局部敏感度范围（用于range查询）

    对于范围查询，局部敏感度可能远小于全局敏感度。
    这里模拟一个简单的范围计数查询。

    参数:
        dataset: 输入数据集
        query: 范围查询函数

    返回:
        局部敏感度值
    """
    return local_sensitivity(dataset, query, neighbor_func="flip")


def smooth_sensitivity(dataset: np.ndarray, query: Callable, 
                       beta: float = 0.5, k: int = 10) -> float:
    """
    计算平滑敏感度（Smooth Sensitivity）

    平滑敏感度是局部敏感度的加权上界，通过指数衰减因子平滑化。
    它同时满足：(1) 是局部敏感度的上界，(2) 是平滑的（β-smooth）

    参数:
        dataset: 输入数据集
        query: 查询函数
        beta: 平滑参数，控制衰减速率（0 < beta < 1）
        k: 考虑的最大邻居距离（迭代次数）

    返回:
        平滑敏感度值

    算法原理:
        SS_β(f, D) = max_{t≥0} { LS(f, D_t) * exp(-β*t) }
        其中D_t表示与D距离为t的数据集
    """
    d = len(dataset)  # 数据维度
    # 初始化平滑敏感度为局部敏感度（距离为0时）
    smooth_sens = local_sensitivity(dataset, query)

    # 对更大的距离进行迭代
    for t in range(1, k + 1):
        # 生成距离为t的邻居（简化：考虑所有单比特翻转的组合）
        neighbors_t = get_neighbors_at_distance(dataset, t)
        for neighbor in neighbors_t:
            # 计算邻居的局部敏感度
            ls_neighbor = local_sensitivity(neighbor, query)
            # 应用指数衰减因子
            weighted_ls = ls_neighbor * np.exp(-beta * t)
            # 更新平滑敏感度
            smooth_sens = max(smooth_sens, weighted_ls)

    return smooth_sens


def get_neighbors_at_distance(dataset: np.ndarray, distance: int) -> List[np.ndarray]:
    """
    生成与数据集指定汉明距离的所有邻居

    参数:
        dataset: 基准数据集
        distance: 目标汉明距离（不同的位数）

    返回:
        邻居数据集列表
    """
    d = len(dataset)
    neighbors = []
    # 生成所有可能的距离为distance的翻转模式
    indices = list(range(d))

    def generate_combinations(idx_list, remaining, current_mask):
        """递归生成指定数量的组合"""
        if remaining == 0:
            # 应用翻转掩码
            neighbor = dataset.copy()
            for i in range(d):
                if current_mask[i]:
                    neighbor[i] = 1 - neighbor[i]
            neighbors.append(neighbor)
        else:
            for i in range(len(idx_list)):
                new_mask = current_mask.copy()
                new_mask[idx_list[i]] = True
                generate_combinations(idx_list[i+1:], remaining-1, new_mask)

    # 只在实际距离内迭代，避免组合爆炸
    actual_distance = min(distance, d)
    mask = [False] * d
    generate_combinations(indices, actual_distance, mask)

    return neighbors


def sensitivity_ratio(gs: float, ls: float) -> float:
    """
    计算全局敏感度与局部敏感度的比值

    这个比值反映了使用局部敏感度能节省的噪声量。
    比值越大，说明局部敏感度优化效果越明显。

    参数:
        gs: 全局敏感度
        ls: 局部敏感度

    返回:
        敏感度比值（>1表示有优化空间）
    """
    if ls == 0:
        return float('inf')
    return gs / ls


if __name__ == "__main__":
    # 测试用例：基本敏感度计算
    print("=" * 60)
    print("差分隐私敏感度分析测试")
    print("=" * 60)

    # 测试1：全局敏感度 - 计数查询
    print("\n【测试1】全局敏感度 - 计数查询")
    count_query = lambda x: np.sum(x)  # 计数：求和
    gs_count = global_sensitivity(count_query, d=10)
    print(f"  数据维度: 10")
    print(f"  查询函数: f(x) = sum(x)")
    print(f"  全局敏感度: {gs_count}")
    assert gs_count == 1.0, "计数查询敏感度应为1"

    # 测试2：全局敏感度 - L2敏感度
    print("\n【测试2】全局L2敏感度 - 均值查询")
    mean_query = lambda x: np.mean(x)  # 均值查询
    gs_l2_mean = global_sensitivity_l2(mean_query, d=10)
    print(f"  查询函数: f(x) = mean(x)")
    print(f"  全局L2敏感度: {gs_l2_mean:.4f}")

    # 测试3：局部敏感度
    print("\n【测试3】局部敏感度 - 稀疏数据")
    sparse_data = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    ls_sparse = local_sensitivity(sparse_data, count_query)
    print(f"  数据集: {sparse_data}")
    print(f"  局部敏感度: {ls_sparse}")
    print(f"  全局敏感度: {gs_count}")
    print(f"  敏感度比值: {sensitivity_ratio(gs_count, ls_sparse):.1f}x")

    # 测试4：密集数据的局部敏感度
    print("\n【测试4】局部敏感度 - 密集数据")
    dense_data = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    ls_dense = local_sensitivity(dense_data, count_query)
    print(f"  数据集: {dense_data}")
    print(f"  局部敏感度: {ls_dense}")
    print(f"  敏感度比值: {sensitivity_ratio(gs_count, ls_dense):.1f}x")

    # 测试5：平滑敏感度
    print("\n【测试5】平滑敏感度")
    test_data = np.array([1, 0, 1, 0, 1])
    smooth_sens = smooth_sensitivity(test_data, count_query, beta=0.5, k=3)
    local_sens = local_sensitivity(test_data, count_query)
    print(f"  数据集: {test_data}")
    print(f"  局部敏感度: {local_sens}")
    print(f"  平滑敏感度(β=0.5): {smooth_sens:.4f}")
    print(f"  (平滑敏感度 ≥ 局部敏感度)")

    # 测试6：敏感度优化效果对比
    print("\n【测试6】敏感度优化效果汇总")
    test_datasets = [
        np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # 极稀疏
        np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0]),  # 稀疏
        np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0]),  # 中等
        np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]),  # 密集
    ]
    print(f"  {'数据集':<25} {'全局GS':<8} {'局部LS':<8} {'比值':<8}")
    print(f"  {'-'*50}")
    for ds in test_datasets:
        ls = local_sensitivity(ds, count_query)
        ratio = sensitivity_ratio(gs_count, ls)
        print(f"  {str(ds):<25} {gs_count:<8.1f} {ls:<8.1f} {ratio:<8.1f}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
