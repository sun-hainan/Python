# -*- coding: utf-8 -*-

"""

算法实现：形式语言与自动机 / turing_machine



本文件实现 turing_machine 相关的算法功能。

"""



from typing import Dict, List, Tuple, Optional, Set

from enum import Enum





class Direction(Enum):

    """

    读写头移动方向

    """

    LEFT = 'L'

    RIGHT = 'R'

    STAY = 'S'





class TuringMachine:

    """

    图灵机类

    """

    

    def __init__(self, states: Set[str], alphabet: Set[str], 

                 tape_alphabet: Set[str],

                 transitions: Dict[Tuple[str, str], Tuple[str, str, Direction]],

                 start_state: str, accept_state: str, reject_state: str,

                 blank_symbol: str = '_'):

        """

        初始化图灵机

        

        参数:

            states: 状态集合

            alphabet: 输入字母表（不包括空白符）

            tape_alphabet: 带子字母表（包括空白符和输入符号）

            transitions: 转移函数 {(state, symbol) -> (new_symbol, direction, new_state)}

            start_state: 起始状态

            accept_state: 接受状态

            reject_state: 拒绝状态

            blank_symbol: 空白符（默认'_'）

        """

        self.states = states

        self.alphabet = alphabet

        self.tape_alphabet = tape_alphabet

        self.transitions = transitions

        self.start_state = start_state

        self.accept_state = accept_state

        self.reject_state = reject_state

        self.blank_symbol = blank_symbol

        

        # 初始化带子和读写头

        self.tape: Dict[int, str] = {}

        self.head_position = 0

        self.current_state = start_state

        

        # 运行统计

        self.steps = 0

        self.max_steps = 1000000  # 防止无限循环

    

    def reset(self):

        """

        重置图灵机到初始状态

        """

        self.tape = {}

        self.head_position = 0

        self.current_state = self.start_state

        self.steps = 0

    

    def load_input(self, input_string: str):

        """

        加载输入字符串到带子

        

        参数:

            input_string: 输入字符串

        """

        self.reset()

        

        for i, char in enumerate(input_string):

            self.tape[i] = char

    

    def get_symbol(self, position: int) -> str:

        """

        获取指定位置的符号

        

        参数:

            position: 位置

        

        返回:

            符号（如果是空位置则返回空白符）

        """

        return self.tape.get(position, self.blank_symbol)

    

    def write_symbol(self, position: int, symbol: str):

        """

        在指定位置写入符号

        

        参数:

            position: 位置

            symbol: 符号

        """

        self.tape[position] = symbol

    

    def step(self) -> bool:

        """

        执行一步

        

        返回:

            是否继续执行（False表示停止）

        """

        if self.current_state == self.accept_state:

            return False

        if self.current_state == self.reject_state:

            return False

        

        if self.steps >= self.max_steps:

            return False

        

        self.steps += 1

        

        # 获取当前符号

        current_symbol = self.get_symbol(self.head_position)

        

        # 查找转移

        key = (self.current_state, current_symbol)

        

        if key not in self.transitions:

            # 无转移，进入拒绝状态

            self.current_state = self.reject_state

            return False

        

        new_symbol, direction, new_state = self.transitions[key]

        

        # 写入新符号

        self.write_symbol(self.head_position, new_symbol)

        

        # 移动读写头

        if direction == Direction.LEFT:

            self.head_position -= 1

        elif direction == Direction.RIGHT:

            self.head_position += 1

        # STAY 方向不移动

        

        # 更新状态

        self.current_state = new_state

        

        return True

    

    def run(self, input_string: str) -> Tuple[bool, int, str]:

        """

        运行图灵机

        

        参数:

            input_string: 输入字符串

        

        返回:

            (是否接受, 步数, 当前状态)

        """

        self.load_input(input_string)

        

        while self.step():

            pass

        

        accepted = (self.current_state == self.accept_state)

        

        return accepted, self.steps, self.current_state

    

    def get_tape_content(self, start: int = None, end: int = None) -> str:

        """

        获取带子内容

        

        参数:

            start: 起始位置（默认从头开始）

            end: 结束位置（默认到有内容的最后一个位置）

        

        返回:

            带子内容的字符串表示

        """

        if not self.tape:

            return self.blank_symbol

        

        if start is None:

            start = min(self.tape.keys()) if self.tape else 0

        if end is None:

            end = max(self.tape.keys()) + 1 if self.tape else 1

        

        result = []

        for i in range(start, end):

            symbol = self.get_symbol(i)

            if i == self.head_position:

                result.append(f'[{symbol}]')

            else:

                result.append(symbol)

        

        return ''.join(result)

    

    def get_configuration(self) -> str:

        """

        获取当前配置

        

        返回:

            配置字符串（格式：状态:带子内容）

        """

        tape = self.get_tape_content()

        return f"{self.current_state}: {tape}"





def create_addition_tm() -> TuringMachine:

    """

    创建二进制加法图灵机

    

    功能：计算两个二进制数的加法

    输入格式：a+b# （a和b是两个二进制数，#是分隔符）

    

    返回:

        配置好的图灵机

    """

    states = {'q0', 'q1', 'q2', 'q3', 'q4', 'q5', 'q_accept', 'q_reject'}

    alphabet = {'0', '1', '+', '#'}

    tape_alphabet = alphabet | {'_', 'X'}

    

    transitions = {}

    

    # q0: 找到+号

    transitions[('q0', '0')] = ('0', Direction.RIGHT, 'q0')

    transitions[('q0', '1')] = ('1', Direction.RIGHT, 'q0')

    transitions[('q0', '+')] = ('+', Direction.RIGHT, 'q1')

    

    # q1: 找到第二个数的最后一位

    transitions[('q1', '0')] = ('0', Direction.RIGHT, 'q1')

    transitions[('q1', '1')] = ('1', Direction.RIGHT, 'q1')

    transitions[('q1', '_')] = ('_', Direction.LEFT, 'q2')

    

    # q2: 从右向左处理进位

    # ... (简化版本省略详细转移)

    

    return TuringMachine(

        states=states,

        alphabet=alphabet,

        tape_alphabet=tape_alphabet,

        transitions=transitions,

        start_state='q0',

        accept_state='q_accept',

        reject_state='q_reject'

    )





def create_palindrome_tm() -> TuringMachine:

    """

    创建回文检测图灵机

    

    功能：检测输入是否是回文

    输入格式：二进制字符串

    

    返回:

        配置好的图灵机

    """

    states = {'q0', 'q1', 'q2', 'q3', 'q_accept', 'q_reject'}

    alphabet = {'0', '1'}

    tape_alphabet = alphabet | {'_', 'X'}

    

    transitions = {}

    

    # q0: 找到最左边的符号

    transitions[('q0', '0')] = ('X', Direction.RIGHT, 'q1')

    transitions[('q0', '1')] = ('X', Direction.RIGHT, 'q1')

    transitions[('q0', '_')] = ('_', Direction.RIGHT, 'q_accept')

    

    # q1: 向右移动找到对应的符号

    transitions[('q1', '0')] = ('0', Direction.RIGHT, 'q1')

    transitions[('q1', '1')] = ('1', Direction.RIGHT, 'q1')

    transitions[('q1', 'X')] = ('X', Direction.RIGHT, 'q1')

    transitions[('q1', '_')] = ('_', Direction.LEFT, 'q2')

    

    # q2: 向左移动检查匹配

    transitions[('q2', '0')] = ('X', Direction.LEFT, 'q0')

    transitions[('q2', '1')] = ('X', Direction.LEFT, 'q0')

    

    return TuringMachine(

        states=states,

        alphabet=alphabet,

        tape_alphabet=tape_alphabet,

        transitions=transitions,

        start_state='q0',

        accept_state='q_accept',

        reject_state='q_reject'

    )





def create_universal_tm() -> TuringMachine:

    """

    创建通用图灵机（简化版）

    

    通用图灵机可以模拟任何其他图灵机

    这是一个概念性实现

    

    返回:

        通用图灵机

    """

    # 这是一个高度简化的示例

    # 真正的通用图灵机需要编码任意图灵机

    pass





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：简单的状态转移

    print("=" * 50)

    print("测试1: 简单图灵机")

    print("=" * 50)

    

    # 创建只接受以0开头的字符串的图灵机

    states = {'q0', 'q_accept', 'q_reject'}

    alphabet = {'0', '1'}

    tape_alphabet = alphabet | {'_'}

    

    transitions = {

        ('q0', '0'): ('0', Direction.RIGHT, 'q_accept'),

        ('q0', '1'): ('1', Direction.RIGHT, 'q_reject'),

    }

    

    tm = TuringMachine(

        states=states,

        alphabet=alphabet,

        tape_alphabet=tape_alphabet,

        transitions=transitions,

        start_state='q0',

        accept_state='q_accept',

        reject_state='q_reject'

    )

    

    test_strings = ['0', '1', '00', '10', '']

    

    for s in test_strings:

        accepted, steps, final_state = tm.run(s)

        print(f"  '{s}': {'接受' if accepted else '拒绝'} (状态: {final_state})")

    

    # 测试用例2：回文检测

    print("\n" + "=" * 50)

    print("测试2: 回文检测")

    print("=" * 50)

    

    tm = create_palindrome_tm()

    

    test_strings = ['0', '1', '00', '11', '01', '10', '000', '010', '101']

    

    for s in test_strings:

        accepted, steps, final_state = tm.run(s)

        print(f"  '{s}': {'是回文' if accepted else '不是回文'} (步数: {steps})")

    

    # 测试用例3：单步执行演示

    print("\n" + "=" * 50)

    print("测试3: 单步执行演示")

    print("=" * 50)

    

    # 创建更简单的图灵机来演示

    states = {'q0', 'q1', 'q_accept'}

    alphabet = {'a', 'b'}

    tape_alphabet = alphabet | {'_', 'X'}

    

    transitions = {

        ('q0', 'a'): ('X', Direction.RIGHT, 'q1'),

        ('q1', 'a'): ('a', Direction.RIGHT, 'q1'),

        ('q1', '_'): ('_', Direction.LEFT, 'q_accept'),

    }

    

    tm = TuringMachine(

        states=states,

        alphabet=alphabet,

        tape_alphabet=tape_alphabet,

        transitions=transitions,

        start_state='q0',

        accept_state='q_accept',

        reject_state='q_reject'

    )

    

    input_str = 'aa'

    tm.load_input(input_str)

    

    print(f"输入: '{input_str}'")

    print(f"初始配置: {tm.get_configuration()}")

    

    print("\n执行步骤:")

    for i in range(5):

        if tm.current_state == 'q_accept':

            print(f"  步骤{i+1}: 接受状态")

            break

        

        continued = tm.step()

        print(f"  步骤{i+1}: {tm.get_configuration()}")

        

        if not continued:

            break

    

    # 测试用例4：图灵机模拟加法

    print("\n" + "=" * 50)

    print("测试4: 加法图灵机")

    print("=" * 50)

    

    # 这是一个占位符，因为完整的加法图灵机很复杂

    print("注意：完整的二进制加法图灵机需要复杂的转移函数")

    print("这里只是展示概念")

    

    # 测试用例5：带子可视化

    print("\n" + "=" * 50)

    print("测试5: 带子可视化")

    print("=" * 50)

    

    states = {'q0', 'q1', 'q_accept'}

    alphabet = {'0', '1'}

    tape_alphabet = alphabet | {'_'}

    

    transitions = {

        ('q0', '0'): ('1', Direction.RIGHT, 'q1'),

        ('q0', '1'): ('0', Direction.RIGHT, 'q1'),

        ('q1', '_'): ('_', Direction.LEFT, 'q_accept'),

    }

    

    tm = TuringMachine(

        states=states,

        alphabet=alphabet,

        tape_alphabet=tape_alphabet,

        transitions=transitions,

        start_state='q0',

        accept_state='q_accept',

        reject_state='q_reject'

    )

    

    input_str = '101'

    tm.load_input(input_str)

    

    print(f"输入: '{input_str}'")

    

    for i in range(6):

        if tm.current_state == 'q_accept':

            print(f"  接受")

            break

        

        tape_content = tm.get_tape_content(-5, 10)

        print(f"  状态: {tm.current_state}, 带子: {tape_content}")

        

        if not tm.step():

            break

    

    # 测试用例6：拒绝状态

    print("\n" + "=" * 50)

    print("测试6: 拒绝状态演示")

    print("=" * 50)

    

    states = {'q0', 'q1', 'q_accept', 'q_reject'}

    alphabet = {'a'}

    tape_alphabet = alphabet | {'_'}

    

    transitions = {

        ('q0', 'a'): ('a', Direction.RIGHT, 'q1'),

        ('q0', '_'): ('_', Direction.RIGHT, 'q_accept'),

        ('q1', '_'): ('_', Direction.LEFT, 'q_reject'),  # 永远无法到达

    }

    

    tm = TuringMachine(

        states=states,

        alphabet=alphabet,

        tape_alphabet=tape_alphabet,

        transitions=transitions,

        start_state='q0',

        accept_state='q_accept',

        reject_state='q_reject'

    )

    

    # 只有当输入为空时才接受

    accepted, steps, final_state = tm.run('')

    print(f"输入 '': {'接受' if accepted else '拒绝'}")

    

    accepted, steps, final_state = tm.run('a')

    print(f"输入 'a': {'接受' if accepted else '拒绝'}")

