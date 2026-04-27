# -*- coding: utf-8 -*-

"""

算法实现：程序分析 / constant_propagation



本文件实现 constant_propagation 相关的算法功能。

"""



from typing import Dict, List, Set, Optional, Tuple, Any

from abc import ABC, abstractmethod

from collections import defaultdict





class ConstantValue:

    """

    常量值类

    

    表示常量传播分析中的抽象值：

    - TOP: 未知值

    - CONST(c): 已知常量c

    - BOTTOM: 不可能到达（矛盾）

    """

    

    def __init__(self, value: Any = None, is_top: bool = False, is_bottom: bool = False):

        """

        初始化常量值

        

        Args:

            value: 常量值（如果已知）

            is_top: 是否是TOP

            is_bottom: 是否是BOTTOM

        """

        self.value = value

        self.is_top = is_top

        self.is_bottom = is_bottom

    

    @staticmethod

    def top() -> 'ConstantValue':

        """创建TOP值"""

        return ConstantValue(is_top=True)

    

    @staticmethod

    def bottom() -> 'ConstantValue':

        """创建BOTTOM值"""

        return ConstantValue(is_bottom=True)

    

    @staticmethod

    def const(value: Any) -> 'ConstantValue':

        """创建常量值"""

        return ConstantValue(value=value)

    

    def join(self, other: 'ConstantValue') -> 'ConstantValue':

        """

        并运算 (Join)：两个值的最小上界

        

        - TOP ∪ x = TOP

        - CONST(c) ∪ CONST(c) = CONST(c)

        - CONST(c1) ∪ CONST(c2) = TOP (如果c1 != c2)

        - x ∪ BOTTOM = x

        - BOTTOM ∪ BOTTOM = BOTTOM

        

        Args:

            other: 另一个常量值

            

        Returns:

            最小上界

        """

        if self.is_bottom:

            return other

        if other.is_bottom:

            return self

        

        if self.is_top or other.is_top:

            return ConstantValue.top()

        

        if self.value == other.value:

            return ConstantValue.const(self.value)

        

        return ConstantValue.top()

    

    def meet(self, other: 'ConstantValue') -> 'ConstantValue':

        """

        交运算 (Meet)：两个值的最大下界

        

        Args:

            other: 另一个常量值

            

        Returns:

            最大下界

        """

        if self.is_top:

            return other

        if other.is_top:

            return self

        

        if self.is_bottom or other.is_bottom:

            return ConstantValue.bottom()

        

        if self.value == other.value:

            return ConstantValue.const(self.value)

        

        return ConstantValue.bottom()

    

    def less_or_equal(self, other: 'ConstantValue') -> bool:

        """偏序关系"""

        if self.is_bottom:

            return True

        if self.is_top:

            return other.is_top

        if other.is_top:

            return True

        if other.is_bottom:

            return False

        return self.value == other.value

    

    def __str__(self) -> str:

        if self.is_top:

            return "⊤"

        if self.is_bottom:

            return "⊥"

        return str(self.value)

    

    def __repr__(self) -> str:

        return str(self)

    

    def __eq__(self, other) -> bool:

        if isinstance(other, ConstantValue):

            return (self.is_top == other.is_top and 

                    self.is_bottom == other.is_bottom and 

                    self.value == other.value)

        return False





class ConstantPropagator:

    """

    常量传播分析器

    

    使用数据流分析传播常量信息。

    """

    

    def __init__(self, num_blocks: int):

        """

        初始化常量传播器

        

        Args:

            num_blocks: 基本块数量

        """

        self.num_blocks = num_blocks

        # 每个块的抽象状态：block_id -> {var -> ConstantValue}

        self.state: Dict[int, Dict[str, ConstantValue]] = {i: {} for i in range(num_blocks)}

        # 每个块的IN状态

        self.in_state: Dict[int, Dict[str, ConstantValue]] = {i: {} for i in range(num_blocks)}

        # 每个块的OUT状态

        self.out_state: Dict[int, Dict[str, ConstantValue]] = {i: {} for i in range(num_blocks)}

        # 前驱关系

        self.predecessors: Dict[int, List[int]] = defaultdict(list)

        # 语句信息

        self.statements: Dict[int, List[Tuple[str, str]]] = {}  # block_id -> [(lhs, rhs)]

    

    def set_predecessors(self, predecessors: Dict[int, List[int]]):

        """

        设置前驱关系

        

        Args:

            predecessors: block_id -> [predecessor_ids]

        """

        self.predecessors = predecessors

    

    def add_statement(self, block_id: int, lhs: str, rhs: str):

        """

        添加语句到块

        

        Args:

            block_id: 基本块ID

            lhs: 左边的变量

            rhs: 右边的表达式

        """

        if block_id not in self.statements:

            self.statements[block_id] = []

        self.statements[block_id].append((lhs, rhs))

    

    def _evaluate_expression(self, expr: str, state: Dict[str, ConstantValue]) -> ConstantValue:

        """

        评估表达式的常量值

        

        Args:

            expr: 表达式字符串

            state: 当前变量状态

            

        Returns:

            表达式的常量值

        """

        expr = expr.strip()

        

        # 尝试解析为数字

        try:

            return ConstantValue.const(int(expr))

        except ValueError:

            pass

        

        # 变量

        if expr.isidentifier():

            return state.get(expr, ConstantValue.top())

        

        # 二元运算

        for op in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=']:

            if op in expr:

                parts = expr.split(op, 1)

                if len(parts) == 2:

                    left = self._evaluate_expression(parts[0], state)

                    right = self._evaluate_expression(parts[1], state)

                    return self._apply_binary_op(left, op, right)

        

        return ConstantValue.top()

    

    def _apply_binary_op(self, left: ConstantValue, op: str, right: ConstantValue) -> ConstantValue:

        """

        应用二元运算符

        

        Args:

            left: 左操作数

            op: 运算符

            right: 右操作数

            

        Returns:

            结果常量值

        """

        if left.is_top or right.is_top or left.is_bottom or right.is_bottom:

            return ConstantValue.top()

        

        try:

            l = int(left.value)

            r = int(right.value)

            

            if op == '+':

                result = l + r

            elif op == '-':

                result = l - r

            elif op == '*':

                result = l * r

            elif op == '/':

                result = l // r if r != 0 else 0

            elif op == '%':

                result = l % r if r != 0 else 0

            elif op == '==':

                result = 1 if l == r else 0

            elif op == '!=':

                result = 1 if l != r else 0

            elif op == '<':

                result = 1 if l < r else 0

            elif op == '>':

                result = 1 if l > r else 0

            elif op == '<=':

                result = 1 if l <= r else 0

            elif op == '>=':

                result = 1 if l >= r else 0

            else:

                return ConstantValue.top()

            

            return ConstantValue.const(result)

        except:

            return ConstantValue.top()

    

    def _transfer_function(self, block_id: int, 

                          in_state: Dict[str, ConstantValue]) -> Dict[str, ConstantValue]:

        """

        传输函数：应用块的语义到输入状态

        

        Args:

            block_id: 基本块ID

            in_state: 入口状态

            

        Returns:

            出口状态

        """

        out_state = dict(in_state)

        

        statements = self.statements.get(block_id, [])

        

        for lhs, rhs in statements:

            # 评估右侧表达式

            rhs_value = self._evaluate_expression(rhs, out_state)

            out_state[lhs] = rhs_value

        

        return out_state

    

    def analyze(self, entry_block: int = 0, max_iterations: int = 100) -> bool:

        """

        执行常量传播分析

        

        Args:

            entry_block: 入口块ID

            max_iterations: 最大迭代次数

            

        Returns:

            是否收敛

        """

        iteration = 0

        

        # 初始化入口块

        self.in_state[entry_block] = {}

        

        changed = True

        while changed and iteration < max_iterations:

            changed = False

            iteration += 1

            

            for block_id in range(self.num_blocks):

                # 计算IN[block_id]

                preds = self.predecessors.get(block_id, [])

                

                if not preds:

                    new_in = {} if block_id != entry_block else self.in_state.get(entry_block, {})

                else:

                    # IN = 合并所有前驱的OUT

                    new_in = None

                    for pred_id in preds:

                        pred_out = self.out_state.get(pred_id, {})

                        if new_in is None:

                            new_in = dict(pred_out)

                        else:

                            for var, val in pred_out.items():

                                if var in new_in:

                                    new_in[var] = new_in[var].join(val)

                                else:

                                    new_in[var] = val

                    

                    if new_in is None:

                        new_in = {}

                

                if new_in != self.in_state.get(block_id, {}):

                    self.in_state[block_id] = new_in

                    changed = True

                

                # 应用传输函数

                new_out = self._transfer_function(block_id, self.in_state[block_id])

                

                if new_out != self.out_state.get(block_id, {}):

                    self.out_state[block_id] = new_out

                    changed = True

        

        return iteration < max_iterations

    

    def get_value(self, block_id: int, var: str) -> ConstantValue:

        """

        获取变量在块出口的值

        

        Args:

            block_id: 基本块ID

            var: 变量名

            

        Returns:

            常量值

        """

        return self.out_state.get(block_id, {}).get(var, ConstantValue.top())

    

    def is_constant(self, block_id: int, var: str) -> bool:

        """

        检查变量在块出口是否是常量

        

        Args:

            block_id: 基本块ID

            var: 变量名

            

        Returns:

            如果是常量返回True

        """

        val = self.get_value(block_id, var)

        return not val.is_top and not val.is_bottom

    

    def get_constant_value(self, block_id: int, var: str) -> Optional[Any]:

        """

        获取变量的常量值

        

        Args:

            block_id: 基本块ID

            var: 变量名

            

        Returns:

            常量值，如果不是常量返回None

        """

        val = self.get_value(block_id, var)

        if not val.is_top and not val.is_bottom:

            return val.value

        return None

    

    def display_results(self):

        """显示分析结果"""

        print("=" * 60)

        print("Constant Propagation Results")

        print("=" * 60)

        

        for block_id in range(self.num_blocks):

            in_vals = self.in_state.get(block_id, {})

            out_vals = self.out_state.get(block_id, {})

            

            in_str = ", ".join(f"{v}={val}" for v, val in sorted(in_vals.items()) if not val.is_top)

            out_str = ", ".join(f"{v}={val}" for v, val in sorted(out_vals.items()) if not val.is_top)

            

            print(f"\nBlock {block_id}:")

            print(f"  IN:  {{{in_str if in_str else 'empty}'}}}")

            print(f"  OUT: {{{out_str if out_str else 'empty}'}}}")





def create_simple_example() -> ConstantPropagator:

    """创建简单示例"""

    cp = ConstantPropagator(num_blocks=4)

    

    # Block 0: x = 5

    cp.add_statement(0, "x", "5")

    

    # Block 1: y = x + 3

    cp.add_statement(1, "y", "x + 3")

    

    # Block 2: z = y + 2

    cp.add_statement(2, "z", "y + 2")

    

    # Block 3: w = z + 1

    cp.add_statement(3, "w", "z + 1")

    

    # 前驱关系

    cp.set_predecessors({

        0: [],

        1: [0],

        2: [1],

        3: [2]

    })

    

    return cp





def create_branch_example() -> ConstantPropagator:

    """创建分支示例"""

    cp = ConstantPropagator(num_blocks=5)

    

    # Block 0: x = 10

    cp.add_statement(0, "x", "10")

    

    # Block 1 (then): y = x + 5

    cp.add_statement(1, "y", "x + 5")

    

    # Block 2 (else): y = x + 10

    cp.add_statement(2, "y", "x + 10")

    

    # Block 3: z = y + 1

    cp.add_statement(3, "z", "y + 1")

    

    # 前驱关系

    cp.set_predecessors({

        0: [],

        1: [0],

        2: [0],

        3: [1, 2],

        4: [3]

    })

    

    return cp





if __name__ == "__main__":

    print("=" * 60)

    print("测试1：简单顺序程序的常量传播")

    print("=" * 60)

    

    cp1 = create_simple_example()

    cp1.analyze()

    

    print("\n程序:")

    print("  Block 0: x = 5")

    print("  Block 1: y = x + 3")

    print("  Block 2: z = y + 2")

    print("  Block 3: w = z + 1")

    

    cp1.display_results()

    

    print("\n常量查询:")

    for var in ['x', 'y', 'z', 'w']:

        for block_id in range(4):

            val = cp1.get_constant_value(block_id, var)

            if val is not None:

                print(f"  Block {block_id} 出口: {var} = {val}")

    

    print("\n" + "=" * 60)

    print("测试2：分支程序的常量传播")

    print("=" * 60)

    

    cp2 = create_branch_example()

    cp2.analyze()

    

    print("\n程序:")

    print("  Block 0: x = 10")

    print("  Block 1 (then): y = x + 5")

    print("  Block 2 (else): y = x + 10")

    print("  Block 3: z = y + 1")

    

    cp2.display_results()

    

    print("\n常量查询:")

    for var in ['x', 'y', 'z']:

        for block_id in range(4):

            val = cp2.get_constant_value(block_id, var)

            if val is not None:

                print(f"  Block {block_id} 出口: {var} = {val}")

    

    print("\n" + "=" * 60)

    print("测试3：常量折叠")

    print("=" * 60)

    

    # 直接评估常量表达式

    cp3 = ConstantPropagator(1)

    result = cp3._evaluate_expression("2 + 3 * 4", {})

    print(f"\n表达式 '2 + 3 * 4' 的值: {result}")

    

    result2 = cp3._evaluate_expression("x + 5", {'x': ConstantValue.const(10)})

    print(f"表达式 'x + 5' (x=10) 的值: {result2}")

    

    print("\n常量传播测试完成!")

    print("\n注意：常量传播可以进一步用于：")

    print("  1. 常量折叠：编译时计算常量表达式")

    print("  2. 分支优化：常量条件分支的化简")

    print("  3. 死代码消除：消除不可能执行的代码")

