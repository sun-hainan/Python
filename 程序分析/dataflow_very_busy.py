# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / dataflow_very_busy

本文件实现 dataflow_very_busy 相关的算法功能。
"""

from typing import Dict, List, Set, Optional
from collections import defaultdict


class VeryBusyExpressions:
    """
    非常忙表达式分析器
    
    使用反向数据流分析计算每个基本块的非常忙表达式集合。
    """
    
    def __init__(self, num_blocks: int):
        """
        初始化非常忙表达式分析器
        
        Args:
            num_blocks: 基本块数量
        """
        self.num_blocks = num_blocks
        # USE集合：块中使用的表达式（不是生成，而是使用）
        self.use: Dict[int, Set['Expression']] = {i: set() for i in range(num_blocks)}
        # KILL集合：块中杀死的表达式（操作数被重新定义）
        self.kill: Dict[int, Set['Expression']] = {i: set() for i in range(num_blocks)}
        # 每个块的IN集合
        self.in_set: Dict[int, Set['Expression']] = {i: set() for i in range(num_blocks)}
        # 每个块的OUT集合
        self.out_set: Dict[int, Set['Expression']] = {i: set() for i in range(num_blocks)}
        # 后继关系
        self.successors: Dict[int, List[int]] = defaultdict(list)
        # 全局表达式集合
        self.all_expressions: Set['Expression'] = set()
    
    def add_expression(self, expr: 'Expression'):
        """添加表达式到全局集合"""
        self.all_expressions.add(expr)
    
    def add_use(self, block_id: int, expr: 'Expression'):
        """
        添加表达式到块的USE集合
        
        Args:
            block_id: 基本块ID
            expr: 表达式
        """
        self.use[block_id].add(expr)
        self.all_expressions.add(expr)
    
    def add_kill(self, block_id: int, expr: 'Expression'):
        """
        添加表达式到块的KILL集合
        
        Args:
            block_id: 基本块ID
            expr: 表达式
        """
        self.kill[block_id].add(expr)
    
    def set_successors(self, successors: Dict[int, List[int]]):
        """
        设置每个基本块的后继块列表
        
        Args:
            successors: block_id -> [successor_block_ids]
        """
        self.successors = successors
    
    def analyze(self, max_iterations: int = 100) -> bool:
        """
        执行非常忙表达式分析迭代
        
        使用反向数据流：
        - OUT[B] = USE[B] ∪ (IN[B] - KILL[B])
        - IN[B] = ∩_{S∈succ(B)} OUT[S]
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            是否在有限次迭代内收敛
        """
        iteration = 0
        changed = True
        
        # 初始化OUT为全集（悲观假设）
        for block_id in range(self.num_blocks):
            self.out_set[block_id] = self.all_expressions.copy()
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            # 反向遍历
            for block_id in range(self.num_blocks - 1, -1, -1):
                # 计算OUT[B] = USE[B] ∪ (IN[B] - KILL[B])
                new_out = self.use[block_id] | (self.in_set[block_id] - self.kill[block_id])
                
                if new_out != self.out_set[block_id]:
                    self.out_set[block_id] = new_out
                    changed = True
                
                # 计算IN[B] = ∩_{S∈succ(B)} OUT[S]
                succs = self.successors.get(block_id, [])
                
                if not succs:
                    # 没有后继，IN等于USE（假设出口会使用所有USE）
                    new_in = self.use[block_id].copy()
                else:
                    # 取所有后继OUT的交集
                    new_in = None
                    for succ_id in succs:
                        succ_out = self.out_set[succ_id]
                        if new_in is None:
                            new_in = succ_out.copy()
                        else:
                            new_in &= succ_out
                    
                    if new_in is None:
                        new_in = set()
                
                if new_in != self.in_set[block_id]:
                    self.in_set[block_id] = new_in
                    changed = True
        
        return iteration < max_iterations
    
    def get_very_busy_in(self, block_id: int) -> Set['Expression']:
        """
        获取基本块入口的非常忙表达式
        
        Args:
            block_id: 基本块ID
            
        Returns:
            非常忙表达式集合
        """
        return self.in_set[block_id].copy()
    
    def get_very_busy_out(self, block_id: int) -> Set['Expression']:
        """
        获取基本块出口的非常忙表达式
        
        Args:
            block_id: 基本块ID
            
        Returns:
            非常忙表达式集合
        """
        return self.out_set[block_id].copy()
    
    def is_very_busy(self, block_id: int, expr: 'Expression', at_entry: bool = True) -> bool:
        """
        检查表达式是否在基本块某点非常忙
        
        Args:
            block_id: 基本块ID
            expr: 表达式
            at_entry: 是否在入口检查（False则在出口）
            
        Returns:
            如果非常忙返回True
        """
        target_set = self.in_set if at_entry else self.out_set
        return expr in target_set[block_id]
    
    def display_results(self):
        """打印分析结果"""
        print("=" * 60)
        print("Very Busy Expressions Analysis Results")
        print("=" * 60)
        
        for block_id in range(self.num_blocks):
            use_exprs = [str(e) for e in sorted(self.use[block_id], key=str)]
            kill_exprs = [str(e) for e in sorted(self.kill[block_id], key=str)]
            in_exprs = [str(e) for e in sorted(self.in_set[block_id], key=str)]
            out_exprs = [str(e) for e in sorted(self.out_set[block_id], key=str)]
            
            print(f"\nBlock {block_id}:")
            print(f"  USE:  {{{', '.join(use_exprs) if use_exprs else 'empty}'}}}")
            print(f"  KILL: {{{', '.join(kill_exprs) if kill_exprs else 'empty}'}}}")
            print(f"  IN:   {{{', '.join(in_exprs) if in_exprs else 'empty}'}}}")
            print(f"  OUT:  {{{', '.join(out_exprs) if out_exprs else 'empty}'}}}")


class Expression:
    """表达式类（简化版）"""
    
    def __init__(self, op: str, left: str, right: str):
        self.op = op
        self.left = left
        self.right = right
    
    def __str__(self) -> str:
        return f"({self.left} {self.op} {self.right})"
    
    def __hash__(self) -> int:
        return hash((self.op, self.left, self.right))
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Expression):
            return self.op == other.op and self.left == other.left and self.right == other.right
        return False


def create_placement_example():
    """
    创建代码placement优化示例
    
    程序：
        x = a + b  # 在块中使用表达式
        y = x * 2
        z = a + b  # 再次使用
        return y + z
    
    非常忙表达式分析可以帮助决定是否应该将(a+b)的结果保存起来。
    """
    analyzer = VeryBusyExpressions(num_blocks=3)
    
    expr_ab = Expression('+', 'a', 'b')
    
    # Block 0: x = a + b; y = x * 2
    # 表达式(a+b)在这里被使用
    analyzer.add_use(0, expr_ab)
    
    # Block 1: z = a + b
    # 表达式(a+b)在这里也被使用
    analyzer.add_use(1, expr_ab)
    
    # Block 2: return y + z
    analyzer.add_use(2, expr_ab)
    
    # 设置后继关系
    analyzer.set_successors({
        0: [1],
        1: [2],
        2: []
    })
    
    return analyzer


if __name__ == "__main__":
    print("=" * 60)
    print("测试：非常忙表达式分析")
    print("=" * 60)
    
    analyzer = create_placement_example()
    converged = analyzer.analyze()
    
    print(f"\n迭代收敛: {converged}")
    analyzer.display_results()
    
    print("\n" + "=" * 60)
    print("表达式非常忙性分析")
    print("=" * 60)
    
    expr_ab = Expression('+', 'a', 'b')
    
    print(f"\n表达式 (a+b) 的非常忙性:")
    for block_id in range(3):
        in_busy = analyzer.is_very_busy(block_id, expr_ab, at_entry=True)
        out_busy = analyzer.is_very_busy(block_id, expr_ab, at_entry=False)
        print(f"  Block {block_id}:")
        print(f"    入口: {'非常忙' if in_busy else '不忙'}")
        print(f"    出口: {'非常忙' if out_busy else '不忙'}")
    
    print("\n非常忙表达式分析测试完成!")
    print("\n应用场景：")
    print("  1. 代码 placement 优化：将表达式计算移到使用点之前")
    print("  2. 寄存器分配：决定哪些表达式应该保持在寄存器中")
    print("  3. 死代码消除：非常忙但未被使用的表达式可能有问题")
