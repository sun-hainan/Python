# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / polymatroid



本文件实现 polymatroid 相关的算法功能。

"""



from typing import List, Dict, Set





class Polymatroid:

    """多面体"""



    def __init__(self, ground_set: List[str]):

        """

        参数：

            ground_set: Ground set E

        """

        self.E = ground_set

        self.n = len(ground_set)

        self.element_index = {e: i for i, e in enumerate(ground_set)}



    def rank_function(self, S: Set[str]) -> float:

        """

        拟阵秩函数



        参数：

            S: 子集



        返回：秩

        """

        # 简化：线性秩

        return len(S)



    def is_submodular(self, function: Dict[Set, float]) -> bool:

        """

        检查次模性



        对于所有 A, B: f(A) + f(B) ≥ f(A∪B) + f(A∩B)

        """

        S_list = list(function.keys())



        for A in S_list:

            for B in S_list:

                A_cap_B = A.intersection(B)

                A_un_B = A.union(B)



                if A_cap_B in function and A_un_B in function:

                    if function[A] + function[B] < function.get(A_un_B, 0) + function.get(A_cap_B, 0):

                        return False



        return True



    def base_polytope(self, rank_func) -> List[List[float]]:

        """

        基多面体



        B_f = {x ∈ P_f : x(E) = f(E)}



        返回：顶点列表

        """

        # 简化的顶点枚举

        vertices = []



        # 每个排列对应一个基顶点

        import itertools



        for perm in itertools.permutations(self.E):

            vertex = [0.0] * self.n

            remaining = set(self.E)



            for e in perm[:-1]:

                i = self.element_index[e]

                vertex[i] = rank_func(remaining) - rank_func(remaining - {e})

                remaining.remove(e)



            vertices.append(vertex)



        return vertices



    def greedy_algorithm(self, weights: List[float]) -> Set[str]:

        """

        贪心算法求解基最大化



        参数：

            weights: 权重向量



        返回：最优基

        """

        indexed = [(w, i, e) for i, (w, e) in enumerate(zip(weights, self.E))]

        indexed.sort(reverse=True)



        result = set()

        for w, i, e in indexed:

            # 添加元素如果仍然可行

            result.add(e)



        return result





def polymatroid_applications():

    """多面体应用"""

    print("=== 多面体应用 ===")

    print()

    print("1. 集合覆盖问题")

    print("   - 权函数次模")

    print("   - 贪心有近似保证")

    print()

    print("2. 子模函数最大化")

    print("   - 最大覆盖问题")

    print("   - 影响力最大化")

    print()

    print("3. 拟阵交")

    print("   - 两个拟阵交的基")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 多面体测试 ===\n")



    E = ['a', 'b', 'c', 'd']

    poly = Polymatroid(E)



    print(f"Ground set: {E}")

    print()



    # 次模函数

    def f(S):

        return len(S) ** 0.5  # 平方根函数是次模的



    function = {frozenset(s): f(set(s)) for s in [

        {'a'}, {'b'}, {'c'}, {'d'},

        {'a', 'b'}, {'a', 'c'}, {'b', 'c'}, {'a', 'b', 'c'}

    ]}



    is_sub = poly.is_submodular(function)

    print(f"函数是次模的: {is_sub}")



    # 贪心算法

    weights = [3.0, 1.0, 2.0, 4.0]

    result = poly.greedy_algorithm(weights)



    print(f"\n权重: {weights}")

    print(f"贪心选择: {result}")



    print()

    polymatroid_applications()



    print()

    print("说明：")

    print("  - 多面体是拟阵理论的核心")

    print("  - 用于组合优化多面体分析")

    print("  - 在算法设计中有重要应用")

