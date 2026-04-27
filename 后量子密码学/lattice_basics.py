# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / lattice_basics



本文件实现 lattice_basics 相关的算法功能。

"""



# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 格密码基础测试 ===\n")



    # 创建简单格

    basis = [

        [2, 0],

        [1, 2]

    ]



    print(f"格基：")

    for v in basis:

        print(f"  {v}")



    # Gram-Schmidt正交化（简化）

    print()

    print("Gram-Schmidt正交化：")

    v1 = basis[0]

    v1_norm_sq = sum(x**2 for x in v1)

    e1 = [x / sqrt(v1_norm_sq) for x in v1]

    print(f"  e1 = {e1}")



    # 计算v2在e1上的投影

    v2 = basis[1]

    dot = sum(v2[i] * e1[i] for i in range(len(v2)))

    proj = [dot * x for x in e1]

    v2_perp = [v2[i] - proj[i] for i in range(len(v2))]

    print(f"  v2' = {v2_perp}")



    print()

    print("格问题应用：")

    print("  - Kyber: 基于Module-LWE")

    print("  - Dilithium: 基于Module-LWE")

    print("  - NTRU: 基于SVP")

    print("  - Homomorphic Encryption: 基于RLWE")



    print()

    lattice_problems_summary()



    print()

    print("说明：")

    print("  - 格密码被认为是抗量子的")

    print("  - Shor算法无法破解格密码")

    print("  - 后量子密码标准（2024）基于格问题")

