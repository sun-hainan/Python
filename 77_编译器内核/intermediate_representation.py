# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / intermediate_representation



本文件实现 intermediate_representation 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import List, Dict, Optional, Any

from enum import Enum, auto





class OpCode(Enum):

    """三地址码操作码"""

    # 算术运算

    ADD = "+"

    SUB = "-"

    MUL = "*"

    DIV = "/"

    MOD = "%"



    # 比较运算

    EQ = "=="

    NE = "!="

    LT = "<"

    GT = ">"

    LE = "<="

    GE = ">="



    # 逻辑运算

    AND = "&&"

    OR = "||"

    NOT = "!"



    # 内存操作

    LOAD = "load"

    STORE = "store"

    LOAD_ADDR = "addr"

    LOAD_PARAM = "param"

    LOAD_RETURN = "return"



    # 控制流

    LABEL = "label"

    JUMP = "jmp"

    JUMP_IF = "jif"  # 条件跳转

    JUMP_IF_NOT = "jnot"  # 条件非跳转

    CALL = "call"

    CALL_END = "call_end"



    # 函数

    FUNC_BEGIN = "func_begin"

    FUNC_END = "func_end"

    RETURN = "ret"



    # 类型转换

    I2F = "i2f"  # int to float

    F2I = "f2i"  # float to int



    # 数组

    ARRAY_LOAD = "aload"

    ARRAY_STORE = "astore"





@dataclass

class Address:

    """

    地址(操作数)

    可以是临时变量、常量、标签、内存位置

    """

    kind: str  # "temp", "const", "label", "var", "param"

    value: Any  # 值内容

    type_name: str = "int"  # 类型名



    def __str__(self):

        if self.kind == "const":

            return f"#{self.value}"

        return f"{self.value}"



    @staticmethod

    def temp(name: str, type_name: str = "int") -> 'Address':

        """创建临时变量地址"""

        return Address(kind="temp", value=name, type_name=type_name)



    @staticmethod

    def constant(value: Any, type_name: str = "int") -> 'Address':

        """创建常量地址"""

        return Address(kind="const", value=value, type_name=type_name)



    @staticmethod

    def label(name: str) -> 'Address':

        """创建标签地址"""

        return Address(kind="label", value=name, type_name="label")



    @staticmethod

    def variable(name: str, type_name: str = "int") -> 'Address':

        """创建变量地址"""

        return Address(kind="var", value=name, type_name=type_name)





@dataclass

class TACInstruction:

    """

    三地址码指令



    格式: result = x op y (双目)

          result = op x    (单目)

          op x, y, z       (控制流)

    """

    op: OpCode  # 操作码

    result: Optional[Address] = None  # 结果

    arg1: Optional[Address] = None  # 第一个操作数

    arg2: Optional[Address] = None  # 第二个操作数

    comment: str = ""  # 注释



    def __str__(self):

        parts = []



        if self.result:

            parts.append(f"{self.result}")

        if self.op:

            parts.append(f"{self.op.value}")

        if self.arg1:

            parts.append(f"{self.arg1}")

        if self.arg2:

            parts.append(f", {self.arg2}")



        line = " ".join(parts)

        if self.comment:

            line += f"  ; {self.comment}"

        return line





@dataclass

class BasicBlock:

    """基本块"""

    label: str  # 块标签

    instructions: List[TACInstruction] = field(default_factory=list)

    predecessors: List[str] = field(default_factory=list)  # 前驱块标签

    successors: List[str] = field(default_factory=list)  # 后继块标签





class IRGenerator:

    """

    IR生成器



    将AST转换为三地址码

    """



    def __init__(self):

        self.instructions: List[TACInstruction] = []  # 指令列表

        self.temp_counter = 0  # 临时变量计数器

        self.label_counter = 0  # 标签计数器

        self.current_func: Optional[str] = None  # 当前函数名



    def new_temp(self, type_name: str = "int") -> Address:

        """生成新的临时变量"""

        self.temp_counter += 1

        return Address.temp(f"t{self.temp_counter}", type_name)



    def new_label(self, prefix: str = "L") -> str:

        """生成新的标签"""

        self.label_counter += 1

        return f"{prefix}{self.label_counter}"



    def emit(self, op: OpCode, result: Address = None,

             arg1: Address = None, arg2: Address = None,

             comment: str = "") -> Address:

        """

        发射指令



        返回:

            result地址

        """

        instr = TACInstruction(op=op, result=result, arg1=arg1, arg2=arg2, comment=comment)

        self.instructions.append(instr)

        return result



    def emit_label(self, label: str):

        """发射标签"""

        self.emit(OpCode.LABEL, result=Address.label(label), comment="basic block start")



    def emit_assign(self, target: Address, source: Address, comment: str = ""):

        """发射赋值指令: target = source"""

        self.emit(OpCode.ADD, result=target, arg1=source, arg2=Address.constant(0), comment=comment)



    def emit_binary(self, op: OpCode, result: Address, left: Address, right: Address):

        """发射双目运算指令"""

        self.emit(op, result=result, arg1=left, arg2=right)



    def emit_jump(self, target_label: str, comment: str = ""):

        """发射无条件跳转"""

        self.emit(OpCode.JUMP, result=Address.label(target_label), comment=comment)



    def emit_cond_jump(self, op: OpCode, cond: Address, true_label: str, false_label: str = None):

        """发射条件跳转"""

        self.emit(op, result=Address.label(true_label), arg1=cond, arg2=Address.label(false_label) if false_label else None)



    def emit_call(self, result: Address, func_name: str, args: List[Address] = None):

        """发射函数调用"""

        # 先发射参数

        if args:

            for arg in args:

                self.emit(OpCode.LOAD_PARAM, arg1=arg)

        # 发射call指令

        self.emit(OpCode.CALL, result=Address.variable(func_name), arg1=result)



    def emit_return(self, value: Address = None):

        """发射返回指令"""

        self.emit(OpCode.RETURN, result=value)



    def emit_func_begin(self, func_name: str):

        """发射函数开始"""

        self.current_func = func_name

        self.emit(OpCode.FUNC_BEGIN, result=Address.variable(func_name), comment=f"function {func_name} begin")



    def emit_func_end(self, func_name: str):

        """发射函数结束"""

        self.emit(OpCode.FUNC_END, result=Address.variable(func_name), comment=f"function {func_name} end")



    def generate(self) -> List[TACInstruction]:

        """获取生成的IR指令"""

        return self.instructions



    def print_ir(self):

        """打印IR(用于调试)"""

        print("=== 三地址码 ===")

        for i, instr in enumerate(self.instructions):

            print(f"{i:4d}: {instr}")





class ASTToIRConverter:

    """AST转IR转换器"""



    def __init__(self):

        self.generator = IRGenerator()



    def convert(self, ast) -> List[TACInstruction]:

        """将AST转换为IR"""

        # 简化实现: 假设AST已经是简化形式

        if hasattr(ast, 'node_type'):

            if ast.node_type == "Function":

                return self._convert_function(ast)

            elif ast.node_type == "Program":

                instructions = []

                for child in ast.children:

                    instructions.extend(self.convert(child))

                return instructions

        return self.generator.instructions



    def _convert_function(self, func_node) -> List[TACInstruction]:

        """转换函数"""

        func_name = func_node.value

        self.generator.emit_func_begin(func_name)



        # 转换函数体

        for child in func_node.children:

            self._convert_statement(child)



        self.generator.emit_func_end(func_name)

        return self.generator.instructions



    def _convert_statement(self, stmt):

        """转换语句"""

        if hasattr(stmt, 'node_type'):

            if stmt.node_type == "Return":

                if stmt.children:

                    ret_val = self._convert_expression(stmt.children[0])

                    self.generator.emit_return(ret_val)

            elif stmt.node_type == "Assignment":

                target = Address.variable(stmt.children[0].value)

                value = self._convert_expression(stmt.children[1])

                self.generator.emit_assign(target, value)

            elif stmt.node_type == "If":

                self._convert_if(stmt)

            elif stmt.node_type == "While":

                self._convert_while(stmt)



    def _convert_expression(self, expr) -> Address:

        """转换表达式"""

        if hasattr(expr, 'node_type'):

            if expr.node_type == "Literal":

                return Address.constant(expr.value)

            elif expr.node_type == "Identifier":

                return Address.variable(expr.value)

            elif expr.node_type == "BinOp":

                left = self._convert_expression(expr.children[0])

                right = self._convert_expression(expr.children[1])

                result = self.generator.new_temp()

                op_map = {

                    "+": OpCode.ADD,

                    "-": OpCode.SUB,

                    "*": OpCode.MUL,

                    "/": OpCode.DIV,

                }

                op = op_map.get(expr.value, OpCode.ADD)

                self.generator.emit_binary(op, result, left, right)

                return result

        return Address.constant(0)



    def _convert_if(self, if_node):

        """转换if语句"""

        cond = self._convert_expression(if_node.children[0])

        else_label = self.generator.new_label("else")

        end_label = self.generator.new_label("endif")



        # 条件跳转

        self.generator.emit_cond_jump(OpCode.JUMP_IF_NOT, cond, else_label)



        # then分支

        self._convert_statement(if_node.children[1])

        self.generator.emit_jump(end_label)



        # else标签

        self.generator.emit_label(else_label)



        # else分支

        if len(if_node.children) > 2:

            self._convert_statement(if_node.children[2])



        self.generator.emit_label(end_label)



    def _convert_while(self, while_node):

        """转换while循环"""

        loop_label = self.generator.new_label("loop")

        end_label = self.generator.new_label("endloop")



        self.generator.emit_label(loop_label)



        cond = self._convert_expression(while_node.children[0])

        self.generator.emit_cond_jump(OpCode.JUMP_IF_NOT, cond, end_label)



        self._convert_statement(while_node.children[1])

        self.generator.emit_jump(loop_label)



        self.generator.emit_label(end_label)





if __name__ == "__main__":

    gen = IRGenerator()



    # 生成示例IR: 计算斐波那契



    # func_begin fib

    gen.emit_func_begin("fib")



    # t1 = param 0

    gen.emit(OpCode.LOAD_PARAM, arg1=Address.temp("t1"), comment="load first param")



    # if n <= 1, return n

    # L0:

    gen.emit_label("L0")

    # t2 = t1 <= 1

    gen.emit_binary(OpCode.LE, Address.temp("t2"), Address.temp("t1"), Address.constant(1))

    # jnot t2, L1

    gen.emit(OpCode.JUMP_IF_NOT, result=Address.label("L1"), arg1=Address.temp("t2"))



    # return n

    gen.emit_return(Address.temp("t1"))

    # jmp L2

    gen.emit_jump("L2")



    # L1:

    gen.emit_label("L1")

    # t3 = fib(n-1)

    t3 = gen.new_temp()

    gen.emit_call(t3, "fib", [gen.new_temp()])  # 简化

    # return fib(n-1) + fib(n-2)

    result = gen.new_temp()

    gen.emit_binary(OpCode.ADD, result, t3, gen.new_temp())



    # L2:

    gen.emit_label("L2")

    gen.emit_func_end("fib")



    # 打印IR

    gen.print_ir()



    # 测试表达式转换

    print("\n=== 表达式IR测试 ===")

    gen2 = IRGenerator()

    # 生成 (a + b) * c 的IR

    a = Address.variable("a")

    b = Address.variable("b")

    c = Address.variable("c")



    t1 = gen2.new_temp()

    gen2.emit_binary(OpCode.ADD, t1, a, b)

    result = gen2.new_temp()

    gen2.emit_binary(OpCode.MUL, result, t1, c)



    gen2.print_ir()

