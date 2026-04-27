# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / symbol_table

本文件实现 symbol_table 相关的算法功能。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto


class SymbolKind(Enum):
    """符号种类"""
    VARIABLE = auto()  # 变量
    FUNCTION = auto()  # 函数
    PARAMETER = auto()  # 参数
    TYPE = auto()  # 类型
    CONSTANT = auto()  # 常量
    STRUCT = auto()  # 结构体
    ENUM = auto()  # 枚举
    LABEL = auto()  # 标签


@dataclass
class Symbol:
    """符号定义"""
    name: str  # 符号名称
    kind: SymbolKind  # 符号种类
    type_name: str  # 类型名称
    scope_level: int  # 作用域层级
    value: Any = None  # 符号值(常量值、函数地址等)
    attributes: Dict[str, Any] = field(default_factory=dict)  # 额外属性
    line: int = 0  # 定义行号
    column: int = 0  # 定义列号


@dataclass
class Scope:
    """作用域"""
    level: int  # 作用域层级
    name: str  # 作用域名称
    symbols: Dict[str, Symbol] = field(default_factory=dict)  # 符号表
    parent: Optional['Scope'] = None  # 父作用域


class SymbolTable:
    """
    符号表

    功能:
    1. 符号的插入、查找、删除
    2. 作用域管理(嵌套作用域)
    3. 符号冲突检测
    4. 作用域链遍历
    """

    def __init__(self):
        self.scopes: List[Scope] = []  # 作用域栈
        self.current_scope: Optional[Scope] = None  # 当前作用域
        self.global_scope: Optional[Scope] = None  # 全局作用域
        self.symbol_count = 0  # 符号总数

    def init_global_scope(self, name: str = "global"):
        """初始化全局作用域"""
        global_scope = Scope(level=0, name=name)
        self.scopes.append(global_scope)
        self.current_scope = global_scope
        self.global_scope = global_scope

    def enter_scope(self, name: str) -> Scope:
        """
        进入新作用域

        参数:
            name: 作用域名称(如函数名、块名)

        返回:
            新创建的作用域
        """
        new_level = self.current_scope.level + 1 if self.current_scope else 0
        new_scope = Scope(level=new_level, name=name, parent=self.current_scope)
        self.scopes.append(new_scope)
        self.current_scope = new_scope
        return new_scope

    def exit_scope(self) -> Optional[Scope]:
        """
        退出当前作用域

        返回:
            父作用域
        """
        if self.current_scope and self.current_scope.parent:
            self.current_scope = self.current_scope.parent
            return self.current_scope
        return None

    def insert(self, name: str, kind: SymbolKind, type_name: str,
              value: Any = None, line: int = 0, column: int = 0) -> Optional[Symbol]:
        """
        插入符号到当前作用域

        参数:
            name: 符号名
            kind: 符号种类
            type_name: 类型名
            value: 符号值
            line: 行号
            column: 列号

        返回:
            成功返回Symbol, 失败返回None(符号已存在)
        """
        if not self.current_scope:
            self.init_global_scope()

        # 检查当前作用域是否已存在同名符号
        if name in self.current_scope.symbols:
            return None

        symbol = Symbol(
            name=name,
            kind=kind,
            type_name=type_name,
            scope_level=self.current_scope.level,
            value=value,
            line=line,
            column=column
        )

        self.current_scope.symbols[name] = symbol
        self.symbol_count += 1
        return symbol

    def lookup(self, name: str, current_scope_only: bool = False) -> Optional[Symbol]:
        """
        查找符号

        参数:
            name: 符号名
            current_scope_only: 是否只查找当前作用域

        返回:
            找到返回Symbol, 未找到返回None
        """
        if not self.current_scope:
            return None

        if current_scope_only:
            return self.current_scope.symbols.get(name)

        # 从当前作用域向上查找
        scope = self.current_scope
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent

        return None

    def lookup_in_scope(self, name: str, scope: Scope) -> Optional[Symbol]:
        """在指定作用域中查找符号"""
        return scope.symbols.get(name)

    def update(self, name: str, **kwargs) -> bool:
        """
        更新符号属性

        返回:
            成功返回True, 失败返回False
        """
        symbol = self.lookup(name)
        if not symbol:
            return False

        for key, value in kwargs.items():
            if hasattr(symbol, key):
                setattr(symbol, key, value)

        return True

    def remove(self, name: str) -> bool:
        """
        从当前作用域删除符号

        返回:
            成功返回True, 失败返回False
        """
        if name in self.current_scope.symbols:
            del self.current_scope.symbols[name]
            self.symbol_count -= 1
            return True
        return False

    def exists(self, name: str) -> bool:
        """检查符号是否存在"""
        return self.lookup(name) is not None

    def get_all_symbols(self) -> List[Symbol]:
        """获取所有符号"""
        all_symbols = []
        for scope in self.scopes:
            all_symbols.extend(scope.symbols.values())
        return all_symbols

    def get_symbols_in_scope(self, scope: Scope) -> List[Symbol]:
        """获取指定作用域的所有符号"""
        return list(scope.symbols.values())

    def get_scope_chain(self) -> List[str]:
        """获取作用域链(用于调试)"""
        chain = []
        scope = self.current_scope
        while scope:
            chain.append(f"L{scope.level}:{scope.name}")
            scope = scope.parent
        return chain


def print_symbol_table(st: SymbolTable):
    """打印符号表(调试用)"""
    print("=== 符号表 ===")
    for scope in st.scopes:
        print(f"\n作用域: {scope.name} (Level {scope.level})")
        if scope.symbols:
            print(f"  {'名称':<15} {'种类':<12} {'类型':<10} {'行号':<6}")
            print(f"  {'-'*50}")
            for sym in scope.symbols.values():
                print(f"  {sym.name:<15} {sym.kind.name:<12} {sym.type_name:<10} {sym.line:<6}")


if __name__ == "__main__":
    st = SymbolTable()
    st.init_global_scope("global")

    # 全局作用域: 定义变量和函数
    print("=== 全局作用域 ===")
    st.insert("x", SymbolKind.VARIABLE, "int", value=10, line=1)
    st.insert("y", SymbolKind.VARIABLE, "float", line=2)
    st.insert("MAX", SymbolKind.CONSTANT, "int", value=100, line=3)

    # 定义函数 add(int a, int b)
    print("\n=== 定义函数 add ===")
    st.enter_scope("add")
    st.insert("a", SymbolKind.PARAMETER, "int", line=5)
    st.insert("b", SymbolKind.PARAMETER, "int", line=5)
    st.insert("result", SymbolKind.VARIABLE, "int", line=6)

    # 在函数内定义内部块
    print("\n=== 进入内部块 ===")
    st.enter_scope("block1")
    st.insert("temp", SymbolKind.VARIABLE, "int", line=8)
    print(f"作用域链: {' -> '.join(st.get_scope_chain())}")

    # 查找符号
    print("\n=== 符号查找 ===")
    print(f"查找 'a': {st.lookup('a')}")
    print(f"查找 'x': {st.lookup('x')}")  # 应在全局作用域
    print(f"查找 'temp': {st.lookup('temp')}")
    print(f"查找 'nonexist': {st.lookup('nonexist')}")

    # 当前作用域查找
    print(f"\n当前作用域查找 'x': {st.lookup('x', current_scope_only=True)}")

    # 退出块
    print("\n=== 退出内部块 ===")
    st.exit_scope()
    print(f"作用域链: {' -> '.join(st.get_scope_chain())}")

    # 退出函数
    st.exit_scope()

    # 定义另一个函数
    print("\n=== 定义函数 sub ===")
    st.enter_scope("sub")
    st.insert("p", SymbolKind.PARAMETER, "int", line=15)
    st.insert("q", SymbolKind.PARAMETER, "int", line=15)

    # 符号冲突测试
    print("\n=== 符号冲突测试 ===")
    result = st.insert("p", SymbolKind.PARAMETER, "int", line=16)
    print(f"在函数 sub 中再次插入 'p': {'成功' if result else '失败(已存在)'}")

    # 打印完整符号表
    print()
    print_symbol_table(st)

    # 统计
    print(f"\n符号总数: {st.symbol_count}")
    print(f"作用域数量: {len(st.scopes)}")
