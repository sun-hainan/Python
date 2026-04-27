# -*- coding: utf-8 -*-

"""

算法实现：编译器优化 / common_subexpression



本文件实现 common_subexpression 相关的算法功能。

"""



from typing import List, Dict, Tuple, Optional, Hashable

from dataclasses import dataclass, field





@dataclass(frozen=True)

class ExprKey:

    """

    表达式的规范化键值，用于哈希去重

    frozen=True 使其可哈希（可用于 dict key）

    """

    op: str

    args: Tuple[Hashable, ...] = field(compare=False)



    def __repr__(self):

        if not self.args:

            return self.op

        return f"({self.args[0]} {self.op} {self.args[1]})" if len(self.args) == 2 else f"{self.op}({self.args})"





@dataclass

class EvalRecord:

    """

    记录表达式的求值信息

    """

    result_var: str      # 保存计算结果的变量名

    block_id: int        # 所在基本块 ID

    stmt_index: int      # 在块内的语句索引

    available: bool = True  # 当前是否仍可用（后续若有变量被重新定义则失效）





class CSEOptimizer:

    """

    公共子表达式消除优化器



    核心思路：

        维护一张表达式表，记录最近一次计算该表达式的变量名。

        扫描时，若当前表达式已在表中且可用，则用已有变量替换；

        否则计算并加入表，若表达式结果被新赋值覆盖则标记为不可用。

    """



    def __init__(self):

        # expr_table: 表达式键 -> 求值记录

        self.expr_table: Dict[ExprKey, EvalRecord] = {}

        # killed_vars: 在当前扫描点之后被重新定义的变量集合

        self.killed_vars: set = set()



    def _make_key(self, op: str, args: List[str]) -> ExprKey:

        """构建表达式的规范化键"""

        # 对变量名进行规范化：替换为各自的"最新版本"（若发生过复制传播）

        norm_args = tuple(args)

        return ExprKey(op=op, args=norm_args)



    def lookup(self, op: str, args: List[str]) -> Optional[str]:

        """

        查找表达式是否已有可用的计算结果



        Returns:

            若可用，返回保存结果的变量名；否则返回 None

        """

        key = self._make_key(op, args)

        record = self.expr_table.get(key)

        if record is None:

            return None

        # 检查所有操作数是否在求值后未被重新定义

        for arg in args:

            if arg in self.killed_vars:

                # 操作数之一被重新定义，该记录失效

                return None

        return record.result_var



    def record(self, op: str, args: List[str], result_var: str, block_id: int, stmt_index: int):

        """记录一次表达式求值"""

        key = self._make_key(op, args)

        self.expr_table[key] = EvalRecord(

            result_var=result_var,

            block_id=block_id,

            stmt_index=stmt_index,

            available=True,

        )



    def invalidate_on_def(self, var: str):

        """

        当变量 var 被重新定义（赋值）时，调用此方法

        所有依赖 var 的表达式记录都应标记为不可用

        """

        if var in self.killed_vars:

            return

        self.killed_vars.add(var)

        # 遍历表，删除依赖该变量的记录（简化处理：重建表）

        to_remove = []

        for key, record in self.expr_table.items():

            if var in key.args:

                to_remove.append(key)

        for key in to_remove:

            del self.expr_table[key]



    def reset_killed(self):

        """每个基本块入口重置 killed 集合"""

        self.killed_vars = set()





def common_subexpression_elimination(

    stmts: List[Tuple[str, str, List[str]]],

    block_id: int = 0,

) -> List[Tuple[str, str, List[str]]]:

    """

    公共子表达式消除主函数



    Args:

        stmts: 语句列表，每条语句为 (lhs, op, [arg1, arg2]) 三元组

               - 若 op == "assign"，则 arg1 为右值变量名

               - 否则为二元运算 op，左侧 arg1，右侧 arg2



    Returns:

        优化后的语句列表



    示例：

        输入: [("t1", "+", ["a", "b"]),

               ("t2", "+", ["a", "b"]),  # 与 t1 相同 -> 替换为 t1

               ("c",  "=",  ["t2"])]

        输出: [("t1", "+", ["a", "b"]),

               ("t2", "=", ["t1"]),       # t2 = t1（冗余赋值，后续 DCE 可消除）

               ("c",  "=",  ["t2"])]

    """

    optimizer = CSEOptimizer()

    result: List[Tuple[str, str, List[str]]] = []



    for stmt_idx, (lhs, op, args) in enumerate(stmts):

        if op == "=":

            # 赋值语句：检查右值是否为已知的公共子表达式

            # 按"二元运算"方式处理：op="var", args=[右值变量名]

            available = optimizer.lookup("var", [args[0]])

            if available:

                # 右值与之前某表达式相同 → 用已有变量替换

                result.append((lhs, "=", [available]))

                # 注意：lhs 被重新定义，后续依赖 lhs 的表达式会失效

            else:

                result.append((lhs, "=", args[:]))

                # 记录这一次赋值产生的"变量"

                optimizer.record("var", [args[0]], lhs, block_id, stmt_idx)



            # lhs 被重新定义，invalidate

            optimizer.invalidate_on_def(lhs)



        else:

            # 二元运算或一元运算

            available = optimizer.lookup(op, args)

            if available:

                # 发现公共子表达式！用已有变量替换

                result.append((lhs, "=", [available]))

            else:

                result.append((lhs, op, args[:]))

                optimizer.record(op, args, lhs, block_id, stmt_idx)



            # lhs 被定义，后续若有使用 lhs 的表达式将查找这里

            optimizer.invalidate_on_def(lhs)



    return result





if __name__ == "__main__":

    print("=" * 50)

    print("公共子表达式消除（CSE）- 单元测试")

    print("=" * 50)



    # 示例：

    # a = x + y

    # b = x + y     <- 公共子表达式，与 a 相同 → 替换为 a

    # c = b + 1     <- 此时 b == a，故 c = a + 1

    # d = x + y     <- 再次出现 → 替换为 a

    # e = c         <- e = c

    # x = z         <- x 被重新定义，后续的 x+y 需重新计算

    # f = x + y     <- 不能再用 a，需重新计算



    stmts = [

        ("a", "+", ["x", "y"]),

        ("b", "+", ["x", "y"]),   # -> "=", ["a"]

        ("c", "+", ["b", "1"]),   # -> "=", ["a"]  (b == a)  但这里 b 仍参与传播

        ("d", "+", ["x", "y"]),   # -> "=", ["a"]  (在 x=z 之前)

        ("e", "=", ["c"]),

        ("x", "=", ["z"]),        # x 被重新定义

        ("f", "+", ["x", "y"]),   # 必须重新计算

    ]



    print("\n原始语句序列:")

    for lhs, op, args in stmts:

        if op == "=":

            print(f"  {lhs} = {args[0]}")

        else:

            print(f"  {lhs} = {args[0]} {op} {args[1]}")



    opt_stmts = common_subexpression_elimination(stmts)



    print("\nCSE 优化后:")

    for lhs, op, args in opt_stmts:

        if op == "=":

            print(f"  {lhs} = {args[0]}")

        else:

            print(f"  {lhs} = {args[0]} {op} {args[1]}")



    print("\n期望效果:")

    print("  b = a    (x+y 已由 a 计算)")

    print("  c = a+1  (b 已传播为 a)")

    print("  d = a    (仍在 x=z 之前)")

    print("  x = z    (清除 a,b,c,d 的可用性)")

    print("  f 重新计算 (x+y)")



    # 验证替换是否正确

    expected_b = ("b", "=", ["a"])

    expected_d = ("d", "=", ["a"])

    expected_f_op = "+"

    print(f"\nb 是否被替换为 a: {'✓' if opt_stmts[1] == expected_b else '✗'}")

    print(f"d 是否被替换为 a: {'✓' if opt_stmts[3] == expected_d else '✗'}")

    print(f"f 是否重新计算: {'✓' if opt_stmts[6][1] == '+' else '✗'}")



    print(f"\n复杂度: O(N * H)，N 为语句数，H 为表达式哈希查找开销")

    print("算法完成。")

