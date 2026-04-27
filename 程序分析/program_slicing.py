# -*- coding: utf-8 -*-

"""

算法实现：程序分析 / program_slicing



本文件实现 program_slicing 相关的算法功能。

"""



from typing import Dict, List, Set, Tuple, Optional

from collections import defaultdict, deque





class Statement:

    """

    语句类，表示程序中的一条语句

    """

    

    def __init__(self, stmt_id: int, text: str, block_id: int = 0):

        """

        初始化语句

        

        Args:

            stmt_id: 语句的唯一标识

            text: 语句的文本表示

            block_id: 所属基本块的ID

        """

        self.stmt_id = stmt_id  # 语句ID

        self.text = text        # 语句文本

        self.block_id = block_id  # 所在块ID

        self.uses: Set[str] = set()   # 使用的变量

        self.defines: Set[str] = set()  # 定义的变量

    

    def __repr__(self):

        return f"Stmt({self.stmt_id}: {self.text})"





class ProgramSlice:

    """

    程序切片器

    

    使用数据流分析（到达定义）实现后向程序切片。

    给定一个切片准则 (语句位置, 变量)，找出所有影响该变量的语句。

    """

    

    def __init__(self, statements: List[Statement]):

        """

        初始化程序切片器

        

        Args:

            statements: 程序语句列表

        """

        self.statements = statements  # 所有语句

        self.num_statements = len(statements)

        # 记录每条语句的语句编号（用于唯一标识）

        self.stmt_map: Dict[int, Statement] = {s.stmt_id: s for s in statements}

        # 前驱语句图：stmt_id -> [predecessor_stmt_ids]

        self.predecessors: Dict[int, List[int]] = defaultdict(list)

        # 后继语句图：stmt_id -> [successor_stmt_ids]

        self.successors: Dict[int, List[int]] = defaultdict(list)

        # 控制依赖关系

        self.control_dependencies: Dict[int, Set[int]] = defaultdict(set)

        # 记录每条语句之后可能跳转的目标（用于控制依赖）

        self.jump_targets: Dict[int, List[int]] = defaultdict(list)

        # 记录每条语句是否是跳转语句

        self.is_jump: Dict[int, bool] = {}

        # 构建程序图

        self._build_graph()

    

    def _build_graph(self):

        """构建语句之间的前驱/后继关系图"""

        for i, stmt in enumerate(self.statements):

            self.is_jump[stmt.stmt_id] = False

            text = stmt.text.strip()

            

            # 检测变量使用和定义

            self._analyze_statement(stmt)

            

            # 顺序前驱/后继

            if i > 0:

                prev_stmt = self.statements[i - 1]

                self.predecessors[stmt.stmt_id].append(prev_stmt.stmt_id)

                self.successors[prev_stmt.stmt_id].append(stmt.stmt_id)

            

            # 检测跳转语句

            if text.startswith('if ') or text.startswith('ifnot '):

                self.is_jump[stmt.stmt_id] = True

                # 解析跳转目标

                if 'goto ' in text:

                    parts = text.split('goto ')

                    if len(parts) > 1:

                        label = parts[1].strip()

                        # 找到目标标签对应的语句

                        for j, s in enumerate(self.statements):

                            if s.text.strip().startswith(label + ':'):

                                self.jump_targets[stmt.stmt_id].append(s.stmt_id)

                                self.control_dependencies[s.stmt_id].add(stmt.stmt_id)

                                break

            elif text.startswith('goto '):

                self.is_jump[stmt.stmt_id] = True

                label = text[5:].strip()

                for j, s in enumerate(self.statements):

                    if s.text.strip().startswith(label + ':'):

                        self.jump_targets[stmt.stmt_id].append(s.stmt_id)

                        self.control_dependencies[s.stmt_id].add(stmt.stmt_id)

                        break

    

    def _analyze_statement(self, stmt: Statement):

        """

        分析语句，提取使用的变量和定义的变量

        

        Args:

            stmt: 待分析的语句

        """

        text = stmt.text.strip()

        

        # 跳过标签行

        if text.endswith(':'):

            return

        

        # 跳过注释

        if text.startswith('#'):

            return

        

        # 分析赋值语句

        if '=' in text and not text.startswith('if'):

            parts = text.split('=', 1)

            lhs = parts[0].strip()

            rhs = parts[1].strip() if len(parts) > 1 else ""

            

            # 定义变量

            stmt.defines.add(lhs)

            

            # 分析右侧使用的变量

            for word in rhs.replace('+', ' ').replace('-', ' ').replace('*', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ').replace(',', ' ').split():

                word = word.strip()

                if word and word.isidentifier() and not word.isdigit():

                    stmt.uses.add(word)

        

        # 分析条件跳转的条件

        elif text.startswith('if ') or text.startswith('ifnot '):

            # 提取条件中的变量

            condition = text

            if 'goto ' in condition:

                condition = condition.split('goto ')[0]

            condition = condition.replace('if ', '').replace('ifnot ', '').replace('>', ' ').replace('<', ' ').replace('==', ' ').replace('>=', ' ').replace('<=', ' ').replace('!=', ' ')

            for word in condition.split():

                word = word.strip()

                if word and word.isidentifier() and not word.isdigit():

                    stmt.uses.add(word)

    

    def compute_backward_slice(self, criterion_stmt_id: int, criterion_var: str) -> Set[int]:

        """

        计算后向切片：找出所有影响指定语句中变量的语句

        

        Args:

            criterion_stmt_id: 切片准则中的语句ID

            criterion_var: 切片准则中的变量名

            

        Returns:

            构成切片的语句ID集合

        """

        # 初始化：目标语句标记

        slice_set: Set[int] = {criterion_stmt_id}

        worklist = deque([criterion_stmt_id])

        

        # 已处理的(语句ID, 变量名)对

        visited: Set[Tuple[int, str]] = {(criterion_stmt_id, criterion_var)}

        

        while worklist:

            current_stmt_id = worklist.popleft()

            current_stmt = self.stmt_map.get(current_stmt_id)

            if current_stmt is None:

                continue

            

            # 如果当前语句定义了我们要跟踪的变量，继续追溯

            # 我们需要找到这个定义的来源

            

            # 遍历前驱语句

            for pred_id in self.predecessors.get(current_stmt_id, []):

                pred_stmt = self.stmt_map.get(pred_id)

                if pred_stmt is None:

                    continue

                

                # 检查前驱是否定义了当前变量或使用了它

                if criterion_var in pred_stmt.defines:

                    pair = (pred_id, criterion_var)

                    if pair not in visited:

                        visited.add(pair)

                        slice_set.add(pred_id)

                        worklist.append(pred_id)

                

                # 如果前驱使用了当前变量，需要跟踪该变量的定义

                if criterion_var in pred_stmt.uses:

                    # 递归地追溯定义

                    self._trace_definitions(pred_id, criterion_var, slice_set, visited, worklist)

            

            # 处理控制依赖

            for ctrl_dep_id in self.control_dependencies.get(current_stmt_id, set()):

                if ctrl_dep_id not in slice_set:

                    ctrl_stmt = self.stmt_map.get(ctrl_dep_id)

                    if ctrl_stmt and criterion_var in ctrl_stmt.uses:

                        slice_set.add(ctrl_dep_id)

                        worklist.append(ctrl_dep_id)

        

        return slice_set

    

    def _trace_definitions(self, stmt_id: int, var: str, slice_set: Set[int], 

                          visited: Set[Tuple[int, str]], worklist: deque):

        """

        追溯变量的定义位置

        

        Args:

            stmt_id: 当前语句ID

            var: 要追踪的变量名

            slice_set: 切片集合

            visited: 已访问的(语句,变量)对

            worklist: 工作队列

        """

        current_stmt_id = stmt_id

        

        while True:

            current_stmt = self.stmt_map.get(current_stmt_id)

            if current_stmt is None:

                break

            

            # 向前查找最近定义该变量的语句

            found_def = False

            for pred_id in self.predecessors.get(current_stmt_id, []):

                pred_stmt = self.stmt_map.get(pred_id)

                if pred_stmt and var in pred_stmt.defines:

                    pair = (pred_id, var)

                    if pair not in visited:

                        visited.add(pair)

                        slice_set.add(pred_id)

                        worklist.append(pred_id)

                        found_def = True

                        break

            

            if not found_def:

                break

            

            # 继续向前追溯

            preds = self.predecessors.get(current_stmt_id, [])

            if not preds:

                break

            current_stmt_id = preds[0]  # 简化：取第一个前驱

    

    def compute_forward_slice(self, start_stmt_id: int, start_var: str) -> Set[int]:

        """

        计算前向切片：找出受指定语句中变量影响的所有语句

        

        Args:

            start_stmt_id: 起始语句ID

            start_var: 起始变量名

            

        Returns:

            构成切片的语句ID集合

        """

        slice_set: Set[int] = {start_stmt_id}

        worklist = deque([(start_stmt_id, start_var)])

        visited: Set[Tuple[int, str]] = {(start_stmt_id, start_var)}

        

        while worklist:

            current_stmt_id, current_var = worklist.popleft()

            current_stmt = self.stmt_map.get(current_stmt_id)

            if current_stmt is None:

                continue

            

            # 遍历后继语句

            for succ_id in self.successors.get(current_stmt_id, []):

                succ_stmt = self.stmt_map.get(succ_id)

                if succ_stmt is None:

                    continue

                

                # 如果后继使用了当前变量

                if current_var in succ_stmt.uses:

                    pair = (succ_id, current_var)

                    if pair not in visited:

                        visited.add(pair)

                        slice_set.add(succ_id)

                        worklist.append((succ_id, current_var))

                    

                    # 如果后继重新定义了该变量，停止跟踪

                    if current_var in succ_stmt.defines:

                        continue

                

                # 如果后继定义了当前变量，停止跟踪

                if current_var in succ_stmt.defines:

                    continue

                

                # 否则，继续跟踪

                for var_in_succ in succ_stmt.uses:

                    pair = (succ_id, var_in_succ)

                    if pair not in visited:

                        visited.add(pair)

                        worklist.append((succ_id, var_in_succ))

            

            # 处理跳转

            for target_id in self.jump_targets.get(current_stmt_id, []):

                target_stmt = self.stmt_map.get(target_id)

                if target_stmt and current_var in target_stmt.uses:

                    pair = (target_id, current_var)

                    if pair not in visited:

                        visited.add(pair)

                        slice_set.add(target_id)

                        worklist.append((target_id, current_var))

        

        return slice_set

    

    def display_slice(self, slice_set: Set[int], title: str = "Program Slice"):

        """

        显示切片结果

        

        Args:

            slice_set: 切片语句ID集合

            title: 标题

        """

        print("=" * 60)

        print(title)

        print("=" * 60)

        

        # 按块和语句顺序排序

        sorted_ids = sorted(slice_set, key=lambda sid: (

            self.stmt_map[sid].block_id if sid in self.stmt_map else 0,

            sid

        ))

        

        for stmt_id in sorted_ids:

            stmt = self.stmt_map.get(stmt_id)

            if stmt:

                print(f"  [{stmt.block_id}:{stmt.stmt_id}] {stmt.text}")





if __name__ == "__main__":

    # 创建示例程序：计算最大公约数（欧几里得算法）

    print("程序切片测试\n")

    

    program_statements = [

        Statement(0, "a = 48", block_id=0),

        Statement(1, "b = 18", block_id=0),

        Statement(2, "while b != 0:", block_id=1),

        Statement(3, "temp = b", block_id=2),

        Statement(4, "b = a % b", block_id=2),

        Statement(5, "a = temp", block_id=2),

        Statement(6, "return a", block_id=3),

    ]

    

    print("原程序:")

    for stmt in program_statements:

        print(f"  [{stmt.block_id}:{stmt.stmt_id}] {stmt.text}")

    print()

    

    # 创建切片器

    slicer = ProgramSlice(program_statements)

    

    # 后向切片：找出影响 "return a" 中变量a的所有语句

    print("后向切片: 影响 return a 中变量a 的所有语句")

    backward = slicer.compute_backward_slice(

        criterion_stmt_id=6,  # return a 语句

        criterion_var="a"

    )

    slicer.display_slice(backward, "后向切片结果 (影响a的值)")

    

    print()

    

    # 后向切片：找出影响 "b = a % b" 中变量b的所有语句

    print("后向切片: 影响 b = a % b 中变量b 的所有语句")

    backward2 = slicer.compute_backward_slice(

        criterion_stmt_id=4,  # b = a % b 语句

        criterion_var="b"

    )

    slicer.display_slice(backward2, "后向切片结果 (影响b的值)")

    

    print()

    

    # 前向切片：找出 "a = 48" 中变量a会影响的所有语句

    print("前向切片: a = 48 中的变量a会影响到哪些语句")

    forward = slicer.compute_forward_slice(

        start_stmt_id=0,  # a = 48 语句

        start_var="a"

    )

    slicer.display_slice(forward, "前向切片结果 (a的传播路径)")

    

    print("\n程序切片测试完成!")

