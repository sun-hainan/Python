# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / dataflow_analysis

本文件实现 dataflow_analysis 相关的算法功能。
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field

# ========== 数据流框架基类 ==========

@dataclass
class DataFlowResult:
    """数据流分析结果"""
    in_set: Set[str]          # IN[B]
    out_set: Set[str]        # OUT[B]
    gen_set: Set[str]        # GEN[B]
    kill_set: Set[str]       # KILL[B]


class DataFlowFramework:
    """
    数据流分析框架
    通用框架，支持多种分析
    """
    
    def __init__(self, cfg, direction: str = "forward"):
        self.cfg = cfg
        self.direction = direction  # "forward" 或 "backward"
        self.workset: List[Any] = []
        self.iteration = 0
    
    def analyze(self) -> Dict[str, DataFlowResult]:
        """
        执行数据流分析
        返回: 每个基本块的IN/OUT集合
        """
        result = {}
        
        # 初始化
        for block in self.cfg.blocks:
            result[block.label] = DataFlowResult(
                in_set=set(),
                out_set=set(),
                gen_set=block.gen_set if hasattr(block, 'gen_set') else set(),
                kill_set=block.kill_set if hasattr(block, 'kill_set') else set()
            )
        
        if self.direction == "forward":
            result = self._forward_analysis(result)
        else:
            result = self._backward_analysis(result)
        
        return result
    
    def _forward_analysis(self, result: Dict) -> Dict:
        """前向分析（如到达定义）"""
        changed = True
        order = self.cfg.compute_rpo()
        
        while changed:
            changed = False
            self.iteration += 1
            
            for block_id in order:
                block = self.cfg.get_block_by_label(block_id) if hasattr(self.cfg, 'get_block_by_label') else None
                if not block:
                    continue
                
                res = result.get(block.label, DataFlowResult(set(), set(), set(), set()))
                
                # IN[B] = ∪ OUT[P] for all P in Pred(B)
                new_in = set()
                for pred in block.predecessors:
                    pred_res = result.get(pred.label, DataFlowResult(set(), set(), set(), set()))
                    new_in |= pred_res.out_set
                
                old_in = res.in_set
                res.in_set = new_in
                
                # OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])
                new_out = res.gen_set | (new_in - res.kill_set)
                
                if new_out != res.out_set:
                    res.out_set = new_out
                    changed = True
        
        return result
    
    def _backward_analysis(self, result: Dict) -> Dict:
        """后向分析（如活跃变量）"""
        changed = True
        
        while changed:
            changed = False
            self.iteration += 1
            
            for block in self.cfg.blocks:
                res = result.get(block.label, DataFlowResult(set(), set(), set(), set()))
                
                # OUT[B] = ∪ IN[S] for all S in Succ(B)
                new_out = set()
                for succ in block.successors:
                    succ_res = result.get(succ.label, DataFlowResult(set(), set(), set(), set()))
                    new_out |= succ_res.in_set
                
                # IN[B] = USE[B] ∪ (OUT[B] - DEF[B])
                new_in = res.gen_set | (new_out - res.kill_set)
                
                if new_in != res.in_set or new_out != res.out_set:
                    res.in_set = new_in
                    res.out_set = new_out
                    changed = True
        
        return result


# ========== 到达定义分析 (Reaching Definitions) ==========

@dataclass
class Definition:
    """定义"""
    var: str           # 变量名
    block_id: str     # 定义所在块
    instr_idx: int    # 指令索引
    
    def __repr__(self):
        return f"{self.var}@{self.block_id}:{self.instr_idx}"
    
    def __hash__(self):
        return hash((self.var, self.block_id, self.instr_idx))
    
    def __eq__(self, other):
        return (self.var == other.var and 
                self.block_id == other.block_id and 
                self.instr_idx == other.instr_idx)


class ReachingDefinitions:
    """
    到达定义分析
    计算每个点的活跃定义
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.definitions: Dict[str, List[Definition]] = {}  # var -> definitions
        self.block_gen: Dict[str, Set[Definition]] = {}
        self.block_kill: Dict[str, Set[str]] = {}  # KILL[B] = 被重新定义的变量
    
    def compute_gen_kill(self):
        """计算每个块的GEN和KILL集合"""
        for block in self.cfg.blocks:
            gen = set()
            kill = set()
            
            for i, instr in enumerate(block.instructions):
                if hasattr(instr, 'result') and instr.result:
                    # 产生新定义
                    defn = Definition(instr.result, block.label, i)
                    gen.add(defn)
                    kill.add(instr.result)
            
            self.block_gen[block.label] = gen
            self.block_kill[block.label] = kill
    
    def analyze(self) -> Dict[str, Tuple[Set[Definition], Set[Definition]]]:
        """
        执行到达定义分析
        返回: {block_label: (IN, OUT)}
        """
        self.compute_gen_kill()
        
        result = {}
        for block in self.cfg.blocks:
            result[block.label] = (set(), set())
        
        changed = True
        while changed:
            changed = False
            
            for block in self.cfg.blocks:
                in_set, out_set = result[block.label]
                
                # IN[B] = ∪ OUT[P] for all P in Pred(B)
                new_in = set()
                for pred in block.predecessors:
                    pred_in, _ = result[pred.label]
                    new_in |= pred_in
                
                if new_in != in_set:
                    result[block.label] = (new_in, out_set)
                    changed = True
                
                # OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])
                new_out = self.block_gen[block.label] | (new_in - {
                    d for d in new_in 
                    if d.var in self.block_kill[block.label]
                })
                
                if new_out != out_set:
                    result[block.label] = (new_in, new_out)
                    changed = True
        
        return result


# ========== 活跃变量分析 (Live Variable Analysis) ==========

class LiveVariables:
    """
    活跃变量分析
    计算每个点的活跃变量（活跃定义）
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.block_use: Dict[str, Set[str]] = {}  # USE[B] - 变量被使用（在定义之前）
        self.block_def: Dict[str, Set[str]] = {}   # DEF[B] - 变量被定义
    
    def compute_use_def(self):
        """计算每个块的USE和DEF集合"""
        for block in self.cfg.blocks:
            use = set()
            def_set = set()
            
            for instr in block.instructions:
                # 收集使用
                for arg in getattr(instr, 'args', []):
                    if arg and arg not in def_set:
                        use.add(arg)
                
                # 收集定义
                if hasattr(instr, 'result') and instr.result:
                    def_set.add(instr.result)
            
            self.block_use[block.label] = use
            self.block_def[block.label] = def_set
    
    def analyze(self) -> Dict[str, Tuple[Set[str], Set[str]]]:
        """
        执行活跃变量分析
        返回: {block_label: (IN, OUT)}
        """
        self.compute_use_def()
        
        result = {}
        for block in self.cfg.blocks:
            result[block.label] = (set(), set())
        
        changed = True
        while changed:
            changed = False
            
            for block in self.cfg.blocks:
                use = self.block_use[block.label]
                def_set = self.block_def[block.label]
                in_set, out_set = result[block.label]
                
                # OUT[B] = ∪ IN[S] for all S in Succ(B)
                new_out = set()
                for succ in block.successors:
                    succ_in, _ = result[succ.label]
                    new_out |= succ_in
                
                if new_out != out_set:
                    result[block.label] = (in_set, new_out)
                    changed = True
                
                # IN[B] = USE[B] ∪ (OUT[B] - DEF[B])
                new_in = use | (new_out - def_set)
                
                if new_in != in_set:
                    result[block.label] = (new_in, new_out)
                    changed = True
        
        return result


# ========== 可用表达式分析 (Available Expressions) ==========

@dataclass
class Expression:
    """表达式"""
    op: str
    arg1: str
    arg2: Optional[str] = None
    
    def __repr__(self):
        if self.arg2:
            return f"{self.arg1} {self.op} {self.arg2}"
        return f"{self.op}{self.arg1}"
    
    def __hash__(self):
        return hash((self.op, self.arg1, self.arg2))
    
    def __eq__(self, other):
        return (self.op == other.op and 
                self.arg1 == other.arg1 and 
                self.arg2 == other.arg2)


class AvailableExpressions:
    """
    可用表达式分析
    用于全局公共子表达式消除
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.block_gen: Dict[str, Set[Expression]] = {}
        self.block_kill: Dict[str, Set[Tuple[str, str]]] = {}  # (var, expr) killed by var
    
    def compute_gen_kill(self):
        """计算每个块的GEN和KILL"""
        for block in self.cfg.blocks:
            gen = set()
            kill = set()  # 被重新定义的变量
            
            for instr in block.instructions:
                if hasattr(instr, 'result') and instr.result:
                    kill.add(instr.result)
                
                # 产生表达式
                if hasattr(instr, 'args') and len(instr.args) >= 2:
                    expr = Expression(
                        op=instr.opcode,
                        arg1=instr.args[0],
                        arg2=instr.args[1] if len(instr.args) > 1 else None
                    )
                    gen.add(expr)
                elif hasattr(instr, 'args') and len(instr.args) == 1:
                    expr = Expression(op=instr.opcode, arg1=instr.args[0])
                    gen.add(expr)
            
            self.block_gen[block.label] = gen
            self.block_kill[block.label] = kill
    
    def analyze(self) -> Dict[str, Tuple[Set[Expression], Set[Expression]]]:
        """
        执行可用表达式分析
        """
        self.compute_gen_kill()
        
        result = {}
        for block in self.cfg.blocks:
            result[block.label] = (set(), set())
        
        # 初始化入口块的OUT为空（底元素）
        if self.cfg.entry_block:
            result[self.cfg.entry_block.label] = (set(), set())
        
        changed = True
        while changed:
            changed = False
            
            for block in self.cfg.blocks:
                if block == self.cfg.entry_block:
                    continue
                
                in_set, out_set = result[block.label]
                
                # IN[B] = ∩ OUT[P] for all P in Pred(B)
                new_in = None
                for pred in block.predecessors:
                    pred_in, _ = result[pred.label]
                    if new_in is None:
                        new_in = set(pred_in)
                    else:
                        new_in &= pred_in
                
                if new_in is None:
                    new_in = set()
                
                if new_in != in_set:
                    result[block.label] = (new_in, out_set)
                    changed = True
                
                # OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])
                killed_exprs = set()
                for killed_var in self.block_kill[block.label]:
                    for expr in new_in:
                        if expr.arg1 == killed_var or expr.arg2 == killed_var:
                            killed_exprs.add(expr)
                
                new_out = self.block_gen[block.label] | (new_in - killed_exprs)
                
                if new_out != out_set:
                    result[block.label] = (new_in, new_out)
                    changed = True
        
        return result


# ========== Very-Busy Expressions ==========

class VeryBusyExpressions:
    """
    Very-Busy Expressions分析
    用于代码提升（将计算移到入口更早的位置）
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.block_gen: Dict[str, Set[Expression]] = {}
    
    def analyze(self) -> Dict[str, Tuple[Set[Expression], Set[Expression]]]:
        """
        执行Very-Busy Expressions分析
        """
        # 计算GEN
        for block in self.cfg.blocks:
            gen = set()
            
            for instr in block.instructions:
                if hasattr(instr, 'args') and len(instr.args) >= 2:
                    expr = Expression(
                        op=instr.opcode,
                        arg1=instr.args[0],
                        arg2=instr.args[1] if len(instr.args) > 1 else None
                    )
                    gen.add(expr)
            
            self.block_gen[block.label] = gen
        
        result = {}
        for block in self.cfg.blocks:
            result[block.label] = (set(), set())
        
        # 初始化所有块的OUT为全集（底元素）
        all_exprs = set()
        for gen in self.block_gen.values():
            all_exprs |= gen
        
        for block in self.cfg.blocks:
            result[block.label] = (set(), all_exprs.copy())
        
        changed = True
        while changed:
            changed = False
            
            for block in self.cfg.blocks:
                in_set, out_set = result[block.label]
                
                # OUT[B] = ∩ IN[S] for all S in Succ(B)
                new_out = None
                for succ in block.successors:
                    succ_in, _ = result[succ.label]
                    if new_out is None:
                        new_out = set(succ_in)
                    else:
                        new_out &= succ_in
                
                if new_out is None:
                    new_out = all_exprs.copy()
                
                if new_out != out_set:
                    result[block.label] = (in_set, new_out)
                    changed = True
                
                # IN[B] = GEN[B] ∪ OUT[B]
                new_in = self.block_gen[block.label] | new_out
                
                if new_in != in_set:
                    result[block.label] = (new_in, new_out)
                    changed = True
        
        return result


if __name__ == "__main__":
    print("=" * 60)
    print("数据流分析演示")
    print("=" * 60)
    
    # 模拟简单CFG
    from collections import defaultdict
    
    class SimpleCFG:
        def __init__(self):
            self.blocks = []
            
        def compute_rpo(self):
            return [b.label for b in self.blocks]
    
    cfg = SimpleCFG()
    
    # 模拟数据
    cfg.blocks = [
        type('Block', (), {
            'label': 'B1',
            'instructions': [
                SSAInstruction("add", "a", ["x", "y"]),
                SSAInstruction("sub", "b", ["a", "1"])
            ],
            'predecessors': [],
            'successors': []
        })(),
        type('Block', (), {
            'label': 'B2',
            'instructions': [
                SSAInstruction("add", "a", ["b", "z"]),  # 重新定义a
                SSAInstruction("mul", "c", ["a", "2"])
            ],
            'predecessors': [],
            'successors': []
        })()
    ]
    
    # 1. 到达定义分析
    print("\n--- 到达定义分析 ---")
    rd = ReachingDefinitions(cfg)
    rd_result = rd.analyze()
    
    for block_label, (in_set, out_set) in rd_result.items():
        print(f"  {block_label}:")
        print(f"    IN: {in_set}")
        print(f"    OUT: {out_set}")
    
    # 2. 活跃变量分析
    print("\n--- 活跃变量分析 ---")
    lv = LiveVariables(cfg)
    lv_result = lv.analyze()
    
    for block_label, (in_set, out_set) in lv_result.items():
        print(f"  {block_label}:")
        print(f"    入口活跃: {in_set}")
        print(f"    出口活跃: {out_set}")
    
    # 3. 可用表达式
    print("\n--- 可用表达式分析 ---")
    ae = AvailableExpressions(cfg)
    ae_result = ae.analyze()
    
    for block_label, (in_set, out_set) in ae_result.items():
        print(f"  {block_label}:")
        print(f"    可用表达式: {out_set}")
    
    print("\n数据流分析应用:")
    print("  - 到达定义: 活跃变量分析、复制传播")
    print("  - 活跃变量: 寄存器分配、死亡代码消除")
    print("  - 可用表达式: 全局公共子表达式消除")
    print("  - Very-Busy: 代码提升、死代码消除")
