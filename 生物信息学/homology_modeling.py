# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / homology_modeling



本文件实现 homology_modeling 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional

import math





def blosum62_score(a1: str, a2: str) -> float:

    """BLOSUM62矩阵评分"""

    blosum = {

        ('A', 'A'): 4, ('A', 'R'): -1, ('A', 'N'): -2, ('A', 'D'): -2,

        ('A', 'C'): 0, ('A', 'Q'): -1, ('A', 'E'): -1, ('A', 'G'): 0,

        ('A', 'H'): -2, ('A', 'I'): -1, ('A', 'L'): -1, ('A', 'K'): -1,

        ('A', 'M'): -1, ('A', 'F'): -2, ('A', 'P'): -1, ('A', 'S'): 1,

        ('A', 'T'): 0, ('A', 'W'): -3, ('A', 'Y'): -2, ('A', 'V'): 0,

        # ... 简化版

    }

    return blosum.get((a1, a2), blosum.get((a2, a1), -4))





def sequence_alignment_score(seq1: str, seq2: str) -> float:

    """

    简化全局序列比对评分



    参数:

        seq1: 序列1

        seq2: 序列2



    返回:

        比对得分

    """

    score = 0

    min_len = min(len(seq1), len(seq2))

    for i in range(min_len):

        score += blosum62_score(seq1[i], seq2[i])

    return score





def backbone_builder(template_ca_coords: np.ndarray, target_seq: str) -> np.ndarray:

    """

    基于模板CA骨架构建目标骨架



    参数:

        template_ca_coords: 模板CA原子坐标 (n, 3)

        target_seq: 目标序列



    返回:

        预测的CA坐标

    """

    n = len(target_seq)

    # 简化：假设相同长度的骨架，直接复制坐标

    # 实际需要考虑插入/缺失

    n_template = len(template_ca_coords)

    n_copy = min(n, n_template)



    model_coords = np.zeros((n, 3))

    model_coords[:n_copy] = template_ca_coords[:n_copy]



    # 对于额外的残基，假设为伸展构象

    for i in range(n_copy, n):

        prev = model_coords[i - 1]

        # 肽键长度约3.8A

        model_coords[i] = prev + np.array([3.8, 0, 0])



    return model_coords





def simple_rotamer_place(

    residue_type: str,

    backbone_coords: np.ndarray,

    phi: float,

    psi: float

) -> Dict[str, np.ndarray]:

    """

    简化Rotamer侧链放置



    参数:

        residue_type: 氨基酸类型

        backbone_coords: 主链原子坐标 [N, CA, C]

        phi, psi: 二面角



    返回:

        侧链原子坐标字典

    """

    n, ca, c = backbone_coords



    # 简化：只放置CB原子

    # 方向由phi, psi决定

    cb_direction = np.array([0.5, 0.5, 0])

    cb_pos = ca + cb_direction



    side_chain = {'CB': cb_pos}



    # 根据氨基酸类型添加更多原子

    if residue_type in ['S', 'T', 'Y']:

        og_pos = cb_pos + np.array([1.2, 0, 0])

        side_chain['OG'] = og_pos if residue_type == 'S' else None

        side_chain['OG1'] = og_pos if residue_type == 'T' else None

        side_chain['OH'] = og_pos if residue_type == 'Y' else None



    return {k: v for k, v in side_chain.items() if v is not None}





def energy_minimize(coords: np.ndarray, n_steps: int = 100) -> np.ndarray:

    """

    简化能量最小化（最速下降法）



    参数:

        coords: 原子坐标

        n_steps: 迭代步数



    返回:

        优化后的坐标

    """

    coords = coords.copy()



    # 简化的Lennard-Jones势

    def energy(c):

        E = 0.0

        for i in range(len(c)):

            for j in range(i + 1, len(c)):

                r = np.linalg.norm(c[i] - c[j])

                if r < 1.0:

                    E += 100 * (r - 1.0) ** 2

                elif r > 10.0:

                    E += 0.01 / r

                else:

                    E += 4 * ((1/r)**12 - (1/r)**6)

        return E



    step_size = 0.1

    for step in range(n_steps):

        grad = np.zeros_like(coords)

        eps = 0.01



        for i in range(len(coords)):

            for dim in range(3):

                coords_plus = coords.copy()

                coords_plus[i, dim] += eps

                coords_minus = coords.copy()

                coords_minus[i, dim] -= eps

                grad[i, dim] = (energy(coords_plus) - energy(coords_minus)) / (2 * eps)



        coords = coords - step_size * grad



        if step % 20 == 0:

            step_size *= 0.9



    return coords





def homology_modeling_quality(rmsd: float, seq_id: float) -> str:

    """

    同源模型质量评估



    参数:

        rmsd: 与模板的RMSD

        seq_id: 序列同一性



    返回:

        质量等级

    """

    if rmsd < 1.5 and seq_id > 0.5:

        return '非常高的精度'

    elif rmsd < 2.5 and seq_id > 0.3:

        return '高精度'

    elif rmsd < 4.0 and seq_id > 0.2:

        return '中等精度'

    elif rmsd < 6.0:

        return '低精度'

    else:

        return '模型不可靠'





if __name__ == '__main__':

    print('=== 同源建模测试 ===')



    # 测试1: 序列比对

    print('\n--- 测试1: 序列比对评分 ---')

    seq1 = 'MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH'

    seq2 = 'MVLSGEDKSNIKAAWGKIGGHGAEYGAEALMERMFLSFPTTKTYFPHFDLSH'

    score = sequence_alignment_score(seq1, seq2)

    print(f'  序列1: {seq1[:30]}...')

    print(f'  序列2: {seq2[:30]}...')

    print(f'  比对得分: {score}')



    # 测试2: 骨架构建

    print('\n--- 测试2: 骨架构建 ---')

    template_ca = np.random.rand(10, 3) * 10

    target = 'ACDEFGHIKL'

    model_ca = backbone_builder(template_ca, target)

    print(f'  模板CA数: {len(template_ca)}')

    print(f'  目标序列长度: {len(target)}')

    print(f'  模型CA数: {len(model_ca)}')

    print(f'  模型坐标范围: [{model_ca.min():.2f}, {model_ca.max():.2f}]')



    # 测试3: 侧链放置

    print('\n--- 测试3: 侧链放置 ---')

    backbone = np.array([[0, 0, 0], [1.5, 0, 0], [2.5, 1.2, 0]])

    for aa in ['A', 'G', 'S']:

        rotamers = simple_rotamer_place(aa, backbone, -1.0, -0.5)

        print(f'  {aa}: {list(rotamers.keys())}')



    # 测试4: 能量最小化

    print('\n--- 测试4: 能量最小化 ---')

    np.random.seed(42)

    coords = np.random.rand(20, 3) * 10

    minimized = energy_minimize(coords, n_steps=50)

    print(f'  初始坐标范围: [{coords.min():.2f}, {coords.max():.2f}]')

    print(f'  最小化后: [{minimized.min():.2f}, {minimized.max():.2f}]')



    # 测试5: 模型质量评估

    print('\n--- 测试5: 模型质量评估 ---')

    test_cases = [(1.2, 0.6), (2.0, 0.4), (3.5, 0.25), (5.0, 0.15)]

    for rmsd, seq_id in test_cases:

        quality = homology_modeling_quality(rmsd, seq_id)

        print(f'  RMSD={rmsd:.1f}A, SeqID={seq_id:.2f}: {quality}')

