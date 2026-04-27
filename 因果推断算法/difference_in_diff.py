# -*- coding: utf-8 -*-

"""

算法实现：因果推断算法 / difference_in_diff



本文件实现 difference_in_diff 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class DifferenceInDifferences:

    """双重差分"""



    def __init__(self):

        pass



    def estimate_att(self,

                    y_pre_treat: List[float], y_post_treat: List[float],

                    y_pre_control: List[float], y_post_control: List[float]) -> dict:

        """

        估计ATT（Average Treatment Effect on Treated）



        参数：

            y_pre_treat: 处理组前期结果

            y_post_treat: 处理组后期结果

            y_pre_control: 对照组前期结果

            y_post_control: 对照组后期结果



        返回：估计结果

        """

        # 计算差分

        treat_diff = np.mean(y_post_treat) - np.mean(y_pre_treat)

        control_diff = np.mean(y_post_control) - np.mean(y_pre_control)



        # DID估计量

        ATT = treat_diff - control_diff



        # 标准误（简化）

        n1 = len(y_pre_treat)

        n2 = len(y_pre_control)



        var_att = (np.var(y_post_treat) / n1 + np.var(y_pre_treat) / n1 +

                   np.var(y_post_control) / n2 + np.var(y_pre_control) / n2)



        se = np.sqrt(var_att)



        return {

            'ATT': ATT,

            'standard_error': se,

            'treat_diff': treat_diff,

            'control_diff': control_diff

        }



    def parallel_trend_test(self,

                           y_pre_treat: List[float],

                           y_pre_control: List[float]) -> dict:

        """

        平行趋势检验



        返回：检验结果

        """

        mean_treat = np.mean(y_pre_treat)

        mean_control = np.mean(y_pre_control)



        diff = mean_treat - mean_control



        # 简化的t检验

        n1, n2 = len(y_pre_treat), len(y_pre_control)

        pooled_std = np.sqrt((np.var(y_pre_treat) + np.var(y_pre_control)) / 2)



        t_stat = diff / (pooled_std * np.sqrt(1/n1 + 1/n2))



        return {

            'mean_difference': diff,

            't_statistic': t_stat,

            'parallel': abs(t_stat) < 1.96  # 95%置信水平

        }





def did_assumptions():

    """DID假设"""

    print("=== DID假设 ===")

    print()

    print("1. 平行趋势")

    print("  - 处理组和对照组在干预前有相似趋势")

    print("  - 可通过事前数据检验")

    print()

    print("2. 无溢出效应")

    print("  - 处理不影响对照组")

    print("  - 个体处理状态稳定")

    print()

    print("3. 共同冲击")

    print("  - 外部冲击同时影响两组")

    print("  - 或者两组受同等影响")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 双重差分测试 ===\n")



    np.random.seed(42)



    # 模拟数据

    n = 500



    # 对照组（无干预）

    y_pre_control = np.random.randn(n) * 10 + 100

    y_post_control = y_pre_control + np.random.randn(n) * 2 + 5  # 有上升趋势



    # 处理组（有干预，效应=10）

    effect = 10

    y_pre_treat = np.random.randn(n) * 10 + 100  # 前期相同

    y_post_treat = y_pre_treat + np.random.randn(n) * 2 + 5 + effect  # 趋势+效应



    print(f"样本数: {n}")

    print(f"模拟效应: {effect}")

    print()



    # DID估计

    did = DifferenceInDifferences()

    result = did.estimate_att(y_pre_treat, y_post_treat,

                              y_pre_control, y_post_control)



    print("DID估计结果：")

    print(f"  ATT: {result['ATT']:.4f}")

    print(f"  标准误: {result['standard_error']:.4f}")

    print(f"  处理组变化: {result['treat_diff']:.4f}")

    print(f"  对照组变化: {result['control_diff']:.4f}")

    print()



    # 平行趋势检验

    pt_result = did.parallel_trend_test(y_pre_treat, y_pre_control)



    print("平行趋势检验（事前）：")

    print(f"  前期差异: {pt_result['mean_difference']:.4f}")

    print(f"  t统计量: {pt_result['t_statistic']:.4f}")

    print(f"  通过检验: {'✅' if pt_result['parallel'] else '❌'}")

    print()



    print("说明：")

    print("  - DID是政策评估的常用方法")

    print("  - 需要平行趋势假设")

    print("  - 经济学中广泛使用")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 双重差分测试 ===\n")



    np.random.seed(42)



    # 模拟数据

    n = 500



    # 对照组（无干预）

    y_pre_control = np.random.randn(n) * 10 + 100

    y_post_control = y_pre_control + np.random.randn(n) * 2 + 5  # 有上升趋势



    # 处理组（有干预，效应=10）

    effect = 10

    y_pre_treat = np.random.randn(n) * 10 + 100  # 前期相同

    y_post_treat = y_pre_treat + np.random.randn(n) * 2 + 5 + effect  # 趋势+效应



    print(f"样本数: {n}")

    print(f"模拟效应: {effect}")

    print()



    # DID估计

    did = DifferenceInDifferences()

    result = did.estimate_att(y_pre_treat, y_post_treat,

                              y_pre_control, y_post_control)



    print("DID估计结果：")

    print(f"  ATT: {result['ATT']:.4f}")

    print(f"  标准误: {result['standard_error']:.4f}")

    print(f"  处理组变化: {result['treat_diff']:.4f}")

    print(f"  对照组变化: {result['control_diff']:.4f}")

    print()



    # 平行趋势检验

    pt_result = did.parallel_trend_test(y_pre_treat, y_pre_control)



    print("平行趋势检验（事前）：")

    print(f"  前期差异: {pt_result['mean_difference']:.4f}")

    print(f"  t统计量: {pt_result['t_statistic']:.4f}")

    print(f"  通过检验: {'✅' if pt_result['parallel'] else '❌'}")



    print()

    did_assumptions()



    print()

    print("说明：")

    print("  - DID是政策评估的常用方法")

    print("  - 需要平行趋势假设")

    print("  - 经济学中广泛使用")

