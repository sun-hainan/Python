# -*- coding: utf-8 -*-

"""

算法实现：可验证计算 / consistency_check



本文件实现 consistency_check 相关的算法功能。

"""



import hashlib

from typing import List, Tuple





class ConsistencyChecker:

    """一致性检查器"""



    def __init__(self, parties: int):

        """

        参数：

            parties: 各方数量

        """

        self.parties = parties

        self.values = {}



    def submit_value(self, party_id: int, value: str) -> None:

        """

        提交值



        参数：

            party_id: 参与方ID

            value: 提交的值

        """

        self.values[party_id] = value



    def check_consistency(self) -> Tuple[bool, List[int]]:

        """

        检查一致性



        返回：(是否一致, 不一致的参与方)

        """

        if len(self.values) < 2:

            return True, []



        values_list = list(self.values.values())

        first_value = values_list[0]



        inconsistent = []

        for party_id, value in self.values.items():

            if value != first_value:

                inconsistent.append(party_id)



        return len(inconsistent) == 0, inconsistent



    def generate_proof(self, value: str) -> str:

        """

        生成一致性证明



        返回：证明字符串

        """

        return hashlib.sha256(value.encode()).hexdigest()





def byzantine_consensus():

    """拜占庭共识"""

    print("=== 拜占庭共识 ===")

    print()

    print("问题：")

    print("  - n 个节点，其中 f 个可能是恶意的")

    print("  - 需要就某个值达成共识")

    print()

    print("容忍：")

    print("  - 拜占庭将军问题")

    print("  - 需要 n > 3f 才能达成共识")

    print()

    print("应用：")

    print("  - 区块链共识")

    print("  - 分布式数据库")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 一致性检查测试 ===\n")



    parties = 4

    checker = ConsistencyChecker(parties)



    # 模拟提交

    checker.submit_value(0, "value_A")

    checker.submit_value(1, "value_A")

    checker.submit_value(2, "value_B")  # 不一致

    checker.submit_value(3, "value_A")



    print("提交值：")

    for pid, val in checker.values.items():

        print(f"  参与方 {pid}: {val}")

    print()



    # 检查一致性

    is_consistent, inconsistent = checker.check_consistency()



    print(f"一致性: {'是' if is_consistent else '否'}")

    if inconsistent:

        print(f"不一致的参与方: {inconsistent}")



    # 生成证明

    proof = checker.generate_proof("value_A")

    print(f"\n证明: {proof[:16]}...")



    print()

    byzantine_consensus()



    print()

    print("说明：")

    print("  - 一致性检查用于多方计算验证")

    print("  - 在拜占庭环境中特别重要")

    print("  - 是区块链共识的基础")

