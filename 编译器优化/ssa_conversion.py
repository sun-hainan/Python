# -*- coding: utf-8 -*-
"""
算法实现：编译器优化 / ssa_conversion

本文件实现 ssa_conversion 相关的算法功能。
"""

from typing import List, Dict, Tuple, Set
from collections import defaultdict


class SSABuilder:
    """
    SSA形式构建器
    """
    
    def __init__(self):
        self.next_version = defaultdict(int)  # 每个变量的下一个版本号
        self.current_defs = {}  # 当前活跃的定义
        self.ssa_vars = {}  # 原始变量 -> SSA变量列表
    
    def new_version(self, var: str) -> str:
        """创建新版本"""
        version = self.next_version[var]
        self.next_version[var] += 1
        ssa_var = f"{var}.{version}"
        
        if var not in self.ssa_vars:
            self.ssa_vars[var] = []
        self.ssa_vars[var].append(ssa_var)
        
        return ssa_var
    
    def get_current_version(self, var: str) -> str:
        """获取变量的当前版本"""
        if var in self.current_defs:
            return self.current_defs[var]
        return var  # 如果没有被定义过,使用原名
    
    def define(self, var: str) -> str:
        """定义变量并返回SSA名"""
        ssa_var = self.new_version(var)
        self.current_defs[var] = ssa_var
        return ssa_var
    
    def use(self, var: str) -> str:
        """使用变量(返回当前版本)"""
        return self.get_current_version(var)


class PhiFunction:
    """Φ函数表示"""
    def __init__(self, lhs: str, predecessors: List[str]):
        self.lhs = lhs
        self.predecessors = predecessors  # 前驱块的SSA变量
    
    def __repr__(self):
        preds = ', '.join(self.predecessors)
        return f"{self.lhs} = phi({preds})"


def to_ssa(blocks: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    将代码转换为SSA形式
    
    Args:
        blocks: 基本块列表,每块有'stmts'和' preds'
    
    Returns:
        (SSA块列表, 变量映射)
    """
    builder = SSABuilder()
    ssa_blocks = []
    
    # 第一次遍历:处理普通赋值
    for block in blocks:
        ssa_block = {'id': block['id'], 'stmts': [], 'phi': []}
        
        for stmt in block.get('stmts', []):
            if hasattr(stmt, 'lhs'):
                # 定义新版本
                ssa_lhs = builder.define(stmt.lhs)
                
                # 替换 rhs 中的变量
                if hasattr(stmt, 'rhs1'):
                    ssa_rhs = builder.use(stmt.rhs1)
                    stmt.ssa_rhs1 = ssa_rhs
                
                if hasattr(stmt, 'rhs2'):
                    ssa_rhs = builder.use(stmt.rhs2)
                    stmt.ssa_rhs2 = ssa_rhs
                
                stmt.ssa_lhs = ssa_lhs
            else:
                # 替换条件中的变量
                if hasattr(stmt, 'cond'):
                    stmt.cond = builder.use(stmt.cond)
            
            ssa_block['stmts'].append(stmt)
        
        ssa_blocks.append(ssa_block)
    
    # 第二次遍历:插入Φ函数
    # 计算每个块的支配边界
    df = compute_dominance_frontier(blocks)
    
    for var in builder.ssa_vars.keys():
        # 找到所有定义该变量的块
        def_blocks = []
        for block in blocks:
            for stmt in block.get('stmts', []):
                if hasattr(stmt, 'lhs') and stmt.lhs == var:
                    def_blocks.append(block['id'])
        
        # 在支配边界的适当位置插入Φ函数
        for block_id in def_blocks:
            for df_block in df.get(block_id, []):
                # 检查是否已经插入过Φ
                if not has_phi(ssa_blocks[df_block], var):
                    # 创建Φ函数
                    preds = [f"{var}.{i}" for i in range(len(blocks[df_block].get('preds', [])))]
                    phi = PhiFunction(f"{var}.{builder.next_version[var]}", preds)
                    builder.define(var)
                    
                    ssa_blocks[df_block]['phi'].append(phi)
    
    # 第三次遍历:替换Φ函数的参数
    for block in ssa_blocks:
        for phi in block.get('phi', []):
            # 根据前驱更新参数
            new_preds = []
            for i, pred_id in enumerate(blocks[block['id']].get('preds', [])):
                # 找到前驱块中var的最新版本
                pred_version = find_version_at_block(var, pred_id, ssa_blocks)
                new_preds.append(pred_version)
            phi.predecessors = new_preds
    
    return ssa_blocks, builder.ssa_vars


def compute_dominance_frontier(blocks: List[Dict]) -> Dict[int, Set[int]]:
    """计算支配边界"""
    n = len(blocks)
    
    # 简化:假设线性顺序
    # 实际应该使用完整的数据流分析
    df = defaultdict(set)
    
    for i, block in enumerate(blocks):
        for succ_id in block.get('succs', []):
            # block的后继的支配边界包含block
            df[succ_id].add(i)
    
    return dict(df)


def has_phi(block: Dict, var: str) -> bool:
    """检查块中是否有var的Φ函数"""
    for phi in block.get('phi', []):
        if var in phi.lhs:
            return True
    return False


def find_version_at_block(var: str, block_id: int, ssa_blocks: List[Dict]) -> str:
    """找到在特定块的变量版本"""
    # 简化:返回最新版本
    # 实际需要更复杂的追踪
    for stmt in reversed(ssa_blocks[block_id].get('stmts', [])):
        if hasattr(stmt, 'ssa_lhs') and var in stmt.ssa_lhs:
            return stmt.ssa_lhs
    return var


def from_ssa(ssa_blocks: List[Dict]) -> List[Dict]:
    """将SSA形式转回普通形式"""
    # 简化实现
    blocks = []
    
    for ssa_block in ssa_blocks:
        block = {'id': ssa_block['id'], 'stmts': []}
        
        for phi in ssa_block.get('phi', []):
            # Φ函数在普通形式中代表合并
            pass
        
        for stmt in ssa_block.get('stmts', []):
            # 恢复原变量名
            if hasattr(stmt, 'ssa_lhs'):
                stmt.lhs = stmt.lhs.split('.')[0]
            block['stmts'].append(stmt)
        
        blocks.append(block)
    
    return blocks


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单变量
    print("测试1 - 简单SSA转换:")
    
    class Stmt:
        def __init__(self, lhs, rhs1, rhs2=None, op=None):
            self.lhs = lhs
            self.rhs1 = rhs1
            self.rhs2 = rhs2
            self.op = op
        
        def __repr__(self):
            if self.rhs2:
                return f"{self.lhs} = {self.rhs1} {self.op or '+'} {self.rhs2}"
            return f"{self.lhs} = {self.rhs1}"
    
    blocks = [
        {'id': 0, 'stmts': [Stmt('x', '1'), Stmt('y', 'x')], 'preds': [], 'succs': [1]},
        {'id': 1, 'stmts': [Stmt('x', 'y', '1', '+')], 'preds': [0], 'succs': []},
    ]
    
    ssa_blocks, var_map = to_ssa(blocks)
    
    print("  原始块:")
    for b in blocks:
        print(f"    Block{b['id']}: {[str(s) for s in b['stmts']]}")
    
    print("  SSA块:")
    for b in ssa_blocks:
        print(f"    Block{b['id']}: stmts={[str(s) for s in b['stmts']]}, phi={b['phi']}")
    
    print(f"  变量版本映射: {var_map}")
    
    # 测试2: 循环中的SSA
    print("\n测试2 - 循环中的SSA:")
    
    blocks2 = [
        {'id': 0, 'stmts': [Stmt('i', '0'), Stmt('x', '1')], 'preds': [], 'succs': [1]},
        {'id': 1, 'stmts': [Stmt('x', 'x', '1', '+'), Stmt('i', 'i', '1', '+')], 'preds': [0, 2], 'succs': [2]},
        {'id': 2, 'stmts': [], 'preds': [1], 'succs': [1]},  # 条件块
    ]
    
    ssa_blocks2, var_map2 = to_ssa(blocks2)
    
    print("  SSA块:")
    for b in ssa_blocks2:
        print(f"    Block{b['id']}: stmts={[str(s) for s in b['stmts']]}, phi={b['phi']}")
    
    # 测试3: 条件分支
    print("\n测试3 - 条件分支:")
    
    blocks3 = [
        {'id': 0, 'stmts': [Stmt('a', '1')], 'preds': [], 'succs': [1, 2]},
        {'id': 1, 'stmts': [Stmt('b', 'a', '2', '+')], 'preds': [0], 'succs': [3]},
        {'id': 2, 'stmts': [Stmt('c', 'a', '3', '+')], 'preds': [0], 'succs': [3]},
        {'id': 3, 'stmts': [Stmt('d', 'b', 'c', '+')], 'preds': [1, 2], 'succs': []},
    ]
    
    ssa_blocks3, var_map3 = to_ssa(blocks3)
    
    print("  SSA块:")
    for b in ssa_blocks3:
        print(f"    Block{b['id']}: stmts={[str(s) for s in b['stmts']]}, phi={b['phi']}")
    
    print("\n所有测试完成!")
