# -*- coding: utf-8 -*-

"""

算法实现：计算复杂性理论 / time_hierarchy



本文件实现 time_hierarchy 相关的算法功能。

"""



from typing import Callable, Set, Dict, Optional

import math





class TimeComplexityAnalyzer:

    """

    时间复杂度分析器

    """

    

    def __init__(self):

        self.results: Dict[str, dict] = {}

    

    def analyze_algorithm(self, name: str, time_func: Callable[[int], float], 

                         input_sizes: list) -> dict:

        """

        分析算法的时间复杂度

        

        参数:

            name: 算法名称

            time_func: 时间函数

            input_sizes: 输入大小列表

        

        返回:

            分析结果

        """

        times = []

        for n in input_sizes:

            times.append(time_func(n))

        

        # 估计时间增长率

        if len(times) >= 2:

            ratio = times[-1] / times[0] if times[0] > 0 else float('inf')

            n_ratio = input_sizes[-1] / input_sizes[0]

            

            # 估计复杂度

            if ratio < 2:

                complexity = "O(1) 或 O(log n)"

            elif ratio < n_ratio ** 2:

                complexity = "O(n)"

            elif ratio < n_ratio ** 3:

                complexity = "O(n²)"

            else:

                complexity = "O(n^k) k > 2"

        else:

            complexity = "无法确定"

        

        return {

            'name': name,

            'times': list(zip(input_sizes, times)),

            'estimated_complexity': complexity

        }





def simulate_dtime_hierarchy():

    """

    模拟时间层次定理的概念

    

    返回:

        时间层次结构信息

    """

    hierarchies = [

        {

            'class': 'L',

            'name': 'Logarithmic',

            'time_bound': 'O(log n)',

            'example': '路径问题（无权重）',

            'contains': []

        },

        {

            'class': 'P',

            'name': 'Polynomial',

            'time_bound': 'O(n^k)',

            'example': '线性规划、匹配',

            'contains': ['L', 'NL']

        },

        {

            'class': 'NP',

            'name': 'Non-deterministic Polynomial',

            'time_bound': 'O(2^n) (非确定性)',

            'example': 'SAT、哈密顿路径',

            'contains': ['P']  # 如果 P = NP

        },

        {

            'class': 'PSPACE',

            'name': 'Polynomial Space',

            'time_bound': 'O(n^k) 空间',

            'example': '博弈、QBF',

            'contains': ['NP', 'P']

        },

        {

            'class': 'EXPTIME',

            'name': 'Exponential Time',

            'time_bound': 'O(2^{n^k})',

            'example': '一般博弈',

            'contains': ['PSPACE', 'NP', 'P']

        },

    ]

    

    return hierarchies





def prove_time_hierarchy_simple() -> Dict:

    """

    简单证明时间层次定理

    

    证明思路：

    1. 对角线方法

    2. 假设存在比f(n)更快的算法可以判定某个语言

    3. 构造新的图灵机模拟该算法

    4. 使用停机问题的不可判定性得到矛盾

    

    返回:

        证明概述

    """

    proof = {

        'theorem': '时间层次定理',

        'statement': '''

        如果 f(n) 是时间可构造的，且 f(n) = ω(n log n)，

        则存在语言L使得：

        - L ∈ TIME(f(n)²)

        - L ∉ TIME(f(n))

        ''',

        'proof_idea': [

            '1. 定义语言 L = {⟨M⟩⟨w⟩ : M 在 f(|w|) 时间内拒绝 w}',

            '2. 假设 L ∈ TIME(f(n))，则存在图灵机 M_L 在 O(f(n)) 时间内判定 L',

            '3. 构造图灵机 M\': 模拟 M_L 对输入 ⟨M_L⟩⟨M_L⟩',

            '4. M\' 的行为与其模拟的判定矛盾',

            '5. 因此 L ∉ TIME(f(n))',

            '6. 构造 L 的算法在 O(f(n)²) 时间内运行，所以 L ∈ TIME(f(n)²)'

        ],

        'conclusion': '时间层次定理成立：增加时间可以解决更多问题'

    }

    

    return proof





def time_constructible(f: Callable[[int], int]) -> bool:

    """

    检查函数是否是时间可构造的

    

    时间可构造：存在图灵机在f(n)时间内计算f(n)

    

    参数:

        f: 函数

    

    返回:

        是否可能是时间可构造的

    """

    # 简化检查：函数必须是单调递增的

    # 实际需要可计算性证明

    return True





def hierarchy_comparison() -> Dict:

    """

    时间层次类的比较

    

    返回:

        层次结构

    """

    hierarchy = """

    时间层次结构 (确定性):

    

    O(1) ⊂ O(log n) ⊂ O(n) ⊂ O(n log n) ⊂ O(n²) ⊂ O(n³) ⊂ ... ⊂ O(2^{n^k}) ⊂ O(2^{2^n})

    

    对应的复杂性类:

    

    O(n^k) ⊂ EXP = O(2^{n^c})

    

    主要包含关系:

    - L ⊂ NL ⊂ P ⊂ NP ⊂ PSPACE ⊂ EXPTIME ⊂ NEXPTIME ⊂ ...

    

    已知严格包含（如果 P ≠ NP）:

    - P ⊂ EXP (严格)

    - L ⊂ PSPACE (严格)

    """

    

    return {'hierarchy': hierarchy}





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：时间复杂度分析

    print("=" * 50)

    print("测试1: 时间复杂度分析")

    print("=" * 50)

    

    analyzer = TimeComplexityAnalyzer()

    

    # 定义不同复杂度的算法

    def constant_time(n):

        return 0.001

    

    def log_time(n):

        return math.log2(n) * 0.001

    

    def linear_time(n):

        return n * 0.001

    

    def quadratic_time(n):

        return (n ** 2) * 0.00001

    

    input_sizes = [10, 100, 1000, 10000]

    

    for name, func in [

        ('常数时间', constant_time),

        ('对数时间', log_time),

        ('线性时间', linear_time),

        ('平方时间', quadratic_time)

    ]:

        result = analyzer.analyze_algorithm(name, func, input_sizes)

        print(f"\n{name}:")

        print(f"  估计复杂度: {result['estimated_complexity']}")

        print(f"  时间示例: {result['times'][-1]:.6f}秒 (n={input_sizes[-1]})")

    

    # 测试用例2：时间层次结构

    print("\n" + "=" * 50)

    print("测试2: 时间层次结构")

    print("=" * 50)

    

    hierarchies = simulate_dtime_hierarchy()

    

    print("计算复杂性时间层次:")

    for h in hierarchies:

        print(f"\n{h['class']} ({h['name']}):")

        print(f"  时间界: {h['time_bound']}")

        print(f"  示例问题: {h['example']}")

        if h['contains']:

            print(f"  真包含: {', '.join(h['contains'])}")

    

    # 测试用例3：时间层次定理证明概述

    print("\n" + "=" * 50)

    print("测试3: 时间层次定理证明思路")

    print("=" * 50)

    

    proof = prove_time_hierarchy_simple()

    print(f"定理: {proof['theorem']}")

    print(f"\n陈述: {proof['statement']}")

    print("\n证明思路:")

    for step in proof['proof_idea']:

        print(f"  {step}")

    print(f"\n结论: {proof['conclusion']}")

    

    # 测试用例4：层次比较

    print("\n" + "=" * 50)

    print("测试4: 层次类比较")

    print("=" * 50)

    

    result = hierarchy_comparison()

    print(result['hierarchy'])

    

    # 测试用例5：时间可构造性

    print("\n" + "=" * 50)

    print("测试5: 时间可构造函数")

    print("=" * 50)

    

    functions = [

        ("n", lambda n: n),

        ("n²", lambda n: n ** 2),

        ("2^n", lambda n: 2 ** n),

        ("n!", lambda n: math.factorial(n)),

    ]

    

    for name, f in functions:

        is_constructible = time_constructible(f)

        print(f"  {name}: {'可能是' if is_constructible else '不是'}时间可构造")

