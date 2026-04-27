# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / branch_misprediction



本文件实现 branch_misprediction 相关的算法功能。

"""



import random

from typing import List, Optional, Dict, Tuple

from dataclasses import dataclass, field

from enum import Enum, auto





class Branch_Outcome(Enum):

    """分支结果"""

    TAKEN = auto()

    NOT_TAKEN = auto()





@dataclass

class Branch_Predictor_Stats:

    """分支预测器统计"""

    total_predictions: int = 0

    correct_predictions: int = 0

    mispredictions: int = 0

    # 方向预测统计

    taken_correct: int = 0

    taken_incorrect: int = 0

    not_taken_correct: int = 0

    not_taken_incorrect: int = 0





class Two_Bit_Predictor:

    """两位饱和计数器分支预测器"""

    def __init__(self, num_entries: int = 256):

        self.num_entries = num_entries

        self.counter_table: List[int] = [1] * num_entries  # 0-3: SN, WN, WT, ST

        self.index_mask = num_entries - 1

        self.stats = Branch_Predictor_Stats()





    def predict(self, pc: int) -> bool:

        """预测分支方向"""

        idx = pc & self.index_mask

        return self.counter_table[idx] >= 2  # 2=WT, 3=ST





    def update(self, pc: int, outcome: Branch_Outcome):

        """更新预测器"""

        idx = pc & self.index_mask

        self.stats.total_predictions += 1

        predicted = self.counter_table[idx] >= 2

        actual = (outcome == Branch_Outcome.TAKEN)

        if predicted == actual:

            self.stats.correct_predictions += 1

            if actual:

                self.stats.taken_correct += 1

            else:

                self.stats.not_taken_correct += 1

        else:

            self.stats.mispredictions += 1

            if actual:

                self.stats.taken_incorrect += 1

            else:

                self.stats.not_taken_incorrect += 1

        # 更新计数器

        if outcome == Branch_Outcome.TAKEN:

            self.counter_table[idx] = min(3, self.counter_table[idx] + 1)

        else:

            self.counter_table[idx] = max(0, self.counter_table[idx] - 1)





    def get_accuracy(self) -> float:

        """获取预测准确率"""

        if self.stats.total_predictions == 0:

            return 0.0

        return self.stats.correct_predictions / self.stats.total_predictions





class Branch_Target_Buffer:

    """分支目标缓冲器"""

    def __init__(self, num_entries: int = 128):

        self.num_entries = num_entries

        self.entries: Dict[int, int] = {}  # PC -> target





    def lookup(self, pc: int) -> Optional[int]:

        """查找分支目标"""

        return self.entries.get(pc)





    def update(self, pc: int, target: int):

        """更新BTB"""

        if len(self.entries) >= self.num_entries:

            # 简单淘汰：删除第一个

            first_key = next(iter(self.entries))

            del self.entries[first_key]

        self.entries[pc] = target





@dataclass

class Pipeline_State:

    """流水线状态"""

    fetch_pc: int = 0x1000

    decode_instr: Optional[str] = None

    execute_ready: bool = False

    commit_ready: bool = False

    flush_signal: bool = False





class Misprediction_Penalty_Calculator:

    """分支预测失败代价计算器"""

    def __init__(self, pipeline_depth: int = 10, fetch_width: int = 4):

        self.pipeline_depth = pipeline_depth        # 流水线深度

        self.fetch_width = fetch_width              # 取指宽度

        self.predictor = Two_Bit_Predictor(num_entries=256)

        self.btb = Branch_Target_Buffer()

        # 模拟流水线状态

        self.stages: List[Optional[str]] = [None] * pipeline_depth

        # 统计

        self.cycles: int = 0

        self.instructions_fetched: int = 0

        self.branches_encountered: int = 0

        self.misprediction_penalty_total: int = 0

        self.misprediction_count: int = 0





    def simulate_misprediction(self, branch_pc: int, actual_target: int, fetch_pc: int):

        """模拟一次分支预测失败"""

        # 模拟流水线刷新代价

        # 假设分支在Execute阶段发现预测错误

        # 需要刷新Fetch和Decode两个阶段

        penalty_cycles = 2  # 典型代价

        # 更新PC到正确目标

        self.stages[0] = actual_target

        # 清除后续流水线级

        for i in range(1, min(3, self.pipeline_depth)):

            self.stages[i] = None

        self.misprediction_penalty_total += penalty_cycles

        self.misprediction_count += 1

        print(f"  分支预测失败! PC=0x{branch_pc:x}, 实际目标=0x{actual_target:x}, 代价={penalty_cycles}周期")





    def run_simulation(self, num_branches: int = 100, mispredict_rate: float = 0.15):

        """运行模拟"""

        print(f"=== 分支预测失败代价模拟 ===")

        print(f"流水线深度: {self.pipeline_depth}")

        print(f"预测器: 两位饱和计数器")

        print(f"预设误预测率: {mispredict_rate:.1%}")

        print()

        for i in range(num_branches):

            branch_pc = 0x1000 + i * 4

            # 随机生成分支结果

            actual_taken = random.random() < 0.6  # 60% taken

            outcome = Branch_Outcome.TAKEN if actual_taken else Branch_Outcome.NOT_TAKEN

            # 预测

            predicted_taken = self.predictor.predict(branch_pc)

            self.predictor.update(branch_pc, outcome)

            # 记录分支

            self.branches_encountered += 1

            # 计算目标

            actual_target = branch_pc + 8 if actual_taken else branch_pc + 4

            # 检查是否误预测

            if predicted_taken != actual_taken:

                self.simulate_misprediction(branch_pc, actual_target, branch_pc)

            else:

                print(f"  分支预测正确: PC=0x{branch_pc:x}, 方向={'Taken' if actual_taken else 'Not Taken'}")

            if i >= 9:  # 只显示前10条

                print(f"  ... (共模拟 {num_branches} 条分支)")

                break

        # 更新BTB

        self.btb.update(branch_pc, actual_target)

        print(f"\n统计结果:")

        print(f"  总分支数: {self.branches_encountered}")

        print(f"  误预测次数: {self.misprediction_count}")

        print(f"  预测准确率: {self.predictor.get_accuracy():.2%}")

        print(f"  总误预测代价: {self.misprediction_penalty_total} 周期")

        print(f"  平均误预测代价: {self.misprediction_penalty_total / max(1, self.misprediction_count):.2f} 周期/次")





def calculate_penalty_theoretical(pipeline_depth: int, fetch_width: int) -> Dict[str, int]:

    """理论计算不同流水线配置下的误预测代价"""

    # Fetch和Decode级被刷新

    flush_stages = 2

    # 每周期可取 fetch_width 条指令

    instructions_lost = flush_stages * fetch_width

    return {

        "pipeline_depth": pipeline_depth,

        "fetch_width": fetch_width,

        "flush_stages": flush_stages,

        "instructions_lost_per_mispredict": instructions_lost,

        "cycles_lost_per_mispredict": flush_stages

    }





def basic_test():

    """基本功能测试"""

    print("=== 分支预测失败代价分析 ===\n")

    # 理论计算

    configs = [

        (5, 1, "5级流水线, 单发射"),

        (10, 1, "10级流水线, 单发射"),

        (10, 4, "10级流水线, 4发射"),

        (15, 4, "15级流水线, 4发射"),

        (20, 8, "20级流水线, 8发射"),

    ]

    print("理论代价分析:")

    for depth, width, desc in configs:

        result = calculate_penalty_theoretical(depth, width)

        print(f"\n  {desc}:")

        print(f"    刷新级数: {result['flush_stages']}")

        print(f"    每次误预测损失: {result['instructions_lost_per_mispredict']} 条指令, {result['cycles_lost_per_mispredict']} 周期")

    # 模拟

    print("\n" + "=" * 50)

    print("\n模拟验证:")

    sim = Misprediction_Penalty_Calculator(pipeline_depth=10, fetch_width=4)

    sim.run_simulation(num_branches=100)





if __name__ == "__main__":

    basic_test()

