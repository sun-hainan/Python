# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / transposition_table

本文件实现 transposition_table 相关的算法功能。
"""

from typing import Dict, Optional, Tuple
import random


class TranspositionTable:
    """置换表：用字典模拟简单的哈希表"""

    # 表项类型
    EXACT = 0          # 精确值（完全在 alpha-beta 窗口内）
    LOWER_BOUND = 1    # 下界（值 >= 这个值）
    UPPER_BOUND = 2    # 上界（值 <= 这个值）

    def __init__(self):
        self.entries: Dict[int, dict] = {}  # key: zobrist_hash, value: 表项
        self.hits = 0
        self.misses = 0

    def probe(self, hash_key: int, depth: int, alpha: float, beta: float) -> Optional[float]:
        """
        查询表：若找到深度足够、类型合适的表项，直接返回评分
        返回：float=命中，None=未命中
        """
        if hash_key not in self.entries:
            self.misses += 1
            return None

        entry = self.entries[hash_key]
        # 深度不够时不能直接使用
        if entry["depth"] < depth:
            self.misses += 1
            return None

        self.hits += 1
        score = entry["score"]

        if entry["node_type"] == self.EXACT:
            return score
        elif entry["node_type"] == self.LOWER_BOUND:
            # 分数是一个下界，实际值可能更大
            if score >= beta:
                return score
        elif entry["node_type"] == self.UPPER_BOUND:
            # 分数是一个上界，实际值可能更小
            if score <= alpha:
                return score

        self.misses += 1
        return None

    def store(self, hash_key: int, depth: int, score: float, node_type: int,
              best_move: Optional[Tuple] = None) -> None:
        """存储表项"""
        self.entries[hash_key] = {
            "depth": depth,
            "score": score,
            "node_type": node_type,
            "best_move": best_move
        }


class ZobristHash:
    """Zobrist 哈希：快速计算博弈状态的哈希值"""
    def __init__(self, board_size: int = 3, num_piece_types: int = 3):
        # 3 种棋子类型：EMPTY=0, X=1, O=2，加上位置索引
        self.hash_table: Dict[Tuple[int, int], int] = {}
        self.board_size = board_size
        self.num_piece_types = num_piece_types
        self._init_table()

    def _init_table(self):
        """初始化 Zobrist 随机数表"""
        random.seed(42)
        for piece in range(self.num_piece_types):
            for pos in range(self.board_size * self.board_size):
                key = random.getrandbits(64)
                self.hash_table[(piece, pos)] = key

    def compute_hash(self, board: list, player: str) -> int:
        """计算棋盘状态的哈希值"""
        h = 0
        piece_map = {'.': 0, 'X': 1, 'O': 2}
        for r in range(self.board_size):
            for c in range(self.board_size):
                pos = r * self.board_size + c
                piece = piece_map.get(board[r][c], 0)
                h ^= self.hash_table[(piece, pos)]
        return h


class TTAlphaBeta:
    """带置换表的 Alpha-Beta 搜索"""
    def __init__(self, max_depth: int = 4, use_tt: bool = True):
        self.max_depth = max_depth
        self.use_tt = use_tt
        self.tt = TranspositionTable() if use_tt else None
        self.nodes_evaluated = 0

    def best_move(self, state, zobrist: ZobristHash, is_max_player: bool = True) -> Optional[object]:
        moves = state.get_moves()
        if not moves:
            return None

        alpha = float('-inf')
        beta = float('inf')
        best_move = None

        hash_key = zobrist.compute_hash(
            [row for row in state.board],
            state.player
        )

        for move in moves:
            next_state = state.apply_move(move)
            score = -self._alphabeta(next_state, zobrist, self.max_depth - 1,
                                     is_max=False, alpha=-beta, beta=-alpha)
            if score > alpha:
                alpha = score
                best_move = move

        return best_move

    def _alphabeta(self, state, zobrist: ZobristHash, depth: int,
                   is_max: bool, alpha: float, beta: float) -> float:
        self.nodes_evaluated += 1

        if depth == 0 or state.is_terminal():
            return state.evaluate()

        hash_key = zobrist.compute_hash(
            [row for row in state.board],
            state.player
        )

        # 查表
        if self.use_tt:
            cached = self.tt.probe(hash_key, depth, alpha, beta)
            if cached is not None:
                return cached

        moves = state.get_moves()
        if not moves:
            return state.evaluate()

        best_move = None
        if is_max:
            for move in moves:
                next_state = state.apply_move(move)
                score = self._alphabeta(state, zobrist, depth - 1, False, alpha, beta)
                if score > alpha:
                    alpha = score
                    best_move = move
                if alpha >= beta:
                    break

            # 存储
            if self.use_tt:
                if alpha >= beta:
                    node_type = TranspositionTable.UPPER_BOUND
                else:
                    node_type = TranspositionTable.EXACT
                self.tt.store(hash_key, depth, alpha, node_type, best_move)

            return alpha
        else:
            for move in moves:
                next_state = state.apply_move(move)
                score = self._alphabeta(state, zobrist, depth - 1, True, alpha, beta)
                if score < beta:
                    beta = score
                    best_move = move
                if beta <= alpha:
                    break

            # 存储
            if self.use_tt:
                if beta <= alpha:
                    node_type = TranspositionTable.LOWER_BOUND
                else:
                    node_type = TranspositionTable.EXACT
                self.tt.store(hash_key, depth, beta, node_type, best_move)

            return beta


# ============================ Tic-Tac-Toe ============================
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
    print("=== 置换表演示（Zobrist Hash + Alpha-Beta）===")

    board = [
        ["X", "O", "X"],
        [".", "X", "."],
        ["O", ".", "."]
    ]
    state = TicTacToe(board, player=TicTacToe.O)
    print("当前局面（O 回合）：")
    print(state)
    print()

    zobrist = ZobristHash(board_size=3, num_piece_types=3)

    # 不使用置换表
    tt_off = TTAlphaBeta(max_depth=5, use_tt=False)
    best_off = tt_off.best_move(state, zobrist, is_max_player=False)
    print(f"不使用 TT: best_move={best_off}, 节点数={tt_off.nodes_evaluated}")

    # 使用置换表
    tt_on = TTAlphaBeta(max_depth=5, use_tt=True)
    best_on = tt_on.best_move(state, zobrist, is_max_player=False)
    print(f"使用 TT: best_move={best_on}, 节点数={tt_on.nodes_evaluated}")
    print(f"TT 命中率: {tt_on.tt.hits}/{tt_on.tt.hits + tt_on.tt.misses} ({tt_on.tt.hits*100/(tt_on.tt.hits+tt_on.tt.misses):.1f}%)")

    assert best_off == best_on, "TT 不应改变搜索结果"
    print("\n✅ 置换表加速搜索且不影响正确性")
    print("时间复杂度：最坏 O(b^d)，实际因去重加速")
    print("空间复杂度：O(N) 存储的局面数")
