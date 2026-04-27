# -*- coding: utf-8 -*-

"""

算法实现：程序语言理论 / type_inference



本文件实现 type_inference 相关的算法功能。

"""



from typing import List, Optional, Dict, Set, Tuple, Generic, TypeVar

from dataclasses import dataclass, field

from enum import Enum, auto





class Type_Kind(Enum):

    """类型种类"""

    VARIABLE = auto()

    CONSTRUCTOR = auto()

    FUNCTION = auto()

    TUPLE = auto()

    LIST = auto()





@dataclass

class Type:

    """类型表达式"""

    kind: Type_Kind

    name: str = ""

    arguments: List['Type'] = field(default_factory=list)





class Type_Variable(Type):

    """类型变量"""

    id: int

    instance: Optional['Type'] = None



    def __init__(self, id: int):

        super().__init__(kind=Type_Kind.VARIABLE, name=f"t{id}")

        self.id = id





class Type_Constructor(Type):

    """类型构造器"""

    def __init__(self, name: str, arity: int = 0, arguments: List[Type] = None):

        super().__init__(kind=Type_Kind.CONSTRUCTOR, name=name, arguments=arguments or [])

        self.arity = arity





# 基础类型

T_INT = Type_Constructor("Int", arity=0)

T_BOOL = Type_Constructor("Bool", arity=0)

T_FLOAT = Type_Constructor("Float", arity=0)

T_STRING = Type_Constructor("String", arity=0)





def make_function_type(domain: Type, codomain: Type) -> Type:

    """创建函数类型"""

    return Type_Constructor("->", arity=2, arguments=[domain, codomain])





@dataclass

class Substitution:

    """类型替换"""

    mapping: Dict[int, Type] = field(default_factory=dict)



    def apply(self, t: Type) -> Type:

        """应用替换到类型"""

        if t.kind == Type_Kind.VARIABLE:

            tv = t

            while tv.instance:

                tv = tv.instance

            return tv.instance if tv.instance else t

        elif t.kind == Type_Kind.CONSTRUCTOR:

            new_args = [self.apply(arg) for arg in t.arguments]

            return Type_Constructor(t.name, t.arity, new_args)

        return t



    def compose(self, other: 'Substitution') -> 'Substitution':

        """组合替换"""

        new_mapping = dict(self.mapping)

        for k, v in other.mapping.items():

            new_mapping[k] = self.apply(v)

        return Substitution(mapping=new_mapping)





class Type_Variable_Manager:

    """类型变量管理器"""

    def __init__(self):

        self.next_id = 0

        self.variables: Dict[int, Type_Variable] = {}



    def fresh(self) -> Type_Variable:

        """创建新的类型变量"""

        tv = Type_Variable(self.next_id)

        self.variables[self.next_id] = tv

        self.next_id += 1

        return tv



    def reset(self):

        """重置"""

        self.next_id = 0

        self.variables = {}





@dataclass

class Constraint:

    """类型约束"""

    left: Type

    right: Type





class Unification_Error(Exception):

    """统一错误"""

    pass





class Unifier:

    """合一器"""

    def __init__(self, type_vars: Type_Variable_Manager):

        self.type_vars = type_vars

        self.substitution = Substitution()





    def occurs_check(self, var: Type_Variable, t: Type) -> bool:

        """occurs check：防止无限类型"""

        if t.kind == Type_Kind.VARIABLE:

            return var.id == t.id

        elif t.kind == Type_Kind.CONSTRUCTOR:

            return any(self.occurs_check(var, arg) for arg in t.arguments)

        return False





    def unify(self, t1: Type, t2: Type) -> Substitution:

        """合一两个类型，返回替换"""

        # 解析实例化

        t1 = self.resolve(t1)

        t2 = self.resolve(t2)

        # 相同类型

        if t1.kind == Type_Kind.VARIABLE and t2.kind == Type_Kind.VARIABLE and t1.id == t2.id:

            return Substitution()

        # 处理变量

        if t1.kind == Type_Kind.VARIABLE:

            if self.occurs_check(t1, t2):

                raise Unification_Error(f"Recursive unification")

            t1.instance = t2

            self.substitution.mapping[t1.id] = t2

            return self.substitution

        if t2.kind == Type_Kind.VARIABLE:

            return self.unify(t2, t1)

        # 构造器

        if t1.kind == Type_Kind.CONSTRUCTOR and t2.kind == Type_Kind.CONSTRUCTOR:

            if t1.name != t2.name:

                raise Unification_Error(f"Type mismatch: {t1.name} vs {t2.name}")

            if len(t1.arguments) != len(t2.arguments):

                raise Unification_Error(f"Arity mismatch")

            subst = Substitution()

            for arg1, arg2 in zip(t1.arguments, t2.arguments):

                subst = subst.compose(self.unify(arg1, arg2))

            return self.substitution.compose(subst)

        raise Unification_Error(f"Cannot unify")





    def resolve(self, t: Type) -> Type:

        """解析类型变量"""

        if t.kind == Type_Kind.VARIABLE and t.instance:

            resolved = self.resolve(t.instance)

            t.instance = resolved

            return resolved

        return t





@dataclass

class Type_Environment:

    """类型环境"""

    env: Dict[str, Type] = field(default_factory=dict)

    parent: Optional['Type_Environment'] = None



    def extend(self, var: str, t: Type) -> 'Type_Environment':

        """扩展环境"""

        return Type_Environment(env={**self.env, var: t}, parent=self)



    def lookup(self, var: str) -> Optional[Type]:

        """查找变量类型"""

        if var in self.env:

            return self.env[var]

        if self.parent:

            return self.parent.lookup(var)

        return None





class W_Algorithm:

    """

    W算法（Hindley-Milner类型推断）

    返回: (推断类型, 约束列表, 最终替换)

    """

    def __init__(self):

        self.type_vars = Type_Variable_Manager()

        self.unifier = Unifier(self.type_vars)

        self.constraints: List[Constraint] = []





    def reset(self):

        """重置算法状态"""

        self.type_vars.reset()

        self.unifier = Unifier(self.type_vars)

        self.constraints = []





    def infer(self, expr, env: Type_Environment) -> Tuple[Type, Substitution]:

        """

        推断表达式类型

        W(Γ, e) = (τ, S)

        """

        # 数值

        if isinstance(expr, int):

            return T_INT, Substitution()

        # 布尔

        if isinstance(expr, bool):

            return T_BOOL, Substitution()

        # 字符串

        if isinstance(expr, str) and expr.startswith('"') and expr.endswith('"'):

            return T_STRING, Substitution()

        # 变量

        if isinstance(expr, str):

            var_type = env.lookup(expr)

            if var_type is None:

                raise TypeError(f"Undefined variable: {expr}")

            return var_type, Substitution()

        # λ抽象 λx.e

        if isinstance(expr, tuple) and len(expr) == 3 and expr[0] == 'lambda':

            _, var, body = expr

            tv = self.type_vars.fresh()

            new_env = env.extend(var, tv)

            body_type, subst1 = self.infer(body, new_env)

            return make_function_type(tv, body_type), subst1

        # 函数应用 (e1 e2)

        if isinstance(expr, tuple) and len(expr) == 2:

            func_expr, arg_expr = expr

            func_type, subst1 = self.infer(func_expr, env)

            arg_type, subst2 = self.infer(arg_expr, env)

            result_var = self.type_vars.fresh()

            # 生成约束: func_type = arg_type -> result_var

            func_type_after = subst2.apply(func_type)

            self.constraints.append(Constraint(func_type_after, make_function_type(arg_type, result_var)))

            # 合一所有约束

            final_subst = subst1.compose(subst2)

            for c in self.constraints:

                final_subst = final_subst.compose(self.unifier.unify(c.left, c.right))

            self.constraints = []

            return final_subst.apply(result_var), final_subst

        # let绑定 let x = e1 in e2

        if isinstance(expr, tuple) and len(expr) == 4 and expr[0] == 'let':

            _, var, e1, e2 = expr

            type1, subst1 = self.infer(e1, env)

            new_env = env.extend(var, type1)

            type2, subst2 = self.infer(e2, new_env)

            return type2, subst1.compose(subst2)

        # if e1 then e2 else e3

        if isinstance(expr, tuple) and len(expr) == 4 and expr[0] == 'if':

            _, cond, then_e, else_e = expr

            cond_type, subst1 = self.infer(cond, env)

            then_type, subst2 = self.infer(then_e, env)

            else_type, subst3 = self.infer(else_e, env)

            # 约束: cond = Bool, then = else

            self.constraints.append(Constraint(cond_type, T_BOOL))

            self.constraints.append(Constraint(then_type, else_type))

            final_subst = subst1.compose(subst2).compose(subst3)

            for c in self.constraints:

                final_subst = final_subst.compose(self.unifier.unify(c.left, c.right))

            self.constraints = []

            return final_subst.apply(then_type), final_subst

        raise TypeError(f"Unknown expression: {expr}")





def generalize(t: Type, env: Type_Environment) -> Type:

    """泛化：创建多态类型∀α.τ"""

    return t  # 简化





def instantiate(t: Type, type_vars: Type_Variable_Manager) -> Type:

    """实例化：用fresh变量替换∀量化的变量"""

    if t.kind == Type_Kind.VARIABLE:

        return type_vars.fresh()

    elif t.kind == Type_Kind.CONSTRUCTOR:

        new_args = [instantiate(arg, type_vars) for arg in t.arguments]

        return Type_Constructor(t.name, t.arity, new_args)

    return t





def basic_test():

    """基本功能测试"""

    print("=== W算法类型推断测试 ===")

    w = W_Algorithm()

    env = Type_Environment()

    # 添加预定义

    for name, t in [('+', make_function_type(T_INT, make_function_type(T_INT, T_INT))),

                   ('-', make_function_type(T_INT, make_function_type(T_INT, T_INT))),

                   ('*', make_function_type(T_INT, make_function_type(T_INT, T_INT))),

                   ('/', make_function_type(T_INT, make_function_type(T_INT, T_INT))),

                   ('==', make_function_type(T_INT, make_function_type(T_INT, T_BOOL))),

                   ('<', make_function_type(T_INT, make_function_type(T_INT, T_BOOL))),

                   ('and', make_function_type(T_BOOL, make_function_type(T_BOOL, T_BOOL))),

                   ('or', make_function_type(T_BOOL, make_function_type(T_BOOL, T_BOOL)))]:

        env = env.extend(name, t)

    # 测试

    print("\n[基本表达式]")

    w.reset()

    t, _ = w.infer(42, env)

    print(f"  42 : {t.name}")

    w.reset()

    t, _ = w.infer(True, env)

    print(f"  True : {t.name}")

    # 变量

    w.reset()

    env2 = env.extend('x', T_INT)

    t, _ = w.infer('x', env2)

    print(f"  x : {t.name}")

    # λ抽象

    print("\n[λ抽象]")

    w.reset()

    lam = ('lambda', 'x', ('lambda', 'y', ('x', 'y')))  # λx.λy.x y

    t, _ = w.infer(lam, env)

    print(f"  λx.λy.x y : inferred")

    # 函数应用

    print("\n[函数应用]")

    w.reset()

    app = (('lambda', 'x', E_Var('x') if False else ('lambda', 'x', E_Var('x'))), 42)

    # 简化测试

    app = ('lambda', 'f', ('f', 42))  # (λf. f 42)

    t, _ = w.infer(app, env)

    print(f"  (λf. f 42) : {t.name}")

    # let多态

    print("\n[Let多态]")

    w.reset()

    let_expr = ('let', 'id', ('lambda', 'x', 'x'), ('id', 42))  # let id = λx.x in id 42

    t, _ = w.infer(let_expr, env)

    print(f"  let id = λx.x in id 42 : {t.name}")

    # 复杂表达式

    print("\n[复杂表达式]")

    w.reset()

    complex_expr = ('let', 'twice', ('lambda', 'f', ('lambda', 'x', ('f', ('f', 'x')))),

                   ('twice', ('lambda', 'x', ('+', 'x', 1)), 0))

    t, _ = w.infer(complex_expr, env)

    print(f"  let twice = λf.λx.f(f x) in twice (λx.x+1) 0 : {t.name}")





if __name__ == "__main__":

    basic_test()

