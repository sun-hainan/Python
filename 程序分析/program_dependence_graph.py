# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / program_dependence_graph

本文件实现 program_dependence_graph 相关的算法功能。
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict, deque


class Statement:
    """
    语句类，表示程序中的一句代码
    """
    
    def __init__(self, stmt_id: int, text: str, block_id: int = 0):
        """
        初始化语句
        
        Args:
            stmt_id: 语句的唯一标识
            text: 语句的文本
            block_id: 所属基本块ID
        """
        self.stmt_id = stmt_id
        self.text = text
        self.block_id = block_id
        self.uses: Set[str] = set()    # 使用的变量
        self.defines: Set[str] = set()  # 定义的变量
        self.is_jump: bool = False     # 是否是跳转语句
        self.is_conditional: bool = False  # 是否是条件跳转
        self.jump_target: Optional[int] = None  # 跳转目标语句ID
    
    def __repr__(self):
        return f"Stmt({self.stmt_id}: {self.text[:30]})"


class DependenceEdge:
    """
    依赖边类
    """
    
    DATA_DEP = "data"    # 数据依赖
    CONTROL_DEP = "control"  # 控制依赖
    
    def __init__(self, from_stmt: int, to_stmt: int, dep_type: str, label: str = ""):
        """
        初始化依赖边
        
        Args:
            from_stmt: 起始语句ID
            to_stmt: 目标语句ID
            dep_type: 依赖类型 (DATA_DEP or CONTROL_DEP)
            label: 边的标签（用于控制依赖）
        """
        self.from_stmt = from_stmt
        self.to_stmt = to_stmt
        self.dep_type = dep_type
        self.label = label
    
    def __repr__(self):
        return f"Edge({self.from_stmt} -{self.dep_type}-> {self.to_stmt})"


class ProgramDependenceGraph:
    """
    程序依赖图 (PDG)
    
    包含：
    - 节点：程序语句
    - 边：数据依赖和控制依赖
    """
    
    def __init__(self):
        """初始化PDG"""
        # 语句映射：stmt_id -> Statement
        self.statements: Dict[int, Statement] = {}
        # 依赖边列表
        self.edges: List[DependenceEdge] = []
        # 出边邻接表：stmt_id -> [dependent_stmt_ids]
        self.out_edges: Dict[int, List[int]] = defaultdict(list)
        # 入边邻接表：stmt_id -> [dependence_stmt_ids]
        self.in_edges: Dict[int, List[int]] = defaultdict(list)
        # 语句计数
        self.stmt_counter = 0
        # CFG信息（可选）
        self.cfg_successors: Dict[int, List[int]] = defaultdict(list)
        self.cfg_predecessors: Dict[int, List[int]] = defaultdict(list)
    
    def add_statement(self, text: str, block_id: int = 0) -> int:
        """
        添加语句
        
        Args:
            text: 语句文本
            block_id: 基本块ID
            
        Returns:
            语句ID
        """
        self.stmt_counter += 1
        stmt_id = self.stmt_counter
        
        stmt = Statement(stmt_id, text, block_id)
        self._analyze_statement(stmt)
        self.statements[stmt_id] = stmt
        
        return stmt_id
    
    def _analyze_statement(self, stmt: Statement):
        """分析语句，提取变量使用和定义"""
        text = stmt.text.strip()
        
        # 检测跳转语句
        if text.startswith('if '):
            stmt.is_jump = True
            stmt.is_conditional = True
        elif text.startswith('goto '):
            stmt.is_jump = True
        elif text.startswith('return'):
            stmt.is_jump = True
        
        # 分析赋值
        if '=' in text and not text.startswith('if'):
            parts = text.split('=', 1)
            lhs = parts[0].strip()
            rhs = parts[1].strip() if len(parts) > 1 else ""
            
            stmt.defines.add(lhs)
            
            # 提取右侧变量
            for word in self._extract_identifiers(rhs):
                if word.isidentifier():
                    stmt.uses.add(word)
        
        # 分析条件跳转的条件
        if stmt.is_conditional:
            condition = text.replace('if ', '', 1)
            if 'goto ' in condition:
                condition = condition.split('goto ')[0]
            for word in self._extract_identifiers(condition):
                if word.isidentifier():
                    stmt.uses.add(word)
    
    def _extract_identifiers(self, text: str) -> List[str]:
        """从文本中提取标识符"""
        import re
        return re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', text)
    
    def add_cfg_edge(self, from_id: int, to_id: int):
        """添加CFG边"""
        self.cfg_successors[from_id].append(to_id)
        self.cfg_predecessors[to_id].append(from_id)
    
    def build_data_dependencies(self):
        """构建数据依赖边"""
        # 记录每个变量的定义语句
        var_defs: Dict[str, List[int]] = defaultdict(list)
        
        # 按语句顺序遍历
        for stmt_id in sorted(self.statements.keys()):
            stmt = self.statements[stmt_id]
            
            # 对于每个使用的变量
            for var in stmt.uses:
                # 找到该变量的所有定义
                for def_stmt_id in var_defs.get(var, []):
                    # 添加数据依赖边（从定义到使用）
                    self._add_dependence_edge(
                        def_stmt_id, stmt_id,
                        DependenceEdge.DATA_DEP,
                        f"data({var})"
                    )
            
            # 更新变量定义列表
            for var in stmt.defines:
                var_defs[var].append(stmt_id)
    
    def build_control_dependencies(self):
        """构建控制依赖边"""
        # 简化版本：基于条件跳转的控制依赖
        # 如果语句S在条件跳转C之后，且受C控制，则S控制依赖于C
        
        # 找到所有条件跳转语句
        conditional_stmts = [
            sid for sid, stmt in self.statements.items()
            if stmt.is_conditional
        ]
        
        for cond_stmt_id in conditional_stmts:
            # 找到条件跳转能到达的所有语句
            reachable = self._find_reachable(cond_stmt_id)
            
            # 这些语句都控制依赖于条件跳转
            for target_id in reachable:
                if target_id != cond_stmt_id:
                    self._add_dependence_edge(
                        cond_stmt_id, target_id,
                        DependenceEdge.CONTROL_DEP,
                        "control"
                    )
    
    def _find_reachable(self, start_id: int) -> Set[int]:
        """找到从start_id可达的所有语句"""
        visited: Set[int] = set()
        worklist = deque([start_id])
        
        while worklist:
            current = worklist.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            for succ_id in self.cfg_successors.get(current, []):
                if succ_id not in visited:
                    worklist.append(succ_id)
        
        return visited - {start_id}
    
    def _add_dependence_edge(self, from_id: int, to_id: int, dep_type: str, label: str = ""):
        """添加依赖边"""
        # 避免重复边
        for edge in self.edges:
            if edge.from_stmt == from_id and edge.to_stmt == to_id:
                return
        
        edge = DependenceEdge(from_id, to_id, dep_type, label)
        self.edges.append(edge)
        self.out_edges[from_id].append(to_id)
        self.in_edges[to_id].append(from_id)
    
    def build(self):
        """构建完整的PDG"""
        self.build_data_dependencies()
        self.build_control_dependencies()
    
    def get_dependents(self, stmt_id: int, dep_type: Optional[str] = None) -> List[int]:
        """
        获取依赖于指定语句的所有语句
        
        Args:
            stmt_id: 语句ID
            dep_type: 依赖类型过滤（None表示所有）
            
        Returns:
            依赖语句ID列表
        """
        dependents = []
        for edge in self.edges:
            if edge.from_stmt == stmt_id:
                if dep_type is None or edge.dep_type == dep_type:
                    dependents.append(edge.to_stmt)
        return dependents
    
    def get_dependencies(self, stmt_id: int, dep_type: Optional[str] = None) -> List[int]:
        """
        获取指定语句依赖的所有语句
        
        Args:
            stmt_id: 语句ID
            dep_type: 依赖类型过滤
            
        Returns:
            所依赖的语句ID列表
        """
        dependencies = []
        for edge in self.edges:
            if edge.to_stmt == stmt_id:
                if dep_type is None or edge.dep_type == dep_type:
                    dependencies.append(edge.from_stmt)
        return dependencies
    
    def compute_slice(self, criterion_stmt_id: int, 
                     criterion_var: Optional[str] = None) -> Set[int]:
        """
        计算程序切片（基于PDG）
        
        Args:
            criterion_stmt_id: 切片准则语句ID
            criterion_var: 切片准则变量名（可选）
            
        Returns:
            切片包含的语句ID集合
        """
        slice_set: Set[int] = {criterion_stmt_id}
        worklist = deque([criterion_stmt_id])
        visited: Set[int] = set([criterion_stmt_id])
        
        while worklist:
            current = worklist.popleft()
            
            # 获取所有依赖当前语句的语句
            for dep_id in self.get_dependencies(current):
                if dep_id not in visited:
                    visited.add(dep_id)
                    slice_set.add(dep_id)
                    worklist.append(dep_id)
        
        return slice_set
    
    def display(self):
        """显示PDG（用于调试）"""
        print("=" * 60)
        print("Program Dependence Graph")
        print("=" * 60)
        
        print("\nStatements:")
        for stmt_id in sorted(self.statements.keys()):
            stmt = self.statements[stmt_id]
            uses_str = f"uses={stmt.uses}" if stmt.uses else ""
            defs_str = f"defs={stmt.defines}" if stmt.defines else ""
            print(f"  [{stmt_id}] {stmt.text}")
            if uses_str or defs_str:
                print(f"      {uses_str} {defs_str}")
        
        print("\nEdges:")
        for edge in self.edges:
            from_text = self.statements[edge.from_stmt].text[:20]
            to_text = self.statements[edge.to_stmt].text[:20]
            print(f"  {edge.from_stmt}({from_text}) --{edge.dep_type}--> {edge.to_stmt}({to_text})")
    
    def display_dot(self) -> str:
        """
        生成DOT格式的PDG表示（用于Graphviz可视化）
        
        Returns:
            DOT格式字符串
        """
        lines = ["digraph PDG {"]
        lines.append("  rankdir=TB;")
        
        # 节点声明
        for stmt_id in sorted(self.statements.keys()):
            stmt = self.statements[stmt_id]
            label = stmt.text.replace('"', '\\"')[:50]
            lines.append(f'  n{stmt_id} [label="{stmt_id}: {label}"];')
        
        # 边声明
        for edge in self.edges:
            style = "solid" if edge.dep_type == DependenceEdge.DATA_DEP else "dashed"
            lines.append(f'  n{edge.from_stmt} -> n{edge.to_stmt} [style={style}, label="{edge.label}"];')
        
        lines.append("}")
        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("测试：程序依赖图构建")
    print("=" * 60)
    
    pdg = ProgramDependenceGraph()
    
    # 添加语句
    sid1 = pdg.add_statement("x = 5")           # x定义
    sid2 = pdg.add_statement("y = x + 1")       # x使用，y定义
    sid3 = pdg.add_statement("if y > 10:")      # y使用，条件跳转
    sid4 = pdg.add_statement("z = x * 2")       # 条件分支内的语句
    sid5 = pdg.add_statement("else:")
    sid6 = pdg.add_statement("z = x * 3")       # else分支
    sid7 = pdg.add_statement("result = z")      # z使用
    
    # 添加CFG边（模拟控制流）
    pdg.add_cfg_edge(sid1, sid2)
    pdg.add_cfg_edge(sid2, sid3)
    pdg.add_cfg_edge(sid3, sid4)  # then分支
    pdg.add_cfg_edge(sid3, sid5)  # else分支
    pdg.add_cfg_edge(sid4, sid7)
    pdg.add_cfg_edge(sid5, sid6)
    pdg.add_cfg_edge(sid6, sid7)
    
    # 构建PDG
    pdg.build()
    
    # 显示PDG
    pdg.display()
    
    print("\n" + "=" * 60)
    print("切片计算")
    print("=" * 60)
    
    # 计算以sid7（result = z）为准则的切片
    slice_result = pdg.compute_slice(sid7)
    
    print(f"\n以语句 {sid7} (result = z) 为准则的切片:")
    for stmt_id in sorted(slice_result):
        stmt = pdg.statements[stmt_id]
        print(f"  [{stmt_id}] {stmt.text}")
    
    print("\n依赖分析:")
    for stmt_id in sorted(pdg.statements.keys()):
        deps = pdg.get_dependencies(stmt_id)
        deps_str = ", ".join(str(d) for d in deps) if deps else "none"
        print(f"  [{stmt_id}] {pdg.statements[stmt_id].text[:30]}")
        print(f"      依赖: {deps_str}")
    
    print("\n" + "=" * 60)
    print("DOT格式输出（用于Graphviz）")
    print("=" * 60)
    print(pdg.display_dot())
    
    print("\n程序依赖图测试完成!")
