# -*- coding: utf-8 -*-

"""

算法实现：编译器优化 / constant_folding



本文件实现 constant_folding 相关的算法功能。

"""



from typing import List, Dict, Optional, Any, Union

import re





class ConstantValue:

    """常量值"""

    def __init__(self, value: Any, is_constant: bool = True):

        self.value = value

        self.is_constant = is_constant

    

    def __repr__(self):

        return str(self.value)





class Expression:

    """表达式基类"""

    def __init__(self):

        pass

    

    def evaluate(self, env: Dict[str, ConstantValue]) -> ConstantValue:

        """在给定环境下求值"""

        raise NotImplementedError

    

    def get_variables(self) -> set:

        """获取变量集合"""

        raise NotImplementedError





class ConstExpr(Expression):

    """常量表达式"""

    def __init__(self, value: Union[int, float]):

        super().__init__()

        self.value = value

    

    def evaluate(self, env: Dict[str, ConstantValue]) -> ConstantValue:

        return ConstantValue(self.value, True)

    

    def get_variables(self) -> set:

        return set()

    

    def __repr__(self):

        return str(self.value)





class VarExpr(Expression):

    """变量表达式"""

    def __init__(self, name: str):

        super().__init__()

        self.name = name

    

    def evaluate(self, env: Dict[str, ConstantValue]) -> ConstantValue:

        if self.name in env:

            return env[self.name]

        return ConstantValue(None, False)  # 非常量

    

    def get_variables(self) -> set:

        return {self.name}

    

    def __repr__(self):

        return self.name





class BinaryOpExpr(Expression):

    """二元操作表达式"""

    def __init__(self, left: Expression, op: str, right: Expression):

        super().__init__()

        self.left = left

        self.op = op

        self.right = right

    

    def evaluate(self, env: Dict[str, ConstantValue]) -> ConstantValue:

        left_val = self.left.evaluate(env)

        right_val = self.right.evaluate(env)

        

        if not left_val.is_constant or not right_val.is_constant:

            return ConstantValue(None, False)

        

        try:

            if self.op == '+':

                result = left_val.value + right_val.value

            elif self.op == '-':

                result = left_val.value - right_val.value

            elif self.op == '*':

                result = left_val.value * right_val.value

            elif self.op == '/':

                result = left_val.value / right_val.value

            elif self.op == '//':

                result = left_val.value // right_val.value

            elif self.op == '%':

                result = left_val.value % right_val.value

            elif self.op == '**':

                result = left_val.value ** right_val.value

            else:

                return ConstantValue(None, False)

            

            return ConstantValue(result, True)

        except:

            return ConstantValue(None, False)

    

    def get_variables(self) -> set:

        return self.left.get_variables() | self.right.get_variables()

    

    def __repr__(self):

        return f"({self.left} {self.op} {self.right})"





class Statement:

    """语句基类"""

    def __init__(self):

        pass

    

    def execute(self, env: Dict[str, ConstantValue], optimized: List) -> bool:

        """执行语句,返回是否进行了优化"""

        raise NotImplementedError





class AssignStmt(Statement):

    """赋值语句"""

    def __init__(self, lhs: str, rhs: Expression):

        super().__init__()

        self.lhs = lhs

        self.rhs = rhs

    

    def execute(self, env: Dict[str, ConstantValue], optimized: List) -> bool:

        value = self.rhs.evaluate(env)

        

        if value.is_constant:

            # 常量折叠

            env[self.lhs] = value

            optimized.append(f"常量折叠: {self.lhs} = {value.value}")

            return True

        else:

            # 常量传播

            variables = self.rhs.get_variables()

            if variables:

                all_const = True

                for v in variables:

                    if v not in env or not env[v].is_constant:

                        all_const = False

                        break

                

                if all_const:

                    env[self.lhs] = value

                    optimized.append(f"常量传播: {self.lhs} = {self.rhs}")

                    return True

            

            env[self.lhs] = ConstantValue(None, False)

            return False

    

    def __repr__(self):

        return f"{self.lhs} = {self.rhs}"





class ConstantFolder:

    """

    常量折叠与传播优化器

    """

    

    def __init__(self):

        self.statements = []

    

    def add_statement(self, stmt: Statement):

        self.statements.append(stmt)

    

    def optimize(self) -> List[Statement]:

        """

        执行常量折叠与传播

        

        Returns:

            优化后的语句列表

        """

        env = {}  # 变量 -> 常量值

        optimized_stmts = []

        optimization_log = []

        

        for stmt in self.statements:

            if isinstance(stmt, AssignStmt):

                # 先尝试常量传播

                propagated = self.propagate_constants(stmt, env)

                

                if propagated:

                    optimized_stmts.append(propagated)

                    optimization_log.append(f"传播: {propagated}")

                else:

                    # 执行并检查是否折叠

                    new_env = env.copy()

                    stmt.execute(new_env, optimization_log)

                    optimized_stmts.append(stmt)

                    env = new_env

            else:

                optimized_stmts.append(stmt)

        

        return optimized_stmts

    

    def propagate_constants(self, stmt: AssignStmt, env: Dict) -> Optional[Statement]:

        """

        尝试用已知常量替换表达式中的变量

        

        Args:

            stmt: 赋值语句

            env: 当前环境

        

        Returns:

            优化后的语句,如果没有优化返回None

        """

        rhs = stmt.rhs

        

        # 检查是否可以用常量替换

        if isinstance(rhs, VarExpr):

            var_name = rhs.name

            if var_name in env and env[var_name].is_constant:

                # 用常量替换变量

                return AssignStmt(stmt.lhs, ConstExpr(env[var_name].value))

        

        elif isinstance(rhs, BinaryOpExpr):

            # 尝试替换左右操作数

            new_left = rhs.left

            new_right = rhs.right

            

            changed = False

            

            if isinstance(rhs.left, VarExpr) and rhs.left.name in env:

                val = env[rhs.left.name]

                if val.is_constant:

                    new_left = ConstExpr(val.value)

                    changed = True

            

            if isinstance(rhs.right, VarExpr) and rhs.right.name in env:

                val = env[rhs.right.name]

                if val.is_constant:

                    new_right = ConstExpr(val.value)

                    changed = True

            

            if changed:

                new_rhs = BinaryOpExpr(new_left, rhs.op, new_right)

                return AssignStmt(stmt.lhs, new_rhs)

        

        return None





def fold_constants(program: List[Statement]) -> List[Statement]:

    """

    常量折叠便捷函数

    

    Args:

        program: 语句列表

    

    Returns:

        优化后的程序

    """

    folder = ConstantFolder()

    for stmt in program:

        folder.add_statement(stmt)

    return folder.optimize()





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单常量折叠

    print("测试1 - 简单常量折叠:")

    

    # a = 5 + 3

    # b = a + 2

    # c = b + 1

    

    stmts = [

        AssignStmt('a', BinaryOpExpr(ConstExpr(5), '+', ConstExpr(3))),

        AssignStmt('b', BinaryOpExpr(VarExpr('a'), '+', ConstExpr(2))),

        AssignStmt('c', BinaryOpExpr(VarExpr('b'), '+', ConstExpr(1))),

    ]

    

    print("  原始程序:")

    for s in stmts:

        print(f"    {s}")

    

    optimized = fold_constants(stmts)

    

    print("  优化后:")

    for s in optimized:

        print(f"    {s}")

    

    # 测试2: 常量传播

    print("\n测试2 - 常量传播:")

    

    # a = 10

    # b = a + 5

    # c = b * 2

    # d = c - a

    

    stmts2 = [

        AssignStmt('a', ConstExpr(10)),

        AssignStmt('b', BinaryOpExpr(VarExpr('a'), '+', ConstExpr(5))),

        AssignStmt('c', BinaryOpExpr(VarExpr('b'), '*', ConstExpr(2))),

        AssignStmt('d', BinaryOpExpr(VarExpr('c'), '-', VarExpr('a'))),

    ]

    

    print("  原始程序:")

    for s in stmts2:

        print(f"    {s}")

    

    optimized2 = fold_constants(stmts2)

    

    print("  优化后:")

    for s in optimized2:

        print(f"    {s}")

    

    # 测试3: 混合情况

    print("\n测试3 - 混合情况:")

    

    # x = 3

    # y = 5

    # z = x + y      # 8

    # w = z * 2      # 16

    # v = w + x      # 19

    

    stmts3 = [

        AssignStmt('x', ConstExpr(3)),

        AssignStmt('y', ConstExpr(5)),

        AssignStmt('z', BinaryOpExpr(VarExpr('x'), '+', VarExpr('y'))),

        AssignStmt('w', BinaryOpExpr(VarExpr('z'), '*', ConstExpr(2))),

        AssignStmt('v', BinaryOpExpr(VarExpr('w'), '+', VarExpr('x'))),

    ]

    

    print("  原始程序:")

    for s in stmts3:

        print(f"    {s}")

    

    optimized3 = fold_constants(stmts3)

    

    print("  优化后:")

    for s in optimized3:

        print(f"    {s}")

    

    # 测试4: 验证折叠结果

    print("\n测试4 - 验证折叠结果:")

    

    # 手动计算期望结果

    x = 3

    y = 5

    z = x + y      # 8

    w = z * 2      # 16

    v = w + x      # 19

    

    print(f"  期望: x=3, y=5, z=8, w=16, v=19")

    

    # 检查优化后的代码

    env = {}

    for s in optimized3:

        val = s.rhs.evaluate(env)

        if val.is_constant:

            env[s.lhs] = val.value

    

    print(f"  实际: x={env.get('x')}, y={env.get('y')}, z={env.get('z')}, w={env.get('w')}, v={env.get('v')}")

    

    # 测试5: 复杂表达式

    print("\n测试5 - 复杂表达式:")

    

    # a = 2 * 3 + 4 * 5  # 26

    # b = a * a          # 676

    # c = b + a          # 702

    

    stmts5 = [

        AssignStmt('a', BinaryOpExpr(

            BinaryOpExpr(ConstExpr(2), '*', ConstExpr(3)),

            '+',

            BinaryOpExpr(ConstExpr(4), '*', ConstExpr(5))

        )),

        AssignStmt('b', BinaryOpExpr(VarExpr('a'), '*', VarExpr('a'))),

        AssignStmt('c', BinaryOpExpr(VarExpr('b'), '+', VarExpr('a'))),

    ]

    

    print("  原始程序:")

    for s in stmts5:

        print(f"    {s}")

    

    optimized5 = fold_constants(stmts5)

    

    print("  优化后:")

    for s in optimized5:

        print(f"    {s}")

    

    # 验证

    env5 = {}

    for s in optimized5:

        val = s.rhs.evaluate(env5)

        if val.is_constant:

            env5[s.lhs] = val.value

    

    print(f"  结果: {env5}")

    

    print("\n所有测试完成!")

