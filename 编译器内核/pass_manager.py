# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / pass_manager

本文件实现 pass_manager 相关的算法功能。
"""

from typing import List, Dict, Type, Callable, Optional, Any, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time

# ========== Pass基类 ==========

@dataclass
class PassResult:
    """Pass执行结果"""
    pass_name: str
    success: bool
    elapsed_time: float = 0.0
    changes_made: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"PassResult({self.pass_name}: {status}, {self.elapsed_time:.2f}ms, changes={self.changes_made})"


class Pass(ABC):
    """
    Pass基类
    所有优化Pass都继承自此基类
    """
    
    def __init__(self, name: str, required_passes: List[str] = None):
        self.name = name
        self.required_passes = required_passes or []
        self.result: Optional[PassResult] = None
    
    @abstractmethod
    def run(self, module: 'Module') -> bool:
        """
        执行Pass
        返回: 是否成功
        """
        pass
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的Pass"""
        return self.required_passes


# ========== Module表示 ==========

@dataclass
class Function:
    """函数"""
    name: str
    params: List[str] = field(default_factory=list)
    local_vars: List[str] = field(default_factory=list)
    instructions: List = field(default_factory=list)
    is_exported: bool = True
    
    def __repr__(self):
        return f"Function({self.name}, {len(self.instructions)} instr)"


@dataclass
class BasicBlock:
    """基本块"""
    label: str
    instructions: List = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)


@dataclass
class Module:
    """模块（表示整个程序）"""
    name: str
    functions: List[Function] = field(default_factory=list)
    global_vars: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_function(self, name: str) -> Optional[Function]:
        """获取函数"""
        for func in self.functions:
            if func.name == name:
                return func
        return None
    
    def __repr__(self):
        return f"Module({self.name}, {len(self.functions)} functions)"


# ========== 具体Pass实现 ==========

class AnalysisPass(Pass):
    """分析Pass基类"""
    pass


class FunctionInlinePass(Pass):
    """内联Pass"""
    
    def __init__(self):
        super().__init__("FunctionInline", required_passes=["Analysis"])
    
    def run(self, module: Module) -> bool:
        """执行函数内联"""
        self.result = PassResult(self.name, True)
        
        inlined_count = 0
        for func in module.functions:
            # 简化模拟
            inlined_count += 0
        
        self.result.changes_made = inlined_count
        return True


class LoopUnrollPass(Pass):
    """循环展开Pass"""
    
    def __init__(self, threshold: int = 100):
        super().__init__("LoopUnroll", required_passes=["LoopAnalysis"])
        self.threshold = threshold
    
    def run(self, module: Module) -> bool:
        """执行循环展开"""
        self.result = PassResult(self.name, True)
        self.result.changes_made = 0
        return True


class ConstantFoldPass(Pass):
    """常量折叠Pass"""
    
    def __init__(self):
        super().__init__("ConstantFold", required_passes=[])
    
    def run(self, module: Module) -> bool:
        """执行常量折叠"""
        self.result = PassResult(self.name, True)
        changes = 0
        
        for func in module.functions:
            for instr in func.instructions:
                # 简化检查
                if hasattr(instr, 'opcode'):
                    if instr.opcode in ('add', 'sub', 'mul', 'div'):
                        changes += 1
        
        self.result.changes_made = changes
        return True


class DeadCodeElimPass(Pass):
    """死代码消除Pass"""
    
    def __init__(self):
        super().__init__("DeadCodeElim", required_passes=["LivenessAnalysis"])
    
    def run(self, module: Module) -> bool:
        """执行死代码消除"""
        self.result = PassResult(self.name, True)
        self.result.changes_made = 0
        return True


class RegisterAllocPass(Pass):
    """寄存器分配Pass"""
    
    def __init__(self):
        super().__init__("RegisterAlloc", required_passes=["LivenessAnalysis"])
    
    def run(self, module: Module) -> bool:
        """执行寄存器分配"""
        self.result = PassResult(self.name, True)
        self.result.changes_made = 1
        return True


class PrologueEpiloguePass(Pass):
    """序言/尾声生成Pass"""
    
    def __init__(self):
        super().__init__("PrologueEpilogue", required_passes=["RegisterAlloc"])
    
    def run(self, module: Module) -> bool:
        """生成序言和尾声"""
        self.result = PassResult(self.name, True)
        return True


# ========== Pass管理器 ==========

class PassManager:
    """
    Pass管理器
    管理和执行优化Pass
    """
    
    def __init__(self):
        self.passes: List[Pass] = []
        self.pass_registry: Dict[str, Type[Pass]] = {}
        self.execution_order: List[str] = []
        self.execution_results: Dict[str, PassResult] = {}
        self.analysis_results: Dict[str, Any] = {}  # 分析Pass的结果缓存
        self.requires: Dict[str, List[str]] = {}    # Pass依赖
        self.modifies: Dict[str, List[str]] = {}   # Pass修改的分析类型
    
    def register_pass(self, pass_class: Type[Pass]):
        """注册Pass类"""
        # 创建临时实例获取名称
        temp = pass_class()
        self.pass_registry[temp.name] = pass_class
        self.requires[temp.name] = temp.get_dependencies()
    
    def add_pass(self, pass_name: str):
        """添加Pass到Pipeline"""
        if pass_name in self.pass_registry:
            pass_class = self.pass_registry[pass_name]
            self.passes.append(pass_class())
            self.execution_order.append(pass_name)
    
    def add_pass_after(self, pass_name: str, after_pass: str):
        """在指定Pass后添加"""
        if pass_name not in self.pass_registry:
            return
        
        pass_class = self.pass_registry[pass_name]
        
        # 找到after_pass的位置
        try:
            idx = self.execution_order.index(after_pass)
            self.passes.insert(idx + 1, pass_class())
            self.execution_order.insert(idx + 1, pass_name)
        except ValueError:
            self.add_pass(pass_name)
    
    def build_pipeline(self, pipeline_desc: str):
        """
        从描述字符串构建Pipeline
        例如: "dce,inline,loop-unroll,cse,regalloc"
        """
        pass_names = [p.strip() for p in pipeline_desc.split(',')]
        
        for name in pass_names:
            self.add_pass(name)
    
    def add_required_passes(self):
        """自动添加缺失的required passes"""
        to_add = []
        
        for pass_name in self.execution_order:
            required = self.requires.get(pass_name, [])
            for req in required:
                if req not in self.execution_order:
                    to_add.append(req)
        
        for req in to_add:
            self.add_pass(req)
    
    def run(self, module: Module) -> Module:
        """执行所有Pass"""
        self.add_required_passes()
        
        print("=" * 60)
        print("Pass执行开始")
        print("=" * 60)
        print(f"Pipeline: {' -> '.join(self.execution_order)}")
        print()
        
        for pass_obj in self.passes:
            print(f"执行 Pass: {pass_obj.name}...", end=" ")
            
            start_time = time.time()
            success = pass_obj.run(module)
            elapsed = (time.time() - start_time) * 1000
            
            pass_obj.result = PassResult(
                pass_name=pass_obj.name,
                success=success,
                elapsed_time=elapsed,
                changes_made=getattr(pass_obj.result, 'changes_made', 0) if pass_obj.result else 0
            )
            
            self.execution_results[pass_obj.name] = pass_obj.result
            
            status = "✓" if success else "✗"
            changes_str = f"[{pass_obj.result.changes_made} changes]" if pass_obj.result else ""
            print(f"{status} ({elapsed:.2f}ms) {changes_str}")
            
            if not success:
                print(f"  错误: Pass执行失败")
                break
        
        print()
        self._print_summary()
        
        return module
    
    def _print_summary(self):
        """打印执行摘要"""
        print("=" * 60)
        print("执行摘要")
        print("=" * 60)
        
        total_time = 0
        total_changes = 0
        
        for name, result in self.execution_results.items():
            status = "✓" if result.success else "✗"
            print(f"  {status} {name:20} {result.elapsed_time:8.2f}ms  {result.changes_made:4} changes")
            total_time += result.elapsed_time
            total_changes += result.changes_made
        
        print(f"\n  总计: {len(self.execution_results)} passes, {total_time:.2f}ms, {total_changes} changes")
        print("=" * 60)


class OptimizationPipeline:
    """
    优化Pipeline构建器
    提供便捷的Pipeline创建接口
    """
    
    PRESET_PIPELINES = {
        "O0": [],  # 无优化
        "O1": ["ConstantFold", "DeadCodeElim"],
        "O2": ["ConstantFold", "Inline", "DeadCodeElim", "LoopUnroll", "CSE", "RegAlloc"],
        "O3": ["ConstantFold", "Inline", "DeadCodeElim", "LoopUnroll", "LoopVectorize", "CSE", "RegAlloc"],
        "size": ["ConstantFold", "DeadCodeElim", "RegAlloc"],
    }
    
    def __init__(self, pass_manager: PassManager):
        self.pm = pass_manager
    
    @classmethod
    def from_preset(cls, pass_manager: PassManager, level: str) -> 'OptimizationPipeline':
        """从预设创建Pipeline"""
        pipeline = cls(pass_manager)
        
        preset_passes = cls.PRESET_PIPELINES.get(level, [])
        
        for pass_name in preset_passes:
            pass_manager.add_pass(pass_name)
        
        return pipeline
    
    def enable_debug_passes(self):
        """启用调试Pass"""
        self.pm.add_pass("PrintIR")  # 打印IR
        self.pm.add_pass("VerifyPass")  # 验证IR


class PassManagerBuilder:
    """
    Pass管理器构建器
    方便构建复杂的Pass管理器
    """
    
    def __init__(self):
        self.pm = PassManager()
        self._register_standard_passes()
    
    def _register_standard_passes(self):
        """注册标准Pass"""
        self.pm.register_pass(ConstantFoldPass)
        self.pm.register_pass(DeadCodeElimPass)
        self.pm.register_pass(FunctionInlinePass)
        self.pm.register_pass(LoopUnrollPass)
        self.pm.register_pass(RegisterAllocPass)
        self.pm.register_pass(PrologueEpiloguePass)
    
    def with_pass(self, pass_name: str) -> 'PassManagerBuilder':
        """添加Pass"""
        self.pm.add_pass(pass_name)
        return self
    
    def after(self, pass_name: str, after_pass: str) -> 'PassManagerBuilder':
        """在某Pass后添加"""
        self.pm.add_pass_after(pass_name, after_pass)
        return self
    
    def build(self) -> PassManager:
        """构建并返回PassManager"""
        self.pm.add_required_passes()
        return self.pm


# ========== 分析Pass示例 ==========

class LivenessAnalysisPass(AnalysisPass):
    """活跃性分析Pass"""
    
    def __init__(self):
        super().__init__("LivenessAnalysis", required_passes=[])
    
    def run(self, module: Module) -> bool:
        """执行活跃性分析"""
        self.result = PassResult(self.name, True)
        
        live_vars = {}
        for func in module.functions:
            func_live = self._analyze_function(func)
            live_vars[func.name] = func_live
        
        self.analysis_results["liveness"] = live_vars
        return True
    
    def _analyze_function(self, func: Function) -> Dict[str, Set[str]]:
        """分析函数的活跃变量"""
        return {}


class LoopAnalysisPass(AnalysisPass):
    """循环分析Pass"""
    
    def __init__(self):
        super().__init__("LoopAnalysis", required_passes=[])
    
    def run(self, module: Module) -> bool:
        """执行循环分析"""
        self.result = PassResult(self.name, True)
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("Pass架构演示")
    print("=" * 60)
    
    # 创建模块
    module = Module(name="test_module")
    module.functions = [
        Function(name="main", params=[], instructions=[]),
        Function(name="helper", params=["x"], instructions=[])
    ]
    
    print(f"\n输入: {module}")
    
    # 使用构建器创建Pipeline
    print("\n--- 构建优化Pipeline ---")
    
    builder = PassManagerBuilder()
    pm = builder.with_pass("ConstantFold").with_pass("FunctionInline").build()
    
    print("已注册Pass:", list(pm.pass_registry.keys()))
    
    # 执行Pipeline
    print("\n--- 执行Pipeline ---")
    result_module = pm.run(module)
    
    # 使用预设Pipeline
    print("\n--- 使用O2预设Pipeline ---")
    
    pm2 = PassManager()
    for pass_cls in [ConstantFoldPass, FunctionInlinePass, DeadCodeElimPass, LoopUnrollPass]:
        pm2.register_pass(pass_cls)
    
    pipeline = OptimizationPipeline(pm2)
    pm2.build_pipeline("ConstantFold,DeadCodeElim,FunctionInline")
    pm2.run(module)
    
    print("\nPass架构要点:")
    print("  1. Pass是编译优化的基本单元")
    print("  2. 分析Pass收集信息，优化Pass使用信息")
    print("  3. Pass管理器处理依赖和执行顺序")
    print("  4. Pipeline描述优化流程")
    print("  5. 可以配置不同优化级别（O0/O1/O2/O3）")
