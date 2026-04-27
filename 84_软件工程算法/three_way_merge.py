# -*- coding: utf-8 -*-

"""

算法实现：软件工程算法 / three_way_merge



本文件实现 three_way_merge 相关的算法功能。

"""



from typing import List, Tuple, Optional, Callable





class ConflictError(Exception):

    """合并冲突异常"""



    def __init__(self, line_no: int, base: str, ours: str, theirs: str):

        self.line_no = line_no

        self.base = base

        self.ours = ours

        self.theirs = theirs

        super().__init__(

            f"冲突 @ 第 {line_no} 行: base='{base}', ours='{ours}', theirs='{theirs}'"

        )





def _compute_diff(base: List[str], target: List[str]) -> List[Tuple[int, Optional[str], Optional[str]]]:

    """

    计算 base -> target 的差异（简化版 LCS）



    Returns:

        List of (base_index, target_line_or_None)

        - base_index: base 中的行号（0-indexed）

        - target_line: 若该行在 target 中存在则为该行，否则为 None（表示删除）

    """

    # 简化的 LCS：逐行比较

    diff: List[Tuple[int, Optional[str], Optional[str]]] = []

    target_remaining = target[:]



    i = 0

    while i < len(base):

        b_line = base[i]

        if b_line in target_remaining:

            # 该行在 target 中存在（匹配），记录映射

            diff.append((i, b_line, b_line))

            target_remaining.remove(b_line)

        else:

            # 该行在 base 中被删除

            diff.append((i, b_line, None))

        i += 1



    # 剩余的 target 行是新增的

    return diff





def three_way_merge(

    base: List[str],

    ours: List[str],

    theirs: List[str],

    conflict_handler: Optional[Callable[[int, str, str], str]] = None,

    raise_on_conflict: bool = False,

) -> Tuple[List[str], List[dict]]:

    """

    三路合并主函数



    Args:

        base:    共同祖先版本

        ours:    我们这边的修改版本

        theirs:  对方（或其他分支）的修改版本

        conflict_handler: 冲突处理回调函数，接受 (line_no, ours_line, theirs_line)

        raise_on_conflict: 若为 True，检测到冲突时抛出 ConflictError



    Returns:

        (merged_lines, conflict_regions)

        - merged_lines: 合并后的文件内容（行列表）

        - conflict_regions: 冲突区域列表，每项为 {line_no, base, ours, theirs}

    """

    # 预计算 base->ours 和 base->theirs 的 diff

    diff_ours = _compute_diff(base, ours)

    diff_theirs = _compute_diff(base, theirs)



    merged: List[str] = []

    conflict_regions: List[dict] = []

    conflicts_present = False



    max_len = max(len(diff_ours), len(diff_theirs))

    i = 0



    while i < max_len:

        ours_line: Optional[str] = None

        theirs_line: Optional[str] = None

        base_line: Optional[str] = None



        # 获取 ours 的当前行

        if i < len(diff_ours):

            _, base_ours, ours_line = diff_ours[i]

            base_line = base_ours

        else:

            base_ours = None



        # 获取 theirs 的当前行

        if i < len(diff_theirs):

            _, base_theirs, theirs_line = diff_theirs[i]

            base_line = base_line or base_theirs

        else:

            base_theirs = None



        # ---- 判定合并策略 ----

        if ours_line is None and theirs_line is None:

            # 两边都删除了该行：直接删除（merged 不加入）

            pass



        elif ours_line is None:

            # ours 删除了，theirs 保留（或修改）

            if theirs_line != base_line:

                # theirs 修改了，ours 删除了 -> 冲突

                if raise_on_conflict:

                    raise ConflictError(i + 1, base_line or "", ours_line or "", theirs_line)

                conflicts_present = True

                conflict_regions.append({"line_no": i + 1, "base": base_line, "ours": ours_line, "theirs": theirs_line})

                merged.append(f"<<<<<<< OURS (deleted in ours)"])

                merged.append(f"||||||| BASE: {base_line}"])

                merged.append(f"======="])

                merged.append(f">>>>>>> THEIRS: {theirs_line}"])

            else:

                merged.append(theirs_line)



        elif theirs_line is None:

            # theirs 删除了，ours 保留（或修改）

            if raise_on_conflict:

                raise ConflictError(i + 1, base_line or "", ours_line, theirs_line or "")

            conflicts_present = True

            conflict_regions.append({"line_no": i + 1, "base": base_line, "ours": ours_line, "theirs": theirs_line})

            merged.append(f"<<<<<<< OURS: {ours_line}"])

            merged.append(f"||||||| BASE: {base_line}"])

            merged.append(f"======="])

            merged.append(f">>>>>>> THEIRS (deleted in theirs)"])



        elif ours_line == theirs_line:

            # 两边修改相同，自动采用

            merged.append(ours_line)



        elif ours_line == base_line:

            # ours 未变，theirs 修改了 -> 采用 theirs

            merged.append(theirs_line)



        elif theirs_line == base_line:

            # theirs 未变，ours 修改了 -> 采用 ours

            merged.append(ours_line)



        else:

            # 两边都修改且内容不同 -> 冲突

            if raise_on_conflict:

                raise ConflictError(i + 1, base_line or "", ours_line, theirs_line)

            conflicts_present = True

            conflict_regions.append({"line_no": i + 1, "base": base_line, "ours": ours_line, "theirs": theirs_line})

            if conflict_handler:

                resolved = conflict_handler(i + 1, ours_line, theirs_line)

                merged.append(resolved)

            else:

                merged.append(f"<<<<<<< OURS: {ours_line}"])

                merged.append(f"||||||| BASE: {base_line}"])

                merged.append(f"======="])

                merged.append(f">>>>>>> THEIRS: {theirs_line}"])



        i += 1



    return merged, conflict_regions





if __name__ == "__main__":

    print("=" * 50)

    print("三路合并（Three-Way Merge）- 单元测试")

    print("=" * 50)



    # 示例场景

    base_lines = [

        "function add(a, b) {",

        "    return a + b;",

        "}",

        "",

        "function sub(a, b) {",

        "    return a - b;",

        "}",

    ]



    ours_lines = [

        "function add(a, b, c = 0) {",

        "    return a + b + c;",

        "}",

        "",

        "// 新增：abs 函数",

        "function abs(x) {",

        "    return x >= 0 ? x : -x;",

        "}",

        "",

        "function sub(a, b) {",

        "    return a - b;",

        "}",

    ]



    theirs_lines = [

        "function add(a, b) {",

        "    return a + b;",

        "}",

        "",

        "// 新增：mul 函数",

        "function mul(a, b) {",

        "    return a * b;",

        "}",

        "",

        "function sub(a, b) {",

        "    return a - b;",

        "}",

        "",

        "// 新增：div 函数",

        "function div(a, b) {",

        "    return a / b;",

        "}",

    ]



    print("\n共同祖先 (base):")

    for i, line in enumerate(base_lines):

        print(f"  {i + 1}: {line}")



    print("\nOurs 修改:")

    for i, line in enumerate(ours_lines):

        print(f"  {i + 1}: {line}")



    print("\nTheirs 修改:")

    for i, line in enumerate(theirs_lines):

        print(f"  {i + 1}: {line}")



    merged, conflicts = three_way_merge(base_lines, ours_lines, theirs_lines)



    print("\n合并结果:")

    for i, line in enumerate(merged):

        print(f"  {i + 1}: {line}")



    print(f"\n冲突数量: {len(conflicts)}")

    if conflicts:

        print("冲突详情:")

        for c in conflicts:

            print(f"  第 {c['line_no']} 行: base='{c['base']}', ours='{c['ours']}', theirs='{c['theirs']}'")



    print(f"\n复杂度: O(N)，N = max(len(base), len(ours), len(theirs))")

    print("算法完成。")

