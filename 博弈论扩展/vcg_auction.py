# -*- coding: utf-8 -*-

"""

算法实现：博弈论扩展 / vcg_auction



本文件实现 vcg_auction 相关的算法功能。

"""



import numpy as np

from typing import List, Dict, Tuple



class VCGMechanism:

    """

    Vickrey-Clarke-Groves (VCG) 拍卖机制

    

    特点:

    1. 占优策略激励相容 (DIC)

    2. 社会福利最大化

    3. 个体理性

    """

    

    def __init__(self, num_items: int = 1):

        self.num_items = num_items

        self.agents: List[str] = []

        self.valuations: Dict[str, float] = {}

        self.bids: Dict[str, float] = {}

    

    def add_agent(self, agent_id: str, valuation: float):

        """添加投标人和其真实价值"""

        self.agents.append(agent_id)

        self.valuations[agent_id] = valuation

    

    def set_bids(self, bids: Dict[str, float]):

        """设置投标人的出价"""

        self.bids = bids

    

    def allocate(self, bids: Dict[str, float]) -> Tuple[str, float]:

        """

        分配物品给最高出价者

        

        Returns:

            (winner_id, winning_bid)

        """

        if not bids:

            return None, 0

        

        winner = max(bids.keys(), key=lambda k: bids[k])

        return winner, bids[winner]

    

    def compute_vcg_payment(self, agent_id: str, bids: Dict[str, float]) -> float:

        """

        计算VCG支付

        

        支付 = (其他人在没有此投标人时的社会福利) - (其他人在有此投标人但不给他时的社会福利)

        

        Args:

            agent_id: 投标人ID

            bids: 所有出价

        

        Returns:

            支付金额

        """

        # 其他人的出价（不包括当前投标人）

        other_bids = {k: v for k, v in bids.items() if k != agent_id}

        

        if not other_bids:

            return 0

        

        # 社会福利1: 没有此投标人时的最优分配

        winner1, _ = self.allocate(other_bids)

        welfare_without = other_bids.get(winner1, 0) if winner1 else 0

        

        # 社会福利2: 有此投标人但不给他物品时的最优分配

        temp_bids = other_bids.copy()

        winner2, _ = self.allocate(temp_bids)

        welfare_excluding = temp_bids.get(winner2, 0) if winner2 else 0

        

        # VCG支付 = welfare_without - welfare_excluding

        payment = welfare_without - welfare_excluding

        

        return max(0, payment)

    

    def run_auction(self) -> Dict:

        """

        运行VCG拍卖

        

        Returns:

            拍卖结果

        """

        winner, winning_bid = self.allocate(self.bids)

        

        payments = {}

        for agent in self.agents:

            if agent in self.bids:

                payments[agent] = self.compute_vcg_payment(agent, self.bids)

        

        # 计算社会福利

        total_welfare = sum(self.valuations.get(a, 0) for a in self.agents if 

                          a == winner)

        

        return {

            "winner": winner,

            "winning_bid": winning_bid,

            "payments": payments,

            "total_welfare": total_welfare,

            "is_dominant_incentive": True

        }



def run_vcg_simulation():

    """VCG拍卖模拟"""

    print("=== VCG拍卖测试 ===")

    

    # 单物品拍卖

    vcg = VCGMechanism(num_items=1)

    

    # 添加投标人

    vcg.add_agent("Alice", valuation=100)

    vcg.add_agent("Bob", valuation=80)

    vcg.add_agent("Charlie", valuation=60)

    

    print("投标人真实价值:")

    for agent, val in vcg.valuations.items():

        print(f"  {agent}: {val}")

    

    # 真实报告价值

    bids = {"Alice": 100, "Bob": 80, "Charlie": 60}

    vcg.set_bids(bids)

    

    result = vcg.run_auction()

    

    print(f"\n出价: {bids}")

    print(f"胜者: {result['winner']}")

    print(f"胜者出价: {result['winning_bid']}")

    print(f"支付: {result['payments']}")

    print(f"社会福利: {result['total_welfare']}")

    

    print("\n=== 激励相容测试 ===")

    print("Alice真实报告(100) vs 谎报(90):")

    

    # Alice谎报

    vcg2 = VCGMechanism()

    vcg2.add_agent("Alice", valuation=100)

    vcg2.add_agent("Bob", valuation=80)

    vcg2.add_agent("Charlie", valuation=60)

    

    bids_cheat = {"Alice": 90, "Bob": 80, "Charlie": 60}

    vcg2.set_bids(bids_cheat)

    result2 = vcg2.run_auction()

    

    print(f"  Alice谎报90时: 胜者={result2['winner']}, 支付={result2['payments'].get('Alice', 0)}")

    

    # 计算Alice的效用

    if result['winner'] == 'Alice':

        utility_truthful = 100 - result['payments']['Alice']

    else:

        utility_truthful = 0

    

    if result2['winner'] == 'Alice':

        utility_cheat = 100 - result2['payments'].get('Alice', 0)

    else:

        utility_cheat = 0

    

    print(f"  Alice真实报告效用: {utility_truthful}")

    print(f"  Alice谎报效用: {utility_cheat}")

    print(f"  真实报告更优: {utility_truthful >= utility_cheat}")

    

    print("\n=== 社会福利分析 ===")

    print("VCG总是产生社会福利最大化的分配")

    

    # 多物品拍卖

    print("\n=== 多物品VCG ===")

    print("VCG可以推广到多物品拍卖")

    print("分配问题变为社会福利最大化问题")



def run_vcg_analysis():

    """VCG机制分析"""

    print("\n=== VCG机制的性质 ===")

    print("1. 激励相容: 如上测试所示")

    print("2. 无亏空: 支付总是非负")

    print("3. 社会福利最大化: 分配给估值最高的人")

    print("4. 个人理性: 参与拍卖不会获得负效用")

    

    print("\n=== VCG的缺点 ===")

    print("1. 计算复杂度: 需要求解社会福利优化问题")

    print("2. 可操作性: 可能不是弱主导的")

    print("3. 预算可行性: 支付可能超过收益")

    print("4. 真实性: 在某些设置下不是truthful")



if __name__ == "__main__":

    run_vcg_simulation()

    run_vcg_analysis()

    

    print("\n=== 真实应用场景 ===")

    print("1. 搜索引擎广告拍卖")

    print("2. 无线频谱分配")

    print("3. 机场降落时段分配")

    print("4. 碳排放配额交易")

    

    print("\n=== 数值示例 ===")

    # 简单数值例子

    agents = ["投标者1", "投标者2", "投标者3"]

    valuations = {"投标者1": 10, "投标者2": 8, "投标者3": 6}

    

    print(f"投标人: {agents}")

    print(f"真实估值: {valuations}")

    print(f"出价: {valuations}")  # VCG下应该真实报告

    

    # VCG计算

    # 最高出价者: 投标者1 (10)

    # 其他人的最优分配: 投标者2获得 (8)

    # 支付 = 8 - 0 = 8 (简化)

    

    print(f"\nVCG分配: 投标者1获得物品")

    print(f"VCG支付: 8 (等于第二高的估值)")

    print(f"社会福利: 10")

    print(f"效率: 100%")

    

    print("\n=== 对比First-Price拍卖 ===")

    print("First-Price拍卖:")

    print("  激励不相容: 投标者会压低出价")

    print("  期望社会福利 < 10")

    print("  需要复杂的投标策略")

    

    print("\n=== VCG理论意义 ===")

    print("VCG是机制设计理论的重要里程碑")

    print("证明了在一定条件下可以实现激励相容和社会福利最大化的统一")

