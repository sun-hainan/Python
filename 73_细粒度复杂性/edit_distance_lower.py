# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / edit_distance_lower



本文件实现 edit_distance_lower 相关的算法功能。

"""



from typing import List, Tuple





class EditDistanceComplexity:

    """编辑距离复杂度"""



    def __init__(self):

        pass



    def dp_edit_distance(self, s: str, t: str) -> int:

        """

        动态规划编辑距离



        返回：编辑距离

        """

        m, n = len(s), len(t)



        # DP表

        dp = [[0] * (n + 1) for _ in range(m + 1)]



        # 初始化

        for i in range(m + 1):

            dp[i][0] = i

        for j in range(n + 1):

            dp[0][j] = j



        # 填充

        for i in range(1, m + 1):

            for j in range(1, n + 1):

                if s[i-1] == t[j-1]:

                    dp[i][j] = dp[i-1][j-1]

                else:

                    dp[i][j] = 1 + min(dp[i-1][j],     # 删除

                                        dp[i][j-1],     # 插入

                                        dp[i-1][j-1])   # 替换



        return dp[m][n]



    def estimate_complexity(self, n: int) -> dict:

        """

        估计复杂度



        返回：复杂度信息

        """

        return {

            'size': n,

            'dp_time': f"O({n}²)",

            'word_romance_time': f"O({n}^{2}/log n)",  # 已知接近最优

            'space': f"O({n})" if n < 1000 else f"O({n}²)"  # 空间优化版本

        }



    def lower_bound_reasoning(self) -> str:

        """

        下界推理



        返回：下界原因

        """

        return """

        编辑距离下界原因：



        1. 组合下界

           - 需要查看字符串的每个位置

           - 任何算法需要 Ω(n²) 操作



        2. 代数下界

           - 问题等价于矩阵计算

           - 需要 Ω(n²) 代数操作



        3. 条件下界

           - 如果有 o(n²) 算法

           - 则某些困难假设失败（如同或性假设）

        """





def edit_distance_applications():

    """编辑距离应用"""

    print("=== 编辑距离应用 ===")

    print()

    print("应用：")

    print("  - DNA序列比对（生物信息学）")

    print("  - 拼写检查")

    print("  - 抄袭检测")

    print()

    print("算法：")

    print("  - 动态规划：O(n²)")

    print("  - 近似算法：O(n)")

    print("  - 量子算法：有望加速")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 编辑距离下界测试 ===\n")



    ed = EditDistanceComplexity()



    # 测试DP算法

    s1 = "abcde"

    s2 = "acebcd"



    distance = ed.dp_edit_distance(s1, s2)



    print(f"字符串1: {s1}")

    print(f"字符串2: {s2}")

    print(f"编辑距离: {distance}")

    print()



    # 复杂度估计

    n = 1000

    info = ed.estimate_complexity(n)



    print(f"字符串长度 n = {n}:")

    print(f"  DP时间: {info['dp_time']}")

    print(f"  最佳时间: {info['word_romance_time']}")



    print()

    print(ed.lower_bound_reasoning())



    print()

    edit_distance_applications()



    print()

    print("说明：")

    print("  - 编辑距离下界用于指导算法设计")

    print("  - 实际中近似算法更实用")

    print("  - DNA比对是重要应用")

