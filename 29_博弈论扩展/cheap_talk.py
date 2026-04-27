# -*- coding: utf-8 -*-

"""

算法实现：博弈论扩展 / cheap_talk



本文件实现 cheap_talk 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict



class CheapTalkGame:

    """

    廉价对话博弈

    

    发送者知道状态θ

    选择发送消息m

    接收者观察到m，选择行动a

    两者收益都取决于(θ, a)

    """

    

    def __init__(self, states: List[str], messages: List[str], actions: List[str],

                 state_prior: List[float], payoff: Dict):

        """

        Args:

            states: 状态空间

            messages: 消息空间

            actions: 行动空间

            state_prior: 状态先验

            payoff: 收益 {(state, action): (sender_payoff, receiver_payoff)}

        """

        self.states = states

        self.messages = messages

        self.actions = actions

        self.state_prior = state_prior

        self.payoff = payoff

    

    def find_equilibria(self) -> List[Dict]:

        """

        寻找均衡

        

        可能的均衡类型:

        1. 无信息均衡: 接收者忽略消息

        2. 分离均衡: 不同状态发送不同消息

        3. 混同均衡: 所有状态发送相同消息

        """

        equilibria = []

        

        # 无信息均衡检查

        print("=== 无信息均衡 ===")

        print("接收者忽略消息，基于先验采取行动")

        

        # 基于先验找最优行动

        expected_payoffs = []

        for action in self.actions:

            exp_payoff = sum(

                self.state_prior[i] * self.payoff.get((state, action), (0, 0))[1]

                for i, state in enumerate(self.states)

            )

            expected_payoffs.append((action, exp_payoff))

        

        best_action = max(expected_payoffs, key=lambda x: x[1])

        print(f"基于先验的最优行动: {best_action[0]} (期望收益: {best_action[1]:.2f})")

        

        equilibria.append({

            "type": "babbling",

            "action": best_action[0]

        })

        

        return equilibria



def run_cheap_talk_simulation():

    """廉价对话模拟"""

    print("=== 廉价对话博弈测试 ===")

    

    # 简单例子: 发送者知道θ ∈ {好, 坏}

    # 接收者选择行动 a ∈ {做, 不做}

    

    states = ["好状态", "坏状态"]

    messages = ["好消息", "坏消息"]

    actions = ["行动", "不行动"]

    state_prior = [0.6, 0.4]  # 60%好状态

    

    payoff = {

        ("好状态", "行动"): (10, 10),

        ("好状态", "不行动"): (0, 0),

        ("坏状态", "行动"): (-5, -5),

        ("坏状态", "不行动"): (0, 5),

    }

    

    game = CheapTalkGame(states, messages, actions, state_prior, payoff)

    

    print("状态空间: 好状态(60%), 坏状态(40%)")

    print("消息空间: 好消息, 坏消息")

    print("行动空间: 行动, 不行动")

    

    print("\n收益矩阵:")

    print("          行动    不行动")

    print("  好状态  (10,10)  (0,0)")

    print("  坏状态  (-5,-5)  (0,5)")

    

    eqs = game.find_equilibria()

    

    print("\n分析:")

    print("  - 如果发送者诚实报告:")

    print("    - 好状态 -> 行动 (10,10)")

    print("    - 坏状态 -> 不行动 (0,5)")

    print("  - 这构成了分离均衡")

    

    print("  - 如果发送者总是说好消息:")

    print("    - 接收者忽略消息，基于先验行动")

    print("    - 行动期望收益: 0.6*10 + 0.4*(-5) = 4")

    print("    - 不行动期望收益: 0.6*0 + 0.4*5 = 2")

    print("    - 最优是不行动 -> 无信息均衡")



def analyze_interest_alignment():

    """分析利益一致性"""

    print("\n=== 利益一致性分析 ===")

    

    print("完全一致 (利益对齐):")

    print("  - 发送者和接收者偏好相同行动")

    print("  - 总是传递真实信息")

    print("  - 分离均衡容易实现")

    

    print("\n部分一致:")

    print("  - 有些状态下利益一致，有些不一致")

    print("  - 可能需要权衡")

    

    print("\n完全冲突:")

    print("  - 发送者和接收者总是相反")

    print("  - 无信息均衡是唯一可能")

    print("  - 信号博弈变为廉价对话")

    

    # 数值例子

    print("\n=== 数值例子 ===")

    

    scenarios = [

        ("完全一致", [1.0, 1.0]),

        ("部分一致", [1.0, -0.5]),

        ("完全冲突", [1.0, -1.0]),

    ]

    

    for name, alignment in scenarios:

        print(f"\n{name} (对齐度={alignment[0]:.1f}, {alignment[1]:.1f}):")

        if alignment[0] > 0 and alignment[1] > 0:

            print("  -> 信息传递")

        elif alignment[0] > 0 and alignment[1] < 0:

            print("  -> 条件性信息传递")

        else:

            print("  -> 无信息传递")



def analyze_repeated_cheap_talk():

    """重复廉价对话"""

    print("\n=== 重复廉价对话 ===")

    

    print("设置:")

    print("  - 多轮廉价对话")

    print("  - 发送者知道真实状态")

    print("  - 接收者可以基于历史消息更新信念")

    

    print("\n长期关系效应:")

    print("  1. 声誉机制:")

    print("     - 如果一方偏离，关系破裂")

    print("     - 触发策略可维持信息传递")

    

    print("  2. 策略性行为:")

    print("     - 发送者可能操纵接收者")

    print("     - 需要考虑长期影响")

    

    print("\n重复博弈的均衡:")

    print("  - 触发策略: 持续诚实")

    print("  - 惩罚偏离者")

    print("  - 可以实现分离均衡")



if __name__ == "__main__":

    run_cheap_talk_simulation()

    analyze_interest_alignment()

    analyze_repeated_cheap_talk()

    

    print("\n=== 廉价对话的启示 ===")

    print("1. 消息本身无成本 -> 容易说谎")

    print("2. 但如果利益一致，诚实是均衡")

    print("3. 重复交互可以建立声誉")

    print("4. 第三方监督可以增强可信度")

    

    print("\n=== 实际应用 ===")

    print("1. 政治演讲")

    print("2. 商业谈判")

    print("3. 学术交流")

    print("4. 社交媒体")

    

    print("\n=== 机制设计 ===")

    print("如何让廉价对话更可信:")

    print("  1. 引入成本 (如签名验证)")

    print("  2. 建立声誉系统")

    print("  3. 重复博弈框架")

    print("  4. 第三方仲裁")

