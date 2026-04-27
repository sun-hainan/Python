# -*- coding: utf-8 -*-

"""

算法实现：博弈论 / iterated_elimination



本文件实现 iterated_elimination 相关的算法功能。

"""



from typing import List, Tuple, Set, Dict

from copy import deepcopy



class NormalFormGame:

    """

    标准形式博弈

    

    博弈由以下元素定义:

    - 玩家集合

    - 每个玩家的策略集合

    - 收益函数

    """

    

    def __init__(self, players: List[str], strategies: Dict[str, List[str]], payoffs: Dict):

        self.players = players

        self.strategies = strategies

        self.payoffs = payoffs

    

    def get_payoff(self, profile: Dict[str, str], player: str) -> float:

        """获取指定玩家的收益"""

        key = tuple(profile[p] for p in self.players)

        if key in self.payoffs:

            player_idx = self.players.index(player)

            return self.payoffs[key][player_idx]

        return 0.0

    

    def is_dominated(self, player: str, strategy: str, other_strategies: List[str]) -> bool:

        """

        检查策略是否被支配

        

        Args:

            player: 玩家

            strategy: 待检查策略

            other_strategies: 其他策略列表

        

        Returns:

            是否被支配

        """

        for other in other_strategies:

            if other == strategy:

                continue

            

            # 检查other是否严格支配strategy

            all_dominated = True

            for profile in self._get_all_profiles(player, strategy):

                my_payoff = self.get_payoff(profile, player)

                other_profile = profile.copy()

                other_profile[player] = other

                other_payoff = self.get_payoff(other_profile, player)

                

                if my_payoff >= other_payoff:

                    all_dominated = False

                    break

            

            if all_dominated:

                return True

        

        return False

    

    def _get_all_profiles(self, fixed_player: str, fixed_strategy: str) -> List[Dict]:

        """获取所有策略组合"""

        profiles = []

        other_players = [p for p in self.players if p != fixed_player]

        

        def generate_profiles(current_profile: Dict, player_idx: int):

            if player_idx == len(other_players):

                full_profile = {fixed_player: fixed_strategy}

                full_profile.update(current_profile)

                profiles.append(full_profile)

                return

            

            player = other_players[player_idx]

            for strategy in self.strategies[player]:

                current_profile[player] = strategy

                generate_profiles(current_profile, player_idx + 1)

        

        generate_profiles({}, 0)

        return profiles



def iterated_elimination_dominated_strategies(game: NormalFormGame) -> List[Dict[str, str]]:

    """

    迭代剔除被支配策略

    

    Args:

        game: 标准形式博弈

    

    Returns:

        每个可能的策略组合

    """

    # 复制策略集合

    remaining_strategies = {p: set(game.strategies[p]) for p in game.players}

    elimination_history = []

    

    iteration = 0

    while True:

        changed = False

        iteration += 1

        

        for player in game.players:

            strategies = list(remaining_strategies[player])

            

            for strategy in strategies:

                other_strategies = [s for s in strategies if s != strategy]

                

                if game.is_dominated(player, strategy, other_strategies):

                    remaining_strategies[player].remove(strategy)

                    elimination_history.append({

                        "iteration": iteration,

                        "player": player,

                        "strategy": strategy

                    })

                    changed = True

        

        if not changed:

            break

    

    # 生成最终可能的策略组合

    final_profiles = []

    def generate_profiles(current: Dict, players: List[str]):

        if not players:

            final_profiles.append(current.copy())

            return

        

        player = players[0]

        for strategy in remaining_strategies[player]:

            current[player] = strategy

            generate_profiles(current, players[1:])

            current.pop(player)

    

    generate_profiles({}, game.players)

    return final_profiles



if __name__ == "__main__":

    print("=== 迭代剔除被支配策略测试 ===")

    

    # 性别之战博弈 (Battle of the Sexes)

    players = ["丈夫", "妻子"]

    strategies = {

        "丈夫": ["足球", "歌剧"],

        "妻子": ["足球", "歌剧"]

    }

    # 收益: (丈夫收益, 妻子收益)

    payoffs = {

        ("足球", "足球"): (2, 1),

        ("足球", "歌剧"): (0, 0),

        ("歌剧", "足球"): (0, 0),

        ("歌剧", "歌剧"): (1, 2),

    }

    

    game = NormalFormGame(players, strategies, payoffs)

    

    print("性别之战博弈:")

    print("  丈夫/妻子   | 足球 | 歌剧")

    print("  ------------|------|------")

    print("  足球        | 2,1  | 0,0")

    print("  歌剧        | 0,0  | 1,2")

    

    print("\n=== 迭代剔除过程 ===")

    result = iterated_elimination_dominated_strategies(game)

    

    print(f"消除历史: {elimination_history if 'elimination_history' in dir() else '无'}")

    print(f"\n最终可能的策略组合: {result}")

    

    # 囚徒困境

    print("\n=== 囚徒困境测试 ===")

    

    pd_players = ["囚徒A", "囚徒B"]

    pd_strategies = {"囚徒A": ["坦白", "抵赖"], "囚徒B": ["坦白", "抵赖"]}

    pd_payoffs = {

        ("坦白", "坦白"): (-5, -5),

        ("坦白", "抵赖"): (0, -10),

        ("抵赖", "坦白"): (-10, 0),

        ("抵赖", "抵赖"): (-1, -1),

    }

    

    pd_game = NormalFormGame(pd_players, pd_strategies, pd_payoffs)

    

    print("囚徒困境:")

    print("  囚徒A/囚徒B | 坦白 | 抵赖")

    print("  -----------|------|------")

    print("  坦白       | -5,-5| 0,-10")

    print("  抵赖       | -10,0| -1,-1")

    

    pd_result = iterated_elimination_dominated_strategies(pd_game)

    print(f"最终策略组合: {pd_result}")

    

    # 斗鸡博弈

    print("\n=== 斗鸡博弈 (Chicken Game) ===")

    

    chicken_players = ["司机A", "司机B"]

    chicken_strategies = {"司机A": ["前进", "让路"], "司机B": ["前进", "让路"]}

    chicken_payoffs = {

        ("前进", "前进"): (-10, -10),

        ("前进", "让路"): (5, -5),

        ("让路", "前进"): (-5, 5),

        ("让路", "让路"): (0, 0),

    }

    

    chicken_game = NormalFormGame(chicken_players, chicken_strategies, chicken_payoffs)

    chicken_result = iterated_elimination_dominated_strategies(chicken_game)

    print(f"斗鸡博弈最终策略组合: {chicken_result}")

    print("注意: 斗鸡博弈没有被支配策略，迭代剔除不会减少策略空间")

