# -*- coding: utf-8 -*-

"""

算法实现：博弈论 / extensive_form_game



本文件实现 extensive_form_game 相关的算法功能。

"""



from typing import List, Dict, Tuple, Optional, Callable

from enum import Enum



class NodeType(Enum):

    """节点类型"""

    CHANCE = 1

    PLAYER = 2

    TERMINAL = 3



class GameNode:

    """博弈树节点"""

    def __init__(self, node_id: int, node_type: NodeType, player: str = None,

                 action: str = None, info_set: str = None):

        self.node_id = node_id

        self.node_type = node_type

        self.player = player

        self.action = action  # 导致这个节点的行动

        self.info_set = info_set  # 信息集标识

        self.children: List[GameNode] = []

        self.parent: Optional[GameNode] = None

        self.payoffs: Dict[str, float] = {}

        self.probability: float = 1.0  # 用于随机节点

    

    def add_child(self, child: 'GameNode'):

        """添加子节点"""

        child.parent = self

        self.children.append(child)

    

    def is_terminal(self) -> bool:

        """是否是终止节点"""

        return self.node_type == NodeType.TERMINAL

    

    def is_chance(self) -> bool:

        """是否是随机节点"""

        return self.node_type == NodeType.CHANCE



class ExtensiveFormGame:

    """

    扩展形式博弈树

    

    用于表示序贯博弈

    """

    

    def __init__(self, players: List[str]):

        self.players = players

        self.root: Optional[GameNode] = None

        self.nodes: Dict[int, GameNode] = {}

        self.next_node_id = 0

    

    def create_node(self, node_type: NodeType, player: str = None,

                   info_set: str = None) -> GameNode:

        """创建新节点"""

        node = GameNode(self.next_node_id, node_type, player, info_set=info_set)

        self.nodes[self.next_node_id] = node

        self.next_node_id += 1

        return node

    

    def set_root(self, node: GameNode):

        """设置根节点"""

        self.root = node

    

    def find_subgame_perfect_equilibrium(self) -> List[Tuple[str, str]]:

        """

        寻找子博弈完美均衡 (SPE)

        

        使用逆向归纳法

        """

        equilibria = []

        

        def backward_induction(node: GameNode):

            if node.is_terminal():

                return node.payoffs

            

            if node.is_chance():

                # 处理随机节点

                expected_payoffs = {p: 0.0 for p in self.players}

                for child in node.children:

                    child_payoffs = backward_induction(child)

                    prob = child.probability

                    for p in self.players:

                        expected_payoffs[p] += child_payoffs[p] * prob

                return expected_payoffs

            

            # 玩家决策节点

            best_child = None

            best_payoffs = None

            player = node.player

            

            for child in node.children:

                child_payoffs = backward_induction(child)

                if best_payoffs is None or child_payoffs[player] > best_payoffs[player]:

                    best_payoffs = child_payoffs

                    best_child = child

            

            equilibria.append((node.player, best_child.action if best_child else None))

            return best_payoffs

        

        if self.root:

            backward_induction(self.root)

        

        return equilibria



def build_simple_extensive_game() -> ExtensiveFormGame:

    """构建简单的扩展形式博弈"""

    game = ExtensiveFormGame(["Player1", "Player2"])

    

    # 创建节点结构

    #        根 (P1决策)

    #       /    \

    #     A        B

    #   (P2)     (P2)

    #   /  \     /  \

    # C    D    E    F

    

    root = game.create_node(NodeType.PLAYER, "Player1")

    game.set_root(root)

    

    node_a = game.create_node(NodeType.PLAYER, "Player2")

    node_b = game.create_node(NodeType.PLAYER, "Player2")

    root.add_child(node_a)

    root.add_child(node_b)

    

    # 叶子节点 (终止节点)

    terminal_c = game.create_node(NodeType.TERMINAL)

    terminal_c.payoffs = {"Player1": 3, "Player2": 2}

    node_a.add_child(terminal_c)

    

    terminal_d = game.create_node(NodeType.TERMINAL)

    terminal_d.payoffs = {"Player1": 1, "Player2": 1}

    node_a.add_child(terminal_d)

    

    terminal_e = game.create_node(NodeType.TERMINAL)

    terminal_e.payoffs = {"Player1": 2, "Player2": 0}

    node_b.add_child(terminal_e)

    

    terminal_f = game.create_node(NodeType.TERMINAL)

    terminal_f.payoffs = {"Player1": 4, "Player2": 3}

    node_b.add_child(terminal_f)

    

    # 设置行动标签

    node_a.action = "左"

    node_b.action = "右"

    

    return game



if __name__ == "__main__":

    print("=== 扩展形式博弈测试 ===")

    

    game = build_simple_extensive_game()

    

    print("博弈树结构:")

    print("""

              根 (Player1决策)

             /    \

           A        B

        (左/P2)   (右/P2)

        /    \     /    \

       C      D   E      F

    """)

    

    print("叶子节点收益:")

    print("  C: (3, 2) - Player1选左, Player2选左")

    print("  D: (1, 1) - Player1选左, Player2选右")

    print("  E: (2, 0) - Player1选右, Player2选左")

    print("  F: (4, 3) - Player1选右, Player2选右")

    

    print("\n=== 子博弈完美均衡 (逆向归纳) ===")

    spe = game.find_subgame_perfect_equilibrium()

    print(f"均衡策略: {spe}")

    

    print("\n分析:")

    print("  在节点A (左分支): Player2选择C (收益2) > D (收益1)")

    print("  在节点B (右分支): Player2选择F (收益3) > E (收益0)")

    print("  在根节点: Player1选择右分支 (期望4) > 左分支 (期望2)")

    print("  SPE: Player1选择右, Player2在B选F")

    

    print("\n=== 复杂博弈示例 ===")

    # 带承诺的博弈

    game2 = ExtensiveFormGame(["Player1", "Player2"])

    

    root2 = game2.create_node(NodeType.PLAYER, "Player1")

    game2.set_root(root2)

    

    # Player1可以选择承诺或不承诺

    commit_node = game2.create_node(NodeType.PLAYER, "Player2")

    no_commit = game2.create_node(NodeType.PLAYER, "Player2")

    root2.add_child(commit_node)

    root2.add_child(no_commit)

    

    commit_node.action = "承诺"

    no_commit.action = "不承诺"

    

    # 承诺后的结果

    commit_terminal = game2.create_node(NodeType.TERMINAL)

    commit_terminal.payoffs = {"Player1": 3, "Player2": 1}

    commit_node.add_child(commit_terminal)

    

    # 不承诺的结果

    no_commit_left = game2.create_node(NodeType.PLAYER, "Player2")

    no_commit_right = game2.create_node(NodeType.PLAYER, "Player2")

    no_commit.add_child(no_commit_left)

    no_commit.add_child(no_commit_right)

    

    no_commit_left.action = "合作"

    no_commit_right.action = "背叛"

    

    no_commit_left_terminal = game2.create_node(NodeType.TERMINAL)

    no_commit_left_terminal.payoffs = {"Player1": 2, "Player2": 2}

    no_commit_left.add_child(no_commit_left_terminal)

    

    no_commit_right_terminal = game2.create_node(NodeType.TERMINAL)

    no_commit_right_terminal.payoffs = {"Player1": 0, "Player2": 3}

    no_commit_right.add_child(no_commit_right_terminal)

    

    print("承诺博弈:")

    print("  Player1选择承诺 -> Player2获得1 (必须接受)")

    print("  Player1不承诺 -> Player2选择:")

    print("    合作: (2, 2)")

    print("    背叛: (0, 3)")

    

    spe2 = game2.find_subgame_perfect_equilibrium()

    print(f"\nSPE: {spe2}")

    print("注意: 承诺可以改变博弈结果")

