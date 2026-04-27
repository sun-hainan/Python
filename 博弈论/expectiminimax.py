# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / expectiminimax

本文件实现 expectiminimax 相关的算法功能。
"""

from typing import List, Tuple, Optional
import random


class ChanceGameState:
    """带有随机性的博弈状态"""
    def get_moves(self) -> List: ...
    def get_chance_outcomes(self) -> List[Tuple[object, float]]: ...
    # 返回: List[(outcome, probability)]
    def apply_move(self, move: object) -> "ChanceGameState": ...
    def apply_chance_outcome(self, outcome: object) -> "ChanceGameState": ...
    def evaluate(self) -> float: ...
    def is_terminal(self) -> bool: ...


class Expectiminimax:
    """期望极大极小搜索"""
    def __init__(self, max_depth: int = 4):
        self.max_depth = max_depth
        self.nodes_evaluated = 0

    def best_move(self, state: ChanceGameState, is_max_player: bool = True) -> Optional[object]:
        """找到最优移动（针对确定性动作）"""
        moves = state.get_moves()
        if not moves:
            return None

        best_score = float('-inf') if is_max_player else float('inf')
        best_move = None

        for move in moves:
            next_state = state.apply_move(move)
            score = -self._expectiminimax(next_state, depth=self.max_depth-1, is_max=not is_max_player)
            if is_max_player:
                if score > best_score:
                    best_score = score
                    best_move = move
            else:
                if score < best_score:
                    best_score = score
                    best_move = move

        return best_move

    def _expectiminimax(self, state: ChanceGameState, depth: int, is_max: bool) -> float:
        """递归期望极大极小"""
        self.nodes_evaluated += 1

        if depth == 0 or state.is_terminal():
            return state.evaluate()

        # 获取 CHANCE 节点的可能结果
        chance_outcomes = state.get_chance_outcomes()

        if is_max:
            # MAX 层：选择最大
            best = float('-inf')
            for move in state.get_moves():
                next_state = state.apply_move(move)
                val = self._expectiminimax(next_state, depth - 1, is_max=False)
                best = max(best, val)
            return best
        else:
            # MIN 层或 CHANCE 层
            # 简化处理：若无机会结果，走 MIN 逻辑；否则走 CHANCE 逻辑
            if not chance_outcomes:
                # MIN 层（无随机性）
                best = float('inf')
                for move in state.get_moves():
                    next_state = state.apply_move(move)
                    val = self._expectiminimax(next_state, depth - 1, is_max=True)
                    best = min(best, val)
                return best
            else:
                # CHANCE 层（期望计算）
                expected = 0.0
                for outcome, prob in chance_outcomes:
                    chance_state = state.apply_chance_outcome(outcome)
                    val = self._expectiminimax(chance_state, depth - 1, is_max=is_max)
                    expected += prob * val
                return expected


# ============================ 演示：简化掷骰子棋类游戏 ============================
class DiceTicTacToe(ChanceGameState):
    """带骰子的井字棋：每回合先掷骰子，只有骰子点数对应的位置才能落子"""
    X = "X"; O = "O"; EMPTY = "."

    def __init__(self, board=None, player="X", dice_face: Optional[int] = None):
        if board is None:
            self.board = [[self.EMPTY for _ in range(3)] for _ in range(3)]
        else:
            self.board = [row[:] for row in board]
        self.player = player
        self.dice_face = dice_face  # 本回合骰子点数（1-9，对应位置索引）

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

    def get_moves(self) -> List[Tuple[int, int]]:
        """只允许骰子点数对应的空位"""
        if self.dice_face is None:
            return []
        row = (self.dice_face - 1) // 3
        col = (self.dice_face - 1) % 3
        if self.board[row][col] == self.EMPTY:
            return [(row, col)]
        return []  # 对应位置已被占

    def get_chance_outcomes(self) -> List[Tuple[int, float]]:
        """骰子结果：每个面概率 1/6"""
        return [(i, 1/6) for i in range(1, 10)]

    def apply_move(self, move: Tuple[int, int]) -> "DiceTicTacToe":
        new_board = [row[:] for row in self.board]
        new_board[move[0]][move[1]] = self.player
        next_player = self.O if self.player == self.X else self.X
        return DiceTicTacToe(new_board, next_player, dice_face=None)

    def apply_chance_outcome(self, outcome: int) -> "DiceTicTacToe":
        """应用骰子结果，产生新状态（当前玩家不变，等待落子）"""
        return DiceTicTacToe([row[:] for row in self.board], self.player, dice_face=outcome)

    def evaluate(self) -> float:
        w = self.get_winner()
        if w == self.X: return 10.0
        if w == self.O: return -10.0
        return 0.0

    def __repr__(self):
        dice_info = f", dice={self.dice_face}" if self.dice_face else ""
        return f"{self.player}'s turn{dice_info}\n" + "\n".join([" ".join(row) for row in self.board])


# ============================ 测试代码 ============================
if __name__ == "__main__":
    print("=== Expectiminimax 演示（掷骰子井字棋）===")

    state = DiceTicTacToe(player=DiceTicTacToe.X)
    print("初始局面（无骰子约束）：")
    print(state)
    print()

    # 创建策略：模拟掷骰子后选择最优落子
    for dice_roll in [1, 5, 9]:  # 3种可能的骰子结果
        state_with_dice = state.apply_chance_outcome(dice_roll)
        moves = state_with_dice.get_moves()

        if moves:
            print(f"若骰子为 {dice_roll}，落子位置: {moves}")

    # 模拟完整一局（简化版）
    print("\n=== 模拟一局 ===")
    state = DiceTicTacToe(player=DiceTacToe.X)
    for turn in range(9):
        # 掷骰子
        dice = random.randint(1, 9)
        state.dice_face = dice

        moves = state.get_moves()
        if not moves:
            print(f"回合 {turn+1}: 骰子={dice}, 无法落子（位置被占），跳过")
            # 直接切换玩家（简化处理）
            state.player = DiceTacToe.O if state.player == DiceTacToe.X else DiceTacToe.X
            continue

        # 使用 expectiminimax 选择落子位置
        e_mm = Expectiminimax(max_depth=3)
        best = e_mm.best_move(state, is_max_player=(state.player == state.X))

        if best:
            state = state.apply_move(best)
            print(f"回合 {turn+1}: 骰子={dice}, {state.player}'s move 实际在上一轮落子")

        if state.is_terminal():
            print(f"游戏结束，胜者: {state.get_winner()}")
            break

    print("\n最终局面：")
    print(state)

    print("\n✅ Expectiminimax 能够处理随机性博弈")
    # 时间复杂度：O(b^d * n^c)，骰子有6种可能
