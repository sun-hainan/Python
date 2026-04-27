# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / ir_generation

本文件实现 ir_generation 相关的算法功能。
"""

from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid

# ========== 三地址码（TAC） ==========

class Opcode(Enum):
    """三地址码操作码"""
    # 算术运算
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    NEG = "neg"
    
    # 比较运算
    CMP = "cmp"
    JMP = "jmp"
    JE = "je"      # ==
    JNE = "jne"    # !=
    JL = "jl"      # <
    JLE = "jle"    # <=
    JG = "jg"      # >
    JGE = "jge"    # >=
    
    # 内存访问
    LOAD = "load"
    STORE = "store"
    LOAD_ADDR = "lea"  # 取地址
    
    # 函数调用
    CALL = "call"
    RET = "ret"
    PARAM = "param"
    CALL_RESULT = "callresult"
    
    # 逻辑运算
    AND = "and"
    OR = "or"
    NOT = "not"
    
    # 类型转换
    I2F = "i2f"    # int to float
    F2I = "f2i"    # float to int
    
    # 其他
    ASSIGN = "assign"
    PHI = "phi"    # SSA形式
    NOP = "nop"


@dataclass
class TACInstruction:
    """三地址码指令"""
    opcode: Opcode
    result: Optional[str] = None   # 目标（变量）
    arg1: Optional[str] = None     # 操作数1
    arg2: Optional[str] = None     # 操作数2
    label: Optional[str] = None    # 跳转标签
    comment: str = ""
    
    def __repr__(self):
        parts = []
        
        if self.label:
            parts.append(f"{self.label}:")
        
        if self.result:
            if self.arg1 and self.arg2:
                parts.append(f"{self.result} = {self.arg1} {self.opcode.value} {self.arg2}")
            elif self.arg1:
                if self.opcode == Opcode.NEG:
                    parts.append(f"{self.result} = -{self.arg1}")
                elif self.opcode == Opcode.NOT:
                    parts.append(f"{self.result} = not {self.arg1}")
                else:
                    parts.append(f"{self.result} = {self.opcode.value} {self.arg1}")
            else:
                parts.append(f"{self.result} = {self.opcode.value}")
        elif self.opcode == Opcode.JMP:
            parts.append(f"jmp {self.label}")
        elif self.opcode == Opcode.RET:
            parts.append(f"ret {self.arg1 if self.arg1 else ''}")
        elif self.opcode == Opcode.PARAM:
            parts.append(f"param {self.arg1}")
        elif self.opcode == Opcode.CALL:
            parts.append(f"call {self.arg1}")
            if self.result:
                parts[-1] = f"{self.result} = {parts[-1]}"
        elif self.opcode == Opcode.PHI:
            parts.append(f"{self.result} = phi({', '.join(self.arg1.split(','))})")
        else:
            parts.append(str(self.opcode.value))
        
        if self.comment:
            parts.append(f"  ; {self.comment}")
        
        return " ".join(parts)


@dataclass
class BasicBlock:
    """基本块"""
    id: int
    label: str = ""
    instructions: List[TACInstruction] = field(default_factory=list)
    predecessors: List['BasicBlock'] = field(default_factory=list)
    successors: List['BasicBlock'] = field(default_factory=list)
    dominator: Optional['BasicBlock'] = None  # 支配节点
    dominated_nodes: List['BasicBlock'] = field(default_factory=list)
    
    def add_instruction(self, instr: TACInstruction):
        self.instructions.append(instr)
    
    def is_empty(self) -> bool:
        return len(self.instructions) == 0


class ControlFlowGraph:
    """
    控制流图（CFG）
    表示程序的控制流结构
    """
    
    def __init__(self, function_name: str = ""):
        self.function_name = function_name
        self.blocks: List[BasicBlock] = []
        self.entry_block: Optional[BasicBlock] = None
        self.exit_block: Optional[BasicBlock] = None
        self.block_map: Dict[str, BasicBlock] = {}  # label -> block
        self.next_block_id = 0
    
    def create_block(self, label: str = "") -> BasicBlock:
        """创建新基本块"""
        block = BasicBlock(
            id=self.next_block_id,
            label=label or f"block_{self.next_block_id}"
        )
        self.next_block_id += 1
        self.blocks.append(block)
        
        if label:
            self.block_map[label] = block
        
        return block
    
    def add_edge(self, from_block: BasicBlock, to_block: BasicBlock):
        """添加控制流边"""
        if to_block not in from_block.successors:
            from_block.successors.append(to_block)
        if from_block not in to_block.predecessors:
            to_block.predecessors.append(from_block)
    
    def get_block_by_label(self, label: str) -> Optional[BasicBlock]:
        """通过标签获取基本块"""
        return self.block_map.get(label)
    
    def compute_dominators(self):
        """
        计算支配关系
        使用数据流算法
        """
        if not self.entry_block or not self.blocks:
            return
        
        # 初始化：所有节点的支配集为所有节点
        doms: Dict[int, Set[int]] = {}
        for block in self.blocks:
            doms[block.id] = set(b.id for b in self.blocks)
        
        # 入口节点的支配集只有自己
        doms[self.entry_block.id] = {self.entry_block.id}
        
        # 迭代直到收敛
        changed = True
        iterations = 0
        while changed and iterations < 100:
            changed = False
            iterations += 1
            
            for block in self.blocks:
                if block == self.entry_block:
                    continue
                
                # D(n) = {n} ∪ (∩ D(p) for p in predecessors)
                new_doms = {block.id}
                
                for pred in block.predecessors:
                    new_doms &= doms[pred.id]
                
                new_doms.add(block.id)
                
                if new_doms != doms[block.id]:
                    doms[block.id] = new_doms
                    changed = True
        
        # 设置支配节点
        for block in self.blocks:
            # 找到最大的支配节点（不是自己）
            block_doms = doms[block.id] - {block.id}
            if block_doms:
                # 选择最近支配节点
                for pred in block.predecessors:
                    if pred.id in block_doms:
                        block.dominator = pred
                        if block not in pred.dominated_nodes:
                            pred.dominated_nodes.append(block)
                        break
    
    def compute_rpo(self) -> List[int]:
        """
        计算反向后序（Reverse Post Order）
        用于CFG遍历
        """
        visited = set()
        order = []
        
        def dfs(block: BasicBlock):
            visited.add(block.id)
            for succ in block.successors:
                if succ.id not in visited:
                    dfs(succ)
            order.append(block.id)
        
        if self.entry_block:
            dfs(self.entry_block)
        
        return list(reversed(order))
    
    def find_loops(self) -> List[Tuple[BasicBlock, BasicBlock]]:
        """
        找出CFG中的循环
        返回: [(循环头, 回边来源), ...]
        """
        loops = []
        
        for block in self.blocks:
            for succ in block.successors:
                # 如果后继节点能到达当前节点，则存在回边
                if self._can_reach(succ, block):
                    loops.append((succ, block))
        
        return loops
    
    def _can_reach(self, from_block: BasicBlock, to_block: BasicBlock) -> bool:
        """检查from_block是否能到达to_block"""
        visited = set()
        stack = [from_block]
        
        while stack:
            block = stack.pop()
            if block == to_block:
                return True
            if block.id in visited:
                continue
            visited.add(block.id)
            stack.extend(block.successors)
        
        return False


# ========== IR生成器 ==========

class IRGenerator:
    """
    IR生成器
    将AST转换为三地址码
    """
    
    def __init__(self):
        self.cfg: Optional[ControlFlowGraph] = None
        self.current_block: Optional[BasicBlock] = None
        self.temp_counter = 0
        self.label_counter = 0
        self.instructions: List[TACInstruction] = []
    
    def new_temp(self) -> str:
        """生成新的临时变量"""
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def new_label(self) -> str:
        """生成新的标签"""
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def emit(self, opcode: Opcode, result: str = None, 
             arg1: str = None, arg2: str = None, comment: str = "") -> str:
        """发射TAC指令"""
        instr = TACInstruction(
            opcode=opcode,
            result=result,
            arg1=arg1,
            arg2=arg2,
            comment=comment
        )
        
        if self.current_block:
            self.current_block.add_instruction(instr)
        else:
            self.instructions.append(instr)
        
        return result if result else ""
    
    def generate(self, ast: Dict) -> ControlFlowGraph:
        """从AST生成IR"""
        self.cfg = ControlFlowGraph()
        self.instructions = []
        
        entry = self.cfg.create_block("entry")
        self.cfg.entry_block = entry
        self.current_block = entry
        
        self._generate_block(ast)
        
        # 添加退出块
        exit_block = self.cfg.create_block("exit")
        self.cfg.exit_block = exit_block
        self.add_edge(self.current_block, exit_block)
        
        return self.cfg
    
    def _generate_block(self, node: Dict):
        """生成单个基本块的指令"""
        if not node:
            return
        
        node_type = node.get('type', '')
        
        if node_type == 'Program':
            for stmt in node.get('body', []):
                self._generate_block(stmt)
        
        elif node_type == 'FunctionDeclaration':
            self._generate_function(node)
        
        elif node_type == 'BinaryExpression':
            result = self._generate_expr(node)
            return result
        
        elif node_type == 'AssignmentExpression':
            result = self._generate_expr(node.get('right', {}))
            # store result to left
            self.emit(Opcode.ASSIGN, node.get('left', {}).get('name', ''), result)
        
        elif node_type == 'ReturnStatement':
            value = node.get('value', {})
            if value:
                result = self._generate_expr(value)
                self.emit(Opcode.RET, arg1=result)
            else:
                self.emit(Opcode.RET)
        
        elif node_type == 'IfStatement':
            self._generate_if(node)
        
        elif node_type == 'WhileStatement':
            self._generate_while(node)
        
        return None
    
    def _generate_expr(self, node: Dict) -> str:
        """生成表达式TAC"""
        node_type = node.get('type', '')
        
        if node_type == 'BinaryExpression':
            left = self._generate_expr(node.get('left', {}))
            right = self._generate_expr(node.get('right', {}))
            result = self.new_temp()
            
            op = node.get('operator', '')
            op_map = {
                '+': Opcode.ADD,
                '-': Opcode.SUB,
                '*': Opcode.MUL,
                '/': Opcode.DIV,
                '==': Opcode.CMP,
                '!=': Opcode.CMP,
                '<': Opcode.CMP,
                '>': Opcode.CMP,
            }
            
            opcode = op_map.get(op, Opcode.ADD)
            self.emit(opcode, result, left, right)
            return result
        
        elif node_type == 'Literal':
            return str(node.get('value', ''))
        
        elif node_type == 'Identifier':
            return node.get('name', '')
        
        elif node_type == 'CallExpression':
            callee = node.get('callee', {}).get('name', '')
            
            for arg in node.get('arguments', []):
                arg_result = self._generate_expr(arg)
                self.emit(Opcode.PARAM, arg1=arg_result)
            
            self.emit(Opcode.CALL, arg1=callee)
            result = self.new_temp()
            self.emit(Opcode.CALL_RESULT, result=result, arg1=callee)
            return result
        
        return self.new_temp()
    
    def _generate_function(self, node: Dict):
        """生成函数TAC"""
        # 创建函数入口块
        func_name = node.get('name', '')
        entry = self.cfg.create_block(f"{func_name}_entry")
        
        # 连接前一个块到函数入口
        if self.current_block and self.current_block.successors:
            pass  # 处理跳转
        
        self.current_block = entry
        
        # 处理参数
        for param in node.get('params', []):
            pass  # 参数处理
        
        # 处理函数体
        for stmt in node.get('body', []):
            self._generate_block(stmt)
    
    def _generate_if(self, node: Dict):
        """生成if语句TAC"""
        condition = node.get('condition', {})
        then_block = self.cfg.create_block(self.new_label())
        else_block = self.cfg.create_block(self.new_label())
        merge_block = self.cfg.create_block(self.new_label())
        
        # 条件跳转
        cond_result = self._generate_expr(condition)
        self.emit(Opcode.JE, arg1=cond_result, arg2="0", label=else_block.label)
        
        # then分支
        old_block = self.current_block
        self.current_block = then_block
        self._generate_block(node.get('consequent', {}))
        self.add_edge(self.current_block, merge_block)
        
        # else分支
        self.current_block = else_block
        if node.get('alternate'):
            self._generate_block(node.get('alternate'))
        self.add_edge(self.current_block, merge_block)
        
        self.current_block = merge_block
    
    def _generate_while(self, node: Dict):
        """生成while语句TAC"""
        loop_header = self.cfg.create_block(self.new_label())
        loop_body = self.cfg.create_block(self.new_label())
        loop_exit = self.cfg.create_block(self.new_label())
        
        # 跳到循环头
        self.emit(Opcode.JMP, label=loop_header.label)
        
        # 循环头：条件判断
        self.current_block = loop_header
        cond_result = self._generate_expr(node.get('condition', {}))
        self.emit(Opcode.JE, arg1=cond_result, arg2="0", label=loop_exit.label)
        
        # 循环体
        self.current_block = loop_body
        self._generate_block(node.get('body', {}))
        self.emit(Opcode.JMP, label=loop_header.label)
        self.add_edge(self.current_block, loop_header)
        
        # 循环出口
        self.current_block = loop_exit
    
    def add_edge(self, from_block: BasicBlock, to_block: BasicBlock):
        """添加边"""
        if from_block and to_block:
            self.cfg.add_edge(from_block, to_block)


if __name__ == "__main__":
    print("=" * 60)
    print("中间表示（IR）演示")
    print("=" * 60)
    
    # 生成测试IR
    gen = IRGenerator()
    
    # 模拟简单函数的IR
    cfg = ControlFlowGraph("add")
    
    entry = cfg.create_block("entry")
    cfg.entry_block = entry
    
    # t0 = 10
    entry.add_instruction(TACInstruction(Opcode.ASSIGN, "t0", arg1="10"))
    # t1 = 20
    entry.add_instruction(TACInstruction(Opcode.ASSIGN, "t1", arg1="20"))
    # t2 = t0 + t1
    entry.add_instruction(TACInstruction(Opcode.ADD, "t2", "t0", "t1"))
    
    # if t2 > 30
    cond_block = cfg.create_block("cond")
    cond_block.add_instruction(TACInstruction(Opcode.CMP, "t3", "t2", "30"))
    cond_block.add_instruction(TACInstruction(Opcode.JG, label="then"))
    
    # else
    else_block = cfg.create_block("else")
    else_block.add_instruction(TACInstruction(Opcode.ASSIGN, "t4", arg1="100"))
    
    # then
    then_block = cfg.create_block("then")
    then_block.add_instruction(TACInstruction(Opcode.ASSIGN, "t4", arg1="200"))
    
    merge_block = cfg.create_block("merge")
    merge_block.add_instruction(TACInstruction(Opcode.RET, arg1="t4"))
    
    exit_block = cfg.create_block("exit")
    
    # 添加边
    cfg.add_edge(entry, cond_block)
    cfg.add_edge(cond_block, then_block)
    cfg.add_edge(cond_block, else_block)
    cfg.add_edge(then_block, merge_block)
    cfg.add_edge(else_block, merge_block)
    cfg.add_edge(merge_block, exit_block)
    
    # 打印CFG
    print("\n控制流图:")
    print(f"  函数: {cfg.function_name}")
    print(f"  块数: {len(cfg.blocks)}")
    
    for block in cfg.blocks:
        print(f"\n  基本块 {block.id} ({block.label}):")
        print(f"    前驱: {[b.id for b in block.predecessors]}")
        print(f"    后继: {[b.id for b in block.successors]}")
        for instr in block.instructions:
            print(f"    {instr}")
    
    # 计算支配关系
    print("\n支配关系:")
    cfg.compute_dominators()
    for block in cfg.blocks:
        if block.dominator:
            print(f"  Block {block.id} 支配于 Block {block.dominator.id}")
        else:
            print(f"  Block {block.id} 是入口节点")
    
    # 打印三地址码
    print("\n三地址码:")
    for block in cfg.blocks:
        for instr in block.instructions:
            print(f"  {instr}")
    
    print("\nIR作用:")
    print("  1. 简化语义：每条指令最多两个操作数，一个结果")
    print("  2. 统一表示：算术、逻辑、控制流都用指令表示")
    print("  3. 便于优化：可以在IR层面进行各种优化变换")
    print("  4. 目标代码生成：更容易映射到目标机器指令")
