# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / constant_propagation



本文件实现 constant_propagation 相关的算法功能。

"""



from typing import Dict, List, Set, Optional, Any, Tuple

from dataclasses import dataclass, field



# ========== 常量传播基础 ==========



@dataclass

class Value:

    """值对象（可以是常量、bot、top）"""

    kind: str  # "constant", "bottom", "top"

    constant: Any = None

    

    def __repr__(self):

        if self.kind == "constant":

            return str(self.constant)

        elif self.kind == "bottom":

            return "⊥"  # 未定义

        elif self.kind == "top":

            return "⊤"  # 可能非常量

        return "?"

    

    @staticmethod

    def bottom():

        return Value(kind="bottom")

    

    @staticmethod

    def top():

        return Value(kind="top")

    

    @staticmethod

    def const(val):

        return Value(kind="constant", constant=val)





class ConstantPropagator:

    """

    常量传播器

    跟踪变量的常量值

    """

    

    def __init__(self):

        self.values: Dict[str, Value] = {}  # variable -> Value

    

    def get_value(self, var: str) -> Value:

        """获取变量的值"""

        return self.values.get(var, Value.top())

    

    def set_value(self, var: str, val: Value):

        """设置变量的值"""

        if var in self.values and self.values[var] == val:

            return  # 没有变化

        self.values[var] = val

    

    def copy(self) -> 'ConstantPropagator':

        """创建拷贝"""

        new_cp = ConstantPropagator()

        new_cp.values = dict(self.values)

        return new_cp

    

    def merge(self, other: 'ConstantPropagator') -> bool:

        """

        合并两个状态

        返回: 是否发生变化

        """

        changed = False

        

        all_vars = set(self.values.keys()) | set(other.values.keys())

        

        for var in all_vars:

            val1 = self.values.get(var, Value.top())

            val2 = other.values.get(var, Value.top())

            

            merged = self._meet(val1, val2)

            

            if var not in self.values or self.values[var] != merged:

                self.values[var] = merged

                changed = True

        

        return changed

    

    def _meet(self, v1: Value, v2: Value) -> Value:

        """meet操作"""

        if v1.kind == "top":

            return v2

        if v2.kind == "top":

            return v1

        if v1.kind == "bottom":

            return v2

        if v2.kind == "bottom":

            return v1

        if v1.constant == v2.constant:

            return v1

        return Value.top()





@dataclass

class Instruction:

    """指令"""

    opcode: str

    result: Optional[str] = None

    arg1: Optional[str] = None

    arg2: Optional[str] = None

    label: Optional[str] = None





class ConstantPropagationAnalysis:

    """

    常量传播分析

    对基本块执行数据流分析

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.results: Dict[str, ConstantPropagator] = {}

    

    def analyze(self) -> Dict[str, ConstantPropagator]:

        """执行常量传播分析"""

        # 初始化入口为常量

        for block in self.cfg.blocks:

            self.results[block.label] = ConstantPropagator()

        

        # 迭代直到收敛

        changed = True

        while changed:

            changed = False

            

            for block in self.cfg.blocks:

                # 合并所有前驱

                propagator = ConstantPropagator()

                first = True

                

                for pred in block.predecessors:

                    if pred.label in self.results:

                        if first:

                            propagator = self.results[pred.label].copy()

                            first = False

                        else:

                            propagator.merge(self.results[pred.label])

                

                # 执行基本块内的指令

                for instr in block.instructions:

                    self._propagate(propagator, instr)

                

                # 检查是否发生变化

                if block.label not in self.results:

                    self.results[block.label] = propagator

                    changed = True

                elif self.results[block.label].values != propagator.values:

                    self.results[block.label] = propagator

                    changed = True

        

        return self.results

    

    def _propagate(self, cp: ConstantPropagator, instr: Instruction):

        """传播单条指令"""

        if instr.opcode == "mov" or instr.opcode == "assign":

            val = cp.get_value(instr.arg1)

            cp.set_value(instr.result, val)

        

        elif instr.opcode in ("add", "sub", "mul", "div"):

            v1 = cp.get_value(instr.arg1)

            v2 = cp.get_value(instr.arg2)

            

            if v1.kind == "constant" and v2.kind == "constant":

                result = self._compute_binary(v1.constant, v2.constant, instr.opcode)

                cp.set_value(instr.result, Value.const(result))

            else:

                cp.set_value(instr.result, Value.top())

        

        elif instr.opcode == "phi":

            # φ函数：合并所有参数

            # 简化处理

            pass

    

    def _compute_binary(self, v1, v2, op) -> Any:

        """计算二元操作"""

        try:

            if op == "add":

                return v1 + v2

            elif op == "sub":

                return v1 - v2

            elif op == "mul":

                return v1 * v2

            elif op == "div" and v2 != 0:

                return v1 / v2

        except:

            pass

        return None





# ========== 稀疏条件常量传播（SCCP） ==========



class SCCPOptimizer:

    """

    稀疏条件常量传播（SCCP）

    在SSA形式上执行常量传播和条件分支优化

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.lattice: Dict[str, Value] = {}  # SSA变量 -> 值

        self.branch_conditions: Dict[str, Any] = {}  # 分支条件

        self.executable_blocks: Set[str] = set()

        self.worklist: List[Tuple[str, int]] = []  # (block, instr_idx)

    

    def optimize(self) -> 'SCCPOptimizer':

        """执行SCCP"""

        # 初始化所有变量为top（未知）

        self._init_lattice()

        

        # 标记入口块可执行

        if self.cfg.entry_block:

            self.executable_blocks.add(self.cfg.entry_block.label)

            self.worklist.append((self.cfg.entry_block.label, 0))

        

        # 处理工作列表

        while self.worklist:

            block_label, instr_idx = self.worklist.pop()

            

            block = self.cfg.get_block_by_label(block_label)

            if not block or instr_idx >= len(block.instructions):

                continue

            

            instr = block.instructions[instr_idx]

            self._visit_instruction(block, instr)

        

        return self

    

    def _init_lattice(self):

        """初始化格"""

        # 所有块和变量初始化为top

        for block in self.cfg.blocks:

            for instr in block.instructions:

                if instr.result:

                    self.lattice[instr.result] = Value.top()

    

    def _visit_instruction(self, block, instr: Instruction):

        """访问指令"""

        opcode = instr.opcode

        

        if opcode in ("add", "sub", "mul", "div"):

            v1 = self._get_value(instr.arg1)

            v2 = self._get_value(instr.arg2)

            

            if v1.kind == "constant" and v2.kind == "constant":

                result = self._compute(v1.constant, v2.constant, opcode)

                self._set_value(instr.result, Value.const(result))

            else:

                self._set_value(instr.result, Value.top())

        

        elif opcode in ("cmp", "test"):

            v1 = self._get_value(instr.arg1)

            v2 = self._get_value(instr.arg2)

            

            if v1.kind == "constant" and v2.kind == "constant":

                result = self._compare(v1.constant, v2.constant)

                self._set_value(instr.result, Value.const(result))

            else:

                self._set_value(instr.result, Value.top())

        

        elif opcode in ("je", "jne", "jl", "jle", "jg", "jge"):

            self._handle_branch(block, instr)

        

        elif opcode == "mov":

            self._set_value(instr.result, self._get_value(instr.arg1))

    

    def _set_value(self, var: str, val: Value):

        """设置值并加入工作列表"""

        if var not in self.lattice or self.lattice[var] != val:

            self.lattice[var] = val

            # 添加所有使用该变量的指令到工作列表

            self._add_users_to_worklist(var)

    

    def _get_value(self, var: str) -> Value:

        """获取值"""

        return self.lattice.get(var, Value.top())

    

    def _add_users_to_worklist(self, var: str):

        """将使用该变量的指令加入工作列表"""

        for block in self.cfg.blocks:

            for i, instr in enumerate(block.instructions):

                if var in [instr.arg1, instr.arg2]:

                    if block.label in self.executable_blocks:

                        self.worklist.append((block.label, i))

    

    def _handle_branch(self, block, instr: Instruction):

        """处理分支指令"""

        condition = instr.arg1

        val = self._get_value(condition)

        

        if val.kind != "constant":

            # 条件不确定，添加两个分支

            for succ in block.successors:

                self.executable_blocks.add(succ.label)

                self.worklist.append((succ.label, 0))

            return

        

        condition_value = val.constant

        

        if instr.opcode == "je":

            target = instr.label

            if condition_value != 0:

                self.executable_blocks.add(target)

            else:

                # 跳过跳转

                for succ in block.successors:

                    if succ.label != target:

                        self.executable_blocks.add(succ.label)

        # 类似处理其他跳转

    

    def _compute(self, v1, v2, op) -> Any:

        """计算二元操作"""

        try:

            if op == "add": return v1 + v2

            if op == "sub": return v1 - v2

            if op == "mul": return v1 * v2

            if op == "div" and v2 != 0: return v1 / v2

        except:

            pass

        return None

    

    def _compare(self, v1, v2) -> int:

        """比较操作"""

        if v1 < v2: return -1

        if v1 > v2: return 1

        return 0

    

    def get_constant_values(self) -> Dict[str, Any]:

        """获取所有已知为常量的变量"""

        result = {}

        for var, val in self.lattice.items():

            if val.kind == "constant":

                result[var] = val.constant

        return result





# ========== 条件常量折叠 ==========



class ConditionalConstantFolder:

    """

    条件常量折叠

    识别总是执行或不执行的条件分支

    """

    

    def __init__(self, cfg):

        self.cfg = cfg

        self.constant_conditions: Dict[str, bool] = {}  # label -> is_always_true

    

    def fold(self) -> List[Instruction]:

        """折叠条件常量"""

        result = []

        

        for block in self.cfg.blocks:

            for instr in block.instructions:

                folded = self._try_fold(instr)

                if folded:

                    result.append(folded)

                else:

                    result.append(instr)

        

        return result

    

    def _try_fold(self, instr: Instruction) -> Optional[Instruction]:

        """尝试折叠单个指令"""

        if instr.opcode in ("je", "jne", "jmp"):

            # 检查条件是否已知

            if instr.arg1 and instr.arg1 in self.constant_conditions:

                # 条件已知，可以折叠或移除

                if instr.opcode == "jmp":

                    return instr  # 无条件跳转，无法优化

            

            # 简化条件跳转

            if instr.label and instr.label in self.constant_conditions:

                # 可以移除此跳转

                return None

        

        return instr

    

    def mark_always_true(self, label: str):

        """标记条件总是为真"""

        self.constant_conditions[label] = True

    

    def mark_always_false(self, label: str):

        """标记条件总是为假"""

        self.constant_conditions[label] = False





if __name__ == "__main__":

    print("=" * 60)

    print("常量传播与SCCP演示")

    print("=" * 60)

    

    # 创建测试代码

    class Block:

        def __init__(self, label):

            self.label = label

            self.instructions = []

            self.predecessors = []

            self.successors = []

    

    # 模拟代码

    instructions = [

        Instruction("mov", "x", arg1="10"),

        Instruction("mov", "y", arg1="20"),

        Instruction("add", "z", arg1="x", arg2="y"),      # z = 10 + 20 = 30

        Instruction("mul", "w", arg1="z", arg2="2"),      # w = 30 * 2 = 60

        Instruction("sub", "v", arg1="w", arg2="v"),      # v = w - v

    ]

    

    print("\n--- 常量传播分析 ---")

    

    cp = ConstantPropagator()

    cp.set_value("x", Value.const(10))

    cp.set_value("y", Value.const(20))

    

    print(f"x = {cp.get_value('x')}")

    print(f"y = {cp.get_value('y')}")

    

    # 执行常量传播

    for instr in instructions:

        if instr.result:

            if instr.opcode == "mov":

                val = cp.get_value(instr.arg1)

            elif instr.opcode == "add":

                v1 = cp.get_value(instr.arg1)

                v2 = cp.get_value(instr.arg2)

                if v1.kind == "constant" and v2.kind == "constant":

                    val = Value.const(v1.constant + v2.constant)

                else:

                    val = Value.top()

            elif instr.opcode == "mul":

                v1 = cp.get_value(instr.arg1)

                v2 = cp.get_value(instr.arg2)

                if v1.kind == "constant" and v2.kind == "constant":

                    val = Value.const(v1.constant * v2.constant)

                else:

                    val = Value.top()

            elif instr.opcode == "sub":

                v1 = cp.get_value(instr.arg1)

                v2 = cp.get_value(instr.arg2)

                if v1.kind == "constant" and v2.kind == "constant":

                    val = Value.const(v1.constant - v2.constant)

                else:

                    val = Value.top()

            else:

                val = Value.top()

            

            cp.set_value(instr.result, val)

    

    print("\n变量值:")

    print(f"  x = {cp.get_value('x')}")

    print(f"  y = {cp.get_value('y')}")

    print(f"  z = {cp.get_value('z')} (应该=30)")

    print(f"  w = {cp.get_value('w')} (应该=60)")

    print(f"  v = {cp.get_value('v')}")

    

    # SCCP演示

    print("\n--- SCCP（稀疏条件常量传播）---")

    

    sccp = SCCPOptimizer(None)  # 简化

    sccp.lattice = {

        "a": Value.const(10),

        "b": Value.const(20),

        "c": Value.const(30),

    }

    

    # 模拟条件

    sccp._set_value("t0", Value.const(10))

    sccp._set_value("t1", Value.const(20))

    sccp._set_value("t2", Value.top())  # 运行时才能确定

    

    print("常量值:")

    result = sccp.get_constant_values()

    for var, val in result.items():

        print(f"  {var} = {val}")

    

    print("\nSCCP特点:")

    print("  1. 仅追踪常量/非常量状态")

    print("  2. 稀疏执行：只在相关位置传播")

    print("  3. 处理条件分支：识别总是为真/假的条件")

    print("  4. 消除死代码：移除不可达分支")

    print("  5. 折叠分支：移除不必要的条件判断")

