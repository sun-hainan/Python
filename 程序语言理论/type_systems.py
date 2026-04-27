# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / type_systems

本文件实现 type_systems 相关的算法功能。
"""

from typing import List, Optional, Dict, Set, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum, auto


class Type_Kind(Enum):
    """类型种类"""
    PRIMITIVE = auto()      # 基元类型（int, bool, string等）
    FUNCTION = auto()       # 函数类型
    PRODUCT = auto()       # 乘积类型（元组）
    SUM = auto()           # 和类型（tagged union）
    POLYMORPHIC = auto()   # 多态类型
    DEPENDENT = auto()     # 从属类型
    REF = auto()           # 引用类型


@dataclass
class Type:
    """类型"""
    kind: Type_Kind
    name: str = ""
    params: List['Type'] = field(default_factory=list)
    # 函数类型参数
    domain: Optional['Type'] = None  # 定义域
    codomain: Optional['Type'] = None  # 值域


class Primitive_Types:
    """基元类型集合"""
    INT = Type(Type_Kind.PRIMITIVE, name="Int")
    BOOL = Type(Type_Kind.PRIMITIVE, name="Bool")
    STRING = Type(Type_Kind.PRIMITIVE, name="String")
    FLOAT = Type(Type_Kind.PRIMITIVE, name="Float")
    UNIT = Type(Type_Kind.PRIMITIVE, name="Unit")
    ANY = Type(Type_Kind.PRIMITIVE, name="Any")


class Type_Variables:
    """类型变量（用于多态）"""
    def __init__(self):
        self.variables: Dict[str, Type] = {}
        self.next_id: int = 0


    def fresh(self, prefix: str = "α") -> Type:
        """生成新的类型变量"""
        name = f"{prefix}{self.next_id}"
        self.next_id += 1
        var = Type(Type_Kind.POLYMORPHIC, name=name)
        self.variables[name] = var
        return var


    def instantiate(self, poly_type: Type) -> Type:
        """多态类型实例化"""
        # 替换类型变量为fresh变量
        if poly_type.kind == Type_Kind.FUNCTION:
            new_domain = self.instantiate(poly_type.domain)
            new_codomain = self.instantiate(poly_type.codomain)
            return Type(Type_Kind.FUNCTION, domain=new_domain, codomain=new_codomain)
        return poly_type


class Type_Environment:
    """类型环境（变量到类型的映射）"""
    def __init__(self):
        self.env: Dict[str, Type] = {}
        self.parent: Optional['Type_Environment'] = None


    def extend(self, var: str, t: Type) -> 'Type_Environment':
        """扩展环境"""
        new_env = Type_Environment()
        new_env.env = dict(self.env)
        new_env.env[var] = t
        new_env.parent = self.parent
        return new_env


    def lookup(self, var: str) -> Optional[Type]:
        """查找变量类型"""
        if var in self.env:
            return self.env[var]
        if self.parent:
            return self.parent.lookup(var)
        return None


@dataclass
class Type_Constraint:
    """类型约束"""
    left: Type
    right: Type


class Type_Checker:
    """类型检查器"""
    def __init__(self):
        self.constraints: List[Type_Constraint] = []
        self.type_vars = Type_Variables()


    def unify(self, t1: Type, t2: Type) -> bool:
        """合一（Unification）"""
        # 基础情况
        if t1.kind == Type_Kind.PRIMITIVE and t2.kind == Type_Kind.PRIMITIVE:
            return t1.name == t2.name
        if t1.kind == Type_Kind.FUNCTION and t2.kind == Type_Kind.FUNCTION:
            # 函数类型需要定义域和值域都匹配
            return self.unify(t1.domain, t2.domain) and self.unify(t1.codomain, t2.codomain)
        if t1.kind == Type_Kind.POLYMORPHIC:
            # 类型变量
            return True  # 简化
        if t2.kind == Type_Kind.POLYMORPHIC:
            return True
        # 乘积类型
        if t1.kind == Type_Kind.PRODUCT and t2.kind == Type_Kind.PRODUCT:
            if len(t1.params) != len(t2.params):
                return False
            return all(self.unify(p1, p2) for p1, p2 in zip(t1.params, t2.params))
        return False


    def check_expression(self, expr: str, env: Type_Environment) -> Tuple[Type, Type_Environment]:
        """
        检查表达式类型
        返回: (类型, 新环境)
        """
        # 简化的表达式解析
        if expr.isdigit():
            return Primitive_Types.INT, env
        if expr in ["True", "False"]:
            return Primitive_Types.BOOL, env
        if expr.startswith("(") and expr.endswith(")"):
            # 函数应用或元组
            return Primitive_Types.UNIT, env
        # 变量
        var_type = env.lookup(expr)
        if var_type:
            return var_type, env
        return Primitive_Types.ANY, env


class Type_System_Properties:
    """类型系统性质"""
    @staticmethod
    def is_sound(system_name: str) -> bool:
        """类型系统是否类型安全"""
        # Progress + Preservation = Safety
        return True  # 大多数现代类型系统是安全的


    @staticmethod
    def is_decidable(system_name: str) -> bool:
        """类型检查是否可判定"""
        # 从属类型检查不可判定
        return system_name != "dependent"


@dataclass
class Subtype_Relation:
    """子类型关系"""
    def __init__(self):
        self.relations: Set[Tuple[str, str]] = set()


    def add_relation(self, sub: str, super_type: str):
        """添加子类型关系"""
        self.relations.add((sub, super_type))


    def is_subtype(self, t1: Type, t2: Type) -> bool:
        """检查是否是子类型"""
        if t1.kind == Type_Kind.PRIMITIVE and t2.kind == Type_Kind.PRIMITIVE:
            return t1.name == t2.name or (t1.name, t2.name) in self.relations
        if t1.kind == Type_Kind.FUNCTION and t2.kind == Type_Kind.FUNCTION:
            # 协变/逆变规则
            return self.is_subtype(t2.domain, t1.domain) and self.is_subtype(t1.codomain, t2.codomain)
        return False


class Dependent_Type_Expr:
    """从属类型表达式（简化）"""
    def __init__(self, base_type: str, predicate: str):
        self.base_type = base_type
        self.predicate = predicate


    def check(self, value: Any) -> bool:
        """检查值是否满足谓词"""
        # 简化实现
        return True


def basic_test():
    """基本功能测试"""
    print("=== 类型系统基础测试 ===")
    # 基元类型
    print("\n[基元类型]")
    print(f"  Int: {Primitive_Types.INT}")
    print(f"  Bool: {Primitive_Types.BOOL}")
    # 函数类型
    print("\n[函数类型]")
    fn_type = Type(Type_Kind.FUNCTION, domain=Primitive_Types.INT, codomain=Primitive_Types.BOOL)
    print(f"  Int -> Bool: {fn_type.name or 'anonymous'}")
    print(f"    定义域: {fn_type.domain.name}, 值域: {fn_type.codomain.name}")
    # 类型变量
    print("\n[类型变量]")
    tv = Type_Variables()
    alpha = tv.fresh()
    beta = tv.fresh()
    print(f"  α0: {alpha.name}")
    print(f"  α1: {beta.name}")
    # 类型环境
    print("\n[类型环境]")
    env = Type_Environment()
    env = env.extend("x", Primitive_Types.INT)
    env = env.extend("f", Type(Type_Kind.FUNCTION, domain=Primitive_Types.INT, codomain=Primitive_Types.INT))
    print(f"  x: {env.lookup('x').name}")
    print(f"  f: {env.lookup('f').name or 'Int->Int'}")
    # 类型检查
    print("\n[类型检查]")
    checker = Type_Checker()
    t, _ = checker.check_expression("42", env)
    print(f"  '42' has type: {t.name}")
    # 子类型
    print("\n[子类型关系]")
    subtype = Subtype_Relation()
    subtype.add_relation("Int", "Num")
    subtype.add_relation("Num", "Any")
    int_type = Type(Type_Kind.PRIMITIVE, name="Int")
    any_type = Type(Type_Kind.PRIMITIVE, name="Any")
    print(f"  Int <: Any? {subtype.is_subtype(int_type, any_type)}")
    # 从属类型
    print("\n[从属类型]")
    dep = Dependent_Type_Expr("Vector", "length > 0")
    print(f"  Vec[n] where n > 0")


if __name__ == "__main__":
    basic_test()
