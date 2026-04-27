# -*- coding: utf-8 -*-

"""

算法实现：程序分析 / control_flow_graph



本文件实现 control_flow_graph 相关的算法功能。

"""



from typing import Dict, List, Set, Optional

from collections import defaultdict, deque





class BasicBlock:

    """

    基本块类，表示CFG中的一个节点

    

    基本块是满足以下条件的最大连续语句序列：

    1. 入口只有一个（第一条语句）

    2. 出口只有一个（最后一条语句）

    3. 块内语句按顺序执行，不会出现跳转目标或跳转语句

    """

    

    def __init__(self, block_id: int, statements: Optional[List[str]] = None):

        """

        初始化基本块

        

        Args:

            block_id: 基本块的唯一标识符

            statements: 块内包含的语句列表

        """

        self.block_id = block_id  # 基本块的唯一ID

        self.statements = statements if statements else []  # 块内的语句序列

        self.predecessors: List[int] = []  # 前驱基本块列表（入边）

        self.successors: List[int] = []   # 后继基本块列表（出边）

    

    def add_successor(self, successor_id: int):

        """

        添加后继基本块

        

        Args:

            successor_id: 后继基本块的ID

        """

        if successor_id not in self.successors:

            self.successors.append(successor_id)

    

    def add_predecessor(self, predecessor_id: int):

        """

        添加前驱基本块

        

        Args:

            predecessor_id: 前驱基本块的ID

        """

        if predecessor_id not in self.predecessors:

            self.predecessors.append(predecessor_id)

    

    def __repr__(self):

        """返回基本块的字符串表示"""

        stmt_preview = self.statements[:2] if self.statements else []

        return f"BasicBlock(id={self.block_id}, stmts={len(self.statements)})"





class ControlFlowGraph:

    """

    控制流图类

    

    控制流图是程序分析的核心数据结构，用于表示程序执行的可达性关系。

    """

    

    def __init__(self):

        """初始化空的控制流图"""

        self.blocks: Dict[int, BasicBlock] = {}  # block_id -> BasicBlock

        self.entry_block_id: Optional[int] = None  # 入口基本块ID

        self.exit_block_id: Optional[int] = None   # 出口基本块ID

    

    def add_block(self, block: BasicBlock):

        """

        向CFG添加一个基本块

        

        Args:

            block: 要添加的基本块对象

        """

        self.blocks[block.block_id] = block

        # 如果是第一个块，设置为入口块

        if self.entry_block_id is None:

            self.entry_block_id = block.block_id

    

    def add_edge(self, from_id: int, to_id: int):

        """

        在两个基本块之间添加控制流边

        

        Args:

            from_id: 起始基本块ID

            to_id: 目标基本块ID

        """

        if from_id in self.blocks and to_id in self.blocks:

            self.blocks[from_id].add_successor(to_id)

            self.blocks[to_id].add_predecessor(from_id)

    

    def get_entry_block(self) -> Optional[BasicBlock]:

        """

        获取入口基本块

        

        Returns:

            入口基本块，如果不存在则返回None

        """

        if self.entry_block_id is not None:

            return self.blocks.get(self.entry_block_id)

        return None

    

    def get_exit_block(self) -> Optional[BasicBlock]:

        """

        获取出口基本块

        

        Returns:

            出口基本块，如果不存在则返回None

        """

        if self.exit_block_id is not None:

            return self.blocks.get(self.exit_block_id)

        return None

    

    def get_predecessors(self, block_id: int) -> List[BasicBlock]:

        """

        获取指定基本块的所有前驱块

        

        Args:

            block_id: 基本块ID

            

        Returns:

            前驱基本块列表

        """

        if block_id not in self.blocks:

            return []

        pred_ids = self.blocks[block_id].predecessors

        return [self.blocks[pid] for pid in pred_ids if pid in self.blocks]

    

    def get_successors(self, block_id: int) -> List[BasicBlock]:

        """

        获取指定基本块的所有后继块

        

        Args:

            block_id: 基本块ID

            

        Returns:

            后继基本块列表

        """

        if block_id not in self.blocks:

            return []

        succ_ids = self.blocks[block_id].successors

        return [self.blocks[sid] for sid in succ_ids if sid in self.blocks]

    

    def compute_reverse_post_order(self) -> List[int]:

        """

        计算反向后序遍历顺序

        

        用于CFG的拓扑排序，对于有向无环图（DAG）有效。

        

        Returns:

            反向后序遍历的块ID列表

        """

        visited: Set[int] = set()

        order: List[int] = []

        

        def dfs(current_id: int):

            """深度优先搜索遍历"""

            if current_id in visited:

                return

            visited.add(current_id)

            # 先访问所有后继

            for succ_id in self.blocks[current_id].successors:

                dfs(succ_id)

            # 后序位置记录

            order.append(current_id)

        

        if self.entry_block_id is not None:

            dfs(self.entry_block_id)

        

        return list(reversed(order))

    

    def display(self):

        """打印CFG的文本表示（用于调试）"""

        print("=" * 50)

        print("Control Flow Graph")

        print("=" * 50)

        for block_id in sorted(self.blocks.keys()):

            block = self.blocks[block_id]

            print(f"\n[Block {block_id}]")

            if block.statements:

                for stmt in block.statements:

                    print(f"  {stmt}")

            print(f"  -> successors: {block.successors}")

            print(f"  <- predecessors: {block.predecessors}")

        print("\n" + "=" * 50)





def build_cfg_from_statements(statements: List[str]) -> ControlFlowGraph:

    """

    从语句列表构建控制流图

    

    这是一个简化的CFG构建函数，假设语句有以下形式：

    - 普通语句：如 "x = 1"

    - 条件跳转：如 "if x goto L" 或 "ifnot x goto L"

    - 标签：如 "L:"

    - 无条件跳转：如 "goto L"

    

    Args:

        statements: 程序语句列表

        

    Returns:

        构建好的控制流图

    """

    cfg = ControlFlowGraph()

    

    # 第一步：识别标签和基本块边界

    labels: Dict[str, int] = {}  # label -> block_id

    block_boundaries: List[int] = [0]  # 块的起始语句索引

    

    for i, stmt in enumerate(statements):

        stmt_stripped = stmt.strip()

        # 检测标签定义

        if stmt_stripped.endswith(':') and not stmt_stripped.startswith('if'):

            label_name = stmt_stripped[:-1].strip()

            labels[label_name] = len(block_boundaries)

            block_boundaries.append(i + 1)

    

    # 第二步：创建基本块

    current_block_id = 0

    current_statements = []

    

    for i, stmt in enumerate(statements):

        stmt_stripped = stmt.strip()

        

        # 跳过单独的标签行（标签会合并到下一个块中）

        if stmt_stripped.endswith(':') and not stmt_stripped.startswith('if'):

            continue

        

        current_statements.append(stmt)

        

        # 检测是否是块结束（跳转语句）

        is_jump = False

        if stmt_stripped.startswith('goto '):

            is_jump = True

        elif stmt_stripped.startswith('if ') or stmt_stripped.startswith('ifnot '):

            is_jump = True

        elif stmt_stripped.startswith('return'):

            is_jump = True

        

        if is_jump:

            # 创建当前基本块

            block = BasicBlock(current_block_id, current_statements.copy())

            cfg.add_block(block)

            current_block_id += 1

            current_statements = []

    

    # 处理最后一个块

    if current_statements:

        block = BasicBlock(current_block_id, current_statements.copy())

        cfg.add_block(block)

    

    # 第三步：添加控制流边

    # 需要重新遍历来确定跳转目标

    jump_targets: Dict[int, List[int]] = defaultdict(list)  # block_id -> [target_block_ids]

    

    for block_id, block in cfg.blocks.items():

        for stmt in block.statements:

            stmt_stripped = stmt.strip()

            # 无条件跳转

            if stmt_stripped.startswith('goto '):

                label = stmt_stripped[5:].strip()

                # 找到目标标签对应的语句索引

                for idx, s in enumerate(statements):

                    if s.strip().startswith(label + ':'):

                        # 找到该语句所在的块

                        for bid, b in cfg.blocks.items():

                            if idx in [i for i, st in enumerate(statements) if st in b.statements]:

                                jump_targets[block_id].append(bid)

                                break

                        break

            # 条件跳转

            elif stmt_stripped.startswith('if ') or stmt_stripped.startswith('ifnot '):

                if 'goto ' in stmt_stripped:

                    parts = stmt_stripped.split('goto ')

                    if len(parts) > 1:

                        label = parts[1].strip()

                        for idx, s in enumerate(statements):

                            if s.strip().startswith(label + ':'):

                                for bid, b in cfg.blocks.items():

                                    if idx in [i for i, st in enumerate(statements) if st in b.statements]:

                                        jump_targets[block_id].append(bid)

                                        break

                                break

    

    # 添加边：顺序执行边和跳转边

    sorted_block_ids = sorted(cfg.blocks.keys())

    for i, block_id in enumerate(sorted_block_ids):

        # 顺序执行边（如果不是跳转语句的块）

        block = cfg.blocks[block_id]

        last_stmt = block.statements[-1].strip() if block.statements else ""

        

        has_jump = any(

            s.strip().startswith('goto') or 

            s.strip().startswith('if') or 

            s.strip().startswith('return')

            for s in block.statements

        )

        

        if not has_jump and i + 1 < len(sorted_block_ids):

            cfg.add_edge(block_id, sorted_block_ids[i + 1])

        

        # 显式跳转边

        if block_id in jump_targets:

            for target_id in jump_targets[block_id]:

                cfg.add_edge(block_id, target_id)

    

    # 设置出口块

    cfg.exit_block_id = sorted_block_ids[-1] if sorted_block_ids else None

    

    return cfg





if __name__ == "__main__":

    # 测试控制流图构建

    print("测试：构建简单程序的控制流图\n")

    

    # 示例程序：计算阶乘

    test_statements = [

        "n = 5",          # 输入值

        "result = 1",     # 初始化结果

        "i = 1",          # 初始化循环变量

        "loop:",          # 循环标签

        "if i > n goto exit",  # 循环条件判断

        "result = result * i", # 循环体

        "i = i + 1",      # 递增

        "goto loop",      # 返回循环开始

        "exit:",          # 退出标签

        "return result"   # 返回结果

    ]

    

    print("程序语句:")

    for i, stmt in enumerate(test_statements):

        print(f"  {i}: {stmt}")

    print()

    

    # 构建CFG

    cfg = build_cfg_from_statements(test_statements)

    

    # 显示CFG

    cfg.display()

    

    # 测试基本块操作

    print("\n反向后序遍历顺序:", cfg.compute_reverse_post_order())

    

    # 查找所有前驱和后继

    print("\n各基本块的可达性分析:")

    for block_id in sorted(cfg.blocks.keys()):

        preds = [p.block_id for p in cfg.get_predecessors(block_id)]

        succs = [s.block_id for s in cfg.get_successors(block_id)]

        print(f"  Block {block_id}: predecessors={preds}, successors={succs}")

    

    print("\n测试完成!")

