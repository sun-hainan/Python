# -*- coding: utf-8 -*-

"""

算法实现：程序语言理论 / effect_systems



本文件实现 effect_systems 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional, Callable, Generic, TypeVar

from dataclasses import dataclass, field

from enum import Enum, auto





class Effect(Enum):

    """效果基类"""

    pass





@dataclass

class E_Read(Effect):

    """读取环境"""

    pass





@dataclass

class E_Write(Effect):

    """写入环境"""

    pass





@dataclass

class E_Alloc(Effect):

    """内存分配"""

    pass





@dataclass

class E_Throw(Effect):

    """异常抛出"""

    pass





@dataclass

class E_State(Effect):

    """状态操作"""

    label: str





class Effect_Set:

    """效果集"""

    def __init__(self, effects: Set[Effect] = None):

        self.effects = effects or set()





    def union(self, other: 'Effect_Set') -> 'Effect_Set':

        return Effect_Set(self.effects | other.effects)





    def is_subset(self, other: 'Effect_Set') -> bool:

        return self.effects <= other.effects





    def __str__(self):

        if not self.effects:

            return "∅"

        return "{" + ", ".join(str(e) for e in self.effects) + "}"





@dataclass

class Type_With_Effect:

    """带效果的类型 τ [ε]"""

    type_expr: 'Type'

    effects: Effect_Set





class Type:

    """类型表达式"""

    pass





@dataclass

class T_Int(Type):

    pass





@dataclass

class T_Bool(Type):

    pass





@dataclass

class T_Unit(Type):

    pass





@dataclass

class T_Fun(Type):

    """函数类型 τ₁ → τ₂ [ε]"""

    domain: Type

    codomain: Type

    effect: Effect_Set





@dataclass

class T_Var(Type):

    name: str





@dataclass

class T_List(Type):

    element: Type





class Effect_Inference:

    """效果推断"""

    def __init__(self):

        self.effect_env: Dict[str, Effect_Set] = {}





    def infer(self, expr) -> Type_With_Effect:

        """推断表达式类型和效果"""

        # 整数

        if isinstance(expr, int):

            return Type_With_Effect(T_Int(), Effect_Set())

        # 布尔

        if isinstance(expr, bool):

            return Type_With_Effect(T_Bool(), Effect_Set())

        # 变量

        if isinstance(expr, str):

            if expr in self.effect_env:

                return Type_With_Effect(T_Var(expr), self.effect_env[expr])

            return Type_With_Effect(T_Var(expr), Effect_Set())

        # λ抽象

        if isinstance(expr, tuple) and len(expr) == 3 and expr[0] == 'lambda':

            _, var, body = expr

            old_env = dict(self.effect_env)

            self.effect_env[var] = Effect_Set()

            body_type = self.infer(body)

            self.effect_env = old_env

            return Type_With_Effect(

                T_Fun(T_Var(var), body_type.type_expr, body_type.effects),

                Effect_Set()

            )

        # 应用

        if isinstance(expr, tuple) and len(expr) == 2:

            func_type = self.infer(expr[0])

            arg_type = self.infer(expr[1])

            if isinstance(func_type.type_expr, T_Fun):

                eff = func_type.effects.union(arg_type.effects)

                return Type_With_Effect(func_type.type_expr.codomain, eff)

            return Type_With_Effect(T_Var("?"), func_type.effects.union(arg_type.effects))

        # let

        if isinstance(expr, tuple) and len(expr) == 4 and expr[0] == 'let':

            _, var, val, body = expr

            val_type = self.infer(val)

            old_env = dict(self.effect_env)

            self.effect_env[var] = val_type.effects

            body_type = self.infer(body)

            self.effect_env = old_env

            return Type_With_Effect(body_type.type_expr, val_type.effects.union(body_type.effects))

        return Type_With_Effect(T_Var("?"), Effect_Set())





class Effect_Polymorphism:

    """效果多态"""

    @staticmethod

    def generalize(t: Type_With_Effect, env: Dict[str, Effect_Set]) -> str:

        """泛化为效果多态类型"""

        # 简化

        effects = t.effects

        type_str = str(t.type_expr)

        if effects.effects:

            return f"{type_str} [{effects}]"

        return type_str





@dataclass

class Effect_Handler:

    """效果处理器"""

    name: str

    handle: Callable





class Handler_Combination:

    """处理器组合"""

    @staticmethod

    def compose(h1: Effect_Handler, h2: Effect_Handler) -> Effect_Handler:

        """组合两个处理器"""

        def combined(eff, continuation):

            # 先尝试h1，再尝试h2

            try:

                return h1.handle(eff, continuation)

            except:

                return h2.handle(eff, continuation)

        return Effect_Handler(f"{h1.name}+{h2.name}", combined)





class Strictness_Analysis:

    """严格性分析（基于效果）"""

    @staticmethod

    def is_strict(effects: Effect_Set) -> bool:

        """检查是否必须严格求值"""

        # 如果有异常效果，必须严格

        for eff in effects.effects:

            if isinstance(eff, E_Throw):

                return True

        return False





class Resource_Bounded_Effects:

    """资源受限效果"""

    @staticmethod

    def check_bounds(effects: Effect_Set, limit: int) -> bool:

        """检查是否在资源限制内"""

        return len(effects.effects) <= limit





def basic_test():

    """基本功能测试"""

    print("=== 效果系统测试 ===")

    # 效果集

    print("\n[效果集]")

    e1 = Effect_Set({E_Read(), E_Write()})

    e2 = Effect_Set({E_Read()})

    print(f"  {{read, write}} ∪ {{read}} = {e1.union(e2)}")

    print(f"  {{read}} ⊆ {{read, write}}? {e2.is_subset(e1)}")

    # 带效果的类型

    print("\n[带效果的类型]")

    t = Type_With_Effect(T_Int(), Effect_Set({E_Read()}))

    print(f"  Int [read] = {t.type_expr}, {t.effects}")

    # 效果推断

    print("\n[效果推断]")

    infer = Effect_Inference()

    # 42

    t1 = infer.infer(42)

    print(f"  42 : {t1.type_expr}, effects={t1.effects}")

    # λx.x

    t2 = infer.infer(('lambda', 'x', 'x'))

    print(f"  λx.x : {t2.type_expr}, effects={t2.effects}")

    # let x = 1 in x

    t3 = infer.infer(('let', 'x', 1, 'x'))

    print(f"  let x = 1 in x : {t3.type_expr}, effects={t3.effects}")

    # 效果多态

    print("\n[效果多态]")

    poly = Effect_Polymorphism.generalize(t2, {})

    print(f"  generalize(λx.x) = {poly}")

    # 效果处理器

    print("\n[效果处理器]")

    h1 = Effect_Handler("state", lambda e, k: k() if isinstance(e, E_State) else None)

    h2 = Effect_Handler("exn", lambda e, k: k() if isinstance(e, E_Throw) else None)

    combined = Handler_Combination.compose(h1, h2)

    print(f"  组合处理器: {combined.name}")





if __name__ == "__main__":

    basic_test()

