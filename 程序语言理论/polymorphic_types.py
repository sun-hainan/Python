# -*- coding: utf-8 -*-

"""

算法实现：程序语言理论 / polymorphic_types



本文件实现 polymorphic_types 相关的算法功能。

"""



from typing import List, Dict, Set, Optional, Tuple

from dataclasses import dataclass, field

from enum import Enum, auto





class Kind(Enum):

    """Kind（类型的类型）"""

    STAR = "*"           # * : 适当类型

    ARROW = "->"         # κ₁ -> κ₂ : 函数Kind





@dataclass

class Type:

    """类型表达式"""

    pass





@dataclass

class T_Var(Type):

    """类型变量"""

    name: str





@dataclass

class T_Const(Type):

    """类型常量（如Int, Bool）"""

    name: str





@dataclass

class T_Forall(Type):

    """全称量化 ∀α::κ. τ"""

    var: str

    kind: Kind

    body: Type





@dataclass

class T_Fun(Type):

    """函数类型 τ₁ → τ₂"""

    domain: Type

    codomain: Type





@dataclass

class T_App(Type):

    """类型应用 T₁ T₂"""

    func: Type

    arg: Type





@dataclass

class T_Abs(Type):

    """类型抽象 λα::κ. τ"""

    var: str

    kind: Kind

    body: Type





@dataclass

class T_Rec(Type):

    """递归类型 μα.τ"""

    var: str

    body: Type





# 标准类型

INT = T_Const("Int")

BOOL = T_Const("Bool")

STRING = T_Const("String")

UNIT = T_Const("Unit")





class Kind_Checker:

    """Kind检查"""

    def __init__(self):

        self.kind_env: Dict[str, Kind] = {}





    def infer_kind(self, t: Type) -> Kind:

        """推断类型的Kind"""

        if isinstance(t, T_Var):

            return self.kind_env.get(t.name, Kind.STAR)

        if isinstance(t, T_Const):

            return Kind.STAR

        if isinstance(t, T_Forall):

            self.kind_env[t.var] = t.kind

            return Kind.STAR

        if isinstance(t, T_Fun):

            return Kind.STAR

        if isinstance(t, T_App):

            func_kind = self.infer_kind(t.func)

            # T_App 的 Kind 取决于函数类型

            return Kind.STAR  # 简化

        if isinstance(t, T_Abs):

            self.kind_env[t.var] = t.kind

            return Kind.ARROW

        return Kind.STAR





@dataclass

class Type_Variable:

    """类型变量（带实例化）"""

    name: str

    level: int = 0

    instance: Optional[Type] = None





@dataclass

class Substitution:

    """类型替换"""

    mapping: Dict[str, Type] = field(default_factory=dict)





    def apply(self, t: Type) -> Type:

        """应用替换"""

        if isinstance(t, T_Var):

            if t.name in self.mapping:

                return self.mapping[t.name]

            return t

        if isinstance(t, T_Forall):

            return T_Forall(t.var, t.kind, self.apply(t.body))

        if isinstance(t, T_Fun):

            return T_Fun(self.apply(t.domain), self.apply(t.codomain))

        if isinstance(t, T_App):

            return T_App(self.apply(t.func), self.apply(t.arg))

        if isinstance(t, T_Abs):

            return T_Abs(t.var, t.kind, self.apply(t.body))

        return t





class Type_Unification:

    """类型统一"""

    @staticmethod

    def unify(t1: Type, t2: Type, subst: Substitution = None) -> Optional[Substitution]:

        """合一两个类型"""

        if subst is None:

            subst = Substitution()

        # 解析实例化

        t1 = subst.apply(t1)

        t2 = subst.apply(t2)

        # 相同类型

        if str(t1) == str(t2):

            return subst

        # 变量

        if isinstance(t1, T_Var):

            subst.mapping[t1.name] = t2

            return subst

        if isinstance(t2, T_Var):

            subst.mapping[t2.name] = t1

            return subst

        # 函数类型

        if isinstance(t1, T_Fun) and isinstance(t2, T_Fun):

            subst = Type_Unification.unify(t1.domain, t2.domain, subst)

            if subst is None:

                return None

            return Type_Unification.unify(t1.codomain, t2.codomain, subst)

        # Forall

        if isinstance(t1, T_Forall) and isinstance(t2, T_Forall):

            return Type_Unification.unify(t1.body, t2.body, subst)

        return None





@dataclass

class Type_Environment:

    """类型环境"""

    env: Dict[str, Type] = field(default_factory=dict)

    parent: Optional['Type_Environment'] = None





    def extend(self, var: str, t: Type) -> 'Type_Environment':

        return Type_Environment(env={**self.env, var: t}, parent=self)





    def lookup(self, var: str) -> Optional[Type]:

        if var in self.env:

            return self.env[var]

        if self.parent:

            return self.parent.lookup(var)

        return None





class FOmega_Type_Checker:

    """Fω类型检查器"""

    def __init__(self):

        self.type_vars: Dict[str, Type_Variable] = {}

        self.next_id: int = 0

        self.substitution = Substitution()





    def fresh_var(self, prefix: str = "α") -> T_Var:

        """生成新的类型变量"""

        name = f"{prefix}{self.next_id}"

        self.next_id += 1

        return T_Var(name)





    def check(self, expr, env: Type_Environment) -> Type:

        """检查表达式类型"""

        # 变量

        if isinstance(expr, str):

            t = env.lookup(expr)

            if t is None:

                raise TypeError(f"Undefined: {expr}")

            return t

        # 整数

        if isinstance(expr, int):

            return INT

        # 布尔

        if isinstance(expr, bool):

            return BOOL

        # λ抽象

        if isinstance(expr, tuple) and len(expr) == 3 and expr[0] == 'lambda':

            _, var, body = expr

            tv = self.fresh_var()

            new_env = env.extend(var, tv)

            body_type = self.check(body, new_env)

            return T_Fun(tv, body_type)

        # 应用

        if isinstance(expr, tuple) and len(expr) == 2:

            func_type = self.check(expr[0], env)

            arg_type = self.check(expr[1], env)

            result_var = self.fresh_var()

            unified = Type_Unification.unify(func_type, T_Fun(arg_type, result_var), self.substitution)

            if unified is None:

                raise TypeError("Type mismatch")

            self.substitution = unified

            return self.substitution.apply(result_var)

        # let

        if isinstance(expr, tuple) and len(expr) == 4 and expr[0] == 'let':

            _, var, val, body = expr

            val_type = self.check(val, env)

            new_env = env.extend(var, val_type)

            return self.check(body, new_env)

        raise TypeError(f"Unknown expr: {expr}")





def generalize(t: Type, env: Type_Environment) -> Type:

    """泛化为多态类型 ∀α.τ"""

    return T_Forall("α", Kind.STAR, t)  # 简化





def instantiate(t: Type, checker: FOmega_Type_Checker) -> Type:

    """实例化多态类型"""

    if isinstance(t, T_Forall):

        fresh = checker.fresh_var()

        return Substitution({t.var: fresh}).apply(t.body)

    return t





def basic_test():

    """基本功能测试"""

    print("=== Fω多态类型系统测试 ===")

    # Kind

    print("\n[Kind]")

    print(f"  Int : *")

    print(f"  α -> β : *")

    print(f"  ∀α.α : *")

    print(f"  λα.α : * -> *")

    # Fω类型

    print("\n[Fω类型]")

    print(f"  T_Var('a') = {T_Var('a')}")

    print(f"  T_Forall('a', STAR, T_Var('a')) = {T_Forall('a', Kind.STAR, T_Var('a'))}")

    print(f"  T_Fun(INT, BOOL) = {T_Fun(INT, BOOL)}")

    # 类型检查

    print("\n[类型检查]")

    checker = FOmega_Type_Checker()

    env = Type_Environment()

    # λx.x

    lam = ('lambda', 'x', 'x')

    t = checker.check(lam, env)

    print(f"  λx.x : {t}")

    # id 42

    app = (('lambda', 'x', 'x'), 42)

    checker2 = FOmega_Type_Checker()

    t = checker2.check(app, env)

    print(f"  (λx.x) 42 : {t}")

    # let多态

    print("\n[Let多态]")

    let_id = ('let', 'id', ('lambda', 'x', 'x'), ('id', 42))

    checker3 = FOmega_Type_Checker()

    t = checker3.check(let_id, env)

    print(f"  let id = λx.x in id 42 : {t}")

    # 类型应用

    print("\n[类型应用]")

    # (Λα.λx:α.x) [Int]

    print("  (Λα.λx:α.x) Int : α → α with α = Int")

    # 递归类型

    print("\n[递归类型]")

    # μα. List α

    rec_type = T_Rec("α", T_App(T_Const("List"), T_Var("α")))

    print(f"  μα. List α = {rec_type}")





if __name__ == "__main__":

    basic_test()

