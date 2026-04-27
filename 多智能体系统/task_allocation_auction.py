# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / task_allocation_auction

本文件实现 task_allocation_auction 相关的算法功能。
"""

import numpy as np
from collections import defaultdict
import heapq


class Task:
    """任务对象"""
    
    def __init__(self, task_id, reward, required_capability, duration):
        # task_id: 任务唯一标识
        # reward: 任务完成奖励
        # required_capability: 所需能力（如 ['sensing', 'manipulation']）
        # duration: 预计执行时间
        self.task_id = task_id
        self.reward = reward
        self.required_capability = required_capability
        self.duration = duration
    
    def __repr__(self):
        return f"Task(id={self.task_id}, reward={self.reward}, " \
               f"cap={self.required_capability}, dur={self.duration})"


class Agent:
    """智能体对象"""
    
    def __init__(self, agent_id, capabilities, max_tasks=3):
        # agent_id: 智能体唯一标识
        # capabilities: 智能体具备的能力列表
        # max_tasks: 最大可接任务数
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.max_tasks = max_tasks
        self.assigned_tasks = []  # 已分配的任务
        self.current_load = 0.0  # 当前工作负载
    
    def can_handle(self, task):
        """检查智能体是否有能力处理任务"""
        return all(cap in self.capabilities for cap in task.required_capability)
    
    def get_cost(self, task):
        """计算智能体处理任务的成本（竞标价格）"""
        # 基于负载和能力的成本估计
        base_cost = task.reward * 0.5  # 基准成本为奖励的50%
        capability_bonus = len(task.required_capability) * 0.1 * base_cost
        load_factor = 1.0 + self.current_load / self.max_tasks
        return base_cost + capability_bonus + load_factor * 0.2 * base_cost
    
    def bid(self, task):
        """对任务进行竞标"""
        if not self.can_handle(task):
            return None
        if len(self.assigned_tasks) >= self.max_tasks:
            return None
        cost = self.get_cost(task)
        # 竞标价格 = 成本 + 利润边际
        profit_margin = 0.1 * np.random.random()
        bid_price = cost * (1 + profit_margin)
        return bid_price
    
    def assign_task(self, task):
        """接收任务分配"""
        self.assigned_tasks.append(task)
        self.current_load += task.duration
    
    def __repr__(self):
        return f"Agent(id={self.agent_id}, cap={self.capabilities}, " \
               f"load={self.current_load:.1f}/{self.max_tasks})"


class Auctioneer:
    """拍卖主持者：管理拍卖流程"""
    
    def __init__(self):
        self.auction_log = []  # 拍卖记录
    
    def hold_auction(self, task, agents):
        """
        为单个任务举行拍卖
        返回: (winner_id, winning_bid) 或 (None, None)
        """
        bids = {}  # agent_id -> bid_price
        
        # 收集竞标
        for agent in agents:
            bid = agent.bid(task)
            if bid is not None:
                bids[agent.agent_id] = bid
        
        if not bids:
            return None, None
        
        # 选择最高出价者
        winner_id = max(bids, key=bids.get)
        winning_bid = bids[winner_id]
        
        # 记录拍卖
        self.auction_log.append({
            'task_id': task.task_id,
            'winner': winner_id,
            'winning_bid': winning_bid,
            'all_bids': bids
        })
        
        return winner_id, winning_bid


class SingleRoundAuction:
    """单轮拍卖：所有任务同时竞标"""
    
    def __init__(self, agents):
        # agents: 智能体列表
        self.agents = agents
        self.auctioneer = Auctioneer()
        self.allocation = {}  # task_id -> agent_id
        self.total_reward = 0.0
    
    def allocate_tasks(self, tasks):
        """执行任务分配"""
        for task in tasks:
            winner_id, winning_bid = self.auctioneer.hold_auction(task, self.agents)
            if winner_id is not None:
                self.allocation[task.task_id] = winner_id
                # 找到获胜智能体并分配任务
                for agent in self.agents:
                    if agent.agent_id == winner_id:
                        agent.assign_task(task)
                        self.total_reward += task.reward - winning_bid
                        break
        
        return self.allocation
    
    def get_result(self):
        """获取分配结果"""
        return {
            'allocation': self.allocation,
            'total_reward': self.total_reward,
            'utilization': {
                agent.agent_id: len(agent.assigned_tasks) / agent.max_tasks
                for agent in self.agents
            }
        }


class IterativeAuction:
    """迭代拍卖：多轮竞标直到收敛"""
    
    def __init__(self, agents, max_rounds=10):
        # agents: 智能体列表
        # max_rounds: 最大迭代轮数
        self.agents = agents
        self.max_rounds = max_rounds
        self.auctioneer = Auctioneer()
        self.allocation_history = []
    
    def allocate_tasks(self, tasks):
        """迭代分配任务"""
        unallocated_tasks = list(tasks)
        
        for round_num in range(self.max_rounds):
            if not unallocated_tasks:
                print(f"  第{round_num}轮: 所有任务已分配")
                break
            
            newly_allocated = []
            
            for task in unallocated_tasks:
                winner_id, _ = self.auctioneer.hold_auction(task, self.agents)
                if winner_id is not None:
                    self.allocation_history.append({
                        'round': round_num,
                        'task_id': task.task_id,
                        'winner': winner_id
                    })
                    # 找到获胜智能体并分配任务
                    for agent in self.agents:
                        if agent.agent_id == winner_id:
                            agent.assign_task(task)
                            newly_allocated.append(task)
                            break
            
            # 移除已分配的任务
            for task in newly_allocated:
                unallocated_tasks.remove(task)
            
            print(f"  第{round_num}轮: 分配了{len(newly_allocated)}个任务，"
                  f"剩余{len(unallocated_tasks)}个")
        
        # 构建最终分配
        final_allocation = {}
        for entry in self.allocation_history:
            final_allocation[entry['task_id']] = entry['winner']
        
        return final_allocation


class CombinatorialAuction:
    """组合拍卖：智能体可以竞标任务组合
    
    简化版实现：智能体可以声明对某些任务组合的偏好，
    通过贪婪算法求解近似最优分配。
    """
    
    def __init__(self, agents):
        self.agents = agents
        self.combination_bids = []  # (bidder_id, task_set, price)
    
    def submit_combination_bid(self, agent_id, task_ids, price, tasks):
        """提交组合竞标"""
        # 验证智能体是否具备所有任务所需能力
        agent = None
        for a in self.agents:
            if a.agent_id == agent_id:
                agent = a
                break
        
        if agent is None:
            return False
        
        # 检查能力
        for task_id in task_ids:
            task = None
            for t in tasks:
                if t.task_id == task_id:
                    task = t
                    break
            if task and not agent.can_handle(task):
                return False
        
        self.combination_bids.append((agent_id, set(task_ids), price))
        return True
    
    def allocate_greedy(self, tasks):
        """贪婪分配组合竞标"""
        allocation = {}  # task_id -> agent_id
        agent_tasks = defaultdict(set)  # agent_id -> set of assigned tasks
        
        # 按价格/任务数比例降序排列
        def value_ratio(bid):
            return bid[2] / max(len(bid[1]), 1)
        
        sorted_bids = sorted(self.combination_bids, key=value_ratio, reverse=True)
        
        for bidder_id, task_set, price in sorted_bids:
            # 检查任务是否已被分配
            available_tasks = [t for t in task_set if t not in allocation]
            
            if available_tasks:
                # 分配该组合中未被占用的任务
                for task_id in available_tasks:
                    allocation[task_id] = bidder_id
                    agent_tasks[bidder_id].add(task_id)
        
        return allocation


if __name__ == "__main__":
    # 测试拍卖算法任务分配
    print("=" * 50)
    print("拍卖算法任务分配测试")
    print("=" * 50)
    
    # 创建智能体
    agents = [
        Agent(0, ['sensing', 'manipulation', 'navigation'], max_tasks=3),
        Agent(1, ['sensing', 'computation'], max_tasks=2),
        Agent(2, ['manipulation', 'navigation'], max_tasks=3),
        Agent(3, ['computation', 'sensing'], max_tasks=4)
    ]
    
    print(f"\n智能体数量: {len(agents)}")
    for agent in agents:
        print(f"  {agent}")
    
    # 创建任务
    tasks = [
        Task(0, reward=100, required_capability=['sensing'], duration=1.0),
        Task(1, reward=150, required_capability=['sensing', 'navigation'], duration=2.0),
        Task(2, reward=80, required_capability=['manipulation'], duration=1.5),
        Task(3, reward=200, required_capability=['sensing', 'computation'], duration=3.0),
        Task(4, reward=120, required_capability=['navigation'], duration=1.0),
        Task(5, reward=90, required_capability=['manipulation', 'navigation'], duration=2.0)
    ]
    
    print(f"\n任务数量: {len(tasks)}")
    for task in tasks:
        print(f"  {task}")
    
    # 测试单轮拍卖
    print("\n--- 单轮拍卖测试 ---")
    auction_agents = [Agent(i, agents[i].capabilities, agents[i].max_tasks) 
                      for i in range(len(agents))]
    single_auction = SingleRoundAuction(auction_agents)
    allocation = single_auction.allocate_tasks(tasks)
    result = single_auction.get_result()
    
    print(f"  分配结果: {allocation}")
    print(f"  总效用: {result['total_reward']:.2f}")
    
    # 测试迭代拍卖
    print("\n--- 迭代拍卖测试 ---")
    iter_agents = [Agent(i, agents[i].capabilities, agents[i].max_tasks) 
                   for i in range(len(agents))]
    iter_auction = IterativeAuction(iter_agents, max_rounds=5)
    iter_allocation = iter_auction.allocate_tasks(tasks)
    
    print(f"  最终分配: {iter_allocation}")
    print(f"  迭代轮数: {len(set(e['round'] for e in iter_auction.allocation_history))}")
    
    # 测试组合拍卖
    print("\n--- 组合拍卖测试 ---")
    combo_agents = [Agent(i, agents[i].capabilities, agents[i].max_tasks) 
                    for i in range(len(agents))]
    combo_auction = CombinatorialAuction(combo_agents)
    
    # 提交组合竞标
    combo_auction.submit_combination_bid(0, [0, 1], 200, tasks)
    combo_auction.submit_combination_bid(1, [3], 180, tasks)
    combo_auction.submit_combination_bid(3, [0, 3], 230, tasks)
    
    combo_allocation = combo_auction.allocate_greedy(tasks)
    print(f"  组合分配结果: {combo_allocation}")
    
    print("\n✓ 拍卖算法任务分配测试完成")
