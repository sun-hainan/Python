# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / ov_complexity



本文件实现 ov_complexity 相关的算法功能。

"""



import random

from typing import List, Tuple





class OVComplexity:

    """OV问题细粒度复杂性"""



    def __init__(self, d: int):

        """

        参数：

            d: 维度

        """

        self.d = d



    def check_orthogonal(self, a: List[int], b: List[int]) -> bool:

        """

        检查两个向量是否正交



        返回：是否正交

        """

        return sum(ai * bi for ai, bi in zip(a, b)) == 0



    def find_orthogonal_pair(self, A: List[List[int]],

                           B: List[List[int]]) -> Tuple[int, int]:

        """

        找一对正交向量



        参数：

            A, B: 向量集合



        返回：(i, j) 或 (-1, -1)

        """

        for i, a in enumerate(A):

            for j, b in enumerate(B):

                if self.check_orthogonal(a, b):

                    return (i, j)

        return (-1, -1)



    def ov_to_3sum_reduction(self, A: List[List[int]]) -> List[List[int]]:

        """

        OV → 3SUM 归约



        将OV实例转换为3SUM实例



        返回：3SUM三元组集合

        """

        # 简化：构造转换

        triples = []



        for a in A:

            # 把向量转成数值

            val = sum(bit << i for i, bit in enumerate(a))

            triples.append([val, val + 1, val + 2])



        return triples





def ov_hardness():

    """OV困难性"""

    print("=== OV问题困难性 ===")

    print()

    print("已知结果：")

    print("  - OV不能在 O(n^{2 - ε}) 解决")

    print("  - 除非SETH不成立")

    print()

    print("应用：")

    print("  - 3SUM: n^{2} 下界")

    print("  - 字符串算法: 编辑距离等")

    print("  - 图算法: APSP等")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== OV问题测试 ===\n")



    random.seed(42)



    # 创建测试数据

    d = 10

    n = 20



    A = [[random.randint(0, 1) for _ in range(d)] for _ in range(n)]

    B = [[random.randint(0, 1) for _ in range(d)] for _ in range(n)]



    ov = OVComplexity(d)



    print(f"集合A: {n}个{d}维向量")

    print(f"集合B: {n}个{d}维向量")

    print()



    # 找正交对

    pair = ov.find_orthogonal_pair(A, B)



    if pair[0] >= 0:

        print(f"找到正交对: A[{pair[0]}] 和 B[{pair[1]}]")

        a, b = A[pair[0]], B[pair[1]]

        dot = sum(ai * bi for ai, bi in zip(a, b))

        print(f"验证: 点积 = {dot}")

    else:

        print("没有找到正交对")



    print()

    ov_hardness()



    print()

    print("说明：")

    print("  - OV是细粒度复杂性的基准问题")

    print("  - 许多问题基于OV的难度")

    print("  - 在密码分析、计算几何中有应用")

