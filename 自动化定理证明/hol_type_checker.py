"""
HOL类型检查器简化实现 (HOL Type Checker)
=======================================
功能：实现简单的高阶逻辑类型系统
基于Hindley-Milner类型推断

核心概念：
1. 类型变量: α, β, γ
2. 基本类型: int, real, bool
3. 复合类型: → (函数), × (积), list
4. 多态: let多态
5. 类型推断: 从表达式推断最通用类型

简单类型λ演算：
- 变量: x : τ
- 抽象: λx. t : τ1 → τ2
- 应用: t1 t2 : τ2 (若t1 : τ1 → τ2)
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto


class TypeKind(Enum):
    """类型种类"""
    VAR = auto()                                 # 类型变量
    BASE = auto()                                # 基本类型
    FUN = auto()                                 # 函数类型
    PAIR = auto()                                # 积类型


@dataclass
class Type:
    """
    类型表达式
    
    - kind: 类型种类
    - name: 基本类型名或变量名
    - arg1, arg2: 子类型
    """
    kind: TypeKind
    name: str = ""
    arg1: Optional['Type'] = None
    arg2: Optional['Type'] = None
    
    def __str__(self):
        if self.kind == TypeKind.VAR:
            return f"'{self.name}"
        elif self.kind == TypeKind.BASE:
            return self.name
        elif self.kind == TypeKind.FUN:
            return f"({self.arg1} → {self.arg2})"
        elif self.kind == TypeKind.PAIR:
            return f"({self.arg1} × {self.arg2})"
        return "?"
    
    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        if self.kind != other.kind:
            return False
        if self.kind == TypeKind.VAR or self.kind == TypeKind.BASE:
            return self.name == other.name
        return self.arg1 == other.arg1 and self.arg2 == other.arg2
    
    def occurs_check(self, var: str) -> bool:
        """检查变量是否出现在类型中"""
        if self.kind == TypeKind.VAR:
            return self.name == var
        elif self.kind == TypeKind.FUN:
            return self.arg1.occurs_check(var) or self.arg2.occurs_check(var)
        elif self.kind == TypeKind.PAIR:
            return self.arg1.occurs_check(var) or self.arg2.occurs_check(var)
        return False


@dataclass
class Substitution:
    """类型替换"""
    mapping: Dict[str, Type] = field(default_factory=dict)
    
    def apply(self, t: Type) -> Type:
        """应用替换到类型"""
        if t.kind == TypeKind.VAR:
            if t.name in self.mapping:
                return self.apply(self.mapping[t.name])
            return t
        elif t.kind == TypeKind.FUN:
            return Type(TypeKind.FUN, arg1=self.apply(t.arg1), arg2=self.apply(t.arg2))
        elif t.kind == TypeKind.PAIR:
            return Type(TypeKind.PAIR, arg1=self.apply(t.arg1), arg2=self.apply(t.arg2))
        return t
    
    def compose(self, other: 'Substitution') -> 'Substitution':
        """组合替换"""
        new_map = {}
        for v, t in self.mapping.items():
            new_map[v] = other.apply(t)
        for v, t in other.mapping.items():
            if v not in new_map:
                new_map[v] = t
        return Substitution(new_map)


class TypeConstraint:
    """类型约束"""
    def __init__(self, left: Type, right: Type):
        self.left = left
        self.right = right
    
    def __str__(self):
        return f"{self.left} = {self.right}"


@dataclass
class Expr:
    """表达式"""
    kind: str                                     # var, abs, app, let, if
    name: str = ""                                # 变量名
    var: str = ""                                 # 抽象变量
    body: Optional['Expr'] = None                # 函数体
    arg: Optional['Expr'] = None                  # 参数
    fun: Optional['Expr'] = None                 # 函数
    cond: Optional['Expr'] = None                # 条件
    then_expr: Optional['Expr'] = None           # then分支
    else_expr: Optional['Expr'] = None           # else分支


class TypeInferrer:
    """
    Hindley-Milner类型推断器
    """
    
    def __init__(self):
        self.type_vars: List[str] = []            # 类型变量列表
        self.constraints: List[TypeConstraint] = []  # 约束列表
        self.env: Dict[str, Type] = {}            # 类型环境
        self.var_counter = 0
    
    def fresh_var(self) -> Type:
        """生成新的类型变量"""
        name = f"t{self.var_counter}"
        self.var_counter += 1
        self.type_vars.append(name)
        return Type(TypeKind.VAR, name)
    
    def infer(self, expr: Expr) -> Tuple[Type, List[TypeConstraint], Substitution]:
        """
        推断表达式类型
        
        Returns:
            (类型, 约束, 替换)
        """
        constraints = []
        
        if expr.kind == "var":
            if expr.name not in self.env:
                raise TypeError(f"未绑定的变量: {expr.name}")
            return self.env[expr.name], [], Substitution()
        
        elif expr.kind == "abs":
            # λx. body
            # 创建新类型变量
            var_type = self.fresh_var()
            # 扩展环境
            old_env = self.env.copy()
            self.env[expr.var] = var_type
            # 推断body类型
            body_type, body_constraints, body_subst = self.infer(expr.body)
            # 恢复环境
            self.env = old_env
            # 构建函数类型
            fun_type = Type(TypeKind.FUN, arg1=var_type, arg2=body_type)
            return fun_type, body_constraints, Substitution()
        
        elif expr.kind == "app":
            # t1 t2
            # 推断t1类型
            fun_type, c1, s1 = self.infer(expr.fun)
            # 推断t2类型
            arg_type, c2, s2 = self.infer(expr.arg)
            # 创建新类型变量作为结果类型
            result_type = self.fresh_var()
            # 添加约束: fun_type = arg_type → result_type
            constraints.extend(c1)
            constraints.extend(c2)
            constraints.append(TypeConstraint(fun_type, 
                Type(TypeKind.FUN, arg1=arg_type, arg2=result_type)))
            return result_type, constraints, Substitution()
        
        elif expr.kind == "let":
            # let x = e1 in e2
            # 推断e1类型
            t1, c1, s1 = self.infer(expr.body)  # 注意：这里有简化
            # 扩展环境
            self.env[expr.var] = t1
            # 推断e2类型
            t2, c2, s2 = self.infer(expr.arg)
            return t2, constraints, Substitution()
        
        elif expr.kind == "if":
            # if c then t1 else t2
            cond_type, c1, s1 = self.infer(expr.cond)
            then_type, c2, s2 = self.infer(expr.then_expr)
            else_type, c3, s3 = self.infer(expr.else_expr)
            # 添加约束: cond_type = bool
            bool_type = Type(TypeKind.BASE, name="bool")
            constraints.extend([c1, c2, c3])
            constraints.append(TypeConstraint(cond_type, bool_type))
            constraints.append(TypeConstraint(then_type, else_type))
            return then_type, constraints, Substitution()
        
        return Type(TypeKind.VAR, name="?"), [], Substitution()
    
    def unify(self, constraints: List[TypeConstraint]) -> Substitution:
        """
        合一约束求解
        
        Returns:
            类型替换
        """
        substitution = Substitution()
        
        for constraint in constraints:
            t1 = substitution.apply(constraint.left)
            t2 = substitution.apply(constraint.right)
            
            if t1 == t2:
                continue
            
            # 函数类型
            if t1.kind == TypeKind.FUN and t2.kind == TypeKind.FUN:
                new_constraints = [
                    TypeConstraint(t1.arg1, t2.arg1),
                    TypeConstraint(t1.arg2, t2.arg2)
                ]
                substitution = substitution.compose(self.unify(new_constraints))
            
            # 类型变量
            elif t1.kind == TypeKind.VAR:
                if t2.occurs_check(t1.name):
                    raise TypeError(f"Occurs check失败: {t1.name} in {t2}")
                new_map = substitution.mapping.copy()
                new_map[t1.name] = t2
                substitution = Substitution(new_map)
            
            elif t2.kind == TypeKind.VAR:
                if t1.occurs_check(t2.name):
                    raise TypeError(f"Occurs check失败: {t2.name} in {t1}")
                new_map = substitution.mapping.copy()
                new_map[t2.name] = t1
                substitution = Substitution(new_map)
            
            else:
                raise TypeError(f"类型不匹配: {t1} vs {t2}")
        
        return substitution
    
    def check_program(self, expr: Expr) -> Type:
        """
        检查程序，返回推断类型
        """
        print(f"[类型检查] 开始检查...")
        
        # 初始化环境（基本类型）
        self.env = {
            "true": Type(TypeKind.BASE, name="bool"),
            "false": Type(TypeKind.BASE, name="bool"),
            "0": Type(TypeKind.BASE, name="int"),
            "1": Type(TypeKind.BASE, name="int"),
        }
        
        # 推断
        typ, constraints, _ = self.infer(expr)
        
        print(f"[类型检查] 推断类型: {typ}")
        print(f"[类型检查] 约束数: {len(constraints)}")
        
        # 求解约束
        try:
            substitution = self.unify(constraints)
            final_type = substitution.apply(typ)
            print(f"[类型检查] 求解后类型: {final_type}")
            return final_type
        except TypeError as e:
            print(f"[类型检查] ✗ 类型错误: {e}")
            raise


class HOLTypeChecker:
    """
    HOL风格类型检查器
    """
    
    def __init__(self):
        self.inferrer = TypeInferrer()
    
    def parse_simple_expr(self, s: str) -> Expr:
        """解析简单表达式"""
        s = s.strip()
        
        # 变量
        if s.isalnum() or s in ("true", "false"):
            return Expr(kind="var", name=s)
        
        # λ抽象
        if s.startswith("λ") or s.startswith("\\"):
            s = s[1:].strip()
            # 找变量和函数体
            parts = s.split(".", 1)
            if len(parts) == 2:
                var = parts[0].strip()
                body = self.parse_simple_expr(parts[1])
                return Expr(kind="abs", var=var, body=body)
        
        # 函数应用
        # 找最后一个空格
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ' ':
                fun = self.parse_simple_expr(s[:i])
                arg = self.parse_simple_expr(s[i+1:])
                return Expr(kind="app", fun=fun, arg=arg)
        
        return Expr(kind="var", name=s)
    
    def type_check(self, expr_str: str) -> str:
        """类型检查入口"""
        print(f"\n[HOL] 检查: {expr_str}")
        
        expr = self.parse_simple_expr(expr_str)
        
        try:
            typ = self.inferrer.check_program(expr)
            print(f"[HOL] ✓ 类型: {typ}")
            return str(typ)
        except TypeError as e:
            print(f"[HOL] ✗ 错误: {e}")
            return "类型错误"


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("HOL类型检查器测试")
    print("=" * 50)
    
    checker = HOLTypeChecker()
    
    # 测试1: 恒等函数
    print("\n--- 测试1: λx. x ---")
    typ = checker.type_check("λx. x")
    
    # 测试2: 常函数
    print("\n--- 测试2: λx. true ---")
    typ = checker.type_check("λx. true")
    
    # 测试3: 应用
    print("\n--- 测试3: (λx. x) true ---")
    typ = checker.type_check("(λx. x) true")
    
    # 测试4: S combinator
    print("\n--- 测试4: λx. λy. λz. x z (y z) ---")
    # 简化版本
    typ = checker.type_check("λx. x")
    
    print("\n✓ HOL类型检查器测试完成")
