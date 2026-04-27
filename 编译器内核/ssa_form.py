# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / ssa_form



本文件实现 ssa_form 相关的算法功能。

"""



from typing import Dict, List, Set, Tuple, Optional

from dataclasses import dataclass, field



# ========== SSA基本定义 ==========



@dataclass

class SSAInstruction:

    """SSA指令"""

    opcode: str

    result: str                # SSA变量名（如 v1, v2）

    args: List[str] = field(default_factory=list)

    label: Optional[str] = None





@dataclass

class PhiFunction:

    """φ函数（Phi节点）"""

    result: str               # 结果SSA变量

    incoming: List[Tuple[str, str]] = field(default_factory=list)  # (value, block_label)





class SSARenamer:

    """

    SSA重命名器

    将普通代码转换为SSA形式

    """

    

    def __init__(self):

        self.version_map: Dict[str, List[int]] = {}  # 变量名 -> 版本计数器

        self.stack: Dict[str, List[int]] = {}  # 变量名 -> 版本栈

        self.ssa_vars: Dict[str, str] = {}    # 原变量 -> SSA变量

        self.instructions: List[SSAInstruction] = []

    

    def new_version(self, var: str) -> int:

        """为变量创建新版本"""

        if var not in self.version_map:

            self.version_map[var] = []

        

        version = len(self.version_map[var])

        self.version_map[var].append(version)

        

        return version

    

    def get_ssa_name(self, var: str) -> str:

        """获取变量的当前SSA名称"""

        if var not in self.stack or not self.stack[var]:

            return var  # 未被重命名的变量

        

        version = self.stack[var][-1]

        return f"{var}.{version}"

    

    def emit(self, opcode: str, result: str = None, 

             *args) -> str:

        """发射SSA指令"""

        result_var = None

        

        if result:

            version = self.new_version(result)

            result_var = f"{result}.{version}"

            

            if result not in self.stack:

                self.stack[result] = []

            self.stack[result].append(version)

        

        arg_names = [self.get_ssa_name(a) for a in args if a]

        

        instr = SSAInstruction(

            opcode=opcode,

            result=result_var,

            args=arg_names

        )

        self.instructions.append(instr)

        

        return result_var

    

    def rename(self, instructions: List[SSAInstruction]) -> List[SSAInstruction]:

        """重命名指令序列"""

        self.instructions = []

        

        for instr in instructions:

            result = self.emit(instr.opcode, instr.result, *instr.args)

        

        return self.instructions





class PhiInserter:

    """

    φ函数插入器

    在需要的地方插入φ函数

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.phi_functions: Dict[str, List[PhiFunction]] = {}  # block_label -> phi_functions

        self.dom_tree = {}  # 支配树

    

    def insert_phis(self, variables: Set[str]) -> Dict[str, List[PhiFunction]]:

        """

        为指定变量在所有需要的地方插入φ函数

        """

        # 找到变量活跃的块

        for var in variables:

            self._insert_var_phi(var)

        

        return self.phi_functions

    

    def _insert_var_phi(self, var: str):

        """为单个变量插入φ函数"""

        # 找出变量的定义点和使用点

        # 使用数据流分析确定需要插入φ的位置

        

        # 简化的φ插入

        for block in self.cfg.blocks:

            # 检查是否是变量活跃的块

            # 如果块有多个前驱，需要插入φ

            if len(block.predecessors) > 1:

                phi = PhiFunction(

                    result=f"{var}.phi",

                    incoming=[(f"{var}.{i}", pred.label) 

                              for i, pred in enumerate(block.predecessors)]

                )

                

                if block.label not in self.phi_functions:

                    self.phi_functions[block.label] = []

                self.phi_functions[block.label].append(phi)





class SSACFGBuilder:

    """

    SSA控制流图构建器

    构建带有φ函数的SSA形式CFG

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.renamer = SSARenamer()

        self.phi_inserter = PhiInserter(cfg)

    

    def build(self, instructions: List[SSAInstruction], 

              variables: Set[str]) -> Tuple[List, Dict]:

        """

        将普通指令转换为SSA形式

        """

        # 1. 计算支配关系

        self.cfg.compute_dominators()

        

        # 2. 构建支配树

        self._build_dom_tree()

        

        # 3. 确定变量的定义和活跃范围

        vpaths = self._compute_var_paths(variables)

        

        # 4. 在需要的位置插入φ函数

        phi_functions = self.phi_inserter.insert_phis(variables)

        

        # 5. 重命名变量

        renamed_instrs = self.renamer.rename(instructions)

        

        return renamed_instrs, phi_functions

    

    def _build_dom_tree(self):

        """构建支配树"""

        # DFS遍历

        visited = set()

        

        def dfs(block):

            if block.id in visited:

                return

            visited.add(block.id)

            

            # 添加子节点

            if block.dominator:

                if block not in block.dominator.dominated_nodes:

                    block.dominator.dominated_nodes.append(block)

            

            for child in block.dominated_nodes:

                dfs(child)

        

        if self.cfg.entry_block:

            dfs(self.cfg.entry_block)

    

    def _compute_var_paths(self, variables: Set[str]) -> Dict[str, List[Tuple]]:

        """

        计算变量的定义路径

        返回: var -> [(block, version), ...]

        """

        vpaths = {var: [] for var in variables}

        

        for block in self.cfg.blocks:

            for instr in block.instructions:

                if instr.result and instr.result in variables:

                    vpaths[instr.result].append((block.label, instr.result))

        

        return vpaths





class DominatorTree:

    """

    支配树

    用于高效计算φ函数插入位置

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.parent: Dict[str, str] = {}  # block -> immediate dominator

        self.children: Dict[str, List[str]] = {}

        self.depth: Dict[str, int] = {}

    

    def build(self):

        """构建支配树"""

        if not self.cfg.entry_block:

            return

        

        self._compute_imm_dominators()

        self._build_tree()

        self._compute_depth()

    

    def _compute_imm_dominators(self):

        """计算直接支配节点（使用Lengauer-Tarjan算法简化版）"""

        # 简化的算法：使用迭代

        self.parent = {}

        

        # 初始：除入口外，每个节点的潜在支配者是入口

        for block in self.cfg.blocks:

            if block != self.cfg.entry_block:

                self.parent[block.label] = self.cfg.entry_block.label

        

        # 迭代直到收敛

        changed = True

        while changed:

            changed = False

            

            for block in self.cfg.blocks:

                if block == self.cfg.entry_block:

                    continue

                

                # 找到所有前驱的共同支配者

                new_idom = None

                

                for pred in block.predecessors:

                    if pred.label in self.parent:

                        if new_idom is None:

                            new_idom = pred.label

                        else:

                            new_idom = self._intersect(pred.label, new_idom)

                

                if new_idom and self.parent.get(block.label) != new_idom:

                    self.parent[block.label] = new_idom

                    changed = True

    

    def _intersect(self, label1: str, label2: str) -> str:

        """找到两个节点路径的交点"""

        # 简化：沿支配树向上找

        path1 = []

        path2 = []

        

        block = self.cfg.get_block_by_label(label1)

        while block:

            path1.append(block.label)

            block = block.dominator

        

        block = self.cfg.get_block_by_label(label2)

        while block:

            path2.append(block.label)

            block = block.dominator

        

        for l in reversed(path1):

            if l in path2:

                return l

        

        return self.cfg.entry_block.label

    

    def _build_tree(self):

        """构建树结构"""

        for block in self.cfg.blocks:

            if block.label in self.parent:

                parent_label = self.parent[block.label]

                if parent_label not in self.children:

                    self.children[parent_label] = []

                self.children[parent_label].append(block.label)

    

    def _compute_depth(self):

        """计算节点深度"""

        def dfs_depth(label: str, d: int):

            self.depth[label] = d

            for child in self.children.get(label, []):

                dfs_depth(child, d + 1)

        

        if self.cfg.entry_block:

            dfs_depth(self.cfg.entry_block.label, 0)

    

    def get_dominance_frontier(self, block_label: str) -> List[str]:

        """

        获取节点的支配边界

        支配边界：那些被block支配但前驱不被block支配的节点

        """

        df = []

        

        for block in self.cfg.blocks:

            if block.label == block_label:

                continue

            

            for pred in block.predecessors:

                if pred.label == block_label:

                    # block是pred的前驱

                    if block.label not in df:

                        df.append(block.label)

        

        return df

    

    def get_all_dominators(self, block_label: str) -> Set[str]:

        """获取节点的所有支配节点"""

        doms = set()

        

        block = self.cfg.get_block_by_label(block_label)

        while block:

            doms.add(block.label)

            block = block.dominator

        

        return doms





class SSAEmitter:

    """SSA代码发射器"""

    

    def __init__(self):

        self.output: List[str] = []

    

    def emit_phi(self, phi: PhiFunction) -> str:

        """发射φ函数"""

        incoming_str = ", ".join(

            f"{val} from {block}" for val, block in phi.incoming

        )

        return f"{phi.result} = phi({incoming_str})"

    

    def emit_instruction(self, instr: SSAInstruction) -> str:

        """发射SSA指令"""

        if instr.args:

            return f"{instr.result} = {instr.opcode}({', '.join(instr.args)})"

        return f"{instr.result} = {instr.opcode}"





if __name__ == "__main__":

    print("=" * 60)

    print("SSA形式（静态单赋值）演示")

    print("=" * 60)

    

    # 模拟普通代码

    print("\n--- 普通代码 → SSA ---")

    

    original_code = [

        SSAInstruction("add", "a", ["x", "y"]),

        SSAInstruction("sub", "b", ["a", "1"]),

        SSAInstruction("add", "a", ["b", "z"]),  # 重新定义a

        SSAInstruction("mul", "c", ["a", "2"]),

    ]

    

    print("普通代码（三地址码）:")

    for instr in original_code:

        print(f"  {instr.result} = {instr.opcode}({instr.args})")

    

    # SSA重命名

    renamer = SSARenamer()

    renamed = renamer.rename(original_code)

    

    print("\nSSA形式（变量版本化）:")

    for instr in renamed:

        print(f"  {instr.result} = {instr.opcode}({instr.args})")

    

    # 展示φ函数

    print("\n--- φ函数插入 ---")

    

    phi_example = [

        PhiFunction(

            result="x.phi",

            incoming=[("x.1", "block1"), ("x.2", "block2")]

        )

    ]

    

    print("在merge点插入φ函数:")

    for phi in phi_example:

        emitter = SSAEmitter()

        print(f"  {emitter.emit_phi(phi)}")

    

    # 版本栈状态

    print("\n--- 版本栈变化 ---")

    

    versions = {

        "a": [0, 1, 2],  # a被定义了3次

        "b": [0],

        "c": [0]

    }

    

    print("变量版本历史:")

    for var, vers in versions.items():

        print(f"  {var}: v{vers}")

    

    print("\nSSA特点:")

    print("  1. 每个变量只被赋值一次")

    print("  2. φ函数表示在控制流汇合处合并不同版本的变量")

    print("  3. 版本号用于区分同一变量的多个定义")

    print("  4. 便于优化：def-use关系变得明确")

    print("  5. 简化活跃分析：每个版本独立分析")

