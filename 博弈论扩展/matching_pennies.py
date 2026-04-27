# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / matching_pennies

本文件实现 matching_pennies 相关的算法功能。
"""

def run_rock_paper_scissors_evolution():
    """石头剪刀布演化"""
    print("\n=== 石头剪刀布演化博弈 ===")
    
    # 收益矩阵
    # R=0, P=1, S=2
    payoff_matrix = np.array([
        [0, -1, 1],   # R vs R,P,S
        [1, 0, -1],   # P vs R,P,S
        [-1, 1, 0]    # S vs R,P,S
    ])
    
    print("收益矩阵 (玩家1):")
    print("       R   P   S")
    print("  R    0  -1   1")
    print("  P    1   0  -1")
    print("  S   -1   1   0")
    
    # 初始种群
    pop = np.array([1/3, 1/3, 1/3])
    
    print(f"\n初始种群: R={pop[0]:.3f}, P={pop[1]:.3f}, S={pop[2]:.3f}")
    
    history = [pop.copy()]
    
    for iteration in range(100):
        # 计算适应度
        fitness = payoff_matrix @ pop
        
        # 平均适应度
        avg_fitness = pop @ fitness
        
        # 复制者动态
        d_pop = pop * (fitness - avg_fitness)
        pop = pop + 0.1 * d_pop
        
        # 限制在[0,1]之间并归一化
        pop = np.maximum(pop, 0)
        pop = pop / pop.sum()
        
        if iteration % 20 == 0:
            print(f"迭代{iteration}: R={pop[0]:.4f}, P={pop[1]:.4f}, S={pop[2]:.4f}")
        
        history.append(pop.copy())
    
    print(f"\n最终种群: R={pop[0]:.4f}, P={pop[1]:.4f}, S={pop[2]:.4f}")
    
    print("\n分析:")
    print("  石头剪刀布存在循环 dominance")
    print("  内部平衡点: 均匀分布 (1/3, 1/3, 1/3)")
    print("  动态在平衡点附近振荡")
    print("  没有稳定收敛到纯策略")

def analyze_evolutionary_stability():
    """分析演化稳定性"""
    print("\n=== 演化稳定策略 (ESS) 分析 ===")
    
    print("匹配硬币:")
    print("  - 没有纯策略ESS")
    print("  - 混合策略 (0.5, 0.5) 是 neutrally stable")
    print("  - 但不是渐进稳定")
    
    print("\n石头剪刀布:")
    print("  - 均匀分布是唯一的内部ESS")
    print("  - 系统在ESS附近做极限环")
    print("  - 振幅取决于初始条件")
    
    print("\n=== 生物学意义 ===")
    print("  - 石头剪刀布常见于自然界")
    print("  - 侧斑蜥蜴的喉部颜色")
    print("  - 蜜蜂的守卫行为")
    print("  - 保持多样性是有利的")
    
    print("\n=== 数学性质 ===")
    print("  - 零和博弈的ESS不唯一")
    print("  - 周期行为常见于循环博弈")
    print("  - 混沌行为在更高维可能出现")

if __name__ == "__main__":
    run_matching_pennies_evolution()
    run_rock_paper_scissors_evolution()
    analyze_evolutionary_stability()
    
    print("\n=== 演化博弈论的应用 ===")
    print("1. 生物学: 物种竞争、捕食策略")
    print("2. 社会科学: 社会规范演化")
    print("3. 计算机科学: 协议设计")
    print("4. 经济学: 市场均衡")
    
    print("\n=== 稳定多态 ===")
    print("石头剪刀布展示了稳定的多态:")
    print("  - 三种策略在种群中共存")
    print("  - 频率依赖选择维持多样性")
    print("  - 类似于生态学中的平衡")
    
    print("\n=== 混沌可能性 ===")
    print("在某些博弈中可能出现混沌:")
    print("  - 高维策略空间")
    print("  - 非对称信息")
    print("  - 时变环境")
    print("  - 需要进一步研究")
