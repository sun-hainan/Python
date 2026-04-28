# -*- coding: utf-8 -*-
"""
数组理论求解器 (Array Theory)
功能：实现SMT-LIB标准中的数组理论

数组理论(数组=映射)：
- select(arr, idx): 读取数组arr在索引idx处的值
- store(arr, idx, val): 返回更新后的数组，arr[idx]=val

公理（read-over-write）：
1. store后读：select(store(a, i, v), i) = v
2. store后读其他位置：i ≠ j → select(store(a, i, v), j) = select(a, j)

作者：Array Theory Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any, Hashable
from abc import ABC, abstractmethod


class ArrayExpr:
    """数组表达式基类"""
    def __init__(self, sort_key: Tuple):
        self.sort_key = sort_key  # (index_sort, value_sort)
    
    @abstractmethod
    def __hash__(self):
        pass
    
    @abstractmethod
    def __eq__(self, other):
        pass


class ArrayConst(ArrayExpr):
    """常量数组"""
    def __init__(self, name: str, idx_sort: str, val_sort: str):
        super().__init__((idx_sort, val_sort))
        self.name = name
    
    def __hash__(self):
        return hash(('const', self.name))
    
    def __eq__(self, other):
        return isinstance(other, ArrayConst) and self.name == other.name
    
    def __repr__(self):
        return self.name


class ArraySelect(ArrayExpr):
    """select(a, i) - 数组读取"""
    def __init__(self, array: ArrayExpr, index: 'ArrayExpr'):
        super().__init__(array.sort_key)
        self.array = array
        self.index = index
    
    def __hash__(self):
        return hash(('select', hash(self.array), hash(self.index)))
    
    def __eq__(self, other):
        return isinstance(other, ArraySelect) and self.array == other.array and self.index == other.index
    
    def __repr__(self):
        return f"select({self.array}, {self.index})"


class ArrayStore(ArrayExpr):
    """store(a, i, v) - 数组更新"""
    def __init__(self, array: ArrayExpr, index: ArrayExpr, value: ArrayExpr):
        super().__init__(array.sort_key)
        self.array = array
        self.index = index
        self.value = value
    
    def __hash__(self):
        return hash(('store', hash(self.array), hash(self.index), hash(self.value)))
    
    def __eq__(self, other):
        return isinstance(other, ArrayStore) and self.array == other.array and self.index == other.index and self.value == other.value
    
    def __repr__(self):
        return f"store({self.array}, {self.index}, {self.value})"


class ArraySolver:
    """
    数组理论求解器
    
    使用符号执行+匹配方法处理数组约束
    维护数组内容的符号映射表
    """

    def __init__(self):
        # 数组变量 → 符号内容映射
        # 格式: {array_name: [(idx1, val1), (idx2, val2), ...]}
        self.array_contents: Dict[str, List[Tuple[Any, Any]]] = {}
        # 等价类
        self.eq_classes: Dict[str, str] = {}
        # 等式约束
        self.equations: Set[Tuple[ArrayExpr, ArrayExpr]] = set()

    def find(self, x: str) -> str:
        """并查集查找"""
        if x not in self.eq_classes:
            self.eq_classes[x] = x
        if self.eq_classes[x] != x:
            self.eq_classes[x] = self.find(self.eq_classes[x])
        return self.eq_classes[x]

    def union(self, x: str, y: str):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.eq_classes[rx] = ry

    def assert_eq(self, e1: ArrayExpr, e2: ArrayExpr):
        """断言数组相等"""
        if isinstance(e1, ArrayConst) and isinstance(e2, ArrayConst):
            self.union(e1.name, e2.name)
        self.equations.add((e1, e2))

    def _get_array_name(self, expr: ArrayExpr) -> Optional[str]:
        """获取数组表达式对应的数组变量名"""
        if isinstance(expr, ArrayConst):
            return self.find(expr.name)
        if isinstance(expr, ArrayStore):
            return self._get_array_name(expr.array)
        return None

    def _eval_select(self, select_expr: ArraySelect) -> Optional[Any]:
        """
        符号求值 select(a, i)
        
        策略：自底向上匹配store表达式
        """
        arr = select_expr.array
        idx = select_expr.index
        
        # 追踪最顶层的store
        stores = []
        while isinstance(arr, ArrayStore):
            stores.append(arr)
            arr = arr.array
        
        # 若底层是常量数组，尝试在映射表中查找
        if isinstance(arr, ArrayConst):
            arr_name = self.find(arr.name)
            if arr_name in self.array_contents:
                for s_idx, s_val in self.array_contents[arr_name]:
                    if self._idx_equal(idx, s_idx):
                        return s_val
        
        # 匹配store：自顶向下查找 i == store_idx
        for store in reversed(stores):
            if self._idx_equal(idx, store.index):
                return store.value
        
        # 无法确定，返回符号值 select(base_arr, idx)
        return select_expr

    def _idx_equal(self, i1: Any, i2: Any) -> bool:
        """检查索引是否相等"""
        if isinstance(i1, ArrayExpr) and isinstance(i2, ArrayExpr):
            return i1 == i2
        return i1 == i2

    def check_sat(self) -> bool:
        """
        检查数组约束可满足性
        
        简化检查：
        1. 检测 select(store(a,i,v), i) = v 形式 → 自动满足
        2. 检测 select(store(a,i,v), j) = select(a,j) where i≠j → 需检查
        """
        for eq1, eq2 in self.equations:
            if isinstance(eq1, ArraySelect) and isinstance(eq2, ArrayConst):
                # 形式: select(...) = const_val
                result = self._eval_select(eq1)
                if result != eq2.name and result != eq2:
                    return False
        
        return True

    def get_model(self) -> Dict[str, Any]:
        """获取模型"""
        return {name: list(content) 
                 for name, content in self.array_contents.items()}


class ExtensionalArraySolver(ArraySolver):
    """
    扩展数组求解器：支持扩展相等性
    
    扩展相等：两个数组相等当且仅当对所有索引它们取值相同
    a = b  ⟺  ∀i. select(a, i) = select(b, i)
    
    在有限域下：展开为所有索引的select相等约束
    """

    def __init__(self, index_domain: List[Any] = None):
        super().__init__()
        self.index_domain = index_domain or []  # 有限索引域

    def check_extensional_eq(self, a1: ArrayExpr, a2: ArrayExpr) -> bool:
        """检查两个数组的扩展相等"""
        if not self.index_domain:
            return True  # 无穷域，无法完全展开
        
        for idx in self.index_domain:
            val1 = self._eval_select(ArraySelect(a1, idx))
            val2 = self._eval_select(ArraySelect(a2, idx))
            if val1 != val2:
                return False
        return True


def example_array_basic():
    """基本数组操作示例"""
    solver = ArraySolver()
    
    a = ArrayConst("a", "Int", "Int")
    b = ArrayConst("b", "Int", "Int")
    i = ArrayConst("i", "Int", "Int")
    j = ArrayConst("j", "Int", "Int")
    v = ArrayConst("v", "Int", "Int")
    
    # b = store(a, i, v)
    store_expr = ArrayStore(a, i, v)
    solver.assert_eq(b, store_expr)
    
    # select(b, i) = v (read-over-write公理1)
    sel = ArraySelect(b, i)
    solver.assert_eq(sel, v)
    
    print(f"store-read公理: {'SAT' if solver.check_sat() else 'UNSAT'}")


def example_array_extensional():
    """扩展相等示例"""
    solver = ExtensionalArraySolver(index_domain=[0, 1, 2, 3])
    
    a = ArrayConst("a", "Int", "Int")
    b = ArrayConst("b", "Int", "Int")
    
    # 在有限域上检查扩展相等
    sat = solver.check_extensional_eq(a, b)
    print(f"数组扩展相等检查: {'可比较' if sat else '无法比较'}")


if __name__ == "__main__":
    print("=" * 50)
    print("数组理论求解器 测试")
    print("=" * 50)
    
    example_array_basic()
    print()
    example_array_extensional()
