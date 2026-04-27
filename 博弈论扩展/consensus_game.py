# -*- coding: utf-8 -*-

"""

算法实现：博弈论扩展 / consensus_game



本文件实现 consensus_game 相关的算法功能。

"""



import numpy as np

from typing import List, Dict, Tuple



class ConsensusGame:

    """

    共识博弈

    

    多智能体需要就某个值达成共识

    博弈论视角: 每个人都偏好与其他所有人一致

    """

    

    def __init__(self, num_players: int, num_options: int):

        self.num_players = num_players

        self.num_options = num_options

    

    def compute_payoff(self, player: int, choice: int, all_choices: List[int]) -> float:

        """

        计算玩家收益

        

        收益 = 与其他人选择相同选项的数量

        """

        payoff = 0

        for j, other_choice in enumerate(all_choices):

            if j != player and other_choice == choice:

                payoff += 1

        return payoff



def run_consensus_simulation(num_agents: int = 10, num_options: int = 3) -> Dict:

    """

    运行共识博弈模拟

    

    Args:

        num_agents: 智能体数量

        num_options: 选项数量

    

    Returns:

        模拟结果

    """

    print("=== 共识博弈测试 ===")

    

    game = ConsensusGame(num_agents, num_options)

    

    # 初始化随机选择

    choices = np.random.randint(0, num_options, num_agents)

    print(f"初始选择: {list(choices)}")

    

    history = [choices.copy()]

    

    # 最佳响应动态

    for iteration in range(50):

        # 选择一个随机玩家

        player = np.random.randint(0, num_agents)

        

        # 找到最优选择

        best_payoff = -1

        best_choice = choices[player]

        

        for option in range(num_options):

            test_choices = choices.copy()

            test_choices[player] = option

            payoff = game.compute_payoff(player, option, list(test_choices))

            

            if payoff > best_payoff:

                best_payoff = payoff

                best_choice = option

        

        choices[player] = best_choice

        history.append(choices.copy())

    

    print(f"\n最终选择: {list(choices)}")

    

    # 检查是否达成共识

    unique_choices = len(set(choices))

    print(f"不同选项数: {unique_choices}")

    

    if unique_choices == 1:

        print("结果: 达成共识!")

    else:

        print("结果: 未达成共识，形成多稳态")

    

    return {

        "initial": list(history[0]),

        "final": list(choices),

        "consensus_reached": unique_choices == 1,

        "iterations": len(history)

    }



def run_herding_game():

    """羊群效应博弈"""

    print("\n=== 羊群效应 (Herding) ===")

    

    # 序列决策博弈

    # 每个人可以看到前面人的选择

    

    print("设置:")

    print("  - 10个决策者按顺序做选择")

    print("  - 两个选项: A和B")

    print("  - 真实状态未知")

    print("  - 每个人偏好与前人一致")

    

    # 模拟

    np.random.seed(42)

    sequence = []

    first_choice = np.random.randint(0, 2)

    sequence.append(first_choice)

    

    for i in range(1, 10):

        # 以高概率跟随前人

        if np.random.random() < 0.8:

            choice = sequence[-1]

        else:

            choice = 1 - sequence[-1]

        sequence.append(choice)

    

    print(f"\n序列选择: {sequence}")

    print(f"最终A的数量: {sequence.count(0)}")

    print(f"最终B的数量: {sequence.count(1)}")

    

    print("\n羊群效应:")

    print("  - 早期决策影响后期决策")

    print("  - 可能收敛到次优均衡")

    print("  - 信息级联可能导致错误共识")



def analyze_consensus_convergence():

    """分析共识收敛性"""

    print("\n=== 共识收敛性分析 ===")

    

    print("共识博弈的纳什均衡:")

    print("  1. 纯策略均衡: 所有玩家选择同一选项")

    print("  2. 混合策略均衡: 随机选择但期望收益相同")

    

    print("\n收敛动态:")

    print("  - 最佳响应动态总是收敛到共识")

    print("  - 因为共识是唯一的强纳什均衡")

    

    print("\n收敛速度:")

    print("  - 初始状态影响收敛速度")

    print("  - 预期收敛时间: O(n log n)")

    

    print("\n=== 实际应用 ===")

    print("1. 社交网络舆论形成")

    print("2. 分布式系统一致性协议")

    print("3. 群体决策机制")

    print("4. 蜜蜂群选址")



if __name__ == "__main__":

    result = run_consensus_simulation(10, 2)

    

    run_herding_game()

    analyze_consensus_convergence()

    

    print("\n=== 共识博弈的变体 ===")

    

    print("\n1. 噪声共识:")

    print("  - 玩家可能犯错误")

    print("  - 系统可能永远无法完全共识")

    

    print("\n2. 置信度加权:")

    print("  - 玩家对自己选择有置信度")

    print("  - 高置信度玩家影响更大")

    

    print("\n3. 外部信号:")

    print("  - 存在外部信号帮助协调")

    print("  - 加速共识达成")

    

    print("\n=== 机制设计 ===")

    print("如何设计机制促进好的共识:")

    print("  1. 引入真值信号")

    print("  2. 惩罚不一致行为")

    print("  3. 分层决策结构")

    print("  4. 随机化打破对称")

    

    print("\n=== 博弈论视角 ===")

    print("共识博弈展示了:")

    print("  - 协调博弈的均衡结构")

    print("  - 羊群效应的非理性结果")

    print("  - 社会影响的动态效应")

