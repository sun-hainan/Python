# -*- coding: utf-8 -*-

"""

算法实现：博弈论 / bayesian_game



本文件实现 bayesian_game 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict

from collections import defaultdict



class BayesianGame:

    """

    贝叶斯博弈 - 不完全信息博弈

    

    每个玩家有一个私有类型，其他玩家只知道类型的概率分布

    """

    

    def __init__(self, players: List[str], types_per_player: Dict[str, List],

                 actions: Dict[str, List], priors: Dict[str, np.ndarray],

                 payoffs: Dict):

        """

        Args:

            players: 玩家列表

            types_per_player: 每个玩家的类型空间

            actions: 每个玩家的行动空间

            priors: 每个玩家对其他玩家类型的先验概率

            payoffs: 收益字典，键为(type_profile, action_profile)

        """

        self.players = players

        self.types = types_per_player

        self.actions = actions

        self.priors = priors

        self.payoffs = payoffs

    

    def get_payoff(self, type_profile: Tuple, action_profile: Tuple, player: str) -> float:

        """获取玩家收益"""

        key = (type_profile, action_profile)

        player_idx = self.players.index(player)

        return self.payoffs.get(key, [0.0] * len(self.players))[player_idx]

    

    def get_posterior(self, player: str, observed_type: str, other_type: str) -> float:

        """计算后验概率（贝叶斯公式）"""

        player_idx = self.players.index(player)

        prior = self.priors[player][self.types[player].index(other_type)]

        

        # 简化为均匀先验

        return 1.0 / len(self.types[player])

    

    def expected_payoff(self, player: str, my_type: str, my_action: str,

                       other_actions: Dict[str, str]) -> float:

        """

        计算期望收益

        

        Args:

            player: 当前玩家

            my_type: 自己的类型

            my_action: 自己的行动

            other_actions: 其他玩家的行动

        """

        expected = 0.0

        other_players = [p for p in self.players if p != player]

        

        # 对每种可能的类型组合加权

        for other_type in self.types[other_players[0]]:

            type_profile = (my_type, other_type) if player == self.players[0] else (other_type, my_type)

            

            action_profile = tuple(other_actions.get(p, "") for p in self.players)

            action_profile_list = list(action_profile)

            my_action_idx = self.actions[player].index(my_action)

            action_profile_list[self.players.index(player)] = my_action_idx

            action_profile = tuple(action_profile_list)

            

            payoff = self.get_payoff(type_profile, action_profile, player)

            prior = 1.0 / len(self.types[other_players[0]])  # 均匀先验

            

            expected += payoff * prior

        

        return expected

    

    def find_bayesian_nash_equilibrium(self) -> List[Dict]:

        """

        求解贝叶斯纳什均衡

        

        Returns:

            均衡策略配置

        """

        equilibria = []

        

        # 对每个玩家的每种类型找到最优行动

        for player in self.players:

            for my_type in self.types[player]:

                best_actions = []

                for action in self.actions[player]:

                    # 简化为只有两个玩家

                    other_players = [p for p in self.players if p != player]

                    if other_players:

                        other_player = other_players[0]

                        for other_action in self.actions[other_player]:

                            expected = self.expected_payoff(

                                player, my_type, action, {other_player: other_action}

                            )

                            best_actions.append((action, expected))

                

                # 选择期望收益最高的行动

                if best_actions:

                    best = max(best_actions, key=lambda x: x[1])

                    print(f"{player} (类型{my_type}) 的最优行动: {best[0]}, 期望收益: {best[1]:.2f}")

        

        return equilibria



def solve_second_price_auction_bayesian() -> Dict:

    """

    求解第二价格拍卖的贝叶斯纳什均衡

    

    在第二价格拍卖中，每个投标人的占优策略是报告真实价值

    """

    print("=== 第二价格拍卖 ===")

    print("在第二价格拍卖中，每个投标人的占优策略是报告真实价值")

    

    valuations = [10, 20, 30, 40]

    

    results = []

    for v in valuations:

        # 投标人的最优策略是出价等于其价值

        bid = v

        results.append({

            "valuation": v,

            "bid": bid,

            "dominant": True

        })

    

    return {

        "equilibrium_type": "弱占优策略均衡",

        "strategy": "出价等于真实价值",

        "results": results

    }



def solve_first_price_auction_bayesian(num_bidders: int = 2, 

                                      value_distribution: str = "uniform") -> Dict:

    """

    求解第一价格拍卖的贝叶斯纳什均衡

    

    在第一价格拍卖中，投标人需要权衡出价和获胜概率

    """

    print("=== 第一价格拍卖 ===")

    

    # 假设价值在[0,1]上均匀分布

    n = num_bidders

    

    # 对称均衡出价函数: b(v) = v * (n-1) / n

    results = []

    for v in [0.2, 0.4, 0.6, 0.8, 1.0]:

        # 简化计算

        bid = v * (n - 1) / n

        results.append({

            "valuation": v,

            "symmetric_bid": round(bid, 3),

            "expected_profit": round((v - bid) * (v ** (n - 1)), 3)

        })

    

    print("对称均衡出价策略:")

    print(f"  出价 = 价值 × (n-1)/n = 价值 × {(n-1)/n}")

    for r in results:

        print(f"  价值={r['valuation']:.1f} -> 出价={r['symmetric_bid']:.3f}")

    

    return {

        "equilibrium_type": "对称贝叶斯纳什均衡",

        "bidding_function": "b(v) = v * (n-1)/n",

        "results": results

    }



if __name__ == "__main__":

    print("=== 贝叶斯博弈测试 ===")

    

    # 简单贝叶斯博弈示例

    # 两个投标人，私下知道自己的价值

    players = ["投标人A", "投标人B"]

    types = {"投标人A": ["高价值", "低价值"], "投标人B": ["高价值", "低价值"]}

    actions = {"投标人A": ["高价投标", "低价投标"], "投标人B": ["高价投标", "低价投标"]}

    

    print("投标人博弈:")

    print("  类型: 高价值(概率0.5), 低价值(概率0.5)")

    print("  行动: 高价投标, 低价投标")

    

    game = BayesianGame(players, types, actions, {}, {})

    game.find_bayesian_nash_equilibrium()

    

    print("\n=== 拍卖理论应用 ===")

    

    # 第二价格拍卖

    sp_eq = solve_second_price_auction_bayesian()

    print(f"\n均衡类型: {sp_eq['equilibrium_type']}")

    print(f"策略: {sp_eq['strategy']}")

    

    # 第一价格拍卖

    fp_eq = solve_first_price_auction_bayesian(num_bidders=2)

    print(f"\n均衡类型: {fp_eq['equilibrium_type']}")

    print(f"出价函数: {fp_eq['bidding_function']}")

    

    print("\n=== 一口价拍卖 ===")

    print("在有一口价选项的拍卖中，竞标者面临权衡")

    print("  - 直接投标: 风险但可能节省")

    print("  - 使用一口价: 确保获胜但支付更多")

    

    # 简单分析

    valuations = [100, 200, 300]

    buy_it_now = 250

    

    print(f"\n假设一口价={buy_it_now}:")

    for v in valuations:

        if v >= buy_it_now:

            print(f"  价值={v}: 使用一口价")

        else:

            print(f"  价值={v}: 投标竞争")

    

    print("\n=== 机制设计示例 ===")

    print("贝叶斯博弈的核心应用:")

    print("1. 拍卖设计 - 确定最优机制")

    print("2. 谈判 - 不完全信息下的策略")

    print("3. 投标 - 竞标策略分析")

    print("4. 合同 - 逆向选择问题")

