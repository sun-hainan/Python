# -*- coding: utf-8 -*-
"""
算法实现：软件工程算法 / diff_algorithm

本文件实现 diff_algorithm 相关的算法功能。
"""

from typing import List, Tuple, Callable


def myers_diff(
    original: List[str],
    revised: List[str],
    eq: Callable[[str, str], bool] = lambda a, b: a == b,
) -> List[Tuple[str, int, int]]:
    """
    Myers Diff 算法主函数

    Args:
        original: 原始序列（如旧版本文件行列表）
        revised:  修订序列（如新版本文件行列表）
        eq:       判断两个元素是否相等的函数（可自定义）

    Returns:
        编辑脚本：List[(op, i, j)] 三元组
        - op == -1: 删除 original[i]（不包含 j）
        - op == +1: 插入 revised[j]（不包含 i）
        - op == 0:  保留 original[i] == revised[j]
    """
    n = len(original)
    m = len(revised)
    max_dist = n + m  # 编辑距离上界

    # ---- 构造 (N+1) x (M+1) 的 V 数组 ----
    # V[dist][k] = 满足 |x - y| = k 时 x 的最大值（x 为在 original 中的位置）
    # k 的范围: -M <= k <= N
    # 实际用 dict 存储以节省空间
    V: dict[int, dict[int, int]] = {}

    # 存储所有可到达的端点，用于回溯
    # end_points[dist] = (x, y)  在给定 dist 下首次到达 (N, M) 的位置
    end_points: dict[int, Tuple[int, int]] = {}

    for dist in range(max_dist + 1):
        V[dist] = {}
        for k in range(-dist, dist + 1, 2):
            if k < -m or k > n:
                continue

            # ---- 计算 V[dist][k] ----
            if dist == 0:
                x = 0
            elif k == -dist or (k != dist and V[dist - 1].get(k - 1, -1) < V[dist - 1].get(k + 1, -1)):
                # 从下方来（删除）
                x = V[dist - 1].get(k + 1, -1)
            else:
                # 从右方来（插入）
                x = V[dist - 1].get(k - 1, -1) + 1

            y = x - k

            # 沿着对角线走（匹配）
            while (
                x < n
                and y < m
                and eq(original[x], revised[y])
            ):
                x += 1
                y += 1

            V[dist][k] = x

            # 检查是否到达终点
            if x == n and y == m:
                end_points[dist] = (x, y)
                # 不立即返回，存储所有 dist 的端点（后续找最小 dist）

    # ---- 找到最小编辑距离 ----
    if not end_points:
        # 退化为全删全增
        min_dist = max_dist
        end_points[min_dist] = (n, m)
    else:
        min_dist = min(end_points.keys())

    # ---- 回溯找到具体编辑路径 ----
    # 从 (N, M) 和最小 dist 回溯
    edits = []
    x, y = n, m
    for dist in range(min_dist, -1, -1):
        if dist not in V:
            break
        # 当前点 (x, y)，上一 dist 的 k
        k = x - y
        prev_k_options = []
        if dist > 0:
            if k == -dist or (k != dist and V[dist - 1].get(k - 1, -1) < V[dist - 1].get(k + 1, -1)):
                prev_k = k + 1
            else:
                prev_k = k - 1
            prev_x = V[dist - 1].get(prev_k, 0)
            prev_y = prev_x - prev_k
        else:
            prev_x, prev_y = 0, 0

        # 对角线上的元素都是匹配的（保留操作）
        while x > prev_x and y > prev_y:
            edits.append((0, x - 1, y - 1))  # 保留
            x -= 1
            y -= 1

        if dist > 0:
            if x < prev_x:
                # 插入操作（y 在前一个状态更靠右）
                edits.append((+1, x, y - 1))  # 插入 revised[y-1]
                y -= 1
            else:
                # 删除操作
                edits.append((-1, x - 1, y))  # 删除 original[x-1]
                x -= 1

    edits.reverse()
    return edits


def format_diff(
    original: List[str],
    revised: List[str],
    edits: List[Tuple[str, int, int]],
) -> str:
    """将编辑脚本格式化为可读的 diff 字符串"""
    output = []
    for op, i, j in edits:
        if op == 0:
            output.append(f"  {original[i]}")
        elif op == -1:
            output.append(f"- {original[i]}")
        elif op == +1:
            output.append(f"+ {revised[j]}")
    return "\n".join(output)


if __name__ == "__main__":
    print("=" * 50)
    print("Myers Diff 算法 - 单元测试")
    print("=" * 50)

    # 示例：两个版本的代码片段
    orig_lines = [
        "def add(a, b):",
        "    return a + b",
        "",
        "def sub(a, b):",
        "    return a - b",
        "",
        "def mul(a, b):",
        "    return a * b",
    ]
    rev_lines = [
        "def add(a, b, c=0):",
        "    return a + b + c",
        "",
        "# 新增: 绝对值函数",
        "def abs(x):",
        "    return x if x >= 0 else -x",
        "",
        "def mul(a, b):",
        "    return a * b",
        "",
        "# 新增: 除法函数",
        "def div(a, b):",
        "    return a / b",
    ]

    edits = myers_diff(orig_lines, rev_lines)

    print("\n原始文件 (旧):")
    for idx, line in enumerate(orig_lines):
        print(f"  {idx + 1}: {line}")

    print("\n修订文件 (新):")
    for idx, line in enumerate(rev_lines):
        print(f"  {idx + 1}: {line}")

    print("\n编辑脚本:")
    print("  op=-1: 删除 | op=0: 保留 | op=+1: 插入")
    diff_text = format_diff(orig_lines, rev_lines, edits)
    print(diff_text)

    # 统计
    deletions = sum(1 for op, _, _ in edits if op == -1)
    insertions = sum(1 for op, _, _ in edits if op == +1)
    matches = sum(1 for op, _, _ in edits if op == 0)
    print(f"\n统计: 删除={deletions}, 插入={insertions}, 保留={matches}")
    print(f"编辑距离 = {deletions + insertions}")

    # 验证 diff 可逆性（可选）
    print(f"\n复杂度: O((N+M)D)，N={len(orig_lines)}, M={len(rev_lines)}")
    print("算法完成。")
