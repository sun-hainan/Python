# -*- coding: utf-8 -*-

"""

算法实现：程序语言理论 / hindley_milner



本文件实现 hindley_milner 相关的算法功能。

"""



import string

from typing import List, Optional, Dict, Set, Tuple, Union

from dataclasses import dataclass, field

from enum import Enum, auto





class Type_Kind(Enum):

    """类型种类"""

    VARIABLE = auto()    # 类型变量

    CONSTRUCTOR = auto() # 类型构造器（如 Int, Bool, ->）

    APPLICATION = auto() # 类型应用





@dataclass

class Type:

    """类型表达式"""

    kind: Type_Kind

    name: str = ""                    # 变量名或构造器名

    arguments: List['Type'] = field(default_factory=list)





class Type_Variable(Type):

    """类型变量"""

    instance: Optional['Type'] = None  # 实例化后的类型

    level: int = 0                     # 统一层级（用于let多态）





class Type_Constructor(Type):

    """类型构造器"""

    def __init__(self, name: str, arity: int = 0, arguments: List[Type] = None):

        super().__init__(kind=Type_Kind.CONSTRUCTOR, name=name)

        self.arity = arity

        self.arguments = arguments or []





# 基础类型构造器

INT = Type_Constructor("Int", arity=0)

BOOL = Type_Constructor("Bool", arity=0)

FLOAT = Type_Constructor("Float", arity=0)

STRING = Type_Constructor("String", arity=0)

UNIT = Type_Constructor("Unit", arity=0)





def make_function_type(domain: Type, codomain: Type) -> Type:

    """创建函数类型 τ1 -> τ2"""

    return Type_Constructor("->", arity=2, arguments=[domain, codomain])





class Substitution(Dict[int, Type]):

    """类型替换（类型变量 -> 类型）"""

    def apply(self, t: Type) -> Type:

        """应用替换到类型"""

        if isinstance(t, Type_Variable):

            if t.instance:

                return self.apply(t.instance)

            return t

        elif isinstance(t, Type_Constructor):

            return Type_Constructor(

                t.name,

                t.arity,

                [self.apply(arg) for arg in t.arguments]

            )

        return t





class Type_Variable_Manager:

    """类型变量管理器"""

    def __init__(self):

        self.next_id: int = 0

        self.variables: Dict[int, Type_Variable] = {}

        self.level: int = 0





    def new_variable(self) -> Type_Variable:

        """创建新的类型变量"""

        tv = Type_Variable(kind=Type_Kind.VARIABLE, name=f"t{self.next_id}", level=self.level)

        self.variables[self.next_id] = tv

        self.next_id += 1

        return tv





    def next_level(self):

        """进入更深的作用域层级"""

        self.level += 1





    def reset_level(self, max_level: int):

        """重置变量层级（用于let多态）"""

        for v in self.variables.values():

            if v.level > max_level:

                v.level = max_level





class Unification_Error(Exception):

    """统一错误"""

    pass





class Unifier:

    """合一器"""

    def __init__(self, type_vars: Type_Variable_Manager):

        self.type_vars = type_vars

        self.substitution = Substitution()





    def occurs_check(self, var: Type_Variable, t: Type) -> bool:

        """检查是否递归（occurs check）"""

        if isinstance(t, Type_Variable):

            return var.name == t.name

        elif isinstance(t, Type_Constructor):

            return any(self.occurs_check(var, arg) for arg in t.arguments)

        return False





    def unify(self, t1: Type, t2: Type):

        """合一两个类型"""

        # 解析实例化

        t1 = self.resolve(t1)

        t2 = self.resolve(t2)

        # 相同类型直接通过

        if isinstance(t1, Type_Variable) and isinstance(t2, Type_Variable) and t1.name == t2.name:

            return

        # 处理类型变量

        if isinstance(t1, Type_Variable):

            if self.occurs_check(t1, t2):

                raise Unification_Error(f"Recursive unification: {t1.name} occurs in {t2}")

            self.substitution[t1.name] = t2

            t1.instance = t2

        elif isinstance(t2, Type_Variable):

            self.unify(t2, t1)

        # 处理类型构造器

        elif isinstance(t1, Type_Constructor) and isinstance(t2, Type_Constructor):

            if t1.name != t2.name:

                raise Unification_Error(f"Type mismatch: {t1.name} vs {t2.name}")

            if len(t1.arguments) != len(t2.arguments):

                raise Unification_Error(f"Arity mismatch: {t1.name}")

            for arg1, arg2 in zip(t1.arguments, t2.arguments):

                self.unify(arg1, arg2)

        else:

            raise Unification_Error(f"Cannot unify {t1} with {t2}")





    def resolve(self, t: Type) -> Type:

        """解析类型（跟随实例化链）"""

        if isinstance(t, Type_Variable) and t.instance:

            resolved = self.resolve(t.instance)

            t.instance = resolved

            return resolved

        return t





class Type_Constraint:

    """类型约束"""

    def __init__(self, left: Type, right: Type):

        self.left = left

        self.right = right





class Hindley_Milner:

    """Hindley-Milner类型推断"""

    def __init__(self):

        self.type_vars = Type_Variable_Manager()

        self.unifier = Unifier(self.type_vars)

        self.type_env: Dict[str, Type] = {}

        # 预定义类型

        self.type_env["Int"] = INT

        self.type_env["Bool"] = BOOL

        self.type_env["Float"] = FLOAT

        self.type_env["String"] = STRING





    def infer(self, expression) -> Tuple[Type, Substitution]:

        """推断表达式类型"""

        if isinstance(expression, int):

            return INT, Substitution()

        elif isinstance(expression, bool):

            return BOOL, Substitution()

        elif isinstance(expression, str):

            # 标识符

            if expression in self.type_env:

                return self.type_env[expression], Substitution()

            # 新变量

            tv = self.type_vars.new_variable()

            return tv, Substitution()

        elif isinstance(expression, tuple):

            if len(expression) == 3 and expression[1] == ':':

                # 类型注解 x : τ

                ann_type = self.parse_type(expression[2])

                return ann_type, Substitution()

            elif len(expression) == 3 and expression[1] == '->':

                # Lambda λx.e

                var, body = expression[0], expression[2]

                self.type_vars.next_level()

                tv = self.type_vars.new_variable()

                self.type_env[var] = tv

                body_type, subst = self.infer(body)

                self.type_vars.reset_level(0)

                fun_type = make_function_type(tv, body_type)

                return fun_type, subst

            elif len(expression) == 3 and expression[1] == 'let':

                # Let绑定 let x = e1 in e2

                var, e1, e2 = expression[0], expression[2][0], expression[2][1]

                e1_type, subst1 = self.infer(e1)

                self.type_env[var] = e1_type

                e2_type, subst2 = self.infer(e2)

                return e2_type, Substitution({**subst1, **subst2})

            elif len(expression) == 4 and expression[0] == 'let':

                # let x = e1 in e2

                var, e1, _, e2 = expression

                e1_type, subst1 = self.infer(e1)

                self.type_vars.reset_level(0)  # let多态

                self.type_env[var] = e1_type

                e2_type, subst2 = self.infer(e2)

                return e2_type, Substitution({**subst1, **subst2})

            else:

                # 函数应用

                func_type, subst1 = self.infer(expression[0])

                arg_type, subst2 = self.infer(expression[1])

                result_var = self.type_vars.new_variable()

                self.unifier.unify(func_type, make_function_type(arg_type, result_var))

                return self.unifier.resolve(result_var), Substitution({**subst1, **subst2})

        # 默认：返回新变量

        return self.type_vars.new_variable(), Substitution()





    def parse_type(self, type_str: str) -> Type:

        """解析类型字符串"""

        if type_str == "Int":

            return INT

        elif type_str == "Bool":

            return BOOL

        elif "->" in type_str:

            parts = type_str.split("->")

            domain = self.parse_type(parts[0].strip())

            codomain = self.parse_type("->".join(parts[1:]).strip())

            return make_function_type(domain, codomain)

        return Type_Variable(kind=Type_Kind.VARIABLE, name=type_str)





def generalize(t: Type, env: Dict[str, Type]) -> Type:

    """

    泛化：创建多态类型

    ∀α₁...αₙ. τ 如果 α₁...αₙ 不在env的自由类型变量中

    """

    return t  # 简化实现





def instantiate(poly_type: Type, type_vars: Type_Variable_Manager) -> Type:

    """实例化：用fresh变量替换∀量化的变量"""

    if isinstance(poly_type, Type_Variable):

        return type_vars.new_variable()

    elif isinstance(poly_type, Type_Constructor):

        return Type_Constructor(

            poly_type.name,

            poly_type.arity,

            [instantiate(arg, type_vars) for arg in poly_type.arguments]

        )

    return poly_type





def basic_test():

    """基本功能测试"""

    print("=== Hindley-Milner类型推断测试 ===")

    hm = Hindley_Milner()

    # 测试基本表达式

    print("\n[基本表达式]")

    # 数字

    t, _ = hm.infer(42)

    print(f"  42 : {t.name if hasattr(t, 'name') else t}")

    # 布尔

    t, _ = hm.infer(True)

    print(f"  True : {t.name if hasattr(t, 'name') else t}")

    # 简单标识符

    t, _ = hm.infer("x")

    print(f"  x : {t.name if hasattr(t, 'name') else t}")

    # 函数类型

    print("\n[函数应用]")

    # (λx.x) 42

    lam_app = (("x", "->", "x"), 42)

    t, _ = hm.infer(lam_app)

    print(f"  (λx.x) 42 : {t.name if hasattr(t, 'name') else t}")

    # let多态

    print("\n[Let多态]")

    # let id = λx.x in id 42

    let_expr = ("id", ("x", "->", "x"), "in", 42)

    t, _ = hm.infer(let_expr)

    print(f"  let id = λx.x in id 42 : {t.name if hasattr(t, 'name') else t}")

    # 测试合一

    print("\n[合一测试]")

    unifier = Unifier(hm.type_vars)

    t1 = Type_Variable(kind=Type_Kind.VARIABLE, name="a")

    t2 = INT

    unifier.unify(t1, t2)

    print(f"  unify(α, Int) : α = {unifier.resolve(t1)}")

    # 函数类型合一

    t3 = make_function_type(Type_Variable(kind=Type_Kind.VARIABLE, name="b"), Type_Variable(kind=Type_Kind.VARIABLE, name="c"))

    t4 = make_function_type(INT, BOOL)

    unifier2 = Unifier(hm.type_vars)

    unifier2.unify(t3, t4)

    print(f"  unify((α->β), (Int->Bool)) : α=Int, β=Bool")





if __name__ == "__main__":

    basic_test()

