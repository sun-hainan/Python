# -*- coding: utf-8 -*-

"""

算法实现：形式验证 / obdd



本文件实现 obdd 相关的算法功能。

"""



import numpy as np

from collections import defaultdict, deque





class OBDDNode:

    """OBDD节点"""

    _id_counter = 0

    

    def __init__(self, var=-1, low=None, high=None, terminal=None):

        self.id = OBDDNode._id_counter

        OBDDNode._id_counter += 1

        

        self.var = var          # 变量索引

        self.low = low          # 0分支

        self.high = high        # 1分支

        self.terminal = terminal  # 叶子值（True/False/None表示非叶子）

    

    def __repr__(self):

        if self.terminal is not None:

            return f"Node({self.id}, val={self.terminal})"

        return f"Node({self.id}, var=x{self.var}, low={self.low}, high={self.high})"





class OBDD:

    """

    有序二叉决策图（OBDD）类

    

    特点：

    1. 变量按固定顺序测试

    2. 相同子结构共享

    3. 不存在冗余测试（low==high的节点被消除）

    """

    

    def __init__(self, var_order):

        """

        初始化OBDD

        

        参数:

            var_order: 变量顺序列表，如 [0,1,2] 表示先测试x0再测试x1

        """

        self.var_order = var_order

        self.num_vars = len(var_order)

        self.var_to_pos = {v: i for i, v in enumerate(var_order)}

        

        self.unique_table = {}  # (var, low, high) -> node_id

        self.nodes = {}         # node_id -> node

        self.apply_cache = {}

        

        # 终端节点

        self.terminal_true = self._make_terminal(True)

        self.terminal_false = self._make_terminal(False)

        

        # 哈希表用于简化（基于BddHash）

        self.hash_table = {}

    

    def _make_terminal(self, value):

        """创建终端节点"""

        node = OBDDNode(var=-1, terminal=value)

        self.nodes[node.id] = node

        return node.id

    

    def _make_node(self, var, low, high):

        """

        创建或复用节点（应用唯一性和简化规则）

        

        参数:

            var: 变量索引

            low: 0分支节点ID

            high: 1分支节点ID

        

        返回:

            节点ID

        """

        # 简化规则1: 终端合并

        if low == self.terminal_true.id and high == self.terminal_true.id:

            return self.terminal_true.id

        if low == self.terminal_false.id and high == self.terminal_false.id:

            return self.terminal_false.id

        

        # 简化规则2: 消除冗余（low==high）

        if low == high:

            return low

        

        # 唯一性检查

        key = (var, low, high)

        if key in self.unique_table:

            return self.unique_table[key]

        

        node = OBDDNode(var=var, low=low, high=high)

        self.nodes[node.id] = node

        self.unique_table[key] = node.id

        

        return node.id

    

    def _var_pos(self, var):

        """获取变量在顺序中的位置"""

        return self.var_to_pos[var]

    

    def _find_min_var(self, u, v):

        """

        找到u和v中顺序最小的变量

        

        返回:

            (var, pos)

        """

        node_u = self.nodes[u]

        node_v = self.nodes[v]

        

        if node_u.terminal:

            pos_u = float('inf')

        else:

            pos_u = self._var_pos(node_u.var)

        

        if node_v.terminal:

            pos_v = float('inf')

        else:

            pos_v = self._var_pos(node_v.var)

        

        if pos_u < pos_v:

            return node_u.var, pos_u

        elif pos_u > pos_v:

            return node_v.var, pos_v

        else:

            # 相同位置，返回变量索引较小的

            if node_u.terminal:

                return node_v.var, pos_v

            elif node_v.terminal:

                return node_u.var, pos_u

            else:

                return min(node_u.var, node_v.var), pos_u

    

    def _apply(self, op, u, v):

        """

        递归应用二元操作（带缓存）

        """

        cache_key = (op, u, v)

        if cache_key in self.apply_cache:

            return self.apply_cache[cache_key]

        

        node_u = self.nodes[u]

        node_v = self.nodes[v]

        

        # 终端情况

        if node_u.terminal and node_v.terminal:

            if op == 'and':

                result = self.terminal_true.id if (node_u.terminal and node_v.terminal) else self.terminal_false.id

            elif op == 'or':

                result = self.terminal_true.id if (node_u.terminal or node_v.terminal) else self.terminal_false.id

            elif op == 'xor':

                result = self.terminal_true.id if (node_u.terminal != node_v.terminal) else self.terminal_false.id

            else:

                raise ValueError(f"Unknown op: {op}")

            self.apply_cache[cache_key] = result

            return result

        

        # 找到最小变量

        min_var, _ = self._find_min_var(u, v)

        

        # 递归计算low和high分支

        if node_u.terminal:

            low_u = high_u = u

        else:

            low_u = node_u.low

            high_u = node_u.high

        

        if node_v.terminal:

            low_v = high_v = v

        else:

            low_v = node_v.low

            high_v = node_v.high

        

        # 确定low分支使用的节点

        if node_u.terminal or self._var_pos(node_u.var) > self._var_pos(min_var):

            low_u = high_u = u

        if node_v.terminal or self._var_pos(node_v.var) > self._var_pos(min_var):

            low_v = high_v = v

        

        if node_u.terminal or self._var_pos(node_u.var) != self._var_pos(min_var):

            low_u = high_u = u

        if node_v.terminal or self._var_pos(node_v.var) != self._var_pos(min_var):

            low_v = high_v = v

        

        low = self._apply(op, low_u, low_v)

        high = self._apply(op, high_u, high_v)

        

        result = self._make_node(min_var, low, high)

        self.apply_cache[cache_key] = result

        return result

    

    def _not(self, u):

        """NOT操作"""

        node = self.nodes[u]

        

        if node.terminal:

            return self.terminal_true.id if not node.terminal else self.terminal_false.id

        

        low = self._not(node.low)

        high = self._not(node.high)

        

        return self._make_node(node.var, low, high)

    

    def var(self, i):

        """

        创建变量x_i的BDD

        

        变量按顺序构建：从当前变量开始，后续都是high分支

        """

        var_pos = self._var_pos(i)

        

        def build(pos):

            if pos == self.num_vars:

                return self.terminal_false.id

            

            current_var = self.var_order[pos]

            low = self.terminal_false.id  # 当前变量为0

            high = build(pos + 1)          # 当前变量为1

            return self._make_node(current_var, low, high)

        

        return build(var_pos)

    

    def and_(self, u, v):

        return self._apply('and', u, v)

    

    def or_(self, u, v):

        return self._apply('or', u, v)

    

    def xor(self, u, v):

        return self._apply('xor', u, v)

    

    def not_(self, u):

        return self._not(u)

    

    def equivalent(self, u, v):

        """

        检测两个OBDD是否等价

        

        参数:

            u, v: 两个OBDD的根节点

        

        返回:

            True/False

        """

        # 如果结构完全相同，则等价

        return u == v

    

    def implies(self, u, v):

        """

        检测 u => v (u蕴含v)

        

        等价于 NOT(u) OR v

        """

        return self.or_(self.not_(u), v)

    

    def sat_count(self, u):

        """

        计算满足u的可满足赋值数量

        

        参数:

            u: OBDD根节点

        

        返回:

            满足赋值的数量

        """

        cache = {}

        

        def count(node_id):

            if node_id in cache:

                return cache[node_id]

            

            node = self.nodes[node_id]

            

            if node.terminal:

                result = 1 if node.terminal else 0

            else:

                # 2^(剩余变量数) * (high分支比例)

                low_count = count(node.low)

                high_count = count(node.high)

                result = low_count + high_count

            

            cache[node_id] = result

            return result

        

        return count(u)

    

    def any_sat(self, u):

        """

        检测是否存在满足u的赋值

        

        参数:

            u: OBDD根节点

        

        返回:

            满足的赋值或None

        """

        assignment = [False] * self.num_vars

        

        def find(node_id):

            node = self.nodes[node_id]

            

            if node.terminal:

                return node.terminal

            

            # 选择一个分支

            if node.low != self.terminal_false.id:

                assignment[node.var] = False

                if find(node.low):

                    return True

            if node.high != self.terminal_false.id:

                assignment[node.var] = True

                if find(node.high):

                    return True

            

            return False

        

        if find(u):

            return assignment

        return None

    

    def all_sat(self, u):

        """

        找出所有满足u的赋值

        

        参数:

            u: OBDD根节点

        

        返回:

            赋值列表

        """

        results = []

        

        def find_all(node_id, assignment):

            node = self.nodes[node_id]

            

            if node.terminal:

                if node.terminal:

                    results.append(assignment.copy())

                return

            

            # low分支

            if node.low != self.terminal_false.id:

                assignment[node.var] = False

                find_all(node.low, assignment)

                assignment[node.var] = None

            

            # high分支

            if node.high != self.terminal_false.id:

                assignment[node.var] = True

                find_all(node.high, assignment)

                assignment[node.var] = None

        

        find_all(u, [None] * self.num_vars)

        return results

    

    def size(self, u):

        """计算OBDD的节点数"""

        visited = set()

        

        def dfs(node_id):

            if node_id in visited or node_id in (self.terminal_true.id, self.terminal_false.id):

                return

            visited.add(node_id)

            node = self.nodes[node_id]

            dfs(node.low)

            dfs(node.high)

        

        dfs(u)

        return len(visited)





def run_demo():

    """运行OBDD简化演示"""

    print("=" * 60)

    print("OBDD（有序二叉决策图）简化算法")

    print("=" * 60)

    

    # 创建OBDD（变量顺序: x0 < x1 < x2）

    obdd = OBDD(var_order=[0, 1, 2])

    

    # 创建变量

    x0 = obdd.var(0)

    x1 = obdd.var(1)

    x2 = obdd.var(2)

    

    print("\n[基础表达式]")

    

    # x0 AND x1 AND x2

    f1 = obdd.and_(obdd.and_(x0, x1), x2)

    print(f"  x0 AND x1 AND x2:")

    print(f"    节点数: {obdd.size(f1)}")

    print(f"    可满足数: {obdd.sat_count(f1)}")

    print(f"    所有赋值: {obdd.all_sat(f1)}")

    

    # x0 OR x1 OR x2

    f2 = obdd.or_(obdd.or_(x0, x1), x2)

    print(f"  x0 OR x1 OR x2:")

    print(f"    节点数: {obdd.size(f2)}")

    print(f"    可满足数: {obdd.sat_count(f2)}")

    print(f"    所有赋值: {obdd.all_sat(f2)}")

    

    # (x0 AND x1) OR (NOT x0 AND x2)

    f3 = obdd.or_(obdd.and_(x0, x1), obdd.and_(obdd.not_(x0), x2))

    print(f"  (x0 AND x1) OR (NOT x0 AND x2):")

    print(f"    节点数: {obdd.size(f3)}")

    print(f"    可满足数: {obdd.sat_count(f3)}")

    print(f"    所有赋值: {obdd.all_sat(f3)}")

    

    print("\n[等价性检测]")

    

    # (x0 AND x1) 与 x0 AND x1

    a = obdd.and_(x0, x1)

    b = obdd.and_(x1, x0)  # 交换顺序

    print(f"  x0 AND x1 等价于 x1 AND x0: {obdd.equivalent(a, b)}")

    

    # (x0 OR x1) AND x0 与 x0

    c = obdd.and_(obdd.or_(x0, x1), x0)

    print(f"  (x0 OR x1) AND x0 等价于 x0: {obdd.equivalent(c, x0)}")

    

    # NOT NOT x0 与 x0

    d = obdd.not_(obdd.not_(x0))

    print(f"  NOT NOT x0 等价于 x0: {obdd.equivalent(d, x0)}")

    

    print("\n[蕴含关系]")

    

    # x0 AND x1 => x0

    e = obdd.and_(x0, x1)

    print(f"  x0 AND x1 => x0: {obdd.equivalent(obdd.implies(e, x0), obdd.terminal_true.id)}")

    

    # x0 => x0 OR x1

    print(f"  x0 => x0 OR x1: {obdd.equivalent(obdd.implies(x0, obdd.or_(x0, x1)), obdd.terminal_true.id)}")

    

    print("\n[可满足性]")

    

    # 永真式: x0 OR NOT x0

    tautology = obdd.or_(x0, obdd.not_(x0))

    print(f"  x0 OR NOT x0:")

    print(f"    是永真式: {obdd.equivalent(tautology, obdd.terminal_true.id)}")

    print(f"    可满足数: {obdd.sat_count(tautology)}")

    

    # 矛盾式: x0 AND NOT x0

    contradiction = obdd.and_(x0, obdd.not_(x0))

    print(f"  x0 AND NOT x0:")

    print(f"    是矛盾式: {obdd.equivalent(contradiction, obdd.terminal_false.id)}")

    print(f"    可满足数: {obdd.sat_count(contradiction)}")

    

    print("\n" + "=" * 60)

    print("OBDD简化核心概念:")

    print("  1. 有序: 变量按固定顺序测试")

    print("  2. 唯一性: 相同结构复用同一节点")

    print("  3. 简化规则:")

    print("     - low==high时消除节点")

    print("     - 终端节点合并")

    print("  4. 性质:")

    print("     - 规范表示（相同顺序下唯一）")

    print("     - 高效等价性检测")

    print("  5. 应用: 模型检查、符号执行、逻辑综合")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

