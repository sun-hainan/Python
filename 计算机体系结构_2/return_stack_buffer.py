# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / return_stack_buffer



本文件实现 return_stack_buffer 相关的算法功能。

"""



import random

from typing import List, Optional

from dataclasses import dataclass





@dataclass

class Call_Record:

    """函数调用记录"""

    return_addr: int = 0  # 返回地址

    caller_pc: int = 0   # 调用者PC

    depth: int = 0       # 调用深度





class Return_Stack_Buffer:

    """返回栈缓冲器"""

    def __init__(self, size: int = 16):

        self.size = size                      # RSB深度

        self.stack: List[int] = []            # 栈存储（返回地址）

        self.max_depth_reached: int = 0       # 历史最大深度

        # 统计信息

        self.push_count: int = 0              # 压栈次数

        self.pop_count: int = 0               # 弹栈次数

        self.hits: int = 0                   # 命中次数

        self.misses: int = 0                 # 未命中次数





    def is_full(self) -> bool:

        """判断RSB是否已满"""

        return len(self.stack) >= self.size





    def is_empty(self) -> bool:

        """判断RSB是否为空"""

        return len(self.stack) == 0





    def push(self, return_addr: int):

        """压入返回地址（CALL指令时调用）"""

        if not self.is_full():

            self.stack.append(return_addr)

            self.push_count += 1

            if len(self.stack) > self.max_depth_reached:

                self.max_depth_reached = len(self.stack)

        else:

            # 栈满时覆盖底部（循环缓冲行为）

            self.stack.pop(0)

            self.stack.append(return_addr)

            self.push_count += 1





    def pop(self) -> Optional[int]:

        """弹出返回地址（RET指令时调用）"""

        if self.is_empty():

            self.misses += 1

            return None

        self.pop_count += 1

        addr = self.stack.pop()

        return addr





    def peek(self) -> Optional[int]:

        """查看栈顶返回地址（不弹出）"""

        if self.is_empty():

            return None

        return self.stack[-1]





    def top_n(self, n: int) -> List[int]:

        """获取栈顶n个返回地址"""

        if len(self.stack) == 0:

            return []

        return self.stack[-n:] if n >= len(self.stack) else self.stack[-n:]





    def get_mispredict_rate(self) -> float:

        """计算错误预测率"""

        total = self.hits + self.misses

        return self.misses / total if total > 0 else 0.0





class RSB_With_BPB:

    """结合BTB的返回预测器（混合预测）"""

    def __init__(self, rsb_size: int = 16, btb_size: int = 128):

        self.rsb = Return_Stack_Buffer(size=rsb_size)

        self.btb_size = btb_size

        # BTB用于存储CALL目标（CALL指令的目标是函数入口）

        self.call_target_cache: dict = {}

        # 返回地址缓存（用于区分直接返回和间接返回）

        self.return_cache: dict = {}





    def handle_call(self, pc: int, next_pc: int):

        """

        处理CALL指令

        pc: CALL指令地址

        next_pc: 下一条指令地址（即返回地址）

        """

        return_addr = next_pc

        # 压入RSB

        self.rsb.push(return_addr)

        # 记录到缓存

        self.call_target_cache[pc] = return_addr





    def handle_ret(self) -> Optional[int]:

        """

        处理RET指令

        返回: 预测的返回地址

        """

        predicted = self.rsb.pop()

        if predicted is not None:

            self.rsb.hits += 1

        return predicted





    def handle_indirect_branch(self, pc: int) -> Optional[int]:

        """处理间接分支（通过缓存预测）"""

        return self.return_cache.get(pc)





def simulate_call_ret_sequence():

    """模拟函数调用/返回序列"""

    print("=== RSB模拟：函数调用序列 ===")

    rsb = Return_Stack_Buffer(size=8)

    # 模拟调用栈

    # main -> func_a -> func_b -> func_c -> func_d -> ret

    call_sequence = [

        ("main", 0x1000, 0x1004),

        ("func_a", 0x2000, 0x2004),

        ("func_b", 0x3000, 0x3004),

        ("func_c", 0x4000, 0x4004),

        ("func_d", 0x5000, 0x5004),

    ]

    print("调用序列:")

    for name, entry, ret_addr in call_sequence:

        rsb.push(ret_addr)

        print(f"  CALL {name}: 压入返回地址 0x{ret_addr:x}, 栈深度={len(rsb.stack)}")

    print("\n返回序列:")

    for name, entry, ret_addr in reversed(call_sequence):

        predicted = rsb.pop()

        match = "✓" if predicted == ret_addr else "✗"

        print(f"  RET from {name}: 预测=0x{predicted:x}, 实际=0x{ret_addr:x} {match}")

    print(f"\n统计: 压栈={rsb.push_count}, 弹栈={rsb.pop_count}, 最大深度={rsb.max_depth_reached}")





def basic_test():

    """基本功能测试"""

    simulate_call_ret_sequence()

    print("\n" + "=" * 50 + "\n")

    # 测试混合预测器

    predictor = RSB_With_BPB(rsb_size=8)

    print("=== 混合RSB-BTB预测器测试 ===")

    # 模拟递归调用

    predictor.handle_call(0x1000, 0x1004)  # main

    predictor.handle_call(0x2000, 0x2004)  # func_a

    predictor.handle_call(0x2000, 0x2008)  # func_a (再次调用)

    predictor.handle_call(0x3000, 0x3004)  # func_b

    print(f"RSB栈内容: {predictor.rsb.stack}")

    print("预测返回:")

    for i in range(4):

        pred = predictor.handle_ret()

        print(f"  第{i+1}次RET: 预测=0x{pred:x if pred else 0:x}")





if __name__ == "__main__":

    basic_test()

