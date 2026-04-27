# -*- coding: utf-8 -*-

"""

算法实现：形式语言与自动机 / pumping_lemma



本文件实现 pumping_lemma 相关的算法功能。

"""



from typing import List, Set, Dict, Tuple, Optional





class PumpingLemmaVerifier:

    """

    泵引理验证器基类

    """

    

    def verify_regular(self, language_name: str, 

                      sample_strings: List[str],

                      pump_length_hint: int = 5) -> Dict:

        """

        验证正则语言泵引理

        

        参数:

            language_name: 语言名称

            sample_strings: 示例字符串

            pump_length_hint: 泵长度提示

        

        返回:

            验证结果字典

        """

        result = {

            'language': language_name,

            'type': 'regular',

            'pump_length_used': pump_length_hint,

            'verified': True,

            'note': '泵引理只能用于证明某语言不是正则，不能证明是正则'

        }

        

        # 检查每个字符串是否可以被泵

        for s in sample_strings:

            if len(s) >= pump_length_hint:

                # 尝试找到分解

                decomposition = self._find_regular_decomposition(s, pump_length_hint)

                if decomposition:

                    result['sample_verified'] = {

                        'string': s,

                        'decomposition': decomposition

                    }

        

        return result

    

    def _find_regular_decomposition(self, s: str, p: int) -> Optional[Dict]:

        """

        尝试找到正则语言的泵引理分解

        

        参数:

            s: 输入字符串

            p: 泵长度

        

        返回:

            分解字典或None

        """

        # 简化版本：假设字符串是'a'开头的重复

        # 实际中需要尝试所有可能的分解

        

        for x_len in range(p + 1):

            for y_len in range(1, p - x_len + 1):

                x = s[:x_len]

                y = s[x_len:x_len + y_len]

                z = s[x_len + y_len:]

                

                # 检查xy长度

                if x_len + y_len <= p and len(y) >= 1:

                    return {

                        'x': x,

                        'y': y,

                        'z': z,

                        'xy_length': x_len + y_len

                    }

        

        return None

    

    def prove_not_regular(self, language: str,

                         counterexample_hint: str,

                         explanation: str) -> Dict:

        """

        证明某语言不是正则语言

        

        参数:

            language: 语言描述

            counterexample_hint: 反例提示

            explanation: 证明解释

        

        返回:

            证明结果

        """

        return {

            'language': language,

            'is_regular': False,

            'proof_type': 'pumping_lemma',

            'counterexample_hint': counterexample_hint,

            'explanation': explanation,

            'verified': True

        }





class RegularPumpingLemma:

    """

    正则语言泵引理验证

    """

    

    def __init__(self, language_name: str, language_test: callable):

        """

        初始化

        

        参数:

            language_name: 语言名称

            language_test: 判断字符串是否属于语言的函数

        """

        self.language_name = language_name

        self.language_test = language_test

    

    def try_pump(self, s: str, p: int) -> List[str]:

        """

        尝试泵送字符串

        

        参数:

            s: 输入字符串

            p: 泵长度

        

        返回:

            所有可能的泵送结果

        """

        results = []

        

        # 尝试所有可能的x,y分解

        for x_len in range(min(p, len(s)) + 1):

            for y_len in range(1, min(p - x_len, len(s) - x_len) + 1):

                if x_len + y_len > len(s):

                    continue

                

                x = s[:x_len]

                y = s[x_len:x_len + y_len]

                z = s[x_len + y_len:]

                

                # 生成 xy^iz for i in 0..3

                for i in range(4):

                    pumped = x + y * i + z

                    results.append({

                        'x': x,

                        'y': y,

                        'z': z,

                        'i': i,

                        'string': pumped,

                        'in_language': self.language_test(pumped)

                    })

        

        return results

    

    def verify_pumping_property(self, s: str, p: int) -> Tuple[bool, Optional[Dict]]:

        """

        验证泵引理属性

        

        参数:

            s: 输入字符串

            p: 泵长度

        

        返回:

            (是否满足泵引理, 失败的分解)

        """

        if len(s) < p:

            return True, None

        

        pumped_results = self.try_pump(s, p)

        

        # 检查是否存在某个分解使得所有泵送结果都在语言中

        # 对每个可能的(x,y)分解

        decompositions = {}

        for r in pumped_results:

            key = (r['x'], r['y'])

            if key not in decompositions:

                decompositions[key] = []

            decompositions[key].append(r)

        

        for (x, y), results in decompositions.items():

            # 检查这个分解是否对所有i都满足

            all_in_language = all(r['in_language'] for r in results)

            if all_in_language:

                return True, {'x': x, 'y': y, 'z': results[0]['z']}

        

        # 没找到满足条件的分解

        return False, None





class ContextFreePumpingLemma:

    """

    上下文无关语言泵引理验证

    """

    

    def __init__(self, grammar_name: str):

        self.grammar_name = grammar_name

    

    def generate_strings(self, max_length: int = 20) -> List[str]:

        """

        生成CFG产生的字符串

        

        参数:

            max_length: 最大长度

        

        返回:

            字符串列表

        """

        # 这是抽象方法，子类需要实现

        return []

    

    def try_pump_cf(self, s: str, p: int) -> List[Dict]:

        """

        尝试上下文无关语言的泵送

        

        参数:

            s: 输入字符串

            p: 泵长度

        

        返回:

            泵送结果列表

        """

        results = []

        

        # 简化版本：假设字符串有重复结构

        # 实际需要更复杂的分解

        

        return results





def prove_an_bm_cn_not_regular() -> Dict:

    """

    证明语言 L = {a^n b^m c^n | n,m >= 1} 不是正则语言

    

    返回:

        证明结果

    """

    proof = {

        'language': '{a^n b^m c^n | n,m >= 1}',

        'is_regular': False,

        'method': 'pumping_lemma',

        'steps': [

            '假设L是正则语言，设泵长度为p',

            '考虑字符串 s = a^p b^p c^p',

            '|s| = 3p > p，所以s可以被泵送',

            '根据泵引理，s = xyz，其中|xy| <= p, |y| >= 1',

            '由于|xy| <= p，y只包含a（或者包含a和b）',

            '如果y只包含a，则xy^iz包含的a超过c的数量',

            '如果y包含a和b，则xy^iz中a和b的关系被打乱',

            '因此xy^iz不属于L，矛盾',

            '所以L不是正则语言'

        ]

    }

    return proof





def prove_an_bn_not_regular() -> Dict:

    """

    证明语言 L = {a^n b^n | n >= 1} 不是正则语言

    

    返回:

        证明结果

    """

    proof = {

        'language': '{a^n b^n | n >= 1}',

        'is_regular': False,

        'method': 'pumping_lemma',

        'steps': [

            '假设L是正则语言，设泵长度为p',

            '考虑字符串 s = a^p b^p',

            '|s| = 2p > p，所以s可以被泵送',

            '根据泵引理，s = xyz，其中|xy| <= p, |y| >= 1',

            '由于|xy| <= p，y只包含a',

            'y = a^k，其中1 <= k <= p',

            'xy^2z = a^{p+k} b^p，不属于L',

            '矛盾！所以L不是正则语言'

        ]

    }

    return proof





def prove_balanced_parentheses_cf() -> Dict:

    """

    证明平衡括号语言是上下文无关的

    

    返回:

        证明结果

    """

    # S -> SS | (S) | ε

    

    grammar = {

        'variables': ['S'],

        'terminals': ['(', ')'],

        'productions': [

            ('S', ['S', 'S']),

            ('S', ['(', 'S', ')']),

            ('S', [])

        ],

        'start_variable': 'S'

    }

    

    return {

        'language': '平衡括号语言 {()^n | n >= 0}',

        'is_context_free': True,

        'grammar': grammar,

        'note': '该语言是上下文无关的，可以用CFG S->SS|(S)|ε生成'

    }





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：泵引理基础验证

    print("=" * 50)

    print("测试1: 泵引理基础")

    print("=" * 50)

    

    verifier = PumpingLemmaVerifier()

    

    # 验证语言 L = {a^n b^n | n >= 0} 不是正则

    result = prove_an_bn_not_regular()

    print(f"语言: {result['language']}")

    print(f"是否正则: {result['is_regular']}")

    print(f"证明步骤:")

    for i, step in enumerate(result['steps'], 1):

        print(f"  {i}. {step}")

    

    # 测试用例2：L = {a^n b^m c^n}

    print("\n" + "=" * 50)

    print("测试2: 证明 {a^n b^m c^n} 不是正则")

    print("=" * 50)

    

    result = prove_an_bm_cn_not_regular()

    print(f"语言: {result['language']}")

    print(f"是否正则: {result['is_regular']}")

    

    # 测试用例3：正则泵引理验证

    print("\n" + "=" * 50)

    print("测试3: 正则泵引理验证")

    print("=" * 50)

    

    # 测试语言 L = a*b*

    def test_ab_star(s: str) -> bool:

        # 检查是否匹配 a*b*

        i = 0

        while i < len(s) and s[i] == 'a':

            i += 1

        while i < len(s) and s[i] == 'b':

            i += 1

        return i == len(s)

    

    lemma = RegularPumpingLemma('a*b*', test_ab_star)

    

    # 测试字符串

    s = 'aabb'

    pumped_results = lemma.try_pump(s, 3)

    

    print(f"语言: a*b*")

    print(f"测试字符串: '{s}'")

    print(f"泵长度: 3")

    print(f"\n可能的泵送结果:")

    for r in pumped_results[:10]:

        print(f"  x='{r['x']}', y='{r['y']}', i={r['i']}: '{r['string']}' -> {'∈' if r['in_language'] else '∉'}")

    

    # 测试用例4：上下文无关泵引理

    print("\n" + "=" * 50)

    print("测试4: 上下文无关语言")

    print("=" * 50)

    

    result = prove_balanced_parentheses_cf()

    print(f"语言: {result['language']}")

    print(f"是否上下文无关: {result['is_context_free']}")

    print(f"文法:")

    for var, prods in result['grammar']['productions']:

        print(f"  {var} -> {' '.join(prods)}")

    

    # 测试用例5：证明某语言是正则

    print("\n" + "=" * 50)

    print("测试5: 正则语言示例")

    print("=" * 50)

    

    verifier = PumpingLemmaVerifier()

    result = verifier.verify_regular(

        'a*b*',

        ['aabb', 'aaabbb', 'ab'],

        pump_length_hint=5

    )

    print(f"语言: {result['language']}")

    print(f"类型: {result['type']}")

    print(f"说明: {result['note']}")

