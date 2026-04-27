# -*- coding: utf-8 -*-
"""
算法实现：生物信息学 / protein_function_prediction

本文件实现 protein_function_prediction 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional
import heapq


def blosum62_matrix() -> np.ndarray:
    """返回BLOSUM62矩阵"""
    aa_order = 'ARNDCQEGHILKMFPSTWYV'
    # 简化BLOSUM62（实际应从文件读取）
    blosum = np.zeros((20, 20))
    # 对角线正值，其他随机
    for i in range(20):
        blosum[i, i] = 11
    return blosum


def smith_waterman_simplified(
    seq1: str,
    seq2: str,
    match: float = 2.0,
    mismatch: float = -1.0,
    gap: float = -2.0
) -> float:
    """
    Smith-Waterman局部比对（简化版，评分而非回溯）

    参数:
        seq1, seq2: 序列
        match: 匹配得分
        mismatch: 错配罚分
        gap: 空位罚分

    返回:
        最高比对得分
    """
    n, m = len(seq1), len(seq2)
    dp = np.zeros((n + 1, m + 1))

    aa_to_idx = {aa: i for i, aa in enumerate('ARNDCQEGHILKMFPSTWYV')}
    # 使用BLOSUM简化评分
    blosum = blosum62_matrix()

    max_score = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            i1 = aa_to_idx.get(seq1[i-1], 0)
            i2 = aa_to_idx.get(seq2[j-1], 0)
            match_score = blosum[i1, i2] if seq1[i-1] == seq2[j-1] else -1

            dp[i, j] = max(0,
                          dp[i-1, j-1] + match_score,
                          dp[i-1, j] + gap,
                          dp[i, j-1] + gap)
            max_score = max(max_score, dp[i, j])

    return max_score


def blast_alignment(
    query: str,
    database: List[str],
    database_ids: List[str],
    evalue_threshold: float = 0.01
) -> List[Tuple[str, float]]:
    """
    简化BLAST搜索

    参数:
        query: 查询序列
        database: 数据库序列
        database_ids: 序列ID
        evalue_threshold: E-value阈值

    返回:
        [(matched_id, bit_score), ...]
    """
    results = []

    for db_seq, db_id in zip(database, database_ids):
        score = smith_waterman_simplified(query, db_seq)

        # 简化的E-value计算
        m, n = len(query), len(db_seq)
        lambda_param = 0.3  # 简化
        K = 0.1
        evalue = K * m * n * np.exp(-lambda_param * score)

        if evalue < evalue_threshold:
            results.append((db_id, score))

    # 按得分排序
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:10]


def go_annotation_propagation(
    go_graph: Dict[str, Set[str]],  # term -> parents
    annotations: Dict[str, Set[str]],  # protein -> GO terms
    target_protein: str
) -> Set[str]:
    """
    GO注释传播

    从已注释的蛋白质传播到目标蛋白质
    如果目标与某蛋白质同源，则继承其GO注释

    参数:
        go_graph: GO term层次图
        annotations: 蛋白质-GO注释
        target_protein: 目标蛋白质

    返回:
        预测的GO term集合
    """
    predicted_terms = set()

    # 简化：直接返回传入蛋白质的注释
    if target_protein in annotations:
        predicted_terms.update(annotations[target_protein])

        # 向上传播（获取更一般的GO term）
        for term in annotations[target_protein]:
            if term in go_graph:
                queue = list(go_graph[term])
                while queue:
                    parent = queue.pop(0)
                    predicted_terms.add(parent)
                    if parent in go_graph:
                        queue.extend(go_graph[parent])

    return predicted_terms


def domain_composition_score(
    query_domains: Set[str],
    target_domains: Set[str]
) -> float:
    """
    结构域组成评分

    参数:
        query_domains: 查询蛋白质的结构域集合
        target_domains: 目标蛋白质的结构域集合

    返回:
        相似度分数
    """
    if not query_domains or not target_domains:
        return 0.0

    intersection = len(query_domains & target_domains)
    union = len(query_domains | target_domains)

    return intersection / union if union > 0 else 0.0


def orthology_prediction(
    target_seq: str,
    ortholog_db: Dict[str, str],  # species -> sequence
    function_db: Dict[str, str]    # sequence -> function
) -> Dict[str, float]:
    """
    直系同源预测

    参数:
        target_seq: 目标序列
        ortholog_db: 直系同源数据库
        function_db: 功能数据库

    返回:
        {function: confidence}
    """
    scores = {}

    for seq_id, seq in ortholog_db.items():
        score = smith_waterman_simplified(target_seq, seq)
        if seq_id in function_db:
            func = function_db[seq_id]
            scores[func] = scores.get(func, 0) + score

    # 归一化
    total = sum(scores.values())
    if total > 0:
        scores = {k: v/total for k, v in scores.items()}

    return scores


if __name__ == '__main__':
    print('=== 蛋白质功能预测测试 ===')

    # 测试1: Smith-Waterman
    print('\n--- 测试1: Smith-Waterman局部比对 ---')
    seq1 = 'MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH'
    seq2 = 'MVLSGEDKSNIKAAWGKIGGHGAEYGAEALMERMFLSFPTTKTYFPHFDLSH'
    score = smith_waterman_simplified(seq1, seq2)
    print(f'  序列1: {seq1[:40]}...')
    print(f'  序列2: {seq2[:40]}...')
    print(f'  比对得分: {score:.2f}')

    # 测试2: BLAST搜索
    print('\n--- 测试2: BLAST搜索 ---')
    database = [
        'MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH',
        'MVLSGEDKSNIKAAWGKIGGHGAEYGAEALMERMFLSFPTTKTYFPHFDLSH',
        'ADLSPGMKTNIKAAGWAIVNSVYPQTAQIHAEALNMNDLSG',
        'MLSPADKTNVKAAWGKVGAHAGEYGAEAL',
        'MKTAIAIAVALAGFATVAQAAPAKTNNKAKWDR',
    ]
    db_ids = ['prot1', 'prot2', 'prot3', 'prot4', 'prot5']
    results = blast_alignment(seq1, database, db_ids, evalue_threshold=0.1)
    print(f'  查询序列长度: {len(seq1)}')
    print(f'  数据库大小: {len(database)}')
    print(f'  结果: {results}')

    # 测试3: GO注释传播
    print('\n--- 测试3: GO注释传播 ---')
    go_graph = {
        'GO:0008150': set(),  # biological_process
        'GO:0009987': set(),  # cellular_process
        'GO:0044237': {'GO:0008150', 'GO:0009987'},
        'GO:0044238': {'GO:0008150'},
    }
    annotations = {
        'prot1': {'GO:0044237', 'GO:0044238'},
        'prot2': {'GO:0008150'},
    }
    terms = go_annotation_propagation(go_graph, annotations, 'prot1')
    print(f'  prot1注释: {annotations["prot1"]}')
    print(f'  传播后: {terms}')

    # 测试4: 结构域组成
    print('\n--- 测试4: 结构域组成评分 ---')
    q_domains = {'PF00042', 'PF00190', 'PF01014'}
    t_domains = {'PF00042', 'PF00190', 'PF00578'}
    score = domain_composition_score(q_domains, t_domains)
    print(f'  查询域: {q_domains}')
    print(f'  目标域: {t_domains}')
    print(f'  相似度: {score:.3f}')

    # 测试5: 直系同源预测
    print('\n--- 测试5: 直系同源预测 ---')
    ortholog_db = {
        'seq1': 'MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH',
        'seq2': 'MVLSGEDKSNIKAAWGKIGGHGAEYGAEALMERMFLSFPTTKTYFPHFDLSH',
        'seq3': 'ADLSPGMKTNIKAAGWAIVNSVYPQTAQIHAEALNMNDLSG',
    }
    function_db = {
        'seq1': 'oxygen_transport',
        'seq2': 'oxygen_transport',
        'seq3': 'electron_transfer',
    }
    target = 'MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH'
    predictions = orthology_prediction(target, ortholog_db, function_db)
    print(f'  预测结果: {predictions}')
