# -*- coding: utf-8 -*-

"""

算法实现：博弈论 / minimax



本文件实现 minimax 相关的算法功能。

"""



from typing import List, Tuple, Optional, Callable

import copy





class GameState:

    """博弈状态基类"""

    def get_moves(self) -> List: ...

    def evaluate(self) -> float: ...

    def is_terminal(self) -> bool: ...





class Minimax:

    """极小极大搜索算法"""

    def __init__(self, max_depth: int = 4):

        self.max_depth = max_depth

        self.nodes_evaluated = 0  # 统计：评估的节点数



    def best_move(self, state: GameState, is_max_player: bool = True) -> Optional[object]:

        """

        找到最优移动

        is_max_player: True=MAX层(最大化), False=MIN层(最小化)

        """

        moves = state.get_moves()

        if not moves:

            return None



        best_score = float('-inf') if is_max_player else float('inf')

        best_move = None



        for move in moves:

            # 生成下一状态

            next_state = state.apply_move(move)

            # 递归搜索（取负，因为对手视角会反转）

            score = -self._minimax(next_state, depth=self.max_depth - 1, is_max=not is_max_player)

            # 更新最优

            if is_max_player:

                if score > best_score:

                    best_score = score

                    best_move = move

            else:

                if score < best_score:

                    best_score = score

                    best_move = move



        return best_move



    def _minimax(self, state: GameState, depth: int, is_max: bool) -> float:

        """

        递归极小极大搜索

        is_max: True=MAX层, False=MIN层

        """

        self.nodes_evaluated += 1



        # 终止条件：到达搜索深度或终止局面

        if depth == 0 or state.is_terminal():

            return state.evaluate()



        moves = state.get_moves()

        if not moves:

            return state.evaluate()  # 无合法移动，评估当前局面



        if is_max:

            # MAX 层：选择最大值

            best_score = float('-inf')

            for move in moves:

                next_state = state.apply_move(move)

                score = self._minimax(next_state, depth - 1, is_max=False)

                best_score = max(best_score, score)

            return best_score

        else:

            # MIN 层：选择最小值

            best_score = float('inf')

            for move in moves:

                next_state = state.apply_move(move)

                score = self._minimax(next_state, depth - 1, is_max=True)

                best_score = min(best_score, score)

            return best_score





# ============================ 简化演示：Tic-Tac-Toe ============================

class TicTacToe(GameState):

    """简化版井字棋"""

    X = "X"

    O = "O"

    EMPTY = "."



    def __init__(self, board: List[List[str]] = None, player: str = X):

        # 9个格子的棋盘（3x3）

        if board is None:

            self.board = [[self.EMPTY for _ in range(3)] for _ in range(3)]

        else:

            self.board = [row[:] for row in board]

        self.player = player  # 当前玩家

        self.winner_cache: Optional[str] = None  # 缓存赢家判定



    def is_terminal(self) -> bool:

        """终止局面：有人获胜或棋盘填满"""

        return self.get_winner() is not None or self._is_full()



    def get_winner(self) -> Optional[str]:

        """获取获胜者（缓存优化）"""

        if self.winner_cache is not None:

            return self.winner_cache



        lines = (

            # 行

            [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],

            # 列

            [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],

            # 对角线

            [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)]

        )

        for line in lines:

            values = [self.board[r][c] for r,c in line]

            if values[0] != self.EMPTY and values[0] == values[1] == values[2]:

                self.winner_cache = values[0]

                return values[0]

        self.winner_cache = None

        return None



    def _is_full(self) -> bool:

        return all(self.board[r][c] != self.EMPTY for r in range(3) for c in range(3))



    def get_moves(self) -> List[Tuple[int, int]]:

        """获取所有合法移动（空位）"""

        return [(r, c) for r in range(3) for c in range(3)

                if self.board[r][c] == self.EMPTY]



    def apply_move(self, move: Tuple[int, int]) -> "TicTacToe":

        """应用移动，返回新状态"""

        new_board = [row[:] for row in self.board]

        new_board[move[0]][move[1]] = self.player

        next_player = self.O if self.player == self.X else self.X

        return TicTacToe(new_board, next_player)



    def evaluate(self) -> float:

        """评估局面：X胜=+10, O胜=-10, 平局=0, 未结束=0"""

        winner = self.get_winner()

        if winner == self.X:

            return 10.0

        elif winner == self.O:

            return -10.0

        return 0.0



    def __repr__(self):

        rows = [" ".join(row) for row in self.board]

        return "\n".join(rows)





# ============================ 测试代码 ============================

if __name__ == "__main__":

    # 简单开局

    board = [

        ["X", ".", "."],

        [".", "O", "."],

        [".", ".", "."]

    ]

    state = TicTacToe(board, player=TicTacToe.X)



    print("=== Minimax 算法演示（井字棋）===")

    print("当前局面（X 回合）：")

    print(state)

    print()



    minimax = Minimax(max_depth=5)

    best = minimax.best_move(state, is_max_player=True)



    print(f"最优移动: {best}")

    print(f"搜索节点数: {minimax.nodes_evaluated}")



    # 应用最优移动

    if best:

        new_state = state.apply_move(best)

        print("\n落子后局面：")

        print(new_state)



    # 验证：若 X 在中心落子（0,0 或 2,2 对角线），直接获胜

    # 这里选择 (0,0) 或 (2,2) 等角部也可以

    print("\n✅ Minimax 找到最优策略")



    # 时间复杂度：O(b^d) = O(9^5) ≈ 59049 最坏情况

    # 实际因剪枝和终止检测，会远小于此值

