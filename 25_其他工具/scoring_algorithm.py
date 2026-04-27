# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / scoring_algorithm

本文件实现 scoring_algorithm 相关的算法功能。
"""

from __future__ import annotations


def get_data(source_data: list[list[float]]) -> list[list[float]]:
    """
    转置数据：将按行存储的数据转为按列存储。
    
    输入: [[row1_col1, row1_col2], [row2_col1, row2_col2]]
    输出: [[col1_row1, col1_row2], [col2_row1, col2_row2]]
    
    Args:
        source_data: 原始数据（行列表）
    
    Returns:
        转置后的数据（列列表）
    
    示例:
        >>> get_data([[20, 60, 2012],[23, 90, 2015],[22, 50, 2011]])
        [[20.0, 23.0, 22.0], [60.0, 90.0, 50.0], [2012.0, 2015.0, 2011.0]]
    """
    data_lists: list[list[float]] = []
    for data in source_data:
        for i, el in enumerate(data):
            if len(data_lists) < i + 1:
                data_lists.append([])
            data_lists[i].append(float(el))
    return data_lists


def calculate_each_score(
    data_lists: list[list[float]], weights: list[int]
) -> list[list[float]]:
    """
    根据权重计算每列的得分。
    
    Args:
        data_lists: 转置后的列数据
        weights: 每列的权重（0=越小越好，1=越大越好）
    
    Returns:
        每列的得分列表
    
    示例:
        >>> calculate_each_score([[20, 23, 22], [60, 90, 50], [2012, 2015, 2011]], [0, 0, 1])
        [[1.0, 0.0, 0.33...], [0.75, 0.0, 1.0], [0.25, 1.0, 0.0]]
    """
    score_lists: list[list[float]] = []
    for dlist, weight in zip(data_lists, weights):
        mind = min(dlist)
        maxd = max(dlist)

        score: list[float] = []
        # 权重 0：越小越好，得分 = 1 - 归一化值
        if weight == 0:
            for item in dlist:
                try:
                    score.append(1 - ((item - mind) / (maxd - mind)))
                except ZeroDivisionError:
                    score.append(1)

        # 权重 1：越大越好，得分 = 归一化值
        elif weight == 1:
            for item in dlist:
                try:
                    score.append((item - mind) / (maxd - mind))
                except ZeroDivisionError:
                    score.append(0)

        else:
            msg = f"Invalid weight of {weight:f} provided"
            raise ValueError(msg)

        score_lists.append(score)

    return score_lists


def generate_final_scores(score_lists: list[list[float]]) -> list[float]:
    """
    将各列得分合并为最终总分。
    
    Args:
        score_lists: 各列得分列表
    
    Returns:
        每个样本的最终得分
    
    示例:
        >>> generate_final_scores([[1.0, 0.0, 0.33...], [0.75, 0.0, 1.0], [0.25, 1.0, 0.0]])
        [2.0, 1.0, 1.33...]
    """
    # 初始化最终得分
    final_scores: list[float] = [0 for i in range(len(score_lists[0]))]

    for slist in score_lists:
        for j, ele in enumerate(slist):
            final_scores[j] = final_scores[j] + ele

    return final_scores


def procentual_proximity(
    source_data: list[list[float]], weights: list[int]
) -> list[list[float]]:
    """
    主函数：计算每个样本的百分比 proximity 得分。
    
    Args:
        source_data: 原始数据 [[值1, 值2, ...], ...]
        weights: 每列权重 [w1, w2, ...]（0=越小越好，1=越大越好）
    
    Returns:
        原始数据 + 最终得分列
    
    示例:
        >>> procentual_proximity([[20, 60, 2012],[23, 90, 2015],[22, 50, 2011]], [0, 0, 1])
        [[20, 60, 2012, 2.0], [23, 90, 2015, 1.0], [22, 50, 2011, 1.33...]]
    """
    # 转置数据
    data_lists = get_data(source_data)
    # 计算每列得分
    score_lists = calculate_each_score(data_lists, weights)
    # 计算最终得分
    final_scores = generate_final_scores(score_lists)

    # 将得分附加到原始数据
    for i, ele in enumerate(final_scores):
        source_data[i].append(ele)

    return source_data


# ==========================================================
# 测试代码
# ==========================================================
if __name__ == "__main__":
    # 示例：车辆选购决策
    # 指标：价格、里程、注册年份
    # 权重：[0, 0, 1] 表示价格越低越好，里程越低越好，年份越新越好
    vehicles = [
        [20000, 60000, 2012],
        [23000, 90000, 2015],
        [22000, 50000, 2011],
    ]
    weights = [0, 0, 1]  # 价格、里程、年份
    
    result = procentual_proximity(vehicles, weights)
    print("=== 车辆评分结果 ===")
    for i, row in enumerate(result):
        print(f"车辆{i+1}: 价格={row[0]}, 里程={row[1]}, 年份={row[2]} -> 得分={row[3]:.2f}")
