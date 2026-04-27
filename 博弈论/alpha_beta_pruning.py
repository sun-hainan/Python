# -*- coding: utf-8 -*-

"""

算法实现：博弈论 / alpha_beta_pruning



本文件实现 alpha_beta_pruning 相关的算法功能。

"""



from typing import Tuple, Optional

import copy





class AlphaBeta:

    """Alpha-Beta 剪枝算法"""

    def __init__(self, max_depth: int = 4):

        self.max_depth = max_depth

        self.nodes_evaluated = 0

        self.nodes_pruned = 0  # 剪枝计数



    def best_move(self, state, is_max_player: bool = True) -> Optional[object]:

        """找到最优移动"""

        moves = state.get_moves()

        if not moves:

            return None



        best_move = None

        # 初始化 alpha/beta

        alpha = float('-inf')

        beta = float('inf')



        for move in moves:

            next_state = state.apply_move(move)

            score = -self._alphabeta(

                next_state,

                depth=self.max_depth - 1,

                is_max=False,

                alpha=-beta,   # 传递负值（因为博弈是零和）

                beta=-alpha

            )



            if is_max_player:

                if score > alpha:

                    alpha = score

                    best_move = move

            else:

                if score < beta:

                    beta = score

                    best_move = move



        return best_move



    def _alphabeta(self, state, depth: int, is_max: bool, alpha: float, beta: float) -> float:

        """

        Alpha-Beta 递归搜索

        alpha: MAX 层下界

        beta: MIN 层上界

        """

        self.nodes_evaluated += 1



        # 终止条件

        if depth == 0 or state.is_terminal():

            return state.evaluate()



        moves = state.get_moves()

        if not moves:

            return state.evaluate()



        if is_max:

            # MAX 层：尝试最大化

            for move in moves:

                next_state = state.apply_move(move)

                score = self._alphabeta(next_state, depth - 1, is_max=False, alpha=alpha, beta=beta)

                if score > alpha:

                    alpha = score

                # 剪枝：若 alpha >= beta，MIN 层不会选择这个分支

                if alpha >= beta:

                    self.nodes_pruned += 1

                    break

            return alpha

        else:

            # MIN 层：尝试最小化

            for move in moves:

                next_state = state.apply_move(move)

                score = self._alphabeta(next_state, depth - 1, is_max=True, alpha=alpha, beta=beta)

                if score < beta:

                    beta = score

                # 剪枝：若 beta <= alpha，MAX 层不会选择这个分支

                if beta <= alpha:

                    self.nodes_pruned += 1

                    break

            return beta





# ============================ 简化演示：Tic-Tac-Toe ============================

class TicTacToe:

    X = "X"; O = "O"; EMPTY = "."



    def __init__(self, board=None, player="X"):

        if board is None:

            self.board = [[self.EMPTY for _ in range(3)] for _ in range(3)]

        else:

            self.board = [row[:] for row in board]

        self.player = player



    def is_terminal(self) -> bool:

        return self.get_winner() is not None or self._is_full()



    def get_winner(self) -> Optional[str]:

        lines = [

            [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],

            [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],

            [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)]

        ]

        for line in lines:

            vals = [self.board[r][c] for r,c in line]

            if vals[0] != self.EMPTY and vals[0] == vals[1] == vals[2]:

                return vals[0]

        return None



    def _is_full(self):

        return all(self.board[r][c] != self.EMPTY for r in range(3) for c in range(3))



    def get_moves(self):

        return [(r,c) for r in range(3) for c in range(3) if self.board[r][c] == self.EMPTY]



    def apply_move(self, move):

        new_board = [row[:] for row in self.board]

        new_board[move[0]][move[1]] = self.player

        next_player = self.O if self.player == self.X else self.X

        return TicTacToe(new_board, next_player)



    def evaluate(self) -> float:

        w = self.get_winner()

        if w == self.X: return 10.0

        if w == self.O: return -10.0

        return 0.0



    def __repr__(self):

        return "\n".join([" ".join(row) for row in self.board])





# ============================ 测试代码 ============================

if __name__ == "__main__":

    # 演示：比较 Minimax 和 Alpha-Beta 效率

    from minimax import Minimax



    board = [

        ["X", "O", "X"],

        ["X", "O", "."],

        ["O", "X", "."]

    ]

    state = TicTacToe(board, player=TicTacToe.O)  # O 的回合



    print("=== Alpha-Beta 剪枝演示（井字棋）===")

    print("当前局面（O 回合）：")

    print(state)

    print()



    # Alpha-Beta

    ab = AlphaBeta(max_depth=6)

    best_ab = ab.best_move(state, is_max_player=False)



    # 普通 Minimax（对比）

    mm = Minimax(max_depth=6)

    best_mm = mm.best_move(state, is_max_player=False)



    print(f"Alpha-Beta 最优移动: {best_ab}")

    print(f"Minimax 最优移动: {best_mm}")

    print()

    print(f"Alpha-Beta 评估节点数: {ab.nodes_evaluated}, 剪枝节点数: {ab.nodes_pruned}")

    print(f"Minimax 评估节点数: {mm.nodes_evaluated}")



    # 计算剪枝效率

    if mm.nodes_evaluated > 0:

        pruning_ratio = ab.nodes_pruned / mm.nodes_evaluated * 100

        print(f"剪枝效率: 减少了 {pruning_ratio:.1f}% 的搜索节点")



    print("\n✅ Alpha-Beta 在保持最优性的同时大幅减少搜索量")

    # 时间复杂度：最优 O(b^(d/2))，但仍保证找到最优解

    # 空间复杂度：O(d)

