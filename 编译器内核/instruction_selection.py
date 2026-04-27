# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / instruction_selection



本文件实现 instruction_selection 相关的算法功能。

"""



from typing import List, Dict, Optional, Tuple, Set

from enum import Enum

from dataclasses import dataclass, field

import re





# =============================================================================

# 指令和模式定义

# =============================================================================



@dataclass

class Instruction:

    """机器指令"""

    mnemonic: str  # 助记符，如 "ADD", "LOAD", "STORE"

    operands: List[str]  # 操作数列表

    result: Optional[str] = None  # 结果寄存器（如果有）



    def __repr__(self):

        if self.result:

            return f"{self.result} = {self.mnemonic} {', '.join(self.operands)}"

        return f"{self.mnemonic} {', '.join(self.operands)}"





@dataclass

class Pattern:

    """指令模式：定义一个 IR 模式如何映射到机器指令"""

    name: str  # 模式名称

    tree_pattern: str  # 树模式表达式（如 "ADD(REG, CONST)"）

    instruction: str  # 生成的指令助记符

    cost: int = 1  # 成本/周期数



    def matches(self, node: 'IRNode') -> bool:

        """检查 IR 节点是否匹配此模式"""

        return node.op == self.tree_pattern.split('(')[0]



    def __repr__(self):

        return f"Pattern({self.name}: {self.tree_pattern} -> {self.instruction}, cost={self.cost})"





# =============================================================================

# IR 节点定义

# =============================================================================



class IRNodeType(Enum):

    """IR 节点类型"""

    CONST = "CONST"  # 常量

    REG = "REG"  # 寄存器

    MEM = "MEM"  # 内存引用

    ADD = "ADD"  # 加法

    SUB = "SUB"  # 减法

    MUL = "MUL"  # 乘法

    DIV = "DIV"  # 除法

    LOAD = "LOAD"  # 加载

    STORE = "STORE"  # 存储

    AND = "AND"  # 逻辑与

    OR = "OR"  # 逻辑或

    NOT = "NOT"  # 逻辑非





@dataclass

class IRNode:

    """

    中间表示（IR）节点



    表示一棵表达式树，如：

        ADD(REG(x), MUL(REG(y), CONST(2)))

    表示: x + y * 2

    """

    op: str  # 操作类型

    children: List['IRNode'] = field(default_factory=list)  # 子节点

    value: Optional[str] = None  # 常量值或寄存器名

    name: str = ""  # 节点名称（用于调试）



    def to_tree_string(self) -> str:

        """将 IR 树转换为字符串表示"""

        if self.children:

            child_strs = [c.to_tree_string() for c in self.children]

            return f"{self.op}({', '.join(child_strs)})"

        else:

            return f"{self.op}({self.value})" if self.value else self.op



    def get_leaves(self) -> List['IRNode']:

        """获取所有叶子节点"""

        if not self.children:

            return [self]

        leaves = []

        for child in self.children:

            leaves.extend(child.get_leaves())

        return leaves





# =============================================================================

# 树模式匹配

# =============================================================================



class PatternMatcher:

    """

    树模式匹配器



    将 IR 树与预定义的指令模式进行匹配，

    生成最优的指令序列（最小成本）

    """



    def __init__(self):

        self.patterns: List[Pattern] = []  # 可用模式列表

        self.memo: Dict[str, List[Tuple[Pattern, IRNode]]] = {}  # 记忆化缓存



    def add_pattern(self, pattern: Pattern):

        """添加一个指令模式"""

        self.patterns.append(pattern)



    def match_node(self, node: IRNode) -> List[Tuple[Pattern, IRNode, int]]:

        """

        匹配一个 IR 节点，返回所有可能的 (模式, 变换后节点, 成本) 列表



        参数:

            node: 要匹配的 IR 节点



        返回:

            匹配结果列表

        """

        results = []



        for pattern in self.patterns:

            if pattern.matches(node):

                # 递归匹配子节点

                if node.children:

                    child_results = []

                    all_match = True

                    for child in node.children:

                        child_matches = self.match_node(child)

                        if not child_matches:

                            all_match = False

                            break

                        # 选择成本最低的子节点匹配

                        child_results.append(min(child_matches, key=lambda x: x[2]))

                    if all_match:

                        total_cost = pattern.cost + sum(c[2] for c in child_results)

                        results.append((pattern, node, total_cost))

                else:

                    # 叶子节点直接匹配

                    results.append((pattern, node, pattern.cost))



        return results



    def select_instructions(self, node: IRNode) -> List[Instruction]:

        """

        为 IR 树选择最优指令序列



        使用自底向上的动态规划选择成本最低的模式



        参数:

            node: IR 根节点



        返回:

            指令序列

        """

        instructions = []

        self._select_instructions_recursive(node, instructions)

        return instructions



    def _select_instructions_recursive(self, node: IRNode, instructions: List[Instruction]):

        """递归选择指令"""

        if not node.children:

            # 叶子节点，生成加载指令

            if node.op == "CONST":

                instructions.append(Instruction("LOADI", [node.value], f"r{len(instructions)}"))

            elif node.op == "REG":

                instructions.append(Instruction("MOV", [node.value], f"r{len(instructions)}"))

            return



        # 递归处理子节点

        for child in node.children:

            self._select_instructions_recursive(child, instructions)



        # 尝试匹配模式

        matches = self.match_node(node)

        if matches:

            best = min(matches, key=lambda x: x[2])

            pattern = best[0]



            # 生成指令

            operands = []

            # 计算子节点的输出寄存器

            reg_count = len([i for i in instructions if i.result and i.result.startswith('r')])

            for i, child in enumerate(node.children):

                operands.append(f"r{reg_count - len(node.children) + i}")



            result_reg = f"r{reg_count}"

            instructions.append(Instruction(pattern.instruction, operands, result_reg))

        else:

            # 没有匹配的模式，递归展开

            for child in node.children:

                self._select_instructions_recursive(child, instructions)





# =============================================================================

# DAG 生成

# =============================================================================



@dataclass

class DAGNode:

    """DAG（有向无环图）节点"""

    id: int  # 节点唯一ID

    op: str  # 操作类型

    value: Optional[str] = None  # 常量值或寄存器名

    parents: List[int] = field(default_factory=list)  # 父节点ID列表

    children: List[int] = field(default_factory=list)  # 子节点ID列表



    def __hash__(self):

        return self.id





class DAGGenerator:

    """

    DAG 生成器



    从 IR 树生成 DAG，共享公共子表达式，

    减少冗余计算

    """



    def __init__(self):

        self.nodes: Dict[int, DAGNode] = {}  # 节点ID -> DAG节点

        self.next_id: int = 0  # 下一个可用节点ID

        self.expr_to_node: Dict[str, int] = {}  # 表达式 -> 节点ID（用于去重）



    def build_from_tree(self, node: IRNode) -> int:

        """

        从 IR 树构建 DAG



        参数:

            node: IR 根节点



        返回:

            DAG 根节点ID

        """

        if not node.children:

            # 叶子节点

            return self._create_or_find_node(node.op, node.value)



        # 递归构建子节点

        child_ids = []

        for child in node.children:

            child_id = self.build_from_tree(child)

            child_ids.append(child_id)



        # 创建当前节点的 DAG 表示

        # 使用操作和子节点创建唯一键

        if child_ids:

            key = f"{node.op}({','.join(map(str, child_ids))})"

        else:

            key = f"{node.op}({node.value})"



        return self._create_or_find_node(node.op, None, child_ids, key)



    def _create_or_find_node(self, op: str, value: Optional[str],

                            child_ids: Optional[List[int]] = None,

                            expr_key: Optional[str] = None) -> int:

        """

        创建新节点或复用已有节点



        参数:

            op: 操作类型

            value: 值（叶子节点）

            child_ids: 子节点ID列表

            expr_key: 表达式键（用于去重）



        返回:

            节点ID

        """

        # 尝试复用已有节点（DAG 的核心优化）

        if expr_key and expr_key in self.expr_to_node:

            return self.expr_to_node[expr_key]



        # 创建新节点

        node_id = self.next_id

        self.next_id += 1



        new_node = DAGNode(id=node_id, op=op, value=value)

        if child_ids:

            new_node.children = child_ids

            for child_id in child_ids:

                self.nodes[child_id].parents.append(node_id)



        self.nodes[node_id] = new_node



        if expr_key:

            self.expr_to_node[expr_key] = node_id



        return node_id



    def find_common_subexpressions(self) -> List[Tuple[int, int]]:

        """

        查找 DAG 中的公共子表达式



        返回:

            (节点ID, 公共节点ID) 对列表

        """

        common_subs = []

        seen: Dict[str, int] = {}



        for node_id, node in self.nodes.items():

            key = f"{node.op}({','.join(map(str, node.children))})"

            if key in seen:

                common_subs.append((node_id, seen[key]))

            else:

                seen[key] = node_id



        return common_subs



    def emit_instructions(self) -> List[Instruction]:

        """

        从 DAG 发射指令序列



        按拓扑顺序处理节点，生成指令

        """

        # 计算入度

        in_degree: Dict[int, int] = {nid: len(self.nodes[nid].parents) for nid in self.nodes}

        instructions = []



        # 使用拓扑排序发射指令

        ready = [nid for nid, deg in in_degree.items() if deg == 0]

        reg_map: Dict[int, str] = {}  # DAG节点ID -> 寄存器

        reg_counter = 0



        while ready:

            node_id = ready.pop(0)

            node = self.nodes[node_id]



            # 分配寄存器

            result_reg = f"r{reg_counter}"

            reg_map[node_id] = result_reg

            reg_counter += 1



            # 生成指令

            if node.op == "CONST" and node.value:

                instructions.append(Instruction("LOADI", [node.value], result_reg))

            elif node.op == "REG" and node.value:

                instructions.append(Instruction("MOV", [node.value], result_reg))

            elif node.children:

                child_regs = [reg_map.get(cid, f"r{reg_counter - 1}") for cid in node.children]

                instr_map = {

                    "ADD": "ADD",

                    "SUB": "SUB",

                    "MUL": "MUL",

                    "DIV": "DIV",

                }

                instr = instr_map.get(node.op, node.op)

                instructions.append(Instruction(instr, child_regs, result_reg))



            # 更新子节点的入度

            for child_id in node.children:

                in_degree[child_id] -= 1

                if in_degree[child_id] == 0:

                    ready.append(child_id)



        return instructions





# =============================================================================

# 测试代码

# =============================================================================



if __name__ == "__main__":

    print("=" * 60)

    print("指令选择测试")

    print("=" * 60)



    # 创建一些指令模式

    patterns = [

        Pattern("add_reg_const", "ADD(REG, CONST)", "ADDI", 1),

        Pattern("add_reg_reg", "ADD(REG, REG)", "ADD", 1),

        Pattern("mul_reg_const", "MUL(REG, CONST)", "MULI", 2),

        Pattern("mul_reg_reg", "MUL(REG, REG)", "MUL", 2),

        Pattern("load", "LOAD(MEM)", "LOAD", 1),

    ]



    # 构建测试 IR：x + y * 2

    # 表示为: ADD(REG(x), MUL(REG(y), CONST(2)))

    ir = IRNode("ADD", [

        IRNode("REG", value="x", name="x"),

        IRNode("MUL", [

            IRNode("REG", value="y", name="y"),

            IRNode("CONST", value="2", name="2")

        ], name="mul")

    ], name="add")



    print(f"\n【测试1：树模式匹配】")

    print(f"IR 树: {ir.to_tree_string()}")



    matcher = PatternMatcher()

    for p in patterns:

        matcher.add_pattern(p)



    matches = matcher.match_node(ir)

    print(f"匹配到的模式数量: {len(matches)}")

    for p, n, cost in matches:

        print(f"  - {p}")



    # 测试2：DAG 生成

    print(f"\n【测试2：DAG 生成】")



    # IR: (a + b) + (a + c)

    # 公共子表达式：a 被共享

    ir2 = IRNode("ADD", [

        IRNode("ADD", [

            IRNode("REG", value="a", name="a"),

            IRNode("REG", value="b", name="b")

        ], name="add1"),

        IRNode("ADD", [

            IRNode("REG", value="a", name="a2"),

            IRNode("REG", value="c", name="c")

        ], name="add2")

    ], name="result")



    print(f"IR 树: {ir2.to_tree_string()}")



    dag_gen = DAGGenerator()

    root_id = dag_gen.build_from_tree(ir2)

    print(f"DAG 根节点 ID: {root_id}")

    print(f"DAG 节点数: {len(dag_gen.nodes)}")



    common_subs = dag_gen.find_common_subexpressions()

    print(f"公共子表达式: {common_subs}")



    # 发射指令

    instrs = dag_gen.emit_instructions()

    print(f"\n生成的指令:")

    for i, instr in enumerate(instrs):

        print(f"  {i + 1}. {instr}")

