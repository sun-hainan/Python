# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / iterative_deepening

本文件实现 iterative_deepening 相关的算法功能。
"""

from typing import Optional, Tuple
import time


class IterativeDeepening:
    """迭代深化搜索"""
    def __init__(self, time_limit: float = 5.0):
        self.time_limit = time_limit          # 时间限制（秒）
        self.best_move_found: Optional[object] = None
        self.final_depth: int = 0
        self.nodes_evaluated = 0

    def search(self, state, is_max_player: bool = True) -> Optional[object]:
        """
        执行迭代深化搜索
        返回：最优着法
        """
        start_time = time.time()
        depth = 1

        while True:
            # 检查时间限制
            elapsed = time.time() - start_time
            if elapsed >= self.time_limit:
                print(f"时间用尽，停止于深度 {depth}")
                break

            alpha_beta = AlphaBetaPruned(max_depth=depth)
            best = alpha_beta.best_move(state, is_max_player)

            self.nodes_evaluated += alpha_beta.nodes_evaluated
            self.final_depth = depth
            self.best_move_found = best

            if best is not None:
                print(f"深度 {depth} 完成，评估 {alpha_beta.nodes_evaluated} 节点，用时 {time.time()-start_time:.2f}s")

            depth += 1

        return self.best_move_found


class AlphaBetaPruned:
    """带 Alpha-Beta 剪枝的搜索（供迭代深化使用）"""
    def __init__(self, max_depth: int = 4):
        self.max_depth = max_depth
        self.nodes_evaluated = 0

    def best_move(self, state, is_max_player: bool = True) -> Optional[object]:
        moves = state.get_moves()
        if not moves:
            return None

        best_move = None
        alpha = float('-inf')
        beta = float('inf')

        for move in moves:
            next_state = state.apply_move(move)
            score = -self._alphabeta(next_state, self.max_depth - 1, is_max=False, alpha=-beta, beta=-alpha)
            if score > alpha:
                alpha = score
                best_move = move

        return best_move

    def _alphabeta(self, state, depth: int, is_max: bool, alpha: float, beta: float) -> float:
        self.nodes_evaluated += 1

        if depth == 0 or state.is_terminal():
            return state.evaluate()

        moves = state.get_moves()
        if not moves:
            return state.evaluate()

        if is_max:
            for move in moves:
                next_state = state.apply_move(move)
                score = self._alphabeta(next_state, depth - 1, False, alpha, beta)
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
            return alpha
        else:
            for move in moves:
                next_state = state.apply_move(move)
                score = self._alphabeta(next_state, depth - 1, True, alpha, beta)
                if score < beta:
                    beta = score
                if beta <= alpha:
                    break
            return beta


# ============================ Tic-Tac-Toe 状态类 ============================
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
    print("=== 迭代深化搜索演示 ===")

    board = [
        ["X", "O", "."],
        [".", "X", "."],
        [".", ".", "O"]
    ]
    state = TicTacToe(board, player=TicTacToe.O)
    print("当前局面（O 回合）：")
    print(state)
    print()

    # 迭代深化搜索（时间限制 2 秒）
    ids = IterativeDeepening(time_limit=2.0)
    best = ids.search(state, is_max_player=False)

    print(f"\n最终选择: {best}")
    print(f"搜索深度: {ids.final_depth}")
    print(f"总评估节点数: {ids.nodes_evaluated}")

    if best:
        new_state = state.apply_move(best)
        print("\n落子后局面：")
        print(new_state)

    print("\n✅ 迭代深化在有限时间内找到最深层的最优着法")
    # 优点：时间可控，每层都给出当前最优解
    # 常用于国际象棋引擎（如 chess engines）
