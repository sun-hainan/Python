# -*- coding: utf-8 -*-

"""

算法实现：形式验证 / invariant_generation



本文件实现 invariant_generation 相关的算法功能。

"""



import numpy as np

from collections import defaultdict

from itertools import product





class InvariantGenerator:

    """

    不变量生成器

    

    使用Fixpoint迭代计算程序不变量

    """

    

    def __init__(self):

        self.variables = set()

        self.program = None

    

    def analyze(self, program):

        """

        分析程序生成不变量

        

        参数:

            program: 程序语句列表

        

        返回:

            不变量字典

        """

        self.program = program

        

        # 收集变量

        self._collect_variables(program)

        

        # 初始化环境

        env = {var: Interval.top() for var in self.variables}

        

        # 分析程序

        return self._analyze_statements(program, env)

    

    def _collect_variables(self, program):

        """收集程序中的变量"""

        for stmt in program:

            if isinstance(stmt, tuple):

                if stmt[0] == 'assign':

                    self.variables.add(stmt[1])

                elif stmt[0] == 'while':

                    self._collect_variables(stmt[2] if len(stmt) > 2 else [])

    

    def _analyze_statements(self, stmts, env):

        """分析语句序列"""

        result_env = env.copy()

        

        for stmt in stmts:

            result_env = self._analyze_stmt(stmt, result_env)

        

        return result_env

    

    def _analyze_stmt(self, stmt, env):

        """分析单条语句"""

        if not isinstance(stmt, tuple):

            return env

        

        op = stmt[0]

        

        if op == 'assign':

            var = stmt[1]

            expr = stmt[2]

            new_interval = self._eval_expr(expr, env)

            env = env.copy()

            env[var] = new_interval

        

        elif op == 'if':

            cond = stmt[1]

            then_stmts = stmt[2] if len(stmt) > 2 else []

            else_stmts = stmt[3] if len(stmt) > 3 else []

            

            # 分析then分支

            then_env = env.copy()

            for s in then_stmts:

                then_env = self._analyze_stmt(s, then_env)

            

            # 分析else分支

            else_env = env.copy()

            for s in else_stmts:

                else_env = self._analyze_stmt(s, else_env)

            

            # 合并

            for var in set(list(then_env.keys()) + list(else_env.keys())):

                t_val = then_env.get(var, Interval.top())

                e_val = else_env.get(var, Interval.top())

                env[var] = t_val.lub(e_val)

        

        elif op == 'while':

            cond = stmt[1]

            body = stmt[2] if len(stmt) > 2 else []

            

            # 迭代计算循环不变量

            env = self._compute_loop_invariant(cond, body, env)

        

        return env

    

    def _compute_loop_invariant(self, cond, body, initial_env):

        """

        计算循环不变量

        

        使用Widening保证终止

        """

        # 初始：假设循环不变量为initial_env

        inv = initial_env.copy()

        old_inv = None

        

        iteration = 0

        max_iterations = 20

        

        while old_inv is None or inv != old_inv:

            if iteration >= max_iterations:

                break

            

            iteration += 1

            

            # 应用循环条件约束

            cond_env = self._apply_condition(cond, inv)

            

            # 应用循环体

            body_env = cond_env.copy()

            for stmt in body:

                body_env = self._analyze_stmt(stmt, body_env)

            

            # Widening：确保收敛

            new_inv = {}

            for var in set(list(inv.keys()) + list(body_env.keys())):

                old_val = inv.get(var, Interval.top())

                new_val = body_env.get(var, Interval.top())

                new_inv[var] = old_val.widening(new_val)

            

            old_inv = inv

            inv = new_inv

        

        return inv

    

    def _eval_expr(self, expr, env):

        """求值表达式"""

        if isinstance(expr, tuple):

            op = expr[0]

            

            if op == 'var':

                return env.get(expr[1], Interval.top())

            

            if op == 'const':

                return Interval(expr[1], expr[1])

            

            if op == '+':

                left = self._eval_expr(expr[1], env)

                right = self._eval_expr(expr[2], env)

                return Interval(left.low + right.low, left.high + right.high)

            

            if op == '-':

                left = self._eval_expr(expr[1], env)

                right = self._eval_expr(expr[2], env)

                return Interval(left.low - right.high, left.high - right.low)

            

            if op == '*':

                left = self._eval_expr(expr[1], env)

                right = self._eval_expr(expr[2], env)

                return Interval(left.low * right.low, left.high * right.high)

        

        return Interval.top()

    

    def _apply_condition(self, cond, env):

        """应用条件约束"""

        if not isinstance(cond, tuple):

            return env

        

        op = cond[0]

        env = env.copy()

        

        if op in ('<', '<=', '>', '>=', '==', '!='):

            # 简化处理

            pass

        

        return env





class RelationalInvariant:

    """

    关系不变量

    

    追踪变量之间的关系，如 x < y, x + y = 10

    """

    

    def __init__(self):

        self.invariants = []  # 不变量列表

    

    def add_invariant(self, inv):

        """添加不变量"""

        self.invariants.append(inv)

    

    def check(self, state):

        """检查状态是否满足所有不变量"""

        for inv in self.invariants:

            if not inv(state):

                return False

        return True

    

    def generate_from_program(self, program):

        """

        从程序生成关系不变量

        

        简化版本：只检测相等关系

        """

        for stmt in program:

            if isinstance(stmt, tuple) and stmt[0] == 'assign':

                var = stmt[1]

                expr = stmt[2]

                

                if isinstance(expr, tuple) and expr[0] == 'var':

                    # 检测 var1 = var2

                    src = expr[1]

                    self.add_invariant(

                        lambda s, v1=var, v2=src: s.get(v1, 0) == s.get(v2, 0)

                    )

                

                elif isinstance(expr, tuple) and expr[0] == '+':

                    # 检测 var = x + y -> var - x = y, var - y = x

                    left = expr[1]

                    right = expr[2]

                    

                    if isinstance(left, tuple) and left[0] == 'var':

                        self.add_invariant(

                            lambda s, v=var, x=left[1], y=right: 

                            s.get(v, 0) == s.get(x, 0) + s.get(y, 0)

                        )





class LinearInvariant:

    """

    线性不变量

    

    形式：a1*x1 + a2*x2 + ... + an*xn <= b

    """

    

    def __init__(self):

        self.coeffs = {}  # (var -> coef)

        self.bound = 0

    

    def __repr__(self):

        terms = [f"{c}*{v}" for v, c in self.coeffs.items() if c != 0]

        return " + ".join(terms) + f" <= {self.bound}"

    

    def holds(self, state):

        """检查不变量是否成立"""

        total = sum(c * state.get(v, 0) for v, c in self.coeffs.items())

        return total <= self.bound

    

    @staticmethod

    def from_assignment(var, expr, env):

        """

        从赋值语句推导不变量

        

        例如: x = y + 5  ->  x - y = 5  ->  x - y <= 5 且 y - x <= -5

        """

        inv = LinearInvariant()

        

        if isinstance(expr, tuple):

            if expr[0] == 'var':

                # x = y  ->  x - y = 0

                inv.coeffs[var] = 1

                inv.coeffs[expr[1]] = -1

                inv.bound = 0

            

            elif expr[0] == 'const':

                # x = 5  ->  x <= 5 且 -x <= -5

                inv.coeffs[var] = 1

                inv.bound = expr[1]

            

            elif expr[0] == '+':

                # x = y + z  ->  x - y - z = 0

                inv.coeffs[var] = 1

                if isinstance(expr[1], tuple) and expr[1][0] == 'var':

                    inv.coeffs[expr[1][1]] = -1

                if isinstance(expr[2], tuple) and expr[2][0] == 'var':

                    inv.coeffs[expr[2][1]] = -1

                inv.bound = 0

        

        return inv





def run_demo():

    """运行不变量生成演示"""

    print("=" * 60)

    print("不变量生成 - Fixpoint迭代")

    print("=" * 60)

    

    # 程序1: 简单变量赋值

    print("\n[程序1] 简单赋值")

    program1 = [

        ('assign', 'x', ('const', 0)),

        ('assign', 'y', ('const', 10)),

        ('assign', 'z', ('+', ('var', 'x'), ('var', 'y'))),

    ]

    

    gen = InvariantGenerator()

    inv1 = gen.analyze(program1)

    print("  程序:")

    print("    x = 0;")

    print("    y = 10;")

    print("    z = x + y;")

    print("  不变量:")

    for var, interval in inv1.items():

        print(f"    {var} ∈ {interval}")

    

    # 程序2: 循环

    print("\n[程序2] 循环不变量")

    program2 = [

        ('assign', 'x', ('const', 0)),

        ('assign', 'sum', ('const', 0)),

        ('while', ('<', ('var', 'x'), ('const', 10)),

          [

            ('assign', 'x', ('+', ('var', 'x'), ('const', 1))),

            ('assign', 'sum', ('+', ('var', 'sum'), ('var', 'x'))),

          ]

        ),

    ]

    

    gen2 = InvariantGenerator()

    inv2 = gen2.analyze(program2)

    print("  程序:")

    print("    x = 0; sum = 0;")

    print("    while (x < 10) {")

    print("      x = x + 1;")

    print("      sum = sum + x;")

    print("    }")

    print("  循环不变量:")

    for var, interval in inv2.items():

        print(f"    {var} ∈ {interval}")

    

    # 关系不变量

    print("\n[关系不变量]")

    rel_inv = RelationalInvariant()

    rel_inv.generate_from_program(program1)

    print("  检测到的关系:")

    for i, inv in enumerate(rel_inv.invariants):

        print(f"    不变量{i+1}: x = y")

    

    # 线性不变量

    print("\n[线性不变量]")

    lin_inv = LinearInvariant.from_assignment('z', ('+', ('var', 'x'), ('var', 'y')), {})

    print(f"  从 z = x + y 推导:")

    print(f"    {lin_inv}")

    

    print("\n" + "=" * 60)

    print("不变量生成核心概念:")

    print("  1. Fixpoint: X = F(X) 的最小/最大解")

    print("  2. Widening: 保证迭代收敛的膨胀算子")

    print("  3. 循环不变量: 循环入口处成立且循环体保持")

    print("  4. 关系不变量: 变量之间的关系约束")

    print("  5. 线性不变量: 线性不等式形式的不变量")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

