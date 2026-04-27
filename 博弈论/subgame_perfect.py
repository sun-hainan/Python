# -*- coding: utf-8 -*-

"""

算法实现：博弈论 / subgame_perfect



本文件实现 subgame_perfect 相关的算法功能。

"""



from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

import numpy as np





@dataclass

class Node:

    """博弈树节点"""

    node_id: str

    is_terminal: bool = False

    player_to_move: Optional[str] = None  # 当前行动的玩家

    children: List["Node"] = None         # 子节点列表

    utility: Optional[Dict[str, float]] = None  # 终止节点的收益



    def __post_init__(self):

        if self.children is None:

            self.children = []





class SubgamePerfectEquilibrium:

    """子博弈完美均衡求解器（逆向归纳）"""



    @staticmethod

    def solve(game_tree: Node) -> Tuple[Dict[str, str], float]:

        """

        通过逆向归纳求解 SPE

        返回：(策略字典 {node_id: chosen_child_id}, 根节点收益)

        """

        strategy_profile = {}



        def backward_induction(node: Node) -> Dict[str, float]:

            """

            逆向归纳：返回该节点处各行动的期望收益

            对于终止节点，直接返回收益

            """

            if node.is_terminal:

                return node.utility



            # 递归求解所有子节点

            child_utilities = []

            for child in node.children:

                child_utils = backward_induction(child)

                child_utilities.append((child, child_utils))



            # 当前玩家选择最优行动（最大化自己的收益）

            player = node.player_to_move

            best_child = None

            best_utility = float('-inf')



            for child, child_utils in child_utilities:

                player_util = child_utils.get(player, 0)

                if player_util > best_utility:

                    best_utility = player_util

                    best_child = child



            # 记录策略

            if best_child:

                strategy_profile[node.node_id] = best_child.node_id



            # 返回最佳子节点的收益

            return child_utilities[[c.node_id for c in node.children].index(best_child)][1] if best_child else {}



        root_utilities = backward_induction(game_tree)

        return strategy_profile, root_utilities





# ============================ 简化博弈树示例 ============================

class ExtensiveFormGame:

    """扩展式博弈构造器"""



    @staticmethod

    def create_simple_game() -> Node:

        """

        创建简单博弈树：

        根节点（玩家1选择）:

            -> A节点（玩家2选择）:

                -> (3, 2) 终止（玩家1=3, 玩家2=2）

                -> (1, 1) 终止

            -> B节点（玩家2选择）:

                -> (0, 0) 终止

                -> (2, 5) 终止

        """

        # 终止节点

        t1 = Node("t1", is_terminal=True, utility={"p1": 3, "p2": 2})

        t2 = Node("t2", is_terminal=True, utility={"p1": 1, "p2": 1})

        t3 = Node("t3", is_terminal=True, utility={"p1": 0, "p2": 0})

        t4 = Node("t4", is_terminal=True, utility={"p1": 2, "p2": 5})



        # 玩家2 决策节点

        node_a = Node("A", player_to_move="p2", children=[t1, t2])

        node_b = Node("B", player_to_move="p2", children=[t3, t4])



        # 玩家1 决策节点（根）

        root = Node("root", player_to_move="p1", children=[node_a, node_b])



        return root



    @staticmethod

    def create_with_threat() -> Node:

        """

        创建包含不可信威胁的博弈：

        玩家1 先动，选择 L 或 R

        - 若选 L，玩家2 可选 U 或 D（收益 L=(2,1), D=(1,0)）

        - 若选 R，玩家2 被迫选 U（收益 (0,0)）

        分析：

        - 若玩家2 先行动，它会选择 U（1 > 0）

        - 但玩家1 选择 L 后，玩家2 的最优是 U（1 > 0）

        - 所以玩家1 应选择 L

        - 子博弈完美均衡：L -> U

        """

        # 终止节点

        t_lu = Node("t_lu", is_terminal=True, utility={"p1": 2, "p2": 1})

        t_ld = Node("t_ld", is_terminal=True, utility={"p1": 1, "p2": 0})

        t_r = Node("t_r", is_terminal=True, utility={"p1": 0, "p2": 0})



        # 玩家2 在 L 分支的选择

        node_l = Node("L", player_to_move="p2", children=[t_lu, t_ld])

        # 玩家2 在 R 分支的选择（实际只有一条路）

        node_r = Node("R", player_to_move="p2", children=[t_r])



        # 玩家1 根节点

        root = Node("root", player_to_move="p1", children=[node_l, node_r])



        return root





# ============================ 测试代码 ============================

if __name__ == "__main__":

    print("=== 子博弈完美均衡演示 ===")



    # 案例1：简单博弈树

    game1 = ExtensiveFormGame.create_simple_game()

    strategy1, _ = SubgamePerfectEquilibrium.solve(game1)



    print("\n博弈树 1（玩家1先手，玩家2后手）：")

    print("  root: 玩家1 选择 A 或 B")

    print("    A -> 玩家2 选择 (3,2) 或 (1,1)")

    print("    B -> 玩家2 选择 (0,0) 或 (2,5)")

    print(f"\nSPE 策略: {strategy1}")

    print("解读：root -> A（因为 A 的最佳结果是 3 > B 的最佳结果 2）")



    # 案例2：不可信威胁

    game2 = ExtensiveFormGame.create_with_threat()

    strategy2, root_util = SubgamePerfectEquilibrium.solve(game2)



    print("\n\n博弈树 2（含不可信威胁）：")

    print("  玩家1 选择 L 或 R")

    print("  L分支: 玩家2 可选 U(2,1) 或 D(1,0)")

    print("  R分支: 玩家2 被迫 U(0,0)")

    print(f"\nSPE 策略: {strategy2}")

    print("解读：玩家1 选 L，玩家2 选 U")

    print("      （虽然若玩家1选R，玩家2会选择U获取0收益，但玩家1不会真的选R）")



    # 验证

    assert "root" in strategy2

    assert strategy2["root"] == "L"

    assert strategy2.get("L") == "t_lu"



    print("\n✅ 逆向归纳正确排除了不可信威胁")

    print("时间复杂度：O(N) — 每个节点访问一次")

    print("空间复杂度：O(H) — 递归栈深度")

