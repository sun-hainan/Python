# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / conflict_detection

本文件实现 conflict_detection 相关的算法功能。
"""

from enum import Enum
from typing import List, Tuple, Optional


class ConflictType(Enum):
    """
    冲突类型枚举
    """
    CONTENT = "content"       # 内容冲突
    STRUCTURAL = "structural"  # 结构冲突
    SEMANTIC = "semantic"    # 语义冲突


class ConflictRegion:
    """
    冲突区域类，表示一个冲突的具体信息
    """
    def __init__(self, start_line, end_line, conflict_type, 
                 original_content=None, content_a=None, content_b=None):
        self.start_line = start_line      # 冲突起始行
        self.end_line = end_line          # 冲突结束行
        self.conflict_type = conflict_type  # 冲突类型
        self.original_content = original_content  # 原始内容
        self.content_a = content_a        # 分支A的内容
        self.content_b = content_b        # 分支B的内容
        self.resolved = False              # 是否已解决
        self.resolution = None             # 解决后的内容


class ConflictDetector:
    """
    冲突检测器
    """
    
    def __init__(self):
        self.conflicts = []
    
    def detect_conflicts(self, original_lines, modified_a, modified_b):
        """
        检测两个修改相对于原始版本是否冲突
        
        参数:
            original_lines: 原始内容的行列表
            modified_a: 分支A修改后的行列表
            modified_b: 分支B修改后的行列表
        
        返回:
            冲突区域列表
        """
        conflicts = []
        
        # 找出两个分支相对于原始版本的修改范围
        changes_a = self.find_changes(original_lines, modified_a)
        changes_b = self.find_changes(original_lines, modified_b)
        
        # 检查修改区域是否有重叠
        for start_a, end_a, content_a in changes_a:
            for start_b, end_b, content_b in changes_b:
                if self.ranges_overlap(start_a, end_a, start_b, end_b):
                    # 发现重叠，需要检查内容是否相同
                    if not self.same_modification(content_a, content_b, 
                                                  original_lines, start_a, start_b):
                        # 存在真正的冲突
                        conflict = ConflictRegion(
                            start_line=min(start_a, start_b),
                            end_line=max(end_a, end_b),
                            conflict_type=ConflictType.CONTENT,
                            original_content=original_lines[start_a:start_a+1],
                            content_a=content_a,
                            content_b=content_b
                        )
                        conflicts.append(conflict)
        
        self.conflicts = conflicts
        return conflicts
    
    def find_changes(self, original, modified):
        """
        找出修改区域的起止位置
        
        参数:
            original: 原始行列表
            modified: 修改后行列表
        
        返回:
            [(start, end, content), ...] 修改区域列表
        """
        changes = []
        
        n = len(original)
        m = len(modified)
        
        # 使用动态规划找最长公共子序列
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if original[i - 1] == modified[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        
        # 回溯找差异区域
        i = n
        j = m
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and original[i - 1] == modified[j - 1]:
                i -= 1
                j -= 1
            elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
                j -= 1
            else:
                # 记录修改开始位置
                start = i - 1
                content_start = j - 1
                
                # 找到修改结束位置
                while i > 0 and (j == 0 or dp[i][j] <= dp[i - 1][j]):
                    i -= 1
                
                changes.append((start, i + 1, modified[content_start:j]))
                i -= 1
                j -= 1
        
        changes.reverse()
        return changes if changes else []
    
    def ranges_overlap(self, start_a, end_a, start_b, end_b):
        """
        检查两个范围是否重叠
        
        参数:
            start_a, end_a: 第一个范围的起止
            start_b, end_b: 第二个范围的起止
        
        返回:
            是否重叠
        """
        return not (end_a <= start_b or end_b <= start_a)
    
    def same_modification(self, content_a, content_b, original, offset_a, offset_b):
        """
        检查两个修改是否相同
        
        参数:
            content_a: 分支A的修改内容
            content_b: 分支B的修改内容
            original: 原始内容
            offset_a, offset_b: 各自的偏移
        
        返回:
            是否相同
        """
        # 如果内容完全相同，则不冲突
        return content_a == content_b


class ConflictResolver:
    """
    冲突解决器
    """
    
    def __init__(self):
        self.strategy = "manual"
    
    def set_strategy(self, strategy):
        """
        设置解决策略
        
        参数:
            strategy: "manual", "ours", "theirs", "both"
        """
        self.strategy = strategy
    
    def resolve(self, conflict):
        """
        解决一个冲突
        
        参数:
            conflict: ConflictRegion对象
        
        返回:
            解决后的内容
        """
        if conflict.resolved:
            return conflict.resolution
        
        if self.strategy == "ours":
            # 采用分支A的版本
            conflict.resolution = conflict.content_a
        elif self.strategy == "theirs":
            # 采用分支B的版本
            conflict.resolution = conflict.content_b
        elif self.strategy == "both":
            # 保留两个版本
            conflict.resolution = conflict.content_a + ["======="] + conflict.content_b
        else:
            # 手动解决，返回None表示需要人工介入
            return None
        
        conflict.resolved = True
        return conflict.resolution
    
    def auto_resolve(self, conflict):
        """
        自动解决冲突（如果可能）
        
        参数:
            conflict: ConflictRegion对象
        
        返回:
            是否成功自动解决
        """
        # 简单策略：如果一个是空的，采用另一个
        if not conflict.content_a or not conflict.content_b:
            conflict.resolution = conflict.content_a or conflict.content_b
            conflict.resolved = True
            return True
        
        # 如果内容完全相同，自动解决
        if conflict.content_a == conflict.content_b:
            conflict.resolution = conflict.content_a
            conflict.resolved = True
            return True
        
        return False


def generate_conflict_markers(original, modified_a, modified_b, conflicts):
    """
    生成带有冲突标记的内容
    
    参数:
        original: 原始内容行列表
        modified_a: 分支A的修改
        modified_b: 分支B的修改
        conflicts: 冲突列表
    
    返回:
        带冲突标记的字符串
    """
    result = []
    conflict_index = 0
    
    # 按行号排序冲突区域
    sorted_conflicts = sorted(conflicts, key=lambda c: c.start_line)
    
    prev_end = 0
    
    for conflict in sorted_conflicts:
        # 添加冲突之前的行
        result.extend(original[prev_end:conflict.start_line])
        
        # 添加冲突标记 <<<<<<<
        result.append("<<<<<<< HEAD (branch A)")
        result.extend(conflict.content_a)
        
        # 添加分隔标记
        result.append("=======")
        result.extend(conflict.content_b)
        
        # 添加冲突结束标记 >>>>>>>
        result.append(">>>>>>> branch B")
        
        prev_end = conflict.end_line
    
    # 添加冲突区域之后的行
    result.extend(original[prev_end:])
    
    return '\n'.join(result)


def parse_conflict_markers(content):
    """
    解析冲突标记内容
    
    参数:
        content: 带冲突标记的字符串
    
    返回:
        (unresolved_conflicts, resolved_content)
    """
    lines = content.split('\n')
    result = []
    conflicts = []
    current_conflict = None
    in_conflict = False
    branch = None
    
    for line in lines:
        if line.startswith("<<<<<<<"):
            in_conflict = True
            current_conflict = {
                'content_a': [],
                'content_b': []
            }
        elif line.startswith("=======") and in_conflict:
            branch = 'b'
        elif line.startswith(">>>>>>>"):
            # 冲突结束
            if current_conflict:
                conflicts.append(current_conflict)
            current_conflict = None
            in_conflict = False
            branch = None
        elif in_conflict:
            if branch == 'b':
                current_conflict['content_b'].append(line)
            else:
                current_conflict['content_a'].append(line)
        else:
            result.append(line)
    
    return conflicts, '\n'.join(result)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：检测内容冲突
    print("=" * 50)
    print("测试1: 冲突检测")
    print("=" * 50)
    
    original = [
        "line 1",
        "line 2",
        "line 3",
        "line 4"
    ]
    modified_a = [
        "line 1",
        "modified by a",
        "line 3",
        "line 4"
    ]
    modified_b = [
        "line 1",
        "modified by b",
        "line 3",
        "line 4"
    ]
    
    detector = ConflictDetector()
    conflicts = detector.detect_conflicts(original, modified_a, modified_b)
    
    print(f"检测到 {len(conflicts)} 个冲突")
    for i, c in enumerate(conflicts):
        print(f"\n冲突 {i+1}:")
        print(f"  位置: 行 {c.start_line+1} - {c.end_line}")
        print(f"  类型: {c.conflict_type.value}")
        print(f"  分支A: {c.content_a}")
        print(f"  分支B: {c.content_b}")
    
    # 测试用例2：无冲突情况
    print("\n" + "=" * 50)
    print("测试2: 无冲突检测")
    print("=" * 50)
    
    original = [
        "line 1",
        "line 2",
        "line 3"
    ]
    modified_a = [
        "line 1",
        "new content a",
        "line 3"
    ]
    modified_b = [
        "line 1",
        "line 2",
        "new content b",
        "line 3"
    ]
    
    conflicts = detector.detect_conflicts(original, modified_a, modified_b)
    print(f"检测到 {len(conflicts)} 个冲突")
    
    # 测试用例3：生成冲突标记
    print("\n" + "=" * 50)
    print("测试3: 生成冲突标记")
    print("=" * 50)
    
    original = [
        "line 1",
        "line 2",
        "line 3",
        "line 4"
    ]
    modified_a = [
        "line 1",
        "modified a",
        "line 3",
        "line 4"
    ]
    modified_b = [
        "line 1",
        "modified b",
        "line 3",
        "line 4"
    ]
    
    conflicts = detector.detect_conflicts(original, modified_a, modified_b)
    marked_content = generate_conflict_markers(original, modified_a, modified_b, conflicts)
    
    print("带冲突标记的内容:")
    print(marked_content)
    
    # 测试用例4：解析冲突标记
    print("\n" + "=" * 50)
    print("测试4: 解析冲突标记")
    print("=" * 50)
    
    content_with_markers = """line 1
<<<<<<< HEAD (branch A)
content from a
=======
content from b
>>>>>>> branch B
line 4"""
    
    conflicts, resolved = parse_conflict_markers(content_with_markers)
    print(f"解析出 {len(conflicts)} 个冲突")
    print(f"\n已解决的内容:\n{resolved}")
    
    # 测试用例5：自动解决
    print("\n" + "=" * 50)
    print("测试5: 冲突自动解决")
    print("=" * 50)
    
    resolver = ConflictResolver()
    
    # 测试采用我们的版本
    resolver.set_strategy("ours")
    conflict = ConflictRegion(1, 2, ConflictType.CONTENT, 
                               content_a=["our version"], 
                               content_b=["their version"])
    resolved = resolver.resolve(conflict)
    print(f"采用 ours: {resolved}")
    
    # 测试采用他们的版本
    resolver.set_strategy("theirs")
    conflict.resolved = False
    resolved = resolver.resolve(conflict)
    print(f"采用 theirs: {resolved}")
