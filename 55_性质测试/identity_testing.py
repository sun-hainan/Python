# -*- coding: utf-8 -*-

"""

算法实现：性质测试 / identity_testing



本文件实现 identity_testing 相关的算法功能。

"""



import random

from typing import Callable, Any





class IdentityTester:

    """相等性测试器"""



    def __init__(self, epsilon: float = 0.01):

        """

        参数：

            epsilon: 错误概率容限

        """

        self.epsilon = epsilon



    def test_function_equality(self,

                              f1: Callable,

                              f2: Callable,

                              domain: list,

                              n_tests: int = None) -> Tuple[bool, float]:

        """

        测试两个函数是否相等



        参数：

            f1, f2: 要比较的函数

            domain: 定义域

            n_tests: 测试次数



        返回：(是否相等, 置信度)

        """

        if n_tests is None:

            n_tests = int(1 / self.epsilon)



        n_tests = min(n_tests, len(domain))



        # 随机测试

        differences = 0



        for _ in range(n_tests):

            x = random.choice(domain)



            try:

                y1 = f1(x)

                y2 = f2(x)



                if not self._equal(y1, y2):

                    differences += 1



            except Exception:

                return False, 0.0



        # 如果发现差异，一定不相等

        if differences > 0:

            return False, 1.0



        # 计算置信度

        confidence = 1.0 - (1.0 / n_tests) ** n_tests



        return True, confidence



    def _equal(self, a: Any, b: Any) -> bool:

        """比较两个值"""

        if isinstance(a, (list, tuple)):

            return list(a) == list(b)

        return a == b



    def test_polynomial_equality(self,

                                poly1_coeffs: list,

                                poly2_coeffs: list) -> Tuple[bool, float]:

        """

        测试多项式是否相等



        参数：

            poly1_coeffs: 多项式1系数

            poly2_coeffs: 多项式2系数



        返回：(是否相等, 置信度)

        """

        # 同一性检测：随机取值验证

        n_tests = int(1 / self.epsilon)



        for _ in range(n_tests):

            x = random.randint(1, 100)



            v1 = sum(c * (x ** i) for i, c in enumerate(poly1_coeffs))

            v2 = sum(c * (x ** i) for i, c in enumerate(poly2_coeffs))



            if v1 != v2:

                return False, 1.0



        confidence = 1.0 - (1.0 / n_tests) ** n_tests

        return True, confidence





def identity_testing_applications():

    """相等性测试应用"""

    print("=== 相等性测试应用 ===")

    print()

    print("1. 程序验证")

    print("   - 验证优化后的代码等价")

    print("   - 形式化验证")

    print()

    print("2. 零知识证明")

    print("   - 证明你知道某个东西")

    print("   - 不泄露具体值")

    print()

    print("3. 数据库查询")

    print("   - 验证查询优化正确性")

    print("   - 测试查询等价")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 相等性测试 ===\n")



    tester = IdentityTester(epsilon=0.001)



    # 定义两个简单函数

    def f1(x):

        return x ** 2 + 2 * x + 1



    def f2(x):

        return (x + 1) ** 2



    def f3(x):

        return x ** 2 + 2 * x + 2



    # 定义域

    domain = list(range(-100, 100))



    print("测试 f1 = (x+1)² 和 f2 = x²+2x+1:")

    equal, conf = tester.test_function_equality(f1, f2, domain)

    print(f"  相等: {'是' if equal else '否'}, 置信度: {conf:.4f}")



    print("\n测试 f1 和 f3:")

    equal, conf = tester.test_function_equality(f1, f3, domain)

    print(f"  相等: {'是' if equal else '否'}, 置信度: {conf:.4f}")



    print()

    print("多项式测试：")

    poly1 = [1, 2, 1]  # x² + 2x + 1

    poly2 = [1, 2, 1]  # 相同

    poly3 = [1, 2, 2]  # 不同



    equal, conf = tester.test_polynomial_equality(poly1, poly2)

    print(f"  poly1 = poly2: {'是' if equal else '否'} (置信度 {conf:.4f})")



    equal, conf = tester.test_polynomial_equality(poly1, poly3)

    print(f"  poly1 = poly3: {'是' if equal else '否'} (置信度 {conf:.4f})")



    print()

    identity_testing_applications()



    print()

    print("说明：")

    print("  - 概率测试可以高效验证等价")

    print("  - 错误概率可控制")

    print("  - 在密码学和验证中有应用")

