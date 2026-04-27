# -*- coding: utf-8 -*-

"""

算法实现：区块链算法 / difficulty_adjustment



本文件实现 difficulty_adjustment 相关的算法功能。

"""



import time

from typing import List



class DifficultyAdjuster:

    """

    区块难度调整算法

    

    比特币使用的方法:

    - 每2016个区块（约两周）调整一次难度

    - 目标: 使平均出块时间保持在10分钟左右

    """

    

    TARGET_BLOCK_TIME = 600  # 10分钟 = 600秒

    TARGET_BLOCKS = 2016  # 调整周期

    

    def __init__(self):

        self.history: List[dict] = []

    

    def calculate_difficulty(self, block_time: int, previous_difficulty: int) -> int:

        """

        根据实际出块时间计算新区块难度

        

        Args:

            block_time: 实际平均出块时间（秒）

            previous_difficulty: 当前难度

        

        Returns:

            新难度

        """

        # 如果出块太快，增加难度

        if block_time < self.TARGET_BLOCK_TIME:

            # 难度增加

            adjustment = previous_difficulty // 2048

            new_difficulty = previous_difficulty + adjustment

        else:

            # 难度降低

            adjustment = previous_difficulty // 2048

            new_difficulty = previous_difficulty - adjustment

        

        # 限制最小难度

        return max(new_difficulty, 1)

    

    def simulate_difficulty_adjustment(self, num_periods: int = 10) -> List[dict]:

        """

        模拟难度调整过程

        

        Args:

            num_periods: 模拟的周期数

        

        Returns:

            每轮的难度数据

        """

        results = []

        difficulty = 1  # 初始难度

        

        for period in range(num_periods):

            # 模拟这个周期的出块时间（使用随机值模拟网络变化）

            import random

            variance = random.uniform(0.8, 1.2)  # ±20%波动

            actual_avg_time = self.TARGET_BLOCK_TIME * variance

            

            # 计算新区块难度

            new_difficulty = self.calculate_difficulty(actual_avg_time, difficulty)

            

            result = {

                "period": period + 1,

                "start_difficulty": difficulty,

                "end_difficulty": new_difficulty,

                "actual_avg_block_time": actual_avg_time,

                "change_pct": (new_difficulty - difficulty) / difficulty * 100

            }

            results.append(result)

            

            self.history.append(result)

            difficulty = new_difficulty

        

        return results

    

    def get_difficulty_bits(self, difficulty: int) -> int:

        """

        将难度值转换为Bits字段

        

        Bits字段是压缩表示的难度目标

        """

        # 计算难度对应的目标值

        target = 0xFFFF * (2 ** (8 * (0x1D - 3))) // difficulty

        

        # 压缩为Bits格式

        if target > 0x7FFF:

            # 需要移动

            size = (target.bit_length() + 7) // 8

            coeff = target >> (8 * (size - 3))

            bits = (size << 24) | coeff

        else:

            bits = target

        

        return bits



def simulate_mining_difficulty():

    """模拟挖矿难度变化"""

    print("=== 难度调整算法测试 ===")

    

    adjuster = DifficultyAdjuster()

    

    # 模拟10个周期

    results = adjuster.simulate_difficulty_adjustment(10)

    

    print("\n各周期难度变化:")

    print(f"{'周期':^6} | {'起始难度':^12} | {'结束难度':^12} | {'变化%':^8} | {'平均出块时间':^12}")

    print("-" * 70)

    

    for r in results:

        print(f"{r['period']:^6} | {r['start_difficulty']:^12} | {r['end_difficulty']:^12} | "

              f"{r['change_pct']:^7.2f}% | {r['actual_avg_block_time']:^11.1f}s")

    

    # 分析

    print("\n=== 难度调整分析 ===")

    final_difficulty = results[-1]['end_difficulty']

    initial_difficulty = results[0]['start_difficulty']

    total_change = (final_difficulty - initial_difficulty) / initial_difficulty * 100

    

    print(f"初始难度: {initial_difficulty}")

    print(f"最终难度: {final_difficulty}")

    print(f"总变化: {total_change:+.2f}%")

    

    # 计算预期出块时间

    avg_block_time = sum(r['actual_avg_block_time'] for r in results) / len(results)

    print(f"平均出块时间: {avg_block_time:.1f}秒 (目标: 600秒)")



if __name__ == "__main__":

    simulate_mining_difficulty()

    

    print("\n=== Bits转换测试 ===")

    adjuster = DifficultyAdjuster()

    

    for difficulty in [1, 1000, 100000, 1000000]:

        bits = adjuster.get_difficulty_bits(difficulty)

        print(f"难度{difficulty}: Bits = 0x{bits:08X}")

