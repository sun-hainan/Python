# -*- coding: utf-8 -*-

"""

算法实现：博弈论扩展 / fair_division



本文件实现 fair_division 相关的算法功能。

"""



import random

from typing import List





class Cake:

    """蛋糕（或者任意连续物品）"""



    def __init__(self, length: float = 1.0):

        """

        参数：

            length: 蛋糕长度（0到1）

        """

        self.length = length



    def value(self, start: float, end: float, player_id: int) -> float:

        """

        计算玩家对蛋糕片段的价值



        参数：

            start, end: 蛋糕的起止位置

            player_id: 玩家ID



        返回：该片段对该玩家的主观价值

        """

        length = end - start

        # 简化：所有玩家价值与蛋糕长度成正比

        # 实际中不同玩家对不同部分可能有不同偏好

        return length





class Player:

    """玩家"""



    def __init__(self, player_id: int):

        self.player_id = player_id

        self.owned_pieces = []

        self.total_value = 0.0



    def cut(self, cake: Cake, pieces: List) -> Tuple[float, float]:

        """

        切割蛋糕



        返回：(cut_position, left_value, right_value)

        """

        # 玩家认为蛋糕是均匀的，切成认为的1/3

        cut = cake.length / 3

        return cut





class KnasterYahalom:

    """Knaster-Yahalom公平分割"""



    def __init__(self, n_players: int):

        self.n_players = n_players

        self.cake = Cake()

        self.players = [Player(i) for i in range(n_players)]



    def run(self) -> dict:

        """

        执行分割协议



        返回：每个玩家得到的蛋糕片段

        """

        results = {i: [] for i in range(self.n_players)}



        # Phase 1: 玩家1切一刀

        player1_cut = self.cake.length / 3

        cuts = [player1_cut]  # 切割位置列表



        # Phase 2: 其他玩家可以调整

        # 简化：从玩家2到玩家n依次检查

        for i in range(1, self.n_players):

            # 玩家i认为当前切割不合理，可以调整

            # 这里简化：玩家i不动刀

            cuts.append(cuts[-1])



        # Phase 3: 从玩家n到玩家1依次选择

        selected_pieces = [False, False]  # 标记蛋糕片段是否被选



        # 分配顺序：玩家n, n-1, ..., 1

        allocation_order = list(range(self.n_players - 1, -1, -1))



        remaining_cuts = [0.0] + sorted(cuts) + [self.cake.length]



        for player_id in allocation_order:

            # 选择最大价值的未分配片段

            best_piece_idx = -1

            best_value = -1



            for i in range(len(remaining_cuts) - 1):

                if selected_pieces[i]:

                    continue



                value = self.players[player_id].value(

                    remaining_cuts[i],

                    remaining_cuts[i + 1],

                    player_id

                )



                if value > best_value:

                    best_value = value

                    best_piece_idx = i



            # 分配

            if best_piece_idx >= 0:

                results[player_id].append((remaining_cuts[best_piece_idx], remaining_cuts[best_piece_idx + 1]))

                self.players[player_id].owned_pieces.append((best_piece_idx, best_value))

                self.players[player_id].total_value += best_value

                selected_pieces[best_piece_idx] = True



        return results





def simple_example():

    """简单示例"""

    print("=== Knaster-Yahalom 公平分割 ===\n")



    n_players = 3

    algo = KnasterYahalom(n_players)

    results = algo.run()



    print("分割结果:")

    for player_id, pieces in results.items():

        print(f"  玩家{player_id}: ", end="")

        for start, end in pieces:

            print(f"[{start:.2f}, {end:.2f}] ", end="")

        print()



    print()

    print("公平性验证:")

    fair_share = 1.0 / n_players

    for player in algo.players:

        print(f"  玩家{player.player_id}: 获得价值 {player.total_value:.4f} (公平份额 {fair_share:.4f})")





def envy_free_check():

    """无嫉妒检查"""

    print()

    print("=== 无嫉妒性 ===")

    print()

    print("Knaster-Yahalom保证：")

    print("  1. 每个玩家认为自己得到了至少1/n")

    print("  2. 最终分配是 envy-free（无嫉妒）的吗？")

    print()

    print("答案：不一定！可能存在嫉妒情况")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    simple_example()

    envy_free_check()



    print("\n说明：")

    print("  - 适用于连续物品（蛋糕、土地）")

    print("  - 离散物品的公平分割更复杂")

    print("  - 还有其他协议：Selfridge-Conway（3人 envy-free）")

