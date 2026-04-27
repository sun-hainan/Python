# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / ssa_construction

本文件实现 ssa_construction 相关的算法功能。
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque


class SSAVariable:
    """
    SSA变量类
    
    用于跟踪变量的版本。
    """
    
    def __init__(self, name: str, version: int = 0):
        """
        初始化SSA变量
        
        Args:
            name: 变量原名
            version: 版本号
        """
        self.name = name      # 变量名
        self.version = version  # 版本号
    
    def __repr__(self):
        return f"{self.name}.{self.version}"
    
    def __str__(self):
        return f"{self.name}.{self.version}"
    
    def __eq__(self, other):
        if isinstance(other, SSAVariable):
            return self.name == other.name and self.version == other.version
        return False
    
    def __hash__(self):
        return hash((self.name, self.version))


class SSABlock:
    """
    SSA基本块类
    """
    
    def __init__(self, block_id: int, label: str = ""):
        """
        初始化SSA基本块
        
        Args:
            block_id: 块的唯一标识
            label: 块的标签
        """
        self.block_id = block_id
        self.label = label if label else f"block_{block_id}"
        self.statements: List[Tuple[str, str]] = []  # (lhs, rhs_or_phi) 元组列表
        self.predecessors: List[int] = []
        self.successors: List[int] = []
        # φ函数的参数映射：变量名 -> [SSAVariable]
        self.phi_args: Dict[str, List[SSAVariable]] = defaultdict(list)
    
    def add_statement(self, lhs: str, rhs: str):
        """
        添加赋值语句
        
        Args:
            lhs: 左边的变量
            rhs: 右边的表达式
        """
        self.statements.append((lhs, rhs))
    
    def add_phi(self, var: str, num_preds: int):
        """
        添加φ函数
        
        Args:
            var: 变量名
            num_preds: 前驱数量
        """
        # φ函数的占位表示
        phi_args = [f"{var}.?" for _ in range(num_preds)]
        phi_str = f"φ({', '.join(phi_args)})"
        self.statements.insert(0, (var, phi_str))
    
    def __repr__(self):
        return f"SSABlock({self.block_id}: {self.label})"


class SSATranslator:
    """
    SSA转换器
    
    将普通程序转换为SSA形式。
    """
    
    def __init__(self, num_blocks: int, entry_block: int = 0):
        """
        初始化SSA转换器
        
        Args:
            num_blocks: 基本块数量
            entry_block: 入口块ID
        """
        self.num_blocks = num_blocks
        self.entry_block = entry_block
        self.blocks: Dict[int, SSABlock] = {}
        # 版本计数器：变量名 -> 当前版本号
        self.version_counter: Dict[str, int] = defaultdict(int)
        # 当前活跃的变量版本：变量名 -> SSAVariable
        self.current_versions: Dict[str, SSAVariable] = {}
        # 语句计数器
        self.stmt_counter: int = 0
        
        # 初始化基本块
        for i in range(num_blocks):
            self.blocks[i] = SSABlock(i)
    
    def add_edge(self, from_id: int, to_id: int):
        """
        添加控制流边
        
        Args:
            from_id: 起始块ID
            to_id: 目标块ID
        """
        if from_id in self.blocks and to_id in self.blocks:
            self.blocks[from_id].successors.append(to_id)
            self.blocks[to_id].predecessors.append(from_id)
    
    def get_new_version(self, var_name: str) -> SSAVariable:
        """
        获取变量的新版本
        
        Args:
            var_name: 变量名
            
        Returns:
            新的SSA变量
        """
        self.version_counter[var_name] += 1
        version = self.version_counter[var_name]
        ssa_var = SSAVariable(var_name, version)
        self.current_versions[var_name] = ssa_var
        return ssa_var
    
    def get_current_version(self, var_name: str) -> SSAVariable:
        """
        获取变量的当前版本
        
        Args:
            var_name: 变量名
            
        Returns:
            当前的SSA变量（如果不存在则创建版本0）
        """
        if var_name not in self.current_versions:
            self.current_versions[var_name] = SSAVariable(var_name, 0)
        return self.current_versions[var_name]
    
    def rename_variable(self, var_name: str) -> str:
        """
        获取变量的新名字（带版本号）
        
        Args:
            var_name: 变量名
            
        Returns:
            重命名后的变量名字符串
        """
        ssa_var = self.get_new_version(var_name)
        return str(ssa_var)
    
    def add_original_instruction(self, block_id: int, lhs: str, rhs: str):
        """
        添加原始指令（带SSA重命名）
        
        Args:
            block_id: 基本块ID
            lhs: 左边的变量
            rhs: 右边的表达式
        """
        if block_id not in self.blocks:
            return
        
        block = self.blocks[block_id]
        
        # 解析右侧表达式中的变量引用
        rhs_vars = self._extract_variables(rhs)
        renamed_rhs = rhs
        
        # 替换右侧的变量为当前版本
        for var in rhs_vars:
            current = self.get_current_version(var)
            renamed_rhs = renamed_rhs.replace(var, str(current))
        
        # 重命名左侧变量
        new_lhs = self.rename_variable(lhs)
        
        # 添加语句
        block.add_statement(new_lhs, renamed_rhs)
    
    def _extract_variables(self, expr: str) -> Set[str]:
        """
        从表达式中提取变量名
        
        Args:
            expr: 表达式字符串
            
        Returns:
            变量名集合
        """
        import re
        # 匹配标识符（排除数字和关键字）
        identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', expr)
        # 过滤掉常见的关键词和函数名
        keywords = {'if', 'goto', 'return', 'phi', 'and', 'or', 'not'}
        return {var for var in identifiers if var not in keywords}
    
    def insert_phi_functions(self, var_names: List[str]):
        """
        为指定变量在适当位置插入φ函数
        
        使用支配边界算法确定φ函数的放置位置。
        
        Args:
            var_names: 需要转换的变量名列表
        """
        # 简化的φ函数插入：每个汇合点插入
        for block_id, block in self.blocks.items():
            if len(block.predecessors) > 1:
                # 多于一个前驱，需要φ函数
                for var in var_names:
                    block.add_phi(var, len(block.predecessors))
    
    def compute_dominance_frontier(self, block_id: int) -> Set[int]:
        """
        计算指定块的支配边界
        
        Args:
            block_id: 基本块ID
            
        Returns:
            支配边界集合
        """
        block = self.blocks.get(block_id)
        if not block:
            return set()
        
        df = set()
        
        # 对于每个后继
        for succ_id in block.successors:
            succ = self.blocks.get(succ_id)
            if not succ:
                continue
            # 如果后继的直接支配者不是当前块
            if block_id != succ_id:
                df.add(succ_id)
        
        # 对于每个支配子节点的后继
        # 这里简化处理，实际应该用完整的支配边界算法
        
        return df
    
    def translate(self, instructions: List[Tuple[int, str, str]]) -> Dict[int, SSABlock]:
        """
        执行完整的SSA转换
        
        Args:
            instructions: (block_id, lhs, rhs) 元组列表
            
        Returns:
            转换后的SSA基本块字典
        """
        # 第一步：添加所有指令
        for block_id, lhs, rhs in instructions:
            self.add_original_instruction(block_id, lhs, rhs)
        
        # 第二步：插入φ函数（简化版本）
        # 收集所有被定义的变量
        all_vars = set()
        for block_id, lhs, rhs in instructions:
            all_vars.add(lhs)
            all_vars.update(self._extract_variables(rhs))
        
        self.insert_phi_functions(list(all_vars))
        
        return self.blocks
    
    def display(self):
        """显示SSA程序"""
        print("=" * 60)
        print("SSA Form Program")
        print("=" * 60)
        
        for block_id in sorted(self.blocks.keys()):
            block = self.blocks[block_id]
            print(f"\n{block.label} (Block {block_id}):")
            
            if block.predecessors:
                print(f"  // predecessors: {block.predecessors}")
            if block.successors:
                print(f"  // successors: {block.successors}")
            
            for lhs, rhs in block.statements:
                print(f"  {lhs} = {rhs}")
        
        print("\n" + "=" * 60)
        print("Variable Versions:")
        print("=" * 60)
        for var_name in sorted(self.version_counter.keys()):
            print(f"  {var_name}: 0.{self.version_counter[var_name]}")


def example_simple_program():
    """
    示例：简单顺序程序的SSA转换
    
    原始程序：
        x = 5
        y = x + 1
        x = y * 2
        z = x + y
    
    预期SSA：
        x.1 = 5
        y.1 = x.1 + 1
        x.2 = y.1 * 2
        z.1 = x.2 + y.1
    """
    translator = SSATranslator(num_blocks=1, entry_block=0)
    
    instructions = [
        (0, "x", "5"),
        (0, "y", "x + 1"),
        (0, "x", "y * 2"),
        (0, "z", "x + y"),
    ]
    
    return translator, instructions


def example_branch_program():
    """
    示例：分支程序的SSA转换
    
    原始程序：
        x = 5
        if condition:
            x = 10
        else:
            x = 15
        y = x
    
    预期SSA：
        x.1 = 5
        if condition:
            x.2 = 10
        else:
            x.3 = 15
        x.4 = φ(x.2, x.3)  // 汇合点
        y.1 = x.4
    """
    translator = SSATranslator(num_blocks=3, entry_block=0)
    
    # 添加控制流边
    translator.add_edge(0, 1)  # 入口 -> then分支
    translator.add_edge(0, 2)  # 入口 -> else分支
    translator.add_edge(1, 3)  # 假设存在汇合块
    translator.add_edge(2, 3)
    
    # 更新块数量
    translator.blocks[3] = SSABlock(3, "merge")
    translator.num_blocks = 4
    
    instructions = [
        (0, "x", "5"),          # Block 0: 入口
        (1, "x", "10"),         # Block 1: then分支
        (2, "x", "15"),         # Block 2: else分支
        (3, "x", "φ(x.2, x.3)"), # Block 3: 汇合点（手动添加φ）
        (3, "y", "x"),          # Block 3: 使用x
    ]
    
    return translator, instructions


if __name__ == "__main__":
    print("=" * 60)
    print("测试1：简单顺序程序的SSA转换")
    print("=" * 60)
    
    translator1, instructions1 = example_simple_program()
    translator1.translate(instructions1)
    translator1.display()
    
    print("\n" + "=" * 60)
    print("测试2：分支程序的SSA转换")
    print("=" * 60)
    
    translator2, instructions2 = example_branch_program()
    translator2.translate(instructions2)
    translator2.display()
    
    print("\n" + "=" * 60)
    print("测试3：带循环的程序的SSA转换")
    print("=" * 60)
    
    # 创建带循环的程序
    translator3 = SSATranslator(num_blocks=3, entry_block=0)
    
    # CFG: 0 -> 1 -> 2 -> 1 (循环)
    translator3.add_edge(0, 1)
    translator3.add_edge(1, 2)
    translator3.add_edge(2, 1)
    
    instructions3 = [
        (0, "i", "0"),           # i = 0
        (1, "sum", "sum + i"),   # sum = sum + i (假设sum初始为0)
        (2, "i", "i + 1"),       # i = i + 1
    ]
    
    translator3.translate(instructions3)
    translator3.display()
    
    print("\nSSA转换测试完成!")
    print("\n注意：实际编译器中，SSA构建还需要：")
    print("  1. 完整的支配边界计算")
    print("  2. φ函数参数的正确绑定")
    print("  3. 变量重命名的一致性处理")
