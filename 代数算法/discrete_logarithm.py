# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / discrete_logarithm

本文件实现 discrete_logarithm 相关的算法功能。
"""

import math
from typing import Optional

def baby_step_giant_step(g: int, h: int, p: int) -> Optional[int]:
    """
    BSGS算法 - 求解离散对数
    
    找到最小的x使得 g^x ≡ h (mod p)
    
    Args:
        g: 底数（生成元）
        h: 目标值
        p: 模数（素数）
    
    Returns:
        离散对数x，如果不存在返回None
    """
    m = math.ceil(math.sqrt(p))
    baby_table = {}
    gj = 1
    
    for j in range(m):
        baby_table[gj] = j
        gj = (gj * g) % p
    
    gm = pow(g, p - 1 - m, p)
    gamma = h % p
    
    for i in range(m):
        if gamma in baby_table:
            x = i * m + baby_table[gamma]
            return x
        gamma = (gamma * gm) % p
    
    return None

if __name__ == "__main__":
    print("=== BSGS离散对数求解测试 ===")
    
    g, h, p = 3, 13, 17
    x = baby_step_giant_step(g, h, p)
    print(f"求解 {g}^x ≡ {h} (mod {p})")
    print(f"求得 x = {x}")
    print(f"验证: {g}^{x} mod {p} = {pow(g, x, p)}")
    
    g, h, p = 2, 15, 23
    x = baby_step_giant_step(g, h, p)
    print(f"求解 {g}^x ≡ {h} (mod {p})")
    print(f"求得 x = {x}")
    if x is not None:
        print(f"验证: {g}^{x} mod {p} = {pow(g, x, p)}")
    
    g, h, p = 2, 7, 13
    x = baby_step_giant_step(g, h, p)
    print(f"求解 {g}^x ≡ {h} (mod {p})")
    print(f"求得 x = {x} (无解情况)")
