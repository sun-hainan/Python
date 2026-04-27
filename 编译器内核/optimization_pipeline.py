# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / optimization_pipeline



本文件实现 optimization_pipeline 相关的算法功能。

"""



from typing import List, Dict, Optional, Callable, Any, Type

from abc import ABC, abstractmethod

from dataclasses import dataclass, field

from enum import Enum

import time





# =============================================================================

# Pass基类和枚举

# =============================================================================



class PassKind(Enum):

    """Pass类型枚举"""

    ANALYSIS = "analysis"  # 分析Pass（只读取IR）

    TRANSFORMATION = "transformation"  # 变换Pass（修改IR）

    UTILITY = "utility"  # 工具Pass





@dataclass

class PassInfo:

    """Pass的元信息"""

    name: str  # Pass名称

    kind: PassKind  # Pass类型

    depends_on: List[str] = field(default_factory=list)  # 依赖的Pass

    invalidates: List[str] = field(default_factory=list)  # 会使其失效的分析Pass





# =============================================================================

# IR表示（简化版）

# =============================================================================



class BasicBlock:

    """基本块：一组连续的指令"""

    def __init__(self, name: str):

        self.name = name

        self.instructions: List['Instruction'] = []



    def add_instruction(self, instr: 'Instruction'):

        self.instructions.append(instr)



    def __repr__(self):

        return f"BasicBlock({self.name}, {len(self.instructions)} instrs)"





class Instruction:

    """指令"""

    def __init__(self, opcode: str, dest: Optional[str] = None, *srcs):

        self.opcode = opcode

        self.dest = dest

        self.srcs = list(srcs)



    def __repr__(self):

        if self.dest:

            return f"{self.dest} = {self.opcode}({', '.join(self.srcs)})"

        return f"{self.opcode}({', '.join(self.srcs)})"





class Function:

    """函数"""

    def __init__(self, name: str):

        self.name = name

        self.blocks: List[BasicBlock] = []



    def add_block(self, block: BasicBlock):

        self.blocks.append(block)



    def __repr__(self):

        return f"Function({self.name}, {len(self.blocks)} blocks)"





class Module:

    """模块（包含多个函数）"""

    def __init__(self, name: str):

        self.name = name

        self.functions: Dict[str, Function] = {}



    def add_function(self, func: Function):

        self.functions[func.name] = func





# =============================================================================

# Pass基类

# =============================================================================



class Pass(ABC):

    """

    Pass基类



    所有优化的基类，定义统一的接口

    """



    def __init__(self, info: PassInfo):

        self.info = info  # Pass的元信息

        self.module: Optional[Module] = None  # 当前的Module

        self.analysis_results: Dict[str, Any] = {}  # 存储的分析结果



    def set_module(self, module: Module):

        """设置当前模块"""

        self.module = module



    def get_analysis(self, name: str) -> Optional[Any]:

        """获取分析结果"""

        return self.analysis_results.get(name)



    def set_analysis(self, name: str, result: Any):

        """存储分析结果"""

        self.analysis_results[name] = result



    @abstractmethod

    def run_on_function(self, func: Function) -> bool:

        """

        在函数上运行Pass



        返回:

            True=进行了修改，False=未修改

        """

        pass



    def run(self) -> bool:

        """运行Pass的入口"""

        if self.module is None:

            raise RuntimeError("Module not set")



        modified = False

        for func in self.module.functions.values():

            if self.run_on_function(func):

                modified = True

        return modified





# =============================================================================

# 常用Pass实现

# =============================================================================



class ConstantFoldingPass(Pass):

    """

    常量折叠Pass



    将编译时可计算的常量表达式直接求值

    例如：x = 1 + 2  ->  x = 3

    """



    def __init__(self):

        super().__init__(PassInfo(

            name="ConstantFolding",

            kind=PassKind.TRANSFORMATION,

            depends_on=["CFGBuilder"]

        ))



    def run_on_function(self, func: Function) -> bool:

        modified = False

        for block in func.blocks:

            new_instructions = []

            for instr in block.instructions:

                folded = self._try_fold(instr)

                if folded:

                    new_instr = Instruction(folded["opcode"], folded.get("dest"), *folded.get("srcs", []))

                    new_instructions.append(new_instr)

                    modified = True

                else:

                    new_instructions.append(instr)

            block.instructions = new_instructions

        return modified



    def _try_fold(self, instr: Instruction) -> Optional[Dict]:

        """尝试折叠常量表达式"""

        if instr.opcode == "add" and len(instr.srcs) == 2:

            try:

                a = int(instr.srcs[0])

                b = int(instr.srcs[1])

                return {"opcode": "add", "dest": instr.dest, "srcs": [str(a + b)]}

            except ValueError:

                pass

        return None





class DeadCodeEliminationPass(Pass):

    """

    死代码消除Pass



    删除不会被使用的代码

    """



    def __init__(self):

        super().__init__(PassInfo(

            name="DeadCodeElimination",

            kind=PassKind.TRANSFORMATION,

            depends_on=["ReachingDefinitions"]

        ))



    def run_on_function(self, func: Function) -> bool:

        # 简化版本：假设所有dest都没有被使用就是死代码

        # 实际需要更复杂的活跃性分析

        modified = False

        for block in func.blocks:

            live_dests = set()

            # 扫描确定哪些dest被使用

            for instr in block.instructions:

                for src in instr.srcs:

                    live_dests.add(src)



            new_instructions = []

            for instr in block.instructions:

                # 如果dest没有被使用，也不是store，则可能是死代码

                if instr.dest and instr.dest not in live_dests and instr.opcode != "store":

                    # 保留有副作用的指令

                    if self._has_side_effect(instr):

                        new_instructions.append(instr)

                        # 更新live_dests

                        if instr.dest:

                            live_dests.add(instr.dest)

                    else:

                        modified = True  # 删除了死代码

                        continue

                new_instructions.append(instr)

                if instr.dest:

                    live_dests.add(instr.dest)



            block.instructions = new_instructions



        return modified



    def _has_side_effect(self, instr: Instruction) -> bool:

        """检查指令是否有副作用"""

        side_effect_ops = {"store", "call", "br", "ret", "print"}

        return instr.opcode in side_effect_ops





class CFGBuilderPass(Pass):

    """

    控制流图构建Pass（分析Pass）



    构建函数的基本块和控制流图

    """



    def __init__(self):

        super().__init__(PassInfo(

            name="CFGBuilder",

            kind=PassKind.ANALYSIS

        ))



    def run_on_function(self, func: Function) -> bool:

        # 构建基本块的后继和前驱关系

        for i, block in enumerate(func.blocks):

            block.successors = []

            block.predecessors = []

            if i < len(func.blocks) - 1:

                block.successors.append(func.blocks[i + 1])

                func.blocks[i + 1].predecessors.append(block)



        self.set_analysis("cfg", {b.name: b for b in func.blocks})

        return False  # 分析Pass不修改IR





class InliningPass(Pass):

    """

    函数内联Pass



    将小函数调用内联到调用点

    """



    def __init__(self, threshold: int = 10):

        super().__init__(PassInfo(

            name="Inlining",

            kind=PassKind.TRANSFORMATION,

            depends_on=["CFGBuilder"]

        ))

        self.threshold = threshold  # 超过此大小的函数不内联



    def run_on_function(self, func: Function) -> bool:

        modified = False

        for block in func.blocks:

            new_instructions = []

            for instr in block.instructions:

                if instr.opcode == "call":

                    # 简化：直接内联函数内容

                    # 实际需要查找被调用函数并复制其指令

                    new_instr = Instruction("add", instr.dest, "0", "0")  # 占位

                    new_instructions.append(new_instr)

                    modified = True

                else:

                    new_instructions.append(instr)

            block.instructions = new_instructions

        return modified





class LoopUnrollingPass(Pass):

    """

    循环展开Pass



    减少循环分支开销，增加指令级并行

    """



    def __init__(self, factor: int = 2):

        super().__init__(PassInfo(

            name="LoopUnrolling",

            kind=PassKind.TRANSFORMATION,

            depends_on=["LoopAnalysis"]

        ))

        self.factor = factor



    def run_on_function(self, func: Function) -> bool:

        # 简化版本，不真正实现循环展开

        # 实际需要检测循环、复制循环体、调整终止条件

        return False





# =============================================================================

# Pass管理器

# =============================================================================



class PassManager:

    """

    Pass管理器



    负责：

        1. 管理Pass的执行顺序

        2. 解决Pass之间的依赖

        3. 缓存分析结果，失效处理

        4. 报告Pass执行统计

    """



    def __init__(self, module: Module):

        self.module = module

        self.passes: List[Pass] = []  # 注册的Pass列表

        self.pass_registry: Dict[str, Pass] = {}  # Pass名称 -> Pass实例

        self.execution_order: List[str] = []  # 执行顺序

        self.statistics: Dict[str, Dict[str, Any]] = {}  # 统计信息



    def register_pass(self, pass_instance: Pass):

        """注册一个Pass"""

        self.passes.append(pass_instance)

        self.pass_registry[pass_instance.info.name] = pass_instance

        pass_instance.set_module(self.module)



    def add_pass(self, pass_class: Type[Pass], *args, **kwargs):

        """添加Pass（自动实例化）"""

        pass_instance = pass_class(*args, **kwargs)

        self.register_pass(pass_instance)



    def topological_sort_passes(self) -> List[Pass]:

        """

        对Pass进行拓扑排序，确定执行顺序



        确保依赖的Pass在当前Pass之前执行

        """

        sorted_passes = []

        remaining = set(self.passes)

        added = set()



        while remaining:

            # 找到所有依赖都满足的Pass

            ready = []

            for p in remaining:

                deps_satisfied = all(dep in added for dep in p.info.depends_on)

                if deps_satisfied:

                    ready.append(p)



            if not ready:

                # 循环依赖或缺失依赖

                remaining_names = [p.info.name for p in remaining]

                raise RuntimeError(f"无法解析Pass依赖: {remaining_names}")



            # 选择一个执行（实际应该按优先级选择）

            p = ready[0]

            sorted_passes.append(p)

            remaining.remove(p)

            added.add(p.info.name)



        return sorted_passes



    def run(self, passes: Optional[List[str]] = None):

        """

        执行所有Pass



        参数:

            passes: 可选，指定要执行的Pass名称列表

        """

        if passes:

            to_run = [self.pass_registry[name] for name in passes if name in self.pass_registry]

        else:

            to_run = self.topological_sort_passes()



        print("=" * 60)

        print("优化管道执行")

        print("=" * 60)



        for p in to_run:

            start_time = time.time()

            try:

                modified = p.run()

                elapsed = time.time() - start_time



                kind_symbol = "🔄" if p.info.kind == PassKind.TRANSFORMATION else "📊"

                status = "修改了IR" if modified else "无修改"



                print(f"{kind_symbol} {p.info.name:<25} [{p.info.kind.value}] - {status} ({elapsed*1000:.2f}ms)")



                self.statistics[p.info.name] = {

                    "modified": modified,

                    "time_ms": elapsed * 1000

                }

            except Exception as e:

                print(f"❌ {p.info.name} 执行失败: {e}")

                raise



        print("=" * 60)

        print("优化完成")





# =============================================================================

# 测试代码

# =============================================================================



if __name__ == "__main__":

    print("=" * 60)

    print("优化PassPipeline测试")

    print("=" * 60)



    # 创建测试模块

    module = Module("test_module")



    # 创建测试函数

    func = Function("test_func")

    block = BasicBlock("entry")



    # 添加测试指令

    # 原始代码: y = x + 2; z = y + 3; w = z + 1

    block.add_instruction(Instruction("add", "y", "x", "2"))  # y = x + 2

    block.add_instruction(Instruction("add", "z", "y", "3"))  # z = y + 3

    block.add_instruction(Instruction("add", "w", "z", "1"))  # w = z + 1

    block.add_instruction(Instruction("store", None, "w"))   # store w



    func.add_block(block)

    module.add_function(func)



    print(f"\n原始IR:")

    for func in module.functions.values():

        for block in func.blocks:

            print(f"  {block}")

            for instr in block.instructions:

                print(f"    {instr}")



    # 创建Pass管理器

    pm = PassManager(module)



    # 注册Pass

    pm.add_pass(CFGBuilderPass)

    pm.add_pass(ConstantFoldingPass)

    pm.add_pass(DeadCodeEliminationPass)

    pm.add_pass(InliningPass)



    # 执行优化

    pm.run()



    print(f"\n优化后IR:")

    for func in module.functions.values():

        for block in func.blocks:

            print(f"  {block}")

            for instr in block.instructions:

                print(f"    {instr}")



    print("\n优化统计:")

    for name, stats in pm.statistics.items():

        print(f"  {name}: 修改={stats['modified']}, 耗时={stats['time_ms']:.2f}ms")

