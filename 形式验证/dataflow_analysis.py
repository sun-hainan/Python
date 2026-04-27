# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / dataflow_analysis

本文件实现 dataflow_analysis 相关的算法功能。
"""

import numpy as np
from collections import defaultdict


class DataFlowAnalysis:
    """
    数据流分析框架
    
    数据流分析计算程序每个点的状态信息
    """
    
    def __init__(self, cfg):
        """
        初始化
        
        参数:
            cfg: 控制流图
        """
        self.cfg = cfg  # 控制流图
        self.in_state = {}  # 每个块的输入状态
        self.out_state = {}  # 每个块的输出状态
    
    def meet(self, state1, state2):
        """
        合并操作（meet operation）
        
        子类需要实现
        """
        raise NotImplementedError
    
    def transfer(self, block, state):
        """
        转移函数
        
        子类需要实现
        """
        raise NotImplementedError
    
    def analyze(self, max_iterations=100):
        """
        迭代分析
        
        使用工作列表算法
        """
        # 初始化
        for block in self.cfg:
            self.in_state[block] = self.bottom()
            self.out_state[block] = self.top()
        
        # 工作列表
        worklist = list(self.cfg)
        
        iteration = 0
        while worklist and iteration < max_iterations:
            iteration += 1
            block = worklist.pop(0)
            
            # 合并所有前驱的输出
            new_in = self.bottom()
            for pred in self.cfg.get_predecessors(block):
                new_in = self.meet(new_in, self.out_state[pred])
            
            old_in = self.in_state[block]
            self.in_state[block] = new_in
            
            # 如果输入变化，重新计算输出
            if new_in != old_in:
                self.out_state[block] = self.transfer(block, new_in)
                
                # 后继加入工作列表
                for succ in self.cfg.get_successors(block):
                    if succ not in worklist:
                        worklist.append(succ)
        
        return iteration
    
    def bottom(self):
        """底元素（最严格的值）"""
        raise NotImplementedError
    
    def top(self):
        """顶元素（最宽松的值）"""
        raise NotImplementedError


class ReachingDefinitions(DataFlowAnalysis):
    """
    到达定义分析
    
    计算每个变量在程序的每个点有哪些赋值语句可以到达
    """
    
    def __init__(self, cfg):
        super().__init__(cfg)
        self.gen = {}  # 生成的定义
        self.kill = {}  # 消灭的定义
    
    def bottom(self):
        return set()  # 空集
    
    def top(self):
        return set()  # 也是空集，但语义不同
    
    def meet(self, state1, state2):
        """合并：并集"""
        return state1 | state2
    
    def transfer(self, block, in_state):
        """转移：(in - kill) ∪ gen"""
        killed = self.kill.get(block, set())
        generated = self.gen.get(block, set())
        return (in_state - killed) | generated


class LiveVariables(DataFlowAnalysis):
    """
    活跃变量分析
    
    计算每个点哪些变量在后续可能被使用
    """
    
    def __init__(self, cfg):
        super().__init__(cfg)
        self.defs = {}  # 块中定义的变量
        self.uses = {}  # 块中使用的变量
    
    def bottom(self):
        return set()
    
    def top(self):
        return set()
    
    def meet(self, state1, state2):
        """合并：并集（后向分析实际上用这个合并前驱）"""
        return state1 | state2
    
    def transfer(self, block, out_state):
        """转移：uses ∪ (out - defs)"""
        defined = self.defs.get(block, set())
        used = self.uses.get(block, set())
        return used | (out_state - defined)


class AvailableExpressions(DataFlowAnalysis):
    """
    可用表达式分析
    
    计算每个点哪些表达式已经计算过且可以重用
    """
    
    def __init__(self, cfg):
        super().__init__(cfg)
        self.gen = {}  # 生成的表达式
        self.kill = {}  # 杀死表达式的赋值
    
    def bottom(self):
        return set()  # 空集
    
    def top(self):
        return set()  # 全集（简化）
    
    def meet(self, state1, state2):
        """合并：交集"""
        return state1 & state2
    
    def transfer(self, block, in_state):
        """转移：(in - kill) ∪ gen"""
        killed = self.kill.get(block, set())
        generated = self.gen.get(block, set())
        return (in_state - killed) | generated


class ControlFlowGraph:
    """
    控制流图
    """
    
    def __init__(self):
        self.blocks = []  # 基本块列表
        self.pred = defaultdict(set)  # 前驱
        self.succ = defaultdict(set)  # 后继
    
    def add_block(self, block_id):
        """添加基本块"""
        if block_id not in self.blocks:
            self.blocks.append(block_id)
    
    def add_edge(self, from_block, to_block):
        """添加边"""
        self.add_block(from_block)
        self.add_block(to_block)
        self.succ[from_block].add(to_block)
        self.pred[to_block].add(from_block)
    
    def get_predecessors(self, block):
        return self.pred.get(block, set())
    
    def get_successors(self, block):
        return self.succ.get(block, set())
    
    def __iter__(self):
        return iter(self.blocks)


class BasicBlock:
    """基本块"""
    
    def __init__(self, block_id):
        self.id = block_id
        self.statements = []  # 语句列表
    
    def add_statement(self, stmt):
        self.statements.append(stmt)
    
    def __repr__(self):
        return f"Block{self.id}({len(self.statements)} stmts)"


class Statement:
    """语句"""
    
    def __init__(self, stmt_type, content):
        self.type = stmt_type  # 'assign', 'if', 'goto', 'return'
        self.content = content  # 具体内容
    
    def __repr__(self):
        return f"{self.type}: {self.content}"


def build_cfg_from_code(code):
    """
    从代码构建控制流图（简化版）
    
    参数:
        code: 语句列表
    
    返回:
        ControlFlowGraph
    """
    cfg = ControlFlowGraph()
    
    # 简化：为每条语句创建一个块
    for i, stmt in enumerate(code):
        cfg.add_block(i)
        
        if i > 0:
            cfg.add_edge(i - 1, i)
        
        # 处理控制流语句
        if isinstance(stmt, tuple):
            if stmt[0] == 'if':
                # if有两条出边
                if i + 1 < len(code):
                    cfg.add_edge(i, i + 1)
                if isinstance(stmt[1], int):
                    cfg.add_edge(i, stmt[1])
            elif stmt[0] == 'goto':
                if isinstance(stmt[1], int):
                    cfg.add_edge(i, stmt[1])
    
    return cfg


def run_demo():
    """运行数据流分析演示"""
    print("=" * 60)
    print("数据流分析框架")
    print("=" * 60)
    
    # 示例代码
    code = [
        Statement('assign', 'x = 5'),
        Statement('assign', 'y = x + 1'),
        Statement('if', 'x < 10'),
        Statement('assign', 'x = x + 1'),
        Statement('goto', 1),  # 回到y = x + 1
        Statement('assign', 'z = x'),
    ]
    
    print("\n[示例代码]")
    for i, stmt in enumerate(code):
        print(f"  {i}: {stmt}")
    
    # 构建CFG
    cfg = build_cfg_from_code(code)
    
    print("\n[控制流图]")
    print(f"  块: {cfg.blocks}")
    print(f"  边: {dict(cfg.succ)}")
    
    # 到达定义分析
    print("\n[到达定义分析]")
    
    rd = ReachingDefinitions(cfg)
    
    # 设置gen/kill
    rd.gen[0] = {'x = 5'}  # x被赋值
    rd.kill[0] = set()  # 不kill任何之前对x的定义
    
    rd.gen[1] = {'y = x + 1'}
    rd.kill[1] = set()
    
    rd.gen[2] = set()  # if语句不定义变量
    rd.kill[2] = set()
    
    rd.gen[3] = {'x = x + 1'}
    rd.kill[3] = {'x = 5'}  # kill之前的x定义
    
    rd.gen[4] = set()
    rd.kill[4] = set()
    
    rd.gen[5] = {'z = x'}
    rd.kill[5] = set()
    
    iterations = rd.analyze()
    print(f"  迭代次数: {iterations}")
    
    for block in cfg:
        print(f"  块{block}: in={rd.in_state[block]}, out={rd.out_state[block]}")
    
    # 活跃变量分析
    print("\n[活跃变量分析]")
    
    lv = LiveVariables(cfg)
    
    # 设置defs/uses
    lv.defs[0] = {'x'}
    lv.uses[0] = set()
    
    lv.defs[1] = {'y'}
    lv.uses[1] = {'x'}
    
    lv.defs[2] = set()
    lv.uses[2] = {'x'}
    
    lv.defs[3] = {'x'}
    lv.uses[3] = {'x'}
    
    lv.defs[4] = set()
    lv.uses[4] = set()
    
    lv.defs[5] = {'z'}
    lv.uses[5] = {'x'}
    
    # 反向分析（需要特殊处理）
    # 简化：只打印设置的def/use
    print(f"  定义变量: {dict(lv.defs)}")
    print(f"  使用变量: {dict(lv.uses)}")
    
    print("\n" + "=" * 60)
    print("数据流分析核心概念:")
    print("  1. 数据流分析: 静态推断程序运行时的状态")
    print("  2. 格理论: 值域构成格，用于合并操作")
    print("  3. 转移函数: 描述语句对状态的影响")
    print("  4. 到达定义: 哪些赋值可以到达某点")
    print("  5. 活跃变量: 哪些变量在后续可能被使用")
    print("  6. 可用表达式: 哪些表达式已计算过")
    print("  7. 迭代算法: 工作列表，直到收敛")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
