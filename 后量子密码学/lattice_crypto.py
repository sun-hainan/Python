# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / lattice_crypto



本文件实现 lattice_crypto 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class LatticeBasics:

    """格基础"""



    def __init__(self, basis: np.ndarray):

        """

        参数：

            basis: 格基（每行是一个基向量）

        """

        self.basis = basis

        self.n, self.m = basis.shape  # n维，m个向量



    def gram_schmidt_orthogonalize(self) -> Tuple[np.ndarray, np.ndarray]:

        """

        Gram-Schmidt正交化



        返回：(正交基, 模长)

        """

        Q = np.zeros_like(self.basis)

        R = np.zeros((self.m, self.m))



        for i in range(self.m):

            v = self.basis[i].copy()



            for j in range(i):

                R[j, i] = np.dot(Q[j], self.basis[i])

                v = v - R[j, i] * Q[j]



            norm = np.linalg.norm(v)

            Q[i] = v / norm if norm > 1e-10 else np.zeros_like(v)

            R[i, i] = norm



        return Q, R



    def shortest_vector_approx(self) -> np.ndarray:

        """

        近似最短向量（使用Gram-Schmidt）



        返回：近似最短向量

        """

        Q, R = self.gram_schmidt_orthogonalize()



        # 简化：返回最短的基向量

        norms = [np.linalg.norm(self.basis[i]) for i in range(self.m)]

        min_idx = np.argmin(norms)



        return self.basis[min_idx]



    def hilbert_basis_reduction(self) -> np.ndarray:

        """

        Hilbert基约简（简化版）



        返回：约简后的基

        """

        # 简化：不做真正的约简

        return self.basis.copy()





def lattice_problems():

    """格问题"""

    print("=== 格问题 ===")

    print()

    print("1. SVP（最短向量问题）")

    print("  - 找最短的非零向量")

    print("  - NP困难")

    print()

    print("2. CVP（最近向量问题）")

    print("  - 找离目标点最近的格点")

    print("  - NP困难")

    print()

    print("3. BDD（有界距离解码）")

    print("  - 目标在格点附近")

    print("  - 在适当条件下可解")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 格基础测试 ===\n")



    # 创建简单格基

    basis = np.array([

        [1, 0, 0],

        [0, 1, 0],

        [0, 0, 1]

    ]).astype(float)



    lattice = LatticeBasics(basis)



    print("格基：")

    print(basis)

    print()



    # Gram-Schmidt正交化

    Q, R = lattice.gram_schmidt_orthogonalize()



    print("Gram-Schmidt正交基：")

    print(Q)

    print()



    # 近似最短向量

    sv = lattice.shortest_vector_approx()



    print(f"近似最短向量: {sv}")

    print(f"长度: {np.linalg.norm(sv):.4f}")



    print()

    lattice_problems()



    print()

    print("说明：")

    print("  - 格理论是现代密码学的基础")

    print("  - 基于格问题的难解性")

    print("  - 后量子密码学核心")

