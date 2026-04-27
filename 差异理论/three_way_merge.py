# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / three_way_merge

本文件实现 three_way_merge 相关的算法功能。
"""

from enum import Enum


class MergeStatus(Enum):
    """
    合并状态枚举
    """
    CLEAN = "clean"          # 干净合并，无冲突
    CONFLICT = "conflict"    # 存在冲突
    MODIFIED = "modified"    # 有修改但无冲突


class MergeResult:
    """
    合并结果类
    """
    def __init__(self):
        self.status = MergeStatus.CLEAN
        self.content = []      # 合并后的行列表
        self.conflicts = []    # 冲突列表
        self.conflict_regions = []  # 冲突区域标记


def three_way_merge(original, branch_a, branch_b):
    """
    三路合并算法
    
    参数:
        original: 原始版本的行列表
        branch_a: 分支A的版本行列表
        branch_b: 分支B的版本行列表
    
    返回:
        MergeResult合并结果
    """
    # 找出两个分支相对于原始版本的修改
    diff_a = compute_diff(original, branch_a)
    diff_b = compute_diff(original, branch_b)
    
    result = MergeResult()
    result.content = list(original)  # 从原始版本开始
    
    # 跟踪冲突区域
    has_conflict = False
    
    # 对每个修改区域进行处理
    for start, end, new_lines in diff_a:
        # 应用分支A的修改
        result.content = apply_change(result.content, start, end, new_lines)
    
    # 暂时存储分支B的修改，稍后处理
    pending_changes_b = []
    for start, end, new_lines in diff_b:
        pending_changes_b.append((start, end, new_lines))
    
    # 简化处理：对于分支B的修改，检查是否与分支A冲突
    # 这里使用简化的行级合并策略
    final_content = []
    i = 0
    j = 0
    n_a = len(branch_a)
    n_b = len(branch_b)
    
    # 使用LCS风格的合并
    lcs_result = lcs_merge(branch_a, branch_b)
    
    result.content = lcs_result
    
    # 检测是否有冲突（简化为检查是否有差异）
    if branch_a != branch_b:
        # 检查是否有无法自动合并的情况
        pass
    
    return result


def compute_diff(original, modified):
    """
    计算从original到modified的差异
    
    参数:
        original: 原始行列表
        modified: 修改后行列表
    
    返回:
        差异列表 [(start, end, new_lines), ...]
    """
    diff_result = []
    
    # 使用简单的行比较
    n = len(original)
    m = len(modified)
    
    # 动态规划找最长公共子序列
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if original[i - 1] == modified[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    # 回溯找差异
    i = n
    j = m
    changes = []
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and original[i - 1] == modified[j - 1]:
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
            # 添加的字符
            changes.append(('add', j - 1, modified[j - 1]))
            j -= 1
        else:
            # 删除的字符
            changes.append(('del', i - 1, original[i - 1]))
            i -= 1
    
    changes.reverse()
    return changes


def apply_change(content, start, end, new_lines):
    """
    将修改应用到内容
    
    参数:
        content: 原始内容行列表
        start: 起始位置
        end: 结束位置
        new_lines: 新的行列表
    
    返回:
        应用修改后的内容
    """
    result = list(content)
    result[start:end] = new_lines
    return result


def lcs_merge(lines_a, lines_b):
    """
    使用LCS风格的合并算法
    
    参数:
        lines_a: 分支A的行列表
        lines_b: 分支B的行列表
    
    返回:
        合并后的行列表
    """
    n = len(lines_a)
    m = len(lines_b)
    
    # 计算LCS长度
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if lines_a[i - 1] == lines_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    # 回溯构建合并结果
    result = []
    i = n
    j = m
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and lines_a[i - 1] == lines_b[j - 1]:
            result.append(lines_a[i - 1])
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] > dp[i - 1][j]):
            result.append(lines_b[j - 1])
            j -= 1
        elif i > 0:
            result.append(lines_a[i - 1])
            i -= 1
    
    result.reverse()
    return result


def recursive_three_way_merge(original, a_changes, b_changes):
    """
    递归式三路合并，处理复杂的合并场景
    
    参数:
        original: 原始内容
        a_changes: 分支A的修改列表
        b_changes: 分支B的修改列表
    
    返回:
        MergeResult合并结果
    """
    result = MergeResult()
    
    # 简化实现：使用字符串级别合并
    result.content = lcs_merge(a_changes, b_changes)
    
    # 检查是否有冲突
    # 冲突的定义：两个分支修改了同一处且内容不同
    if has_conflicts(original, a_changes, b_changes):
        result.status = MergeStatus.CONFLICT
    else:
        result.status = MergeStatus.CLEAN
    
    return result


def has_conflicts(original, changes_a, changes_b):
    """
    检测是否存在冲突
    
    参数:
        original: 原始内容
        changes_a: 分支A的修改
        changes_b: 分支B的修改
    
    返回:
        是否存在冲突
    """
    # 简化实现：检查修改区域是否有重叠
    # 如果两个分支修改了相同的行号区域，且内容不同，则是冲突
    
    # 获取修改的行号范围
    ranges_a = get_modified_ranges(original, changes_a)
    ranges_b = get_modified_ranges(original, changes_b)
    
    for start_a, end_a in ranges_a:
        for start_b, end_b in ranges_b:
            # 检查范围是否重叠
            if not (end_a < start_b or end_b < start_a):
                # 范围重叠，需要检查内容是否相同
                return True
    
    return False


def get_modified_ranges(original, changes):
    """
    获取修改的行号范围
    
    参数:
        original: 原始内容
        changes: 修改列表
    
    返回:
        [(start, end), ...] 范围列表
    """
    ranges = []
    if not changes:
        return ranges
    
    # 简化：假设changes是行号列表
    if isinstance(changes, list) and changes:
        if isinstance(changes[0], int):
            # 直接是行号列表
            current_start = changes[0]
            current_end = changes[0]
            for line_no in changes[1:]:
                if line_no == current_end + 1:
                    current_end = line_no
                else:
                    ranges.append((current_start, current_end))
                    current_start = line_no
                    current_end = line_no
            ranges.append((current_start, current_end))
    
    return ranges


def format_merge_result(result):
    """
    格式化合并结果
    
    参数:
        result: MergeResult对象
    
    返回:
        格式化的字符串
    """
    lines = []
    lines.append("=" * 60)
    lines.append("三路合并结果")
    lines.append("=" * 60)
    
    lines.append(f"\n合并状态: {result.status.value}")
    
    if result.status == MergeStatus.CONFLICT:
        lines.append(f"\n冲突数量: {len(result.conflicts)}")
        for i, conflict in enumerate(result.conflicts):
            lines.append(f"\n冲突 {i+1}:")
            lines.append(f"  位置: {conflict.get('position', '?')}")
            lines.append(f"  内容A: {conflict.get('content_a', '')}")
            lines.append(f"  内容B: {conflict.get('content_b', '')}")
    else:
        lines.append("\n合并后的内容:")
        for i, line in enumerate(result.content[:20]):
            lines.append(f"  {i+1}: {line}")
        if len(result.content) > 20:
            lines.append(f"  ... 共 {len(result.content)} 行")
    
    return '\n'.join(lines)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：简单合并，无冲突
    print("=" * 50)
    print("测试1: 简单三路合并")
    print("=" * 50)
    
    original = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5"
    ]
    branch_a = [
        "line 1",
        "line 2",
        "modified line 3",
        "line 4",
        "line 5"
    ]
    branch_b = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "extra line from b",
        "line 5"
    ]
    
    result = three_way_merge(original, branch_a, branch_b)
    print(f"合并状态: {result.status.value}")
    print("\n合并后的内容:")
    for i, line in enumerate(result.content):
        print(f"  {i+1}: {line}")
    
    # 测试用例2：不同位置修改
    print("\n" + "=" * 50)
    print("测试2: 不同位置修改")
    print("=" * 50)
    
    original = [
        "def func():",
        "    pass",
        "",
        "class MyClass:",
        "    pass"
    ]
    branch_a = [
        "def func():",
        "    return 1",
        "",
        "class MyClass:",
        "    pass"
    ]
    branch_b = [
        "def func():",
        "    pass",
        "",
        "class MyClass:",
        "    def method(self):",
        "        pass"
    ]
    
    result = three_way_merge(original, branch_a, branch_b)
    print(f"合并状态: {result.status.value}")
    print("\n合并后的内容:")
    for i, line in enumerate(result.content):
        print(f"  {i+1}: {line}")
    
    # 测试用例3：冲突检测
    print("\n" + "=" * 50)
    print("测试3: 冲突场景")
    print("=" * 50)
    
    original = [
        "line 1",
        "line 2",
        "line 3"
    ]
    branch_a = [
        "line 1",
        "content from a",
        "line 3"
    ]
    branch_b = [
        "line 1",
        "content from b",
        "line 3"
    ]
    
    result = three_way_merge(original, branch_a, branch_b)
    print(f"合并状态: {result.status.value}")
    print("\n合并后的内容:")
    for i, line in enumerate(result.content):
        print(f"  {i+1}: {line}")
    
    # 测试用例4：LCS合并结果验证
    print("\n" + "=" * 50)
    print("测试4: LCS合并算法")
    print("=" * 50)
    
    lines_a = ["a", "b", "c", "d", "e"]
    lines_b = ["a", "x", "c", "d", "y"]
    
    merged = lcs_merge(lines_a, lines_b)
    print(f"分支A: {lines_a}")
    print(f"分支B: {lines_b}")
    print(f"合并结果: {merged}")
