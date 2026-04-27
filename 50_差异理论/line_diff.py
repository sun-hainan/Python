# -*- coding: utf-8 -*-

"""

算法实现：差异理论 / line_diff



本文件实现 line_diff 相关的算法功能。

"""



import difflib





class LineDiffResult:

    """

    行级diff结果类

    """

    def __init__(self):

        self.added_lines = []     # 新增的行

        self.removed_lines = []   # 删除的行

        self.changed_lines = []   # 修改的行（包含旧值和新值）

        self.unchanged_lines = []  # 未改变的上下文行

    

    @property

    def total_changes(self):

        """总变更数"""

        return len(self.added_lines) + len(self.removed_lines) + len(self.changed_lines)





def compute_line_diff(original_lines, new_lines, context=3):

    """

    计算两个文本的行级差异

    

    参数:

        original_lines: 原始文件的行列表

        new_lines: 新文件的行列表

        context: 上下文行数

    

    返回:

        LineDiffResult对象

    """

    # 使用difflib进行比较

    matcher = difflib.SequenceMatcher(None, original_lines, new_lines)

    

    result = LineDiffResult()

    

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == 'equal':

            # 未修改的行

            result.unchanged_lines.extend(original_lines[i1:i2])

        elif tag == 'delete':

            # 删除的行

            for i in range(i1, i2):

                result.removed_lines.append(original_lines[i])

        elif tag == 'insert':

            # 新增的行

            for j in range(j1, j2):

                result.added_lines.append(new_lines[j])

        elif tag == 'replace':

            # 替换：先删除后添加

            for i in range(i1, i2):

                result.removed_lines.append(original_lines[i])

            for j in range(j1, j2):

                result.added_lines.append(new_lines[j])

    

    return result





def unified_line_diff(original_lines, new_lines, original_name="a.txt", new_name="b.txt", context=3):

    """

    生成统一diff格式（unified diff）

    

    参数:

        original_lines: 原始行列表

        new_lines: 新行列表

        original_name: 原始文件名

        new_name: 新文件名

        context: 上下文行数

    

    返回:

        统一diff格式字符串

    """

    matcher = difflib.SequenceMatcher(None, original_lines, new_lines)

    

    lines = []

    

    # 添加文件头

    lines.append(f"--- {original_name}")

    lines.append(f"+++ {new_name}")

    

    # 获取带上下文的分组差异

    for group in matcher.get_grouped_opcodes(context):

        # 计算hunk头

        i1, i2, j1, j2 = group

        

        # 行号从1开始

        original_start = i1 + 1

        original_count = i2 - i1

        new_start = j1 + 1

        new_count = j2 - j1

        

        lines.append(f"@@ -{original_start},{original_count} +{new_start},{new_count} @@")

        

        # 添加差异行

        for tag, i1, i2, j1, j2 in [group]:

            if tag == 'equal':

                for i in range(i1, i2):

                    lines.append(f" {original_lines[i]}")

            elif tag == 'delete':

                for i in range(i1, i2):

                    lines.append(f"-{original_lines[i]}")

            elif tag == 'insert':

                for j in range(j1, j2):

                    lines.append(f"+{new_lines[j]}")

            elif tag == 'replace':

                for i in range(i1, i2):

                    lines.append(f"-{original_lines[i]}")

                for j in range(j1, j2):

                    lines.append(f"+{new_lines[j]}")

    

    return '\n'.join(lines)





def side_by_side_diff(original_lines, new_lines, width=80):

    """

    生成并排diff格式

    

    参数:

        original_lines: 原始行列表

        new_lines: 新行列表

        width: 总显示宽度

    

    返回:

        并排diff字符串

    """

    half_width = (width - 3) // 2

    

    matcher = difflib.SequenceMatcher(None, original_lines, new_lines)

    

    lines = []

    

    # 头部

    lines.append("=" * width)

    lines.append(f"{'ORIGINAL':^{half_width}}|{'NEW':^{half_width}}")

    lines.append("-" * width)

    

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == 'equal':

            for i in range(i1, i2):

                orig = original_lines[i][:half_width].ljust(half_width)

                new = new_lines[j1 + (i - i1)][:half_width].ljust(half_width)

                lines.append(f"{orig}|{new}")

        elif tag == 'delete':

            for i in range(i1, i2):

                orig = original_lines[i][:half_width].ljust(half_width)

                new = ''.ljust(half_width)

                lines.append(f"{orig}|{new}")

        elif tag == 'insert':

            for j in range(j1, j2):

                orig = ''.ljust(half_width)

                new = new_lines[j][:half_width].ljust(half_width)

                lines.append(f"{orig}|{new}")

        elif tag == 'replace':

            max_lines = max(i2 - i1, j2 - j1)

            for k in range(max_lines):

                if k < i2 - i1:

                    orig = original_lines[i1 + k][:half_width].ljust(half_width)

                else:

                    orig = ''.ljust(half_width)

                

                if k < j2 - j1:

                    new = new_lines[j1 + k][:half_width].ljust(half_width)

                else:

                    new = ''.ljust(half_width)

                

                lines.append(f"{orig}|{new}")

    

    lines.append("=" * width)

    

    return '\n'.join(lines)





def context_diff(original_lines, new_lines, original_name="original.txt", new_name="new.txt", context=3):

    """

    生成上下文diff格式

    

    参数:

        original_lines: 原始行列表

        new_lines: 新行列表

        original_name: 原始文件名

        new_name: 新文件名

        context: 上下文行数

    

    返回:

        上下文diff字符串

    """

    matcher = difflib.SequenceMatcher(None, original_lines, new_lines)

    

    lines = []

    

    lines.append(f"*** {original_name}")

    lines.append(f"--- {new_name}")

    

    for group in matcher.get_grouped_opcodes(context):

        i1, i2, j1, j2 = group

        

        lines.append("***************")

        lines.append(f"*** {i1 + 1},{i2} ***")

        

        for tag, i1, i2, j1, j2 in [group]:

            if tag == 'equal':

                for i in range(i1, i2):

                    lines.append(f"  {original_lines[i]}")

            elif tag == 'delete':

                for i in range(i1, i2):

                    lines.append(f"- {original_lines[i]}")

            elif tag == 'replace':

                for i in range(i1, i2):

                    lines.append(f"- {original_lines[i]}")

        

        lines.append(f"--- {j1 + 1},{j2} ---")

        

        for tag, i1, i2, j1, j2 in [group]:

            if tag == 'equal':

                for j in range(j1, j2):

                    lines.append(f"  {new_lines[j]}")

            elif tag == 'insert':

                for j in range(j1, j2):

                    lines.append(f"+ {new_lines[j]}")

            elif tag == 'replace':

                for j in range(j1, j2):

                    lines.append(f"+ {new_lines[j]}")

    

    return '\n'.join(lines)





def format_diff_report(diff_result):

    """

    格式化diff报告

    

    参数:

        diff_result: LineDiffResult对象

    

    返回:

        格式化的报告字符串

    """

    lines = []

    lines.append("=" * 60)

    lines.append("行级Diff报告")

    lines.append("=" * 60)

    lines.append(f"新增行数: {len(diff_result.added_lines)}")

    lines.append(f"删除行数: {len(diff_result.removed_lines)}")

    lines.append(f"未改变行数: {len(diff_result.unchanged_lines)}")

    lines.append(f"总变更数: {diff_result.total_changes}")

    

    if diff_result.added_lines:

        lines.append("\n【新增的行】")

        for i, line in enumerate(diff_result.added_lines[:10]):

            lines.append(f"  + {line}")

        if len(diff_result.added_lines) > 10:

            lines.append(f"  ... 还有 {len(diff_result.added_lines) - 10} 行")

    

    if diff_result.removed_lines:

        lines.append("\n【删除的行】")

        for i, line in enumerate(diff_result.removed_lines[:10]):

            lines.append(f"  - {line}")

        if len(diff_result.removed_lines) > 10:

            lines.append(f"  ... 还有 {len(diff_result.removed_lines) - 10} 行")

    

    return '\n'.join(lines)





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：基本行diff

    print("=" * 50)

    print("测试1: 基本行级diff")

    print("=" * 50)

    

    original = [

        "line 1",

        "line 2",

        "line 3",

        "line 4",

        "line 5"

    ]

    new = [

        "line 1",

        "modified line 2",

        "line 3",

        "line 4",

        "new line 5",

        "new line 6"

    ]

    

    result = compute_line_diff(original, new)

    print(format_diff_report(result))

    

    # 测试用例2：统一diff格式

    print("\n" + "=" * 50)

    print("测试2: 统一diff格式")

    print("=" * 50)

    

    original = [

        "def hello():",

        "    print('world')",

        "    return 1"

    ]

    new = [

        "def hello():",

        "    print('hello world')",

        "    return 2"

    ]

    

    unified = unified_line_diff(original, new, "old.py", "new.py")

    print(unified)

    

    # 测试用例3：并排diff

    print("\n" + "=" * 50)

    print("测试3: 并排diff格式")

    print("=" * 50)

    

    original = [

        "Hello world",

        "This is line 2",

        "And line 3"

    ]

    new = [

        "Hello there",

        "This is line 2",

        "And line 4"

    ]

    

    side_by_side = side_by_side_diff(original, new, width=60)

    print(side_by_side)

    

    # 测试用例4：上下文diff

    print("\n" + "=" * 50)

    print("测试4: 上下文diff格式")

    print("=" * 50)

    

    original = [

        "a",

        "b",

        "c",

        "d",

        "e",

        "f",

        "g"

    ]

    new = [

        "a",

        "x",

        "c",

        "d",

        "e",

        "y",

        "g"

    ]

    

    context = context_diff(original, new, context=2)

    print(context)

    

    # 测试用例5：统计信息

    print("\n" + "=" * 50)

    print("测试5: 详细diff统计")

    print("=" * 50)

    

    result = compute_line_diff(original, new)

    print(f"新增: {len(result.added_lines)} 行")

    print(f"删除: {len(result.removed_lines)} 行")

    print(f"保持不变: {len(result.unchanged_lines)} 行")

