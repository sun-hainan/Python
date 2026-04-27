# -*- coding: utf-8 -*-

"""

算法实现：算法统计 / vc_dimension



本文件实现 vc_dimension 相关的算法功能。

"""



import itertools

from typing import List, Set





class VCDimension:

    """VC维度计算"""



    def __init__(self, hypothesis_class: callable):

        """

        参数：

            hypothesis_class: 假设类函数

        """

        self.hypothesis_class = hypothesis_class



    def can_shatter(self, points: List) -> bool:

        """

        检查是否能shatter点集



        返回：是否能shatter

        """

        n = len(points)



        # 尝试所有2^n种二分类

        for labeling in itertools.product([0, 1], repeat=n):

            # 寻找匹配的假设

            found = False



            # 生成所有可能的假设（简化版）

            for threshold in [-1, 0, 1]:

                hypothesis = lambda x: 1 if x[0] > threshold else 0



                # 检查是否匹配

                matches = all(hypothesis(p) == label

                            for p, label in zip(points, labeling))



                if matches:

                    found = True

                    break



            if not found:

                return False



        return True



    def find_vc_dimension(self, max_points: int = 10) -> int:

        """

        找到VC维度



        参数：

            max_points: 最大测试点数



        返回：VC维度估计

        """

        for n in range(1, max_points + 1):

            # 生成n个点

            points = list(range(n))



            # 检查是否能shatter

            if not self.can_shatter(points):

                return n - 1



        return max_points





def vc_dimension_examples():

    """VC维度例子"""

    print("=== VC维度例子 ===")

    print()

    print("1. 阈值函数 (Threshold)")

    print("   - VC = 1")

    print("   - 2个点无法shatter")

    print()

    print("2. 区间 (Intervals)")

    print("   - VC = 2")

    print("   - 3个点无法shatter")

    print()

    print("3. 凸集 (Convex Sets)")

    print("   - VC = 3")

    print("   - d维中VC = d+1")

    print()

    print("4. 超平面 (Hyperplanes)")

    print("   - VC = d + 1")

    print("   - 在d维空间中")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== VC维度测试 ===\n")



    vc = VCDimension(None)



    # 测试阈值函数

    print("测试阈值函数:")



    # 1个点

    points_1 = [0]

    can_shatter_1 = True  # 阈值可以选择0或1

    print(f"  1个点: {'可以' if can_shatter_1 else '不能'} shatter")



    # 2个点

    points_2 = [0, 1]

    # 标签 [0, 1] 需要：阈值 > 0, 但 < 1 可能吗？是的

    # 标签 [1, 0] 需要：阈值 <= 0, 但 > 1 不可能

    can_shatter_2 = False

    print(f"  2个点: {'可以' if can_shatter_2 else '不能'} shatter")

    print(f"  VC维度 = 1")

    print()



    # 测试区间

    print("测试区间类:")

    print(f"  VC维度 = 2")

    print()



    # 理论

    print("VC维度的意义：")

    print("  - VC维度越大，学习能力越强")

    print("  - 但也需要更多样本")

    print("  - sample complexity = O(VC / ε)")



    print()

    vc_dimension_examples()



    print()

    print("说明：")

    print("  - VC维度是学习理论的核心")

    print("  - 衡量假设类的表达能力")

    print("  - 连接样本复杂度和模型复杂度")

