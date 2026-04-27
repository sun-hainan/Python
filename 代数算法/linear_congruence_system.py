# -*- coding: utf-8 -*-

"""

算法实现：代数算法 / linear_congruence_system



本文件实现 linear_congruence_system 相关的算法功能。

"""



from typing import List, Tuple, Optional



def extended_euclidean(a: int, b: int) -> tuple:

    if a == 0:

        return b, 0, 1

    if b == 0:

        return a, 1, 0

    gcd_val, x1, y1 = extended_euclidean(b, a % b)

    return gcd_val, y1, x1 - (a // b) * y1



def chinese_remainder_theorem(remainders: List[int], moduli: List[int]) -> Optional[int]:

    """

    中国剩余定理 - 求解同余方程组

    

    Args:

        remainders: 余数列表

        moduli: 模数列表（两两互质）

    

    Returns:

        满足所有同余式的最小非负整数

    """

    M = 1

    for mod in moduli:

        M *= mod

    

    result = 0

    for ai, mi in zip(remainders, moduli):

        Mi = M // mi

        _, yi, _ = extended_euclidean(Mi, mi)

        yi = yi % mi

        result = (result + ai * Mi * yi) % M

    

    return result



def solve_general_congruence_system(remainders: List[int], moduli: List[int]) -> Optional[Tuple[int, int]]:

    """求解一般同余方程组（模数不必互质）"""

    if len(remainders) != len(moduli):

        return None

    

    x = remainders[0]

    lcm_val = moduli[0]

    

    for i in range(1, len(remainders)):

        ai, mi = remainders[i], moduli[i]

        diff = (ai - x) % mi

        

        gcd_val, s, _ = extended_euclidean(lcm_val, mi)

        if diff % gcd_val != 0:

            return None

        

        t = (s * (diff // gcd_val)) % mi

        x = x + lcm_val * t

        lcm_val = lcm_val * (mi // gcd_val)

        x = x % lcm_val

    

    return (x, lcm_val)



if __name__ == "__main__":

    print("=== 中国剩余定理测试 ===")

    

    remainders = [2, 3, 2]

    moduli = [3, 5, 7]

    x = chinese_remainder_theorem(remainders, moduli)

    print(f"同余方程组: x ≡ {remainders} (mod {moduli})")

    print(f"解: x = {x}")

    

    if x is not None:

        for r, m in zip(remainders, moduli):

            print(f"验证: {x} % {m} = {x % m}, 期望 {r}")

    

    print("\n=== 一般同余方程组测试 ===")

    remainders2 = [2, 3, 1]

    moduli2 = [4, 6, 8]

    result = solve_general_congruence_system(remainders2, moduli2)

    if result:

        x3, lcm3 = result

        print(f"同余方程组: x ≡ {remainders2} (mod {moduli2})")

        print(f"解: x = {x3} (模 {lcm3})")

