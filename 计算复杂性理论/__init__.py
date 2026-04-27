# -*- coding: utf-8 -*-
"""
计算复杂性理论算法包

本包包含计算复杂性理论的各种算法和概念实现。

主要模块：
- time_hierarchy: 时间层次定理
- bpp_algorithm: BPP（多项式时间随机算法）
- cook_levin: Cook-Levin定理（SAT的NP完全性）

使用方法：
    from cook_levin import prove_sat_in_np
    proof = prove_sat_in_np()
"""

# 版本信息
__version__ = "1.0.0"
__all__ = [
    "time_hierarchy",
    "bpp_algorithm",
    "cook_levin",
]
