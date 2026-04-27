# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / dataflow_liveness

本文件实现 dataflow_liveness 相关的算法功能。
"""

from typing import Dict, List, Set, Optional
from collections import defaultdict


class LivenessAnalyzer:
    """
    活跃变量分析器
    
    使用反向数据流分析，从程序出口向入口迭代计算：
    - IN[B] = USE[B] ∪ (OUT[B] - DEF[B])
    - OUT[B] = ∪_{S∈succ(B)} IN[S]
    
    其中：
    - USE[B]：块B中在重新定义前使用的变量集合
    - DEF[B]：块B中定义的变量集合（定值）
    """
    
    def __init__(self, num_blocks: int):
        """
        初始化活跃变量分析器
        
        Args:
            num_blocks: 程序中基本块的数量
        """
        self.num_blocks = num_blocks
        # 每个块的USE集合：block_id -> {variables}
        self.use: Dict[int, Set[str]] = {i: set() for i in range(num_blocks)}
        # 每个块的DEF集合：block_id -> {variables}
        self.def_set: Dict[int, Set[str]] = {i: set() for i in range(num_blocks)}
        # 每个块的IN集合
        self.in_set: Dict[int, Set[str]] = {i: set() for i in range(num_blocks)}
        # 每个块的OUT集合
        self.out_set: Dict[int, Set[str]] = {i: set() for i in range(num_blocks)}
        # 后继关系
        self.successors: Dict[int, List[int]] = {}
    
    def add_use(self, block_id: int, variable: str):
        """
        添加一个变量使用到块的USE集合
        
        Args:
            block_id: 基本块ID
            variable: 变量名
        """
        self.use[block_id].add(variable)
    
    def add_def(self, block_id: int, variable: str):
        """
        添加一个变量定义到块的DEF集合
        
        Args:
            block_id: 基本块ID
            variable: 变量名
        """
        self.def_set[block_id].add(variable)
    
    def set_successors(self, successors: Dict[int, List[int]]):
        """
        设置每个基本块的后继块列表
        
        Args:
            successors: block_id -> [successor_block_ids]
        """
        self.successors = successors
    
    def analyze(self, max_iterations: int = 100) -> bool:
        """
        执行活跃变量分析迭代
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            是否在有限次迭代内收敛
        """
        iteration = 0
        changed = True
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            # 反向遍历（从后往前）
            for block_id in range(self.num_blocks - 1, -1, -1):
                # 计算OUT[B] = ∪_{S∈succ(B)} IN[S]
                new_out: Set[str] = set()
                for succ_id in self.successors.get(block_id, []):
                    new_out |= self.in_set[succ_id]
                
                if new_out != self.out_set[block_id]:
                    self.out_set[block_id] = new_out
                    changed = True
                
                # 计算IN[B] = USE[B] ∪ (OUT[B] - DEF[B])
                # 只有当变量在OUT中但不在DEF中时，它才是活跃的
                new_in = self.use[block_id] | (self.out_set[block_id] - self.def_set[block_id])
                
                if new_in != self.in_set[block_id]:
                    self.in_set[block_id] = new_in
                    changed = True
        
        return iteration < max_iterations
    
    def get_live_in(self, block_id: int) -> Set[str]:
        """
        获取进入指定基本块时活跃的变量集合
        
        Args:
            block_id: 基本块ID
            
        Returns:
            活跃变量集合
        """
        return self.in_set[block_id].copy()
    
    def get_live_out(self, block_id: int) -> Set[str]:
        """
        获取离开指定基本块时活跃的变量集合
        
        Args:
            block_id: 基本块ID
            
        Returns:
            活跃变量集合
        """
        return self.out_set[block_id].copy()
    
    def get_register_pressure(self, block_id: int) -> int:
        """
        估算基本块的寄存器压力（即需要同时活跃的变量数量）
        
        用于寄存器分配决策。
        
        Args:
            block_id: 基本块ID
            
        Returns:
            活跃变量数量
        """
        return len(self.in_set[block_id] | self.out_set[block_id])
    
    def display_results(self):
        """打印分析结果（用于调试）"""
        print("=" * 60)
        print("Liveness Analysis Results")
        print("=" * 60)
        
        for block_id in range(self.num_blocks):
            live_in = sorted(self.in_set[block_id])
            live_out = sorted(self.out_set[block_id])
            use_vars = sorted(self.use[block_id])
            def_vars = sorted(self.def_set[block_id])
            
            print(f"\nBlock {block_id}:")
            print(f"  USE:  {{{', '.join(use_vars) if use_vars else 'empty}'}}}")
            print(f"  DEF:  {{{', '.join(def_vars) if def_vars else 'empty}'}}}")
            print(f"  IN:   {{{', '.join(live_in) if live_in else 'empty}'}}}")
            print(f"  OUT:  {{{', '.join(live_out) if live_out else 'empty}'}}}")


def create_loop_example():
    """
    创建循环程序示例用于测试
    
    程序示例：
        i = 0
        sum = 0
    loop:
        if i >= 10: goto exit
        sum = sum + i
        i = i + 1
        goto loop
    exit:
        return sum
    
    这个例子展示循环中活跃变量的传播：
    - i在循环入口是活跃的（因为条件判断需要它）
    - sum在循环中始终活跃（每次迭代都被使用和更新）
    """
    analyzer = LivenessAnalyzer(num_blocks=5)
    
    # Block 0: i = 0
    # 定义i，使用无
    analyzer.add_def(0, "i")
    
    # Block 1: sum = 0
    # 定义sum，使用无
    analyzer.add_def(1, "sum")
    
    # Block 2: if i >= 10 goto exit
    # 使用i进行条件判断，定义无
    analyzer.add_use(2, "i")
    
    # Block 3: sum = sum + i; i = i + 1
    # 使用sum和i，定义sum和i
    analyzer.add_use(3, "sum")
    analyzer.add_use(3, "i")
    analyzer.add_def(3, "sum")
    analyzer.add_def(3, "i")
    
    # Block 4: return sum
    # 使用sum
    analyzer.add_use(4, "sum")
    
    # CFG结构：
    #   [0] -> [1] -> [2] -> [3] -> (goto [2])
    #                    |
    #                    v
    #                   [4]
    
    analyzer.set_successors({
        0: [1],
        1: [2],
        2: [3, 4],   # 条件跳转：then分支到3，else分支到4
        3: [2],      # 循环回到2
        4: []        # 出口块
    })
    
    return analyzer


def create_branch_example():
    """
    创建分支程序示例用于测试
    
    程序示例：
        a = input()
        if a > 0:
            b = a * 2
        else:
            c = a * 3
        d = b + c  # 这里b或c只有一个是活跃的
    
    活跃分析结果：
    - d使用之前，b和c都是活跃的（但不知道哪个有值）
    - 这是活跃变量分析的保守性：假设两者都可能需要
    """
    analyzer = LivenessAnalyzer(num_blocks=4)
    
    # Block 0: a = input()
    analyzer.add_def(0, "a")
    
    # Block 1: b = a * 2 (then分支)
    analyzer.add_use(1, "a")
    analyzer.add_def(1, "b")
    
    # Block 2: c = a * 3 (else分支)
    analyzer.add_use(2, "a")
    analyzer.add_def(2, "c")
    
    # Block 3: d = b + c
    analyzer.add_use(3, "b")
    analyzer.add_use(3, "c")
    analyzer.add_def(3, "d")
    
    # CFG结构：
    #      [0]
    #    /     \
    # [1]     [2]
    #    \     /
    #     [3]
    
    analyzer.set_successors({
        0: [1, 2],
        1: [3],
        2: [3],
        3: []
    })
    
    return analyzer


if __name__ == "__main__":
    print("=" * 60)
    print("测试1：循环程序的活跃变量分析")
    print("=" * 60)
    
    analyzer = create_loop_example()
    converged = analyzer.analyze()
    
    print(f"\n迭代收敛: {converged}")
    analyzer.display_results()
    
    print("\n寄存器压力分析:")
    for block_id in range(analyzer.num_blocks):
        pressure = analyzer.get_register_pressure(block_id)
        print(f"  Block {block_id}: {pressure} registers needed")
    
    print("\n" + "=" * 60)
    print("测试2：分支程序的活跃变量分析")
    print("=" * 60)
    
    analyzer2 = create_branch_example()
    converged2 = analyzer2.analyze()
    
    print(f"\n迭代收敛: {converged2}")
    analyzer2.display_results()
    
    print("\n分析说明:")
    print("  分支示例中，Block 3的IN包含b和c，")
    print("  即使我们知道只有其中一个会被定义。")
    print("  这是活跃分析的保守性假设。")
    
    print("\n活跃变量分析测试完成!")
