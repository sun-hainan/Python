# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / cse_value_numbering

本文件实现 cse_value_numbering 相关的算法功能。
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field

# ========== 表达式和值编号 ==========

@dataclass
class Expression:
    """表达式"""
    opcode: str
    arg1: Optional[str] = None
    arg2: Optional[str] = None
    
    def __repr__(self):
        if self.arg2:
            return f"{self.arg1} {self.opcode} {self.arg2}"
        elif self.arg1:
            return f"{self.opcode} {self.arg1}"
        return self.opcode
    
    def __hash__(self):
        return hash((self.opcode, self.arg1, self.arg2))
    
    def __eq__(self, other):
        return (self.opcode == other.opcode and 
                self.arg1 == other.arg1 and 
                self.arg2 == other.arg2)


@dataclass
class ValueNumberEntry:
    """值编号表项"""
    expr: Expression
    value_number: int
    result_var: str  # 表达式结果的变量名


class ValueNumbering:
    """
    Value Numbering算法
    识别并消除公共子表达式
    """
    
    def __init__(self):
        self.value_number_map: Dict[int, Expression] = {}  # value_number -> expression
        self.expr_value_map: Dict[Expression, int] = {}    # expression -> value_number
        self.var_value_map: Dict[str, int] = {}            # variable -> value_number
        self.next_value_number = 1
    
    def lookup(self, expr: Expression) -> Optional[int]:
        """查找表达式的值编号"""
        return self.expr_value_map.get(expr)
    
    def insert(self, expr: Expression, result_var: str) -> int:
        """插入新的表达式"""
        if expr not in self.expr_value_map:
            vn = self.next_value_number
            self.next_value_number += 1
            
            self.value_number_map[vn] = expr
            self.expr_value_map[expr] = vn
            self.var_value_map[result_var] = vn
            
            return vn
        
        return self.expr_value_map[expr]
    
    def get_value_number(self, var: str) -> Optional[int]:
        """获取变量的值编号"""
        return self.var_value_map.get(var)
    
    def get_expression(self, vn: int) -> Optional[Expression]:
        """通过值编号获取表达式"""
        return self.value_number_map.get(vn)


class CommonSubexpressionEliminator:
    """
    公共子表达式消除器（CSE）
    使用Value Numbering算法
    """
    
    def __init__(self):
        self.vn = ValueNumbering()
        self.replacements: List[Tuple[str, str]] = []  # (old_var, new_var)
        self.eliminated_count = 0
    
    def eliminate(self, instructions: List) -> List:
        """
        执行公共子表达式消除
        返回: 优化后的指令序列
        """
        result = []
        
        for instr in instructions:
            optimized = self._process_instruction(instr)
            
            if optimized:
                result.append(optimized)
        
        return result
    
    def _process_instruction(self, instr) -> Optional:
        """处理单条指令"""
        # 获取操作数
        arg1 = getattr(instr, 'arg1', None)
        arg2 = getattr(instr, 'arg2', None)
        
        # 获取操作数对应的值编号
        vn1 = self.vn.get_value_number(arg1) if arg1 else None
        vn2 = self.vn.get_value_number(arg2) if arg2 else None
        
        # 构建表达式
        if arg1 and arg2:
            expr = Expression(opcode=instr.opcode, arg1=arg1, arg2=arg2)
        elif arg1:
            expr = Expression(opcode=instr.opcode, arg1=arg1)
        else:
            expr = Expression(opcode=instr.opcode)
        
        # 查找已有的值编号
        existing_vn = self.vn.lookup(expr)
        
        if existing_vn is not None:
            # 找到公共子表达式，可以复用
            existing_expr = self.vn.get_expression(existing_vn)
            
            # 需要确定之前的结果变量
            # 简化：假设存在一个变量名
            old_result = self._find_result_var(existing_vn)
            
            if old_result:
                self.replacements.append((instr.result, old_result))
                self.eliminated_count += 1
                
                # 创建复用指令（mov）
                return self._create_reuse_instruction(instr, old_result)
        
        # 没有找到，新表达式
        result_var = getattr(instr, 'result', None)
        if result_var:
            self.vn.insert(expr, result_var)
        
        return instr
    
    def _find_result_var(self, value_number: int) -> Optional[str]:
        """找到值编号对应的变量"""
        for var, vn in self.vn.var_value_map.items():
            if vn == value_number:
                return var
        return None
    
    def _create_reuse_instruction(self, instr, new_var: str):
        """创建复用指令（通常是mov）"""
        return type('Instruction', (), {
            'opcode': 'mov',
            'result': getattr(instr, 'result', None),
            'arg1': new_var,
            'arg2': None
        })()


class HashValueNumbering:
    """
    基于哈希的Value Numbering
    改进版，处理更大规模的代码
    """
    
    def __init__(self, hash_size: int = 1024):
        self.hash_table: List[List[Tuple[Expression, int]]] = [[] for _ in range(hash_size)]
        self.hash_size = hash_size
        self.value_numbers: Dict[int, str] = {}  # vn -> result_var
        self.expr_to_vn: Dict[Expression, int] = {}
        self.next_vn = 1
    
    def _hash_expr(self, expr: Expression) -> int:
        """哈希表达式"""
        h = hash((expr.opcode, expr.arg1, expr.arg2))
        return abs(h) % self.hash_size
    
    def lookup_or_insert(self, expr: Expression, result_var: str) -> Tuple[int, bool]:
        """
        查找或插入表达式
        返回: (value_number, is_new)
        """
        bucket_idx = self._hash_expr(expr)
        bucket = self.hash_table[bucket_idx]
        
        # 查找
        for existing_expr, vn in bucket:
            if existing_expr == expr:
                return (vn, False)
        
        # 插入
        vn = self.next_vn
        self.next_vn += 1
        
        bucket.append((expr, vn))
        self.value_numbers[vn] = result_var
        self.expr_to_vn[expr] = vn
        
        return (vn, True)


class LocalCSE:
    """
    局部公共子表达式消除（Local CSE）
    在基本块内消除
    """
    
    def __init__(self):
        self.expr_map: Dict[Expression, str] = {}  # expr -> result_var
    
    def process_block(self, instructions: List) -> List:
        """处理基本块"""
        result = []
        self.expr_map.clear()
        
        for instr in instructions:
            expr = self._make_expr(instr)
            
            if expr and instr.result:
                if expr in self.expr_map:
                    # 公共子表达式，复用
                    old_var = self.expr_map[expr]
                    result.append(self._make_mov(instr.result, old_var))
                else:
                    # 新表达式
                    self.expr_map[expr] = instr.result
                    result.append(instr)
            else:
                result.append(instr)
        
        return result
    
    def _make_expr(self, instr) -> Optional[Expression]:
        """从指令创建表达式"""
        opcode = getattr(instr, 'opcode', None)
        arg1 = getattr(instr, 'arg1', None)
        arg2 = getattr(instr, 'arg2', None)
        
        if not opcode or not arg1:
            return None
        
        return Expression(opcode=opcode, arg1=arg1, arg2=arg2)
    
    def _make_mov(self, result: str, arg: str):
        """创建mov指令"""
        return type('Instruction', (), {
            'opcode': 'mov',
            'result': result,
            'arg1': arg,
            'arg2': None
        })()


class GlobalCSE:
    """
    全局公共子表达式消除（Global CSE）
    跨基本块消除
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.available_exprs: Dict[str, Dict[Expression, str]] = {}  # block -> (expr -> result)
        self.local_cse = LocalCSE()
    
    def compute_available_expressions(self):
        """计算每个块的可用表达式"""
        # 使用数据流分析
        # OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])
        
        for block in self.cfg.blocks:
            available = {}
            
            # GEN[B]: 当前块新产生的表达式
            for instr in block.instructions:
                expr = self._make_expr(instr)
                if expr and instr.result:
                    available[expr] = instr.result
            
            # 从前驱继承
            for pred in block.predecessors:
                pred_avail = self.available_exprs.get(pred.label, {})
                for expr, result in pred_avail.items():
                    if expr not in available:
                        available[expr] = result
            
            self.available_exprs[block.label] = available
    
    def _make_expr(self, instr) -> Optional[Expression]:
        """创建表达式"""
        opcode = getattr(instr, 'opcode', None)
        arg1 = getattr(instr, 'arg1', None)
        arg2 = getattr(instr, 'arg2', None)
        
        if not opcode or not arg1:
            return None
        
        return Expression(opcode=opcode, arg1=arg1, arg2=arg2)
    
    def optimize(self) -> 'GlobalCSE':
        """执行全局CSE"""
        self.compute_available_expressions()
        
        for block in self.cfg.blocks:
            new_instrs = []
            
            for instr in block.instructions:
                expr = self._make_expr(instr)
                
                if expr and instr.result:
                    # 检查是否有可用的公共表达式
                    for pred in block.predecessors:
                        pred_avail = self.available_exprs.get(pred.label, {})
                        if expr in pred_avail:
                            old_result = pred_avail[expr]
                            new_instrs.append(self._make_mov(instr.result, old_result))
                            break
                    else:
                        new_instrs.append(instr)
                else:
                    new_instrs.append(instr)
            
            block.instructions = new_instrs
        
        return self


if __name__ == "__main__":
    print("=" * 60)
    print("公共子表达式消除（CSE）演示")
    print("=" * 60)
    
    # 模拟指令
    class Instr:
        def __init__(self, opcode, result=None, arg1=None, arg2=None):
            self.opcode = opcode
            self.result = result
            self.arg1 = arg1
            self.arg2 = arg2
        
        def __repr__(self):
            if self.arg1 and self.arg2:
                return f"{self.result} = {self.arg1} {self.opcode} {self.arg2}"
            elif self.arg1:
                return f"{self.result} = {self.arg1}"
            return f"{self.opcode}"
    
    instructions = [
        Instr("add", "t0", "a", "b"),   # t0 = a + b
        Instr("add", "t1", "a", "b"),   # t1 = a + b  <- 公共子表达式
        Instr("sub", "t2", "t0", "c"),  # t2 = t0 - c
        Instr("sub", "t3", "t1", "c"),  # t3 = t1 - c  <- 可以复用t0
        Instr("mul", "t4", "t0", "t1"), # t4 = t0 * t1
    ]
    
    print("\n原代码:")
    for instr in instructions:
        print(f"  {instr}")
    
    print("\n--- Value Numbering ---")
    cse = CommonSubexpressionEliminator()
    optimized = cse.eliminate(instructions)
    
    print("优化后:")
    for instr in optimized:
        print(f"  {instr}")
    
    print(f"\n消除的公共子表达式数: {cse.eliminated_count}")
    print(f"替换: {cse.replacements}")
    
    # 局部CSE示例
    print("\n--- 局部CSE ---")
    local = LocalCSE()
    
    local_instrs = [
        Instr("add", "x", "a", "b"),
        Instr("add", "y", "a", "b"),  # 可以复用x
        Instr("add", "z", "x", "y"),  # 可以复用前面的计算
    ]
    
    print("优化前:")
    for instr in local_instrs:
        print(f"  {instr}")
    
    result = local.process_block(local_instrs)
    
    print("\n优化后:")
    for instr in result:
        print(f"  {instr}")
    
    print("\nValue Numbering算法:")
    print("  1. 维护表达式 -> 值编号的映射")
    print("  2. 遇到新表达式，分配新编号")
    print("  3. 遇到已有表达式，复用之前的计算结果")
    print("  4. 需要处理变量重命名（SSA形式）")
    
    print("\nCSE优势:")
    print("  - 避免重复计算")
    print("  - 减少指令数")
    print("  - 降低功耗")
    print("  - 改善代码大小")
