# -*- coding: utf-8 -*-

"""

算法实现：程序语言理论 / fixpoint_theory



本文件实现 fixpoint_theory 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional, Callable, Generic

from dataclasses import dataclass, field

from enum import Enum, auto





T = TypeVar('T')





class Partial_Order:

    """偏序集"""

    def __init__(self, le: Callable[[T, T], bool]):

        self.le = le



    def is_leq(self, x: T, y: T) -> bool:

        return self.le(x, y)



    def is_geq(self, x: T, y: T) -> bool:

        return self.le(y, x)



    def is_eq(self, x: T, y: T) -> bool:

        return self.le(x, y) and self.le(y, x)





@dataclass

class Lattice:

    """格（全序偏序集）"""

    elements: List

    le: Callable

    # lub: Callable  # least upper bound

    # glb: Callable  # greatest lower bound





@dataclass

class Complete_Lattice(Lattice):

    """完全格（每个子集都有lub和glb）"""

    def __init__(self, elements: List, le: Callable):

        super().__init__(elements, le)

        self._lub_cache: Dict[frozenset, any] = {}

        self._glb_cache: Dict[frozenset, any] = {}





    def lub(self, S: Set) -> Optional:

        """最小上界（join）"""

        if not S:

            return None

        # 假设S非空且有上界

        candidates = [x for x in self.elements if all(self.le(y, x) for y in S)]

        if candidates:

            return min(candidates, key=lambda x: sum(1 for y in S if self.le(x, y) and x != y))

        return None





    def glb(self, S: Set) -> Optional:

        """最大下界（meet）"""

        if not S:

            return None

        candidates = [x for x in self.elements if all(self.le(x, y) for y in S)]

        if candidates:

            return max(candidates, key=lambda x: sum(1 for y in S if self.le(y, x) and x != y))

        return None





class Knaster_Tarski:

    """

    Knaster-Tarski不动点定理

    在完全格上，单调函数f有最小不动点和最大不动点

    """

    @staticmethod

    def fixpoint(f: Callable, lattice: Complete_Lattice) -> Tuple[Optional, Optional]:

        """

        计算f的最小和最大不动点

        返回: (least_fixpoint, greatest_fixpoint)

        """

        # 最小不动点：⊔ { x | f(x) ⊑ x }

        pre_fixpoints = {x for x in lattice.elements if lattice.le(f(x), x)}

        least = lattice.lub(set(pre_fixpoints)) if pre_fixpoints else None

        # 最大不动点：⊓ { x | x ⊑ f(x) }

        post_fixpoints = {x for x in lattice.elements if lattice.le(x, f(x))}

        greatest = lattice.glb(set(post_fixpoints)) if post_fixpoints else None

        return least, greatest





    @staticmethod

    def kleene_iteration(f: Callable, lattice: Complete_Lattice, max_iter: int = 100) -> Optional:

        """

        Kleene迭代（用于计算最小不动点）

        ⊥, f(⊥), f(f(⊥)), ... → lfp(f)

        """

        # 找到最小的元素

        bottom = lattice.lub(set())  # 最小元素

        if bottom is None:

            # 假设第一个元素是最小的

            bottom = lattice.elements[0] if lattice.elements else None

        if bottom is None:

            return None

        current = bottom

        for _ in range(max_iter):

            next_val = f(current)

            if lattice.le(next_val, current) and lattice.le(current, next_val):

                return current

            current = next_val

        return current





class Least_Fixed_Point:

    """最小不动点（lfp）"""

    @staticmethod

    def compute(f: Callable, lattice: Complete_Lattice) -> Optional:

        """计算单调函数f的lfp"""

        return Knaster_Tarski.kleene_iteration(f, lattice)





class Greatest_Fixed_Point:

    """最大不动点（gfp）"""

    @staticmethod

    def compute(f: Callable, lattice: Complete_Lattice) -> Optional:

        """计算单调函数f的gfp"""

        # 对偶迭代

        # ⊤, f(⊤), f(f(⊤)), ... → gfp(f)

        top = lattice.glb(set(lattice.elements)) if lattice.elements else None

        if top is None and lattice.elements:

            top = lattice.elements[-1]

        if top is None:

            return None

        current = top

        for _ in range(100):

            next_val = f(current)

            if lattice.le(next_val, current) and lattice.le(current, next_val):

                return current

            current = next_val

        return current





@dataclass

class Galois_Connection:

    """伽罗瓦连接 α ⊣ γ"""

    abstract: Callable  # α : C → A

    concrete: Callable   # γ : A → C





class Abstract_Interpretation_Fixpoint:

    """抽象解释不动点"""

    @staticmethod

    def compute_fp(transfer: Callable, lattice: Complete_Lattice, widening: Callable = None) -> Optional:

        """

        计算传递函数的不动点

        使用可选的加宽操作加速收敛

        """

        if widening is None:

            return Least_Fixed_Point.compute(transfer, lattice)

        # 加宽版本

        current = lattice.lub(set()) or lattice.elements[0] if lattice.elements else None

        if current is None:

            return None

        for _ in range(100):

            next_val = transfer(current)

            widened = widening(current, next_val)

            if lattice.le(widened, current) and lattice.le(current, widened):

                return current

            current = widened

        return current





def widening_default(a, b, le) -> any:

    """默认加宽操作"""

    return b  # 简化





@dataclass

class Fixpoint_Equation:

    """不动点方程 X = F(X)"""

    variable: str

    function: Callable





class System_of_Equations:

    """不动点方程组"""

    def __init__(self, equations: List[Fixpoint_Equation]):

        self.equations = equations





    def solve(self, lattice: Complete_Lattice) -> Dict[str, any]:

        """求解方程组"""

        # 简化的联合迭代

        values = {eq.variable: None for eq in self.equations}

        for _ in range(100):

            new_values = {}

            for eq in self.equations:

                new_values[eq.variable] = eq.function(values)

            # 检查收敛

            converged = all(

                (values[k] is None and v is None) or

                (values[k] is not None and v is not None and lattice.le(values[k], v) and lattice.le(v, values[k]))

                for k, v in new_values.items()

            )

            values = new_values

            if converged:

                break

        return values





def basic_test():

    """基本功能测试"""

    print("=== 不动点理论测试 ===")

    # 完全格

    print("\n[完全格]")

    elements = [0, 1, 2, 3, 4, 5]

    lattice = Complete_Lattice(elements, lambda x, y: x <= y)

    print(f"  格元素: {elements}")

    print(f"  lub({{2, 4}}) = {lattice.lub({2, 4})}")

    print(f"  glb({{2, 4}}) = {lattice.glb({2, 4})}")

    # Knaster-Tarski

    print("\n[Knaster-Tarski定理]")

    f = lambda x: min(5, x + 1)  # 单调函数

    lfp, gfp = Knaster_Tarski.fixpoint(f, lattice)

    print(f"  f(x) = min(5, x+1)")

    print(f"  最小不动点: {lfp}")

    print(f"  最大不动点: {gfp}")

    # Kleene迭代

    print("\n[Kleene迭代]")

    fix = Knaster_Tarski.kleene_iteration(f, lattice)

    print(f"  Kleene迭代结果: {fix}")

    # lfp计算

    print("\n[最小不动点]")

    lfp_val = Least_Fixed_Point.compute(f, lattice)

    print(f"  lfp(f) = {lfp_val}")

    # gfp计算

    print("\n[最大不动点]")

    gfp_val = Greatest_Fixed_Point.compute(f, lattice)

    print(f"  gfp(f) = {gfp_val}")

    # 方程组

    print("\n[不动点方程组]")

    eq1 = Fixpoint_Equation("x", lambda vals: min(10, vals.get("y", 0) + 1))

    eq2 = Fixpoint_Equation("y", lambda vals: min(10, vals.get("x", 0) + 2))

    system = System_of_Equations([eq1, eq2])

    result = system.solve(lattice)

    print(f"  x = min(10, y+1)")

    print(f"  y = min(10, x+2)")

    print(f"  解: x={result['x']}, y={result['y']}")





if __name__ == "__main__":

    basic_test()

