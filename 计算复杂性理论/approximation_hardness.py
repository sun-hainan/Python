# -*- coding: utf-8 -*-
"""
算法实现：计算复杂性理论 / approximation_hardness

本文件实现 approximation_hardness 相关的算法功能。
"""

from typing import List, Tuple, Set, Dict


# ==================== 近似硬度基础 ====================

def approx_hardness_intro():
    """
    近似硬度简介

    问题的分类：
    - APX：存在常数因子近似算法的问题
    - PTAS：任意ε存在多项式时间(1+ε)-近似的问题
    - APX-难：不能常数因子近似的（除非P=NP）
    - PO：存在多项式时间近似方案的问题

    典型问题：
    - Max-3SAT(1/8)：常数因子近似（2）
    - Max-Cut：0.878-近似（Goemans-Williamson）
    - Set Cover：ln n-近似（不可改进到O(log n)）
    - Knapsack：FPTAS存在
    - Vertex Cover：2-近似（最好可能）
    """
    print("【近似硬度分类】")
    print()
    print("APX类（可近似到常数因子）：")
    print("  - Max-3SAT：有1/8-近似算法")
    print("  - Max-Cut：0.878-近似（GW算法）")
    print("  - Vertex Cover：2-近似（最好可能）")
    print()
    print("PTAS类（任意ε可近似）：")
    print("  - Knapsack：有FPTAS")
    print("  - Euclidean TSP：有PTAS")
    print()
    print("APX-难（不可近似到常数因子）：")
    print("  - Max-Indset：n²-近似以外都难")
    print("  - 着色问题：常数因子以外都难")
    print()


# ==================== PCP定理应用 ====================

def pcp_implies_hardness():
    """
    PCP定理推论

    PCP(n, 1) = NP 意味着：

    对于很多优化问题，如果能近似到(1-ε)因子，
    那么可以用于求解NP完全问题。

    示例：Max-3SAT
    - 最优解≥某个分数时，可以二分搜索求解SAT
    - 所以(7/8 + ε)-近似是不可能的（除非P=NP）

    时间复杂度：O(log n) 用于随机验证
    """
    print("【PCP定理的近似硬度推论】")
    print()
    print("PCP定理：NP = PCP(O(log n), O(1))")
    print()
    print("对于Max-3SAT：")
    print("  - 如果能(7/8 + ε)-近似，则可以解SAT")
    print("  - 所以(7/8 + ε)-近似是NP难的")
    print("  - 即1.001-近似是NP难的")
    print()
    print("对于Max-Cut：")
    print("  - Goemans-Williamson：0.878-近似")
    print("  - 更好的近似需要Unique Games猜想")
    print()
    print("对于Set Cover：")
    print("  - 简单的ln n-近似是已知的最好")
    print("  - 改进到(1-ε)ln n需要P=NP")


# ==================== 归约技术 ====================

def gap_preserving_reduction():
    """
    Gap-preserving归约

    归约的核心思想：
    - 将优化问题转化为决策问题
    - 保持gap（最优解与次优解的差距）

    示例：从SAT到Max-3SAT
    - SAT可满足 ⟺ Max-3SAT = m（所有子句满足）
    - SAT不可满足 ⟺ Max-3SAT ≤ (7/8)m

    这是一个gap-preserving归约：
    - gap: [1, 7/8] → [1, 7/8]
    """
    print("【Gap-Preserving归约】")
    print()
    print("Gap定义：")
    print("  - 一个最大化问题有gap [α, β]如果：")
    print("    * 最优解 ≥ β ⇒ 实例是"是"")
    print("    * 最优解 ≤ α ⇒ 实例是"否"")
    print()
    print("归约性质：")
    print("  - 如果L ≤_p L'是gap-preserving [α,β]归约")
    print("  - 那么L'的近似硬度 ⇒ L的近似硬度")
    print()
    print("示例：SAT → Max-3SAT")
    print("  - gap: [1, 7/8]")
    print("  - 满足时最优=1，不可满足时最优≤7/8")
    print("  - 所以(7/8+ε)-近似是NP难的")


def lsh_reduction():
    """
    Lenstra, Shmoys, Tardos 归约

    用于证明调度问题的近似硬度

    技术：基于线性规划舍入的硬度证明
    """
    print("【LSH归约（调度问题）】")
    print()
    print("问题：2处理器近似调度（P2||C_max）")
    print()
    print("归约：从Partition问题")
    print("  - 给定a1,...,an，判断能否划分使得和=C/2")
    print("  - 构造调度实例：")
    print("    * 每个作业时长ai，依赖关系形成链")
    print("    * 如果Partition可解，最优调度=C/2")
    print("    * 否则最优调度>C/2+ε")
    print()
    print("结论：P2||C_max不能(4/3 - ε)-近似")


# ==================== Unique Games猜想 ====================

def unique_games_conjecture():
    """
    Unique Games Conjecture (UGC)

    猜想：
        对于任意ε>0，给定一个2-prover 1-round UG系统，
        正确回答的比例≥1-ε，但随机猜测只能答对1/2，
        则存在多项式时间算法达到1-ε。

    重要性：
    - 如果UGC成立，很多近似问题是最优的
    - Goemans-Williamson的0.878-近似是最优的
    - 所有Unique Games问题都是APX-难的

    状态：未证明，但广泛相信为真
    """
    print("【Unique Games猜想】")
    print()
    print("UGC陈述：")
    print("  给定一个2-prover 1-round UG系统")
    print("  如果赋值满足≥1-ε的约束")
    print("  则可以在多项式时间内找到满足≥1-ε'的赋值")
    print()
    print("推论（如果UGC成立）：")
    print("  - Max-Cut：0.878-近似是最优的")
    print("  - Vertex Cover：2-近似是最优的")
    print("  - Sparsest Cut：(log n)-近似是最优的")
    print()
    print("状态：未证明，但很多结果基于此")


# ==================== 复杂度分类 ====================

def complexity_classification():
    """
    近似复杂度的分类

    PO (Polynomial-time Optimum): 存在多项式时间最优算法
    APX: 常数因子可近似
    PTAS: 任意ε可近似（时间指数于1/ε）
    FPTAS: 伪多项式PTAS
    APX-难: 不能常数因子近似
    Poly-APX: 多项式因子可近似
    Log-APX: 对数因子可近似
    """
    print("【近似复杂度类】")
    print()
    print("类名         定义                      示例")
    print("─────────────────────────────────────────────────────")
    print("PO           多项式时间最优            最小生成树")
    print("APX          常数因子近似              Max-Cut(0.878)")
    print("PTAS         (1+ε)-近似，多项式        Knapsack(FPTAS)")
    print("FPTAS        伪多项式PTAS             Subset Sum")
    print("APX-难       不能常数近似             Max-IndSet")
    print("Poly-APX     n^c-近似可行             Set Cover(ln n)")
    print("Log-APX      log n-近似可行           Set Cover")
    print()
    print("关系：PO ⊂ PTAS ⊂ APX ⊂ Poly-APX")
    print("      APX-难 问题在最底层")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 近似硬度理论 ===\n")

    approx_hardness_intro()

    print()
    pcp_implies_hardness()

    print()
    gap_preserving_reduction()

    print()
    print("【PCP定理的复杂度分析】")
    print("验证复杂度：O(log n) 随机位")
    print("查询复杂度：O(1) 查询位置")
    print()
    print("PCP(n, 1) = NP 的意义：")
    print("  - 可以用很少的随机性验证NP语句")
    print("  - 验证只需要查询常数个位置")
    print("  - 这是概率可检查证明(Probabilistically Checkable Proof)的基础")
    print()
    print("【近似硬度总结】")
    print("技术         应用问题        近似比下界")
    print("─────────────────────────────────────────")
    print("PCP          Max-3SAT        7/8+ε")
    print("UGC          Max-Cut         0.878+ε")
    print("LSH          调度            4/3+ε")
    print("LP舍入      Set Cover       ln n")
