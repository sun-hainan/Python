# -*- coding: utf-8 -*-

"""

算法实现：多智能体系统 / market_mechanism



本文件实现 market_mechanism 相关的算法功能。

"""



import numpy as np

from collections import defaultdict





class Bidder:

    """竞价者（买家或卖家）"""

    

    def __init__(self, bidder_id, valuation, is_buyer=True, budget=None):

        # bidder_id: 竞价者ID

        # valuation: 估值（买家：愿付价格，卖家：最低接受价格）

        # is_buyer: 是否为买家

        # budget: 买家预算限制

        self.bidder_id = bidder_id

        self.valuation = valuation

        self.is_buyer = is_buyer

        self.budget = budget

        self.quantity = 0  # 成交量

        self.payment = 0.0  # 支付金额

    

    def get_utility(self):

        """计算效用（买家：估值 - 支付）"""

        if self.is_buyer:

            return self.valuation * self.quantity - self.payment

        else:

            return self.payment - self.valuation * self.quantity





class Resource:

    """资源对象"""

    

    def __init__(self, resource_id, initial_price=0.0):

        # resource_id: 资源ID

        # initial_price: 初始价格

        self.resource_id = resource_id

        self.current_price = initial_price

        self.quantity = 1.0  # 数量（可分割资源）

        self.owner = None

    

    def update_price(self, new_price):

        """更新资源价格"""

        self.current_price = max(0, new_price)

    

    def get_asking_price(self):

        """获取要价"""

        return self.current_price





class DoubleAuction:

    """双向拍卖：买家和卖家同时竞价"""

    

    def __init__(self, market_clearing_fee=0.0):

        # market_clearing_fee: 市场清算费用比例

        self.market_clearing_fee = market_clearing_fee

        self.buyers = []

        self.sellers = []

        self.cleared_quantity = 0

        self.clearing_price = 0.0

        self.transaction_history = []

    

    def add_buyer(self, buyer):

        """添加买家"""

        self.buyers.append(buyer)

    

    def add_seller(self, seller):

        """添加卖家"""

        self.sellers.append(seller)

    

    def clear_market(self):

        """

        市场清算

        按价格排序，买家从高到低，卖家从低到高

        找到均衡点

        """

        # 按估值排序买家（从高到低）

        sorted_buyers = sorted(self.buyers, key=lambda x: x.valuation, reverse=True)

        # 按要价排序卖家（从低到高）

        sorted_sellers = sorted(self.sellers, key=lambda x: x.valuation)

        

        # 找到均衡

        transactions = []

        buyer_idx = 0

        seller_idx = 0

        

        while buyer_idx < len(sorted_buyers) and seller_idx < len(sorted_sellers):

            buyer = sorted_buyers[buyer_idx]

            seller = sorted_sellers[seller_idx]

            

            # 检查是否有利可图

            if buyer.valuation < seller.valuation:

                # 无交易空间

                break

            

            # 执行交易

            price = (buyer.valuation + seller.valuation) / 2  # 中间价

            quantity = min(buyer.quantity, seller.quantity)

            

            buyer.payment += price * quantity * (1 + self.market_clearing_fee)

            seller.payment += price * quantity * (1 - self.market_clearing_fee)

            buyer.quantity = max(0, buyer.quantity - quantity)

            seller.quantity = max(0, seller.quantity - quantity)

            

            transactions.append({

                'buyer': buyer.bidder_id,

                'seller': seller.bidder_id,

                'price': price,

                'quantity': quantity

            })

            

            if buyer.quantity == 0:

                buyer_idx += 1

            if seller.quantity == 0:

                seller_idx += 1

        

        self.transaction_history.extend(transactions)

        self.cleared_quantity = sum(t['quantity'] for t in transactions)

        

        if transactions:

            self.clearing_price = np.mean([t['price'] for t in transactions])

        

        return transactions

    

    def get_market_summary(self):

        """获取市场汇总"""

        total_buyer_utility = sum(b.get_utility() for b in self.buyers)

        total_seller_utility = sum(s.get_utility() for s in self.sellers)

        

        return {

            'cleared_quantity': self.cleared_quantity,

            'clearing_price': self.clearing_price,

            'n_transactions': len(self.transaction_history),

            'total_buyer_utility': total_buyer_utility,

            'total_seller_utility': total_seller_utility,

            'total_social_welfare': total_buyer_utility + total_seller_utility

        }





class WalrasianEquilibrium:

    """瓦尔拉斯均衡求解器"""

    

    def __init__(self, n_goods):

        # n_goods: 商品数量

        self.n_goods = n_goods

        self.prices = np.ones(n_goods)  # 初始价格

        self.agents = []

        self.allocation = None

    

    def add_agent(self, agent_type, valuation_vector, endowment_vector):

        """

        添加经济主体

        agent_type: 'consumer' 或 'producer'

        valuation_vector: 估值向量（消费者）或 成本向量（生产者）

        endowment_vector: 初始禀赋向量

        """

        self.agents.append({

            'type': agent_type,

            'valuation': np.array(valuation_vector),

            'endowment': np.array(endowment_vector)

        })

    

    def compute_demand(self, agent, prices):

        """计算需求（简化版）"""

        if agent['type'] == 'consumer':

            # 消费者在预算约束下最大化效用

            budget = np.sum(agent['endowment'] * prices)

            # 简化：按比例分配预算到各商品

            demand = agent['valuation'] * budget / (np.sum(agent['valuation']) + 1e-8)

            return demand

        else:

            # 生产者选择产量使得边际成本=价格

            return np.ones(self.n_goods) * 0.5

    

    def compute_supply(self, agent, prices):

        """计算供给（简化版）"""

        if agent['type'] == 'producer':

            # 生产者利润最大化

            return np.maximum(0, prices - agent['valuation'])

        return np.zeros(self.n_goods)

    

    def find_equilibrium(self, max_iterations=100, tolerance=1e-4):

        """寻找瓦尔拉斯均衡"""

        print("\n===== 瓦尔拉斯均衡求解 =====")

        

        for iteration in range(max_iterations):

            # 计算总需求和总供给

            total_demand = np.zeros(self.n_goods)

            total_supply = np.zeros(self.n_goods)

            

            for agent in self.agents:

                total_demand += self.compute_demand(agent, self.prices)

                total_supply += self.compute_supply(agent, self.prices)

            

            # 调整价格

            excess_demand = total_demand - total_supply

            

            # 价格调整规则

            price_adjustment = excess_demand * 0.1

            self.prices += price_adjustment

            self.prices = np.maximum(self.prices, 0.01)  # 价格下限

            

            # 检查收敛

            max_excess = np.max(np.abs(excess_demand))

            

            if iteration % 20 == 0:

                print(f"  迭代 {iteration}: 价格={self.prices.round(4)}, "

                      f" excess_demand={max_excess:.6f}")

            

            if max_excess < tolerance:

                print(f"  在第 {iteration} 轮收敛")

                break

        

        return {

            'prices': self.prices,

            'excess_demand': excess_demand,

            'n_iterations': iteration + 1

        }





class VickreyAuction:

    """维克瑞拍卖（第二价格拍卖）

    

    特点：赢家支付第二高的出价

    激励兼容：说真话是最优策略

    """

    

    def __init__(self, item_id, reserve_price=0.0):

        # item_id: 拍卖物品ID

        # reserve_price: 保留价

        self.item_id = item_id

        self.reserve_price = reserve_price

        self.bids = {}  # bidder_id -> bid_value

        self.winner_id = None

        self.winning_price = 0.0

    

    def submit_bid(self, bidder_id, bid_value):

        """提交出价"""

        if bid_value >= self.reserve_price:

            self.bids[bidder_id] = bid_value

            return True

        return False

    

    def close_auction(self):

        """关闭拍卖并确定赢家"""

        if not self.bids:

            return None, None

        

        # 按出价排序

        sorted_bids = sorted(self.bids.items(), key=lambda x: x[1], reverse=True)

        

        # 最高出价者赢

        self.winner_id = sorted_bids[0][0]

        

        # 第二价格（如果有多个高于保留价的出价）

        if len(sorted_bids) > 1:

            self.winning_price = sorted_bids[1][1]

        else:

            self.winning_price = self.reserve_price

        

        return self.winner_id, self.winning_price

    

    def get_result(self):

        """获取拍卖结果"""

        return {

            'winner': self.winner_id,

            'winning_price': self.winning_price,

            'all_bids': self.bids,

            'n_bidders': len(self.bids)

        }





class GSPMechanism:

    """广义 second-price (GSP) 竞价机制

    

    用于广告拍卖等多槽位资源分配

    """

    

    def __init__(self, n_slots):

        # n_slots: 可用槽位数

        self.n_slots = n_slots

        self.bidders = []  # (bidder_id, bid_value, quality_score)

        self.allocation = []

        self.payments = {}

    

    def submit_bid(self, bidder_id, bid_value, quality_score=1.0):

        """提交出价（带有质量分数，如CTR）"""

        self.bidders.append({

            'id': bidder_id,

            'bid': bid_value,

            'quality': quality_score,

            'effective_bid': bid_value * quality_score

        })

    

    def allocate_slots(self):

        """分配槽位（按有效出价排序）"""

        # 按有效出价排序

        sorted_bidders = sorted(self.bidders, 

                              key=lambda x: x['effective_bid'], 

                              reverse=True)

        

        self.allocation = []

        self.payments = {}

        

        for rank, bidder in enumerate(sorted_bidders[:self.n_slots]):

            slot = {

                'bidder_id': bidder['id'],

                'rank': rank + 1,

                'effective_bid': bidder['effective_bid']

            }

            self.allocation.append(slot)

            

            # 计算支付：下一个位置的出价（如果存在）

            if rank < self.n_slots - 1:

                next_bidder = sorted_bidders[rank + 1]

                # 简化的GSP支付

                next_effective = next_bidder['effective_bid']

                payment = next_effective / bidder['quality'] if bidder['quality'] > 0 else next_effective

            else:

                payment = 0

            

            self.payments[bidder['id']] = payment

        

        return self.allocation

    

    def get_allocation_result(self):

        """获取分配结果"""

        return {

            'allocation': self.allocation,

            'payments': self.payments,

            'total_revenue': sum(self.payments.values())

        }





class GittinsIndexCalculator:

    """Gittins Index计算器（用于多臂老虎机场景的资源分配）"""

    

    def __init__(self, n_arms):

        # n_arms: 臂的数量

        self.n_arms = n_arms

        self.trial_counts = np.zeros(n_arms)  # 各臂试验次数

        self.rewards = np.zeros(n_arms)  # 各臂累计奖励

    

    def update(self, arm_id, reward):

        """更新臂的统计"""

        self.trial_counts[arm_id] += 1

        self.rewards[arm_id] += reward

    

    def compute_gittins_index(self, arm_id, discount=0.95):

        """

        计算Gittins Index

        GI_i = (r_i + beta_i * V_i) / (1 + beta_i * trial_count_i)

        

        简化版本：

        GI_i = average_reward + sqrt(2 * log(1/delta) / trial_count_i)

        """

        if self.trial_counts[arm_id] == 0:

            return float('inf')

        

        avg_reward = self.rewards[arm_id] / self.trial_counts[arm_id]

        confidence_radius = np.sqrt(

            2 * np.log(1.0 / 0.1) / self.trial_counts[arm_id]

        )

        

        return avg_reward + confidence_radius

    

    def select_arm(self, epsilon=0.0):

        """选择臂（epsilon-greedy）"""

        if np.random.random() < epsilon:

            return np.random.randint(self.n_arms)

        

        indices = [self.compute_gittins_index(i) for i in range(self.n_arms)]

        return np.argmax(indices)





if __name__ == "__main__":

    # 测试市场机制资源分配

    print("=" * 50)

    print("市场机制资源分配测试")

    print("=" * 50)

    

    # 测试1: 双向拍卖

    print("\n--- 双向拍卖测试 ---")

    auction = DoubleAuction()

    

    # 添加买家

    for i in range(5):

        buyer = Bidder(i, valuation=10.0 + np.random.uniform(0, 5), is_buyer=True)

        buyer.quantity = 1.0

        auction.add_buyer(buyer)

    

    # 添加卖家

    for i in range(5):

        seller = Bidder(i + 10, valuation=5.0 + np.random.uniform(0, 3), is_buyer=False)

        seller.quantity = 1.0

        auction.add_seller(seller)

    

    transactions = auction.clear_market()

    summary = auction.get_market_summary()

    

    print(f"  成交数量: {summary['cleared_quantity']}")

    print(f"  清算价格: {summary['clearing_price']:.2f}")

    print(f"  交易笔数: {summary['n_transactions']}")

    print(f"  社会总福利: {summary['total_social_welfare']:.2f}")

    

    # 测试2: 维克瑞拍卖

    print("\n--- 维克瑞拍卖测试 ---")

    vickrey = VickreyAuction(item_id="item001", reserve_price=100)

    

    bidders = [(1, 150), (2, 200), (3, 120), (4, 180)]

    for bidder_id, bid in bidders:

        vickrey.submit_bid(bidder_id, bid)

        print(f"  竞价者 {bidder_id} 出价: {bid}")

    

    winner, price = vickrey.close_auction()

    result = vickrey.get_result()

    

    print(f"  赢家: 竞价者 {winner}")

    print(f"  支付价格: {price:.2f}")

    

    # 测试3: GSP竞价

    print("\n--- GSP竞价机制测试 ---")

    gsp = GSPMechanism(n_slots=3)

    

    gsp.submit_bid(1, bid_value=10.0, quality_score=0.05)  # eCPM = 0.5

    gsp.submit_bid(2, bid_value=8.0, quality_score=0.08)  # eCPM = 0.64

    gsp.submit_bid(3, bid_value=15.0, quality_score=0.03)  # eCPM = 0.45

    gsp.submit_bid(4, bid_value=12.0, quality_score=0.06)  # eCPM = 0.72

    

    allocation = gsp.allocate_slots()

    result = gsp.get_allocation_result()

    

    print(f"  分配结果:")

    for slot in result['allocation']:

        print(f"    第{slot['rank']}位: 竞价者{slot['bidder_id']}, "

              f"有效出价={slot['effective_bid']:.4f}")

    

    print(f"  支付: {result['payments']}")

    print(f"  总收入: {result['total_revenue']:.2f}")

    

    # 测试4: Gittins Index

    print("\n--- Gittins Index 资源分配测试 ---")

    gittins = GittinsIndexCalculator(n_arms=4)

    

    # 模拟选择过程

    for step in range(20):

        arm = gittins.select_arm(epsilon=0.1)

        reward = np.random.randn() + [2, 1, 3, 0][arm]  # 不同臂不同均值

        gittins.update(arm, reward)

        

        if step % 5 == 0:

            indices = [gittins.compute_gittins_index(i) for i in range(4)]

            print(f"  Step {step}: 指数={[f'{x:.2f}' for x in indices]}, "

                  f"选择臂={[gittins.select_arm(epsilon=0) for _ in range(1)]}")

    

    print("\n✓ 市场机制资源分配测试完成")

