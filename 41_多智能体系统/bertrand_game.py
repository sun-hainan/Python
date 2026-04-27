# -*- coding: utf-8 -*-

"""

算法实现：多智能体系统 / bertrand_game



本文件实现 bertrand_game 相关的算法功能。

"""



import numpy as np

from scipy.optimize import minimize, brentq





class BertrandFirm:

    """伯特兰德模型中的企业"""

    

    def __init__(self, firm_id, marginal_cost, capacity=None, product_differentiation=0.0):

        # firm_id: 企业ID

        # marginal_cost: 边际成本

        # capacity: 生产容量限制（None表示无限制）

        # product_differentiation: 产品差异化程度

        self.firm_id = firm_id

        self.marginal_cost = marginal_cost

        self.capacity = capacity

        self.product_differentiation = product_differentiation

        

        # 策略空间

        self.price = None

        self.profit = 0.0

    

    def set_price(self, price):

        """设置销售价格"""

        if price < self.marginal_cost:

            price = self.marginal_cost  # 价格不能低于边际成本

        if self.capacity and price < self.marginal_cost * 0.9:

            price = self.marginal_cost * 0.9

        self.price = price

        return price





class BertrandOligopoly:

    """伯特兰德寡头垄断模型"""

    

    def __init__(self, market_size=100.0, elasticity=-2.0):

        # market_size: 市场规模（最大需求量）

        # elasticity: 价格弹性

        self.market_size = market_size

        self.elasticity = elasticity

        

        # 企业列表

        self.firms = []

    

    def add_firm(self, firm):

        """添加企业到市场"""

        self.firms.append(firm)

    

    def demand(self, price, differentiation_matrix):

        """

        计算需求函数

        price: 当前价格（或价格向量）

        differentiation_matrix: 产品差异化矩阵

        """

        if len(self.firms) == 1:

            # 单企业：需求与价格负相关

            base_demand = self.market_size * (price[0] ** self.elasticity)

            return np.array([max(0, base_demand)])

        

        # 多企业：考虑差异化

        n_firms = len(self.firms)

        demands = []

        

        for i, firm_i in enumerate(self.firms):

            # 自身价格吸引力

            if firm_i.price is None:

                continue

            

            # 与竞争对手的价格差（考虑差异化）

            price_diff = []

            for j, firm_j in enumerate(self.firms):

                if i != j and firm_j.price is not None:

                    diff = firm_i.price - firm_j.price

                    # 差异化调整

                    adj_diff = diff / (1 + differentiation_matrix[i, j])

                    price_diff.append(adj_diff)

            

            # 需求模型：D_i = S * exp(alpha * (P_j - P_i))

            if price_diff:

                avg_diff = np.mean(price_diff)

                alpha = 0.1  # 价格敏感度

                demand = self.market_size / n_firms * np.exp(alpha * avg_diff)

            else:

                demand = self.market_size / n_firms

            

            demands.append(max(0, demand))

        

        return np.array(demands)

    

    def compute_profit(self, firm_idx, demands):

        """计算企业利润"""

        firm = self.firms[firm_idx]

        if firm.price is None or demands[firm_idx] == 0:

            return 0.0

        

        quantity = demands[firm_idx]

        revenue = firm.price * quantity

        cost = firm.marginal_cost * quantity

        

        return revenue - cost

    

    def best_response(self, firm_idx, rival_prices):

        """

        计算企业的最优反应函数

        firm_idx: 当前企业的索引

        rival_prices: 竞争对手的价格列表

        """

        firm = self.firms[firm_idx]

        

        def profit_function(price):

            firm.set_price(price)

            prices = [f.price for f in self.firms]

            demands = self.demand(prices, np.zeros((len(self.firms), len(self.firms))))

            return -self.compute_profit(firm_idx, demands)

        

        # 在[mc, 10*mc]范围内搜索最优价格

        mc = firm.marginal_cost

        result = minimize(profit_function, x0=mc * 1.5, bounds=[(mc, mc * 10)])

        

        optimal_price = result.x[0]

        firm.set_price(optimal_price)

        

        return optimal_price, -result.fun





class BertrandGameSolver:

    """伯特兰德博弈求解器"""

    

    def __init__(self, tolerance=1e-6, max_iterations=100):

        # tolerance: 收敛容差

        # max_iterations: 最大迭代次数

        self.tolerance = tolerance

        self.max_iterations = max_iterations

        self.convergence_history = []

    

    def find_nash_equilibrium(self, market):

        """

        寻找纳什均衡

        使用迭代最佳反应动态

        """

        print("\n===== 伯特兰德博弈纳什均衡求解 =====")

        

        # 初始化价格

        for firm in market.firms:

            firm.set_price(firm.marginal_cost * 2.0)

        

        # 差异化矩阵（对称）

        n_firms = len(market.firms)

        diff_matrix = np.zeros((n_firms, n_firms))

        for i in range(n_firms):

            for j in range(n_firms):

                if i != j:

                    diff_matrix[i, j] = np.random.uniform(0.1, 0.5)

        

        # 迭代最佳反应

        for iteration in range(self.max_iterations):

            price_changes = []

            

            for i, firm in enumerate(market.firms):

                # 获取竞争对手价格

                rival_prices = [f.price for j, f in enumerate(market.firms) if j != i]

                

                # 计算最佳反应

                new_price, profit = market.best_response(i, rival_prices)

                price_change = abs(new_price - firm.price)

                price_changes.append(price_change)

                

                firm.price = new_price

                firm.profit = profit

            

            max_change = max(price_changes)

            self.convergence_history.append(max_change)

            

            if iteration % 10 == 0:

                prices = [f.price for f in market.firms]

                profits = [f.profit for f in market.firms]

                print(f"  迭代{iteration}: 价格={[f'{p:.2f}' for p in prices]}, "

                      f"最大变化={max_change:.6f}")

            

            if max_change < self.tolerance:

                print(f"  在第{iteration+1}轮收敛")

                break

        

        return self.extract_equilibrium(market)

    

    def extract_equilibrium(self, market):

        """提取均衡结果"""

        return {

            'prices': [f.price for f in market.firms],

            'profits': [f.profit for f in market.firms],

            'marginal_costs': [f.marginal_cost for f in market.firms],

            'n_firms': len(market.firms)

        }





if __name__ == "__main__":

    # 测试伯特兰德博弈

    print("=" * 50)

    print("伯特兰德寡头垄断竞争博弈测试")

    print("=" * 50)

    

    # 创建市场

    market = BertrandOligopoly(market_size=1000.0, elasticity=-1.5)

    

    # 添加企业（不同边际成本）

    market.add_firm(BertrandFirm(0, marginal_cost=5.0, product_differentiation=0.2))

    market.add_firm(BertrandFirm(1, marginal_cost=8.0, product_differentiation=0.2))

    market.add_firm(BertrandFirm(2, marginal_cost=6.0, product_differentiation=0.2))

    

    print(f"\n市场结构（{len(market.firms)}个企业）:")

    for firm in market.firms:

        print(f"  企业{firm.firm_id}: 边际成本={firm.marginal_cost}")

    

    # 求解纳什均衡

    solver = BertrandGameSolver(tolerance=1e-8, max_iterations=200)

    equilibrium = solver.find_nash_equilibrium(market)

    

    print(f"\n===== 均衡结果 =====")

    print(f"  企业数量: {equilibrium['n_firms']}")

    for i, (price, profit, mc) in enumerate(zip(

            equilibrium['prices'], equilibrium['profits'], equilibrium['marginal_costs'])):

        markup = (price - mc) / mc * 100

        print(f"  企业{i}: 价格={price:.2f}, 利润={profit:.2f}, "

              f"加成率={markup:.1f}%, 边际成本={mc:.2f}")

    

    print(f"\n收敛历史: {len(solver.convergence_history)}轮")

    

    print("\n✓ 伯特兰德寡头垄断竞争博弈测试完成")

