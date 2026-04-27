# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构 / btb



本文件实现 btb 相关的算法功能。

"""



from typing import List, Dict, Optional, Tuple

from dataclasses import dataclass, field

from enum import Enum





class BranchDirection(Enum):

    """分支方向"""

    NOT_TAKEN = "not_taken"

    TAKEN = "taken"





@dataclass

class BTBEntry:

    """

    BTB条目



    存储分支指令的信息：

    - tag: 标签（用于区分不同分支）

    - target_address: 分支目标地址

    - last_target: 上次分支目标（用于检测目标变化）

    - confidence: 置信度（预测可靠性）

    - instruction: 原始指令信息

    """

    tag: int

    target_address: int

    last_target: int = 0

    confidence: int = 2  # 0-3，3为最高

    instruction: Optional[any] = None

    valid: bool = True





class BranchHistoryRegister:

    """

    全局分支历史寄存器 (GHR)



    记录最近N次分支的结果，用于分支预测。

    """



    def __init__(self, history_length: int = 8):

        self.history_length = history_length

        self.history: int = 0  # 位向量



    def update(self, taken: bool):

        """更新历史"""

        self.history = ((self.history << 1) | (1 if taken else 0)) & ((1 << self.history_length) - 1)



    def get_history(self) -> int:

        """获取当前历史"""

        return self.history



    def clear(self):

        """清除历史"""

        self.history = 0





class BTB:

    """

    分支目标缓冲器 (BTB)



    实现：

    - 直接映射BTB

    - 使用PC索引

    - 存储目标地址和分支历史



    参数：

    - num_entries: BTB条目数量

    - tag_bits: 标签位数

    """



    def __init__(self, num_entries: int = 256, tag_bits: int = 8):

        self.num_entries = num_entries

        self.tag_bits = tag_bits

        self.tag_mask = (1 << tag_bits) - 1



        # BTB存储

        self.entries: List[Optional[BTBEntry]] = [None] * num_entries



        # 分支历史表（可选，用于更复杂的预测）

        self.branch_history_table: Dict[int, int] = {}



        # GHR

        self.ghr = BranchHistoryRegister()



        # 统计

        self.total_lookups = 0

        self.btb_hits = 0

        self.btb_misses = 0



    def _get_index(self, pc: int) -> int:

        """获取BTB索引"""

        return pc & (self.num_entries - 1)



    def _get_tag(self, pc: int) -> int:

        """获取标签"""

        return (pc >> 8) & self.tag_mask  # 简化：使用PC的高位作为tag



    def lookup(self, pc: int) -> Optional[BTBEntry]:

        """

        查找BTB

        param pc: 分支指令地址

        return: BTBEntry或None

        """

        self.total_lookups += 1

        index = self._get_index(pc)

        tag = self._get_tag(pc)



        entry = self.entries[index]

        if entry and entry.tag == tag and entry.valid:

            self.btb_hits += 1

            return entry



        self.btb_misses += 1

        return None



    def update(self, pc: int, target_address: int, taken: bool):

        """

        更新BTB

        param pc: 分支指令地址

        param target_address: 分支目标地址

        param taken: 分支是否被采取

        """

        index = self._get_index(pc)

        tag = self._get_tag(pc)



        if self.entries[index] is None:

            self.entries[index] = BTBEntry(

                tag=tag,

                target_address=target_address,

                last_target=target_address

            )

        else:

            self.entries[index].target_address = target_address

            self.entries[index].last_target = target_address

            self.entries[index].tag = tag

            self.entries[index].valid = True



            # 更新置信度

            if taken:

                self.entries[index].confidence = min(3, self.entries[index].confidence + 1)

            else:

                self.entries[index].confidence = max(0, self.entries[index].confidence - 1)



        # 更新GHR

        self.ghr.update(taken)



    def predict(self, pc: int) -> Tuple[bool, Optional[int]]:

        """

        分支预测

        param pc: 分支指令地址

        return: (预测taken, 目标地址或None)

        """

        entry = self.lookup(pc)



        if entry is None:

            # BTB miss，使用默认预测（假设不跳）

            return False, None



        # 使用置信度和GHR做预测

        if entry.confidence >= 2:

            # 高置信度，预测taken

            return True, entry.target_address

        elif entry.confidence == 1:

            # 低置信度，结合GHR

            history = self.ghr.get_history()

            if history & 1:  # 最近一次分支taken

                return True, entry.target_address

            return False, None

        else:

            # 最低置信度，预测not taken

            return False, None



    def invalidate(self, pc: int):

        """使某个分支的BTB条目无效"""

        index = self._get_index(pc)

        if self.entries[index]:

            self.entries[index].valid = False



    def flush(self):

        """刷新整个BTB"""

        self.entries = [None] * self.num_entries

        self.ghr.clear()



    def get_hit_rate(self) -> float:

        """获取BTB命中率"""

        if self.total_lookups == 0:

            return 0.0

        return self.btb_hits / self.total_lookups





class BTBWithReturnStack:

    """

    带返回栈的BTB



    用于处理子程序调用(Call)和返回(Return)。

    Return指令的目标地址是最近的Call的返回地址。

    """



    def __init__(self, num_entries: int = 256, return_stack_size: int = 8):

        self.btb = BTB(num_entries)

        self.return_stack_size = return_stack_size

        self.return_stack: List[int] = []  # 存储返回地址



    def record_call(self, return_address: int):

        """

        记录函数调用

        在遇到CALL指令时调用

        """

        self.return_stack.append(return_address)

        if len(self.return_stack) > self.return_stack_size:

            self.return_stack.pop(0)



    def predict_return(self) -> Optional[int]:

        """

        预测返回地址

        在遇到RETURN指令时调用

        """

        if not self.return_stack:

            return None

        return self.return_stack[-1]



    def handle_call(self, pc: int, target: int, return_address: int):

        """

        处理CALL指令

        """

        self.btb.update(pc, target, True)

        self.record_call(return_address)



    def handle_return(self) -> Optional[int]:

        """

        处理RETURN指令

        return: 预测的返回地址

        """

        return self.predict_return()



    def handle_branch(self, pc: int, target: int, taken: bool):

        """处理普通分支指令"""

        self.btb.update(pc, target, taken)





class CombinedBTB:

    """

    组合BTB



    结合BTB和分支历史表(BHT)进行更准确的预测。

    """



    def __init__(self, num_btb_entries: int = 256, num_bht_entries: int = 256):

        self.btb = BTB(num_btb_entries)

        self.bht_size = num_bht_entries

        self.bht: List[int] = [0] * num_bht_entries  # 2位饱和计数器



    def _get_bht_index(self, pc: int) -> int:

        """获取BHT索引"""

        return pc & (self.bht_size - 1)



    def predict(self, pc: int) -> Tuple[bool, Optional[int]]:

        """

        组合预测

        使用BTB获取目标地址，使用BHT预测方向

        """

        # BHT预测

        bht_index = self._get_bht_index(pc)

        counter = self.bht[bht_index]

        predicted_taken = counter >= 2



        # BTB查找目标地址

        btb_entry = self.btb.lookup(pc)

        target = btb_entry.target_address if btb_entry else None



        return predicted_taken, target



    def update(self, pc: int, target: int, taken: bool):

        """

        更新BTB和BHT

        """

        # 更新BTB

        self.btb.update(pc, target, taken)



        # 更新BHT

        bht_index = self._get_bht_index(pc)

        counter = self.bht[bht_index]



        if taken:

            self.bht[bht_index] = min(3, counter + 1)

        else:

            self.bht[bht_index] = max(0, counter - 1)





class BTBPerformanceCounter:

    """BTB性能计数器"""



    def __init__(self):

        self.total_branches = 0

        self.btb_hits = 0

        self.btb_misses = 0

        self.mispredictions = 0

        self.call_instructions = 0

        self.return_instructions = 0



    def record_btb_hit(self):

        """记录BTB命中"""

        self.btb_hits += 1



    def record_btb_miss(self):

        """记录BTB未命中"""

        self.btb_misses += 1



    def record_misprediction(self):

        """记录预测错误"""

        self.mispredictions += 1



    def record_call(self):

        """记录CALL指令"""

        self.call_instructions += 1



    def record_return(self):

        """记录RETURN指令"""

        self.return_instructions += 1



    def get_stats(self) -> Dict:

        """获取统计信息"""

        total = self.btb_hits + self.btb_misses

        hit_rate = self.btb_hits / total if total > 0 else 0



        return {

            'total_branches': self.total_branches,

            'btb_hits': self.btb_hits,

            'btb_misses': self.btb_misses,

            'btb_hit_rate': hit_rate * 100,

            'mispredictions': self.mispredictions,

            'misprediction_rate': self.mispredictions / self.total_branches * 100 if self.total_branches > 0 else 0,

            'calls': self.call_instructions,

            'returns': self.return_instructions,

        }





def simulate_btb():

    """

    模拟BTB工作过程

    """

    print("=" * 60)

    print("分支目标缓冲器 (BTB) 模拟")

    print("=" * 60)



    # 创建BTB

    btb = BTB(num_entries=16, tag_bits=4)



    print("\nBTB配置: 16 entries, 4-bit tag")



    # 模拟分支序列

    # 格式: (pc, target, taken)

    branch_sequence = [

        (0x1000, 0x2000, True),   # 分支1：跳转

        (0x1004, 0x2100, False),  # 分支2：不跳

        (0x1008, 0x2200, True),   # 分支3：跳转

        (0x1000, 0x2000, True),   # 分支1再次执行

        (0x100C, 0x2300, True),   # 分支4

        (0x1000, 0x2000, True),   # 分支1

        (0x1008, 0x2200, True),   # 分支3

    ]



    print("\n分支执行序列:")

    print("-" * 50)

    for pc, target, taken in branch_sequence:

        # 预测

        predicted_taken, predicted_target = btb.predict(pc)

        prediction_correct = (predicted_taken == taken) and (predicted_target == target or predicted_target is None)



        # 更新BTB

        btb.update(pc, target, taken)



        # 状态

        entry = btb.lookup(pc)

        status = "命中" if entry else "未命中"



        print(f"PC=0x{pc:04X} | 目标=0x{target:04X} | 实际={'跳' if taken else '不跳'} | "

              f"预测={'跳' if predicted_taken else '不跳'} | {status} | "

              f"{'✓' if prediction_correct else '✗'}")



    print(f"\nBTB统计:")

    print(f"  总查找: {btb.total_lookups}")

    print(f"  命中: {btb.btb_hits}")

    print(f"  未命中: {btb.btb_misses}")

    print(f"  命中率: {btb.get_hit_rate() * 100:.1f}%")



    # 带返回栈的BTB

    print("\n" + "=" * 60)

    print("带返回栈的BTB")

    print("=" * 60)



    btb_rs = BTBWithReturnStack(num_entries=16, return_stack_size=4)



    print("\n函数调用/返回模拟:")

    print("-" * 50)



    # 模拟函数调用

    # main -> func1 -> func2 -> return -> return -> main



    print("1. 主函数调用func1 (PC=0x1000, Target=0x5000)")

    btb_rs.handle_call(0x1000, 0x5000, 0x1004)  # 返回地址0x1004

    print(f"   返回栈: {btb_rs.return_stack}")



    print("2. func1调用func2 (PC=0x5000, Target=0x6000)")

    btb_rs.handle_call(0x5000, 0x6000, 0x5004)

    print(f"   返回栈: {btb_rs.return_stack}")



    print("3. func2返回")

    ret_addr = btb_rs.handle_return()

    print(f"   预测返回地址: 0x{ret_addr:04X} (应该是0x5004)")



    print("4. func1返回")

    ret_addr = btb_rs.handle_return()

    print(f"   预测返回地址: 0x{ret_addr:04X} (应该是0x1004)")



    # 组合BTB+BHT

    print("\n" + "=" * 60)

    print("组合BTB + BHT预测")

    print("=" * 60)



    combined = CombinedBTB(num_btb_entries=16, num_bht_entries=16)



    print("\n组合预测:")

    print("-" * 50)



    test_cases = [

        (0x1000, 0x2000, True),

        (0x1000, 0x2000, True),

        (0x1004, 0x2100, False),

        (0x1008, 0x2200, True),

    ]



    for pc, target, taken in test_cases:

        pred_taken, pred_target = combined.predict(pc)

        combined.update(pc, target, taken)

        print(f"PC=0x{pc:04X} | 实际:{'跳' if taken else '不跳'} | 预测:{'跳' if pred_taken else '不跳'} "

              f"| {'✓' if pred_taken == taken else '✗'}")





if __name__ == "__main__":

    simulate_btb()

