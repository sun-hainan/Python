# -*- coding: utf-8 -*-
"""
算法实现：生物信息学 / methylation_analysis

本文件实现 methylation_analysis 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict
import math


def bisulfite_conversion_check(converted_seq: str, original_seq: str) -> float:
    """
    检查亚硫酸氢盐转化效率

    未甲基化C -> T（转化）
    甲基化C -> C（保持）

    参数:
        converted_seq: 转化后序列
        original_seq: 原始序列

    返回:
        转化率
    """
    if len(converted_seq) != len(original_seq):
        return 0.0

    n_c = 0
    n_converted = 0

    for c, r in zip(converted_seq, original_seq):
        if r == 'C':
            n_c += 1
            if c == 'T':
                n_converted += 1

    return n_converted / n_c if n_c > 0 else 0.0


def methylation_level(
    methylated_count: int,
    total_count: int
) -> float:
    """
    计算甲基化水平

    参数:
        methylated_count: 甲基化reads数
        total_count: 总reads数

    返回:
        甲基化百分比
    """
    if total_count == 0:
        return 0.0
    return 100.0 * methylated_count / total_count


def cpg_observation_density(genome_seq: str, window_size: int = 1000) -> List[float]:
    """
    计算CpG观测密度

    参数:
        genome_seq: 基因组序列
        window_size: 窗口大小

    返回:
        每窗口的CpG密度
    """
    densities = []
    n = len(genome_seq)

    for i in range(0, n - window_size, window_size):
        window = genome_seq[i:i+window_size]
        cpg_count = window.count('CG')
        # 期望值：(num_C * num_G) / window_size
        expected = (window.count('C') * window.count('G')) / window_size
        # 观测/期望比
        density = cpg_count / expected if expected > 0 else 0
        densities.append(density)

    return densities


def methylation_calling(
    bismark_cov: List[Tuple[int, str, int, int]],  # (pos, strand, meth, total)
    threshold: float = 0.5
) -> Dict[str, List[Tuple[int, float]]]:
    """
    甲基化位点识别

    参数:
        bismark_cov: Bismark coverage格式
        threshold: 甲基化阈值

    返回:
        {chromosome: [(position, methylation_level), ...]}
    """
    results = defaultdict(list)

    for pos, strand, meth_count, total_count in bismark_cov:
        if total_count >= 5:  # 最小覆盖度
            level = methylation_level(meth_count, total_count)
            if level >= threshold * 100:
                results['chr1'].append((pos, level))

    return dict(results)


def differential_methylation(
    sample1_levels: Dict[int, float],
    sample2_levels: Dict[int, float],
    min_diff: float = 20.0
) -> List[Tuple[int, float, float]]:
    """
    差异甲基化分析

    参数:
        sample1_levels: 样本1甲基化水平 {pos: level}
        sample2_levels: 样本2甲基化水平
        min_diff: 最小差异阈值

    返回:
        [(position, level1, level2), ...] 差异甲基化位点
    """
    diff_sites = []

    all_pos = set(sample1_levels.keys()) & set(sample2_levels.keys())

    for pos in all_pos:
        l1 = sample1_levels[pos]
        l2 = sample2_levels[pos]
        diff = abs(l1 - l2)

        if diff >= min_diff:
            diff_sites.append((pos, l1, l2))

    return sorted(diff_sites, key=lambda x: abs(x[1] - x[2]), reverse=True)


def methylation_beta_value(intensity_m: float, intensity_u: float) -> float:
    """
    计算Beta值（Illumina芯片用）

    Beta = M / (M + U + 100)

    参数:
        intensity_m: 甲基化探针强度
        intensity_u: 非甲基化探针强度

    返回:
        Beta值 [0, 1]
    """
    return intensity_m / (intensity_m + intensity_u + 100)


def methylation_m_value(intensity_m: float, intensity_u: float) -> float:
    """
    计算M值（统计用，更正态）

    M = log2((M + 100) / (U + 100))

    参数:
        intensity_m: 甲基化探针强度
        intensity_u: 非甲基化探针强度

    返回:
        M值
    """
    return math.log2((intensity_m + 100) / (intensity_u + 100))


if __name__ == '__main__':
    print('=== 甲基化分析测试 ===')

    # 测试1: 亚硫酸氢盐转化
    print('\n--- 测试1: 亚硫酸氢盐转化效率 ---')
    original = 'ATCGGCCAATTCCGG'
    converted = 'ATTGGTTAATTGG'  # 简化
    # 更现实的例子
    original2 = 'ATCGATCGATCGTACG'
    converted2 = 'ATTGATTGATTGTATG'  # C->T
    efficiency = bisulfite_conversion_check(converted2, original2)
    print(f'  原始: {original2}')
    print(f'  转化: {converted2}')
    print(f'  转化率: {efficiency:.2%}')

    # 测试2: 甲基化水平
    print('\n--- 测试2: 甲基化水平 ---')
    for meth, total in [(5, 10), (8, 10), (2, 10), (0, 10)]:
        level = methylation_level(meth, total)
        print(f'  甲基化{meth}/{total}: {level:.1f}%')

    # 测试3: CpG密度
    print('\n--- 测试3: CpG观测密度 ---')
    seq = 'ATCGATCGATCGTACGATCGATCGCGCGCGCGATCGATCG'
    densities = cpg_observation_density(seq, window_size=20)
    print(f'  序列: {seq}')
    print(f'  CpG密度: {[f"{d:.2f}" for d in densities]}')

    # 测试4: 差异甲基化
    print('\n--- 测试4: 差异甲基化分析 ---')
    sample1 = {100: 80.0, 200: 50.0, 300: 90.0, 400: 10.0, 500: 60.0}
    sample2 = {100: 20.0, 200: 55.0, 300: 95.0, 400: 15.0, 500: 30.0}
    diff_sites = differential_methylation(sample1, sample2, min_diff=25.0)
    print(f'  差异甲基化位点: {diff_sites}')

    # 测试5: Beta vs M值
    print('\n--- 测试5: Beta值和M值 ---')
    for m_int, u_int in [(500, 100), (100, 500), (300, 300), (1000, 50)]:
        beta = methylation_beta_value(m_int, u_int)
        m_val = methylation_m_value(m_int, u_int)
        print(f'  M={m_int}, U={u_int}: Beta={beta:.3f}, M={m_val:.3f}')
