# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / follow_the_leader

本文件实现 follow_the_leader 相关的算法功能。
"""

import random
import math
from typing import List, Tuple, Callable, Optional
from dataclasses import dataclass


@dataclass
class Expert:
    """专家/假设"""
    id: int
    name: str
    loss: float = 0.0
    
    def predict(self) -> int:
        """预测（子类实现）"""
        raise NotImplementedError


class FTLFramework:
    """
    Follow the Leader 框架
    
    T轮之后，总损失与最佳专家损失的差异称为"遗憾"
    """
    
    def __init__(self, num_experts: int):
        self.num_experts = num_experts
        self.expert_losses: List[float] = [0.0] * num_experts
        self.round = 0
        
        # 历史记录
        self.history_expert_losses: List[List[float]] = []
        self.history_predictions: List[int] = []
    
    def update(self, expert_id: int, loss: float):
        """
        更新专家损失
        
        Args:
            expert_id: 专家ID
            loss: 本轮损失
        """
        self.expert_losses[expert_id] += loss
        self.round += 1
    
    def get_leader(self) -> int:
        """获取当前领导者（损失最低的专家）"""
        return min(range(self.num_experts), 
                  key=lambda i: self.expert_losses[i])
    
    def predict_with_leader(self) -> int:
        """使用领导者预测"""
        leader_id = self.get_leader()
        self.history_predictions.append(leader_id)
        return leader_id
    
    def get_best_static_expert(self) -> Tuple[int, float]:
        """
        获取最佳静态专家（事后诸葛亮）
        
        Returns:
            (专家ID, 累积损失)
        """
        min_loss = min(self.expert_losses)
        min_id = self.expert_losses.index(min_loss)
        return min_id, min_loss
    
    def regret(self) -> float:
        """
        计算遗憾度
        
        Returns:
            遗憾度 = FTL总损失 - 最优专家损失
        """
        leader_loss = self.expert_losses[self.get_leader()]
        best_loss = min(self.expert_losses)
        return leader_loss - best_loss
    
    def get_regret_bound(self) -> float:
        """
        获取遗憾度上界
        
        Returns:
            遗憾度上界
        """
        return math.sqrt(2 * self.round * math.log(self.num_experts))


class FTLWithRandomization:
    """
    带随机化的FTL (FTRL)
    
    不只选择最佳专家，而是根据损失分布随机选择
    """
    
    def __init__(self, num_experts: int, learning_rate: float = 0.1):
        self.num_experts = num_experts
        self.learning_rate = learning_rate
        self.expert_losses: List[float] = [0.0] * num_experts
        self.weights: List[float] = [1.0] * num_experts
        self.round = 0
    
    def _compute_weights(self):
        """基于损失计算权重（指数加权）"""
        total_weight = 0.0
        
        for i in range(self.num_experts):
            self.weights[i] = math.exp(-self.learning_rate * self.expert_losses[i])
            total_weight += self.weights[i]
        
        # 归一化
        for i in range(self.num_experts):
            self.weights[i] /= total_weight if total_weight > 0 else 1
    
    def predict(self) -> int:
        """随机化预测"""
        self._compute_weights()
        
        # 轮盘赌选择
        r = random.random()
        cumulative = 0.0
        
        for i in range(self.num_experts):
            cumulative += self.weights[i]
            if r <= cumulative:
                return i
        
        return self.num_experts - 1
    
    def update(self, expert_id: int, loss: float):
        """更新"""
        self.expert_losses[expert_id] += loss
        self.round += 1
    
    def get_best_expert(self) -> int:
        """获取最佳专家"""
        return min(range(self.num_experts),
                  key=lambda i: self.expert_losses[i])


class ExpertFramework:
    """
    简化的专家框架
    
    每个专家可以有自己的预测逻辑
    """
    
    def __init__(self, expert_makers: List[Callable[[], Expert]]):
        self.experts = [maker() for maker in expert_makers]
        self.expert_losses = [0.0] * len(self.experts)
        self.round = 0
    
    def round_predict(self) -> int:
        """一轮预测"""
        # FTL：选择到目前为止损失最低的专家
        min_loss = min(self.expert_losses)
        for i, loss in enumerate(self.expert_losses):
            if loss == min_loss:
                return self.experts[i].predict()
        return self.experts[0].predict()
    
    def round_update(self, expert_id: int, loss: float):
        """一轮更新"""
        self.expert_losses[expert_id] += loss
        self.round += 1


class PredictionExpert(Expert):
    """预测专家"""
    
    def __init__(self, expert_id: int, name: str, predictions: List[int]):
        super().__init__(expert_id, name)
        self.predictions = predictions
        self.current_idx = 0
    
    def predict(self) -> int:
        """返回下一个预测"""
        if self.current_idx < len(self.predictions):
            pred = self.predictions[self.current_idx]
            self.current_idx += 1
            return pred
        return 0


def simulate_ftl():
    """模拟FTL"""
    print("=== FTL在线学习模拟 ===\n")
    
    # 创建专家（每个专家有不同的预测序列）
    num_experts = 5
    num_rounds = 100
    
    ftl = FTLFramework(num_experts)
    
    # 模拟真实结果（0或1）
    true_outcomes = [random.randint(0, 1) for _ in range(num_rounds)]
    
    # 每个专家的预测能力
    expert_skills = [
        [0.6, 0.4, 0.7, 0.5, 0.8],  # 专家1擅长模式1
        [0.4, 0.6, 0.5, 0.7, 0.3],  # 专家2擅长模式2
        [0.5, 0.5, 0.5, 0.5, 0.5],  # 专家3平均
        [0.3, 0.7, 0.3, 0.7, 0.3],  # 专家4交替
        [0.7, 0.3, 0.7, 0.3, 0.7],  # 专家5交替
    ]
    
    print(f"轮数: {num_rounds}, 专家数: {num_experts}")
    print()
    
    # 运行
    ftl_predictions = []
    leader_changes = []
    last_leader = None
    
    for t in range(num_rounds):
        # FTL选择领导者
        leader = ftl.predict_with_leader()
        
        if last_leader is not None and leader != last_leader:
            leader_changes.append(t)
        last_leader = leader
        
        # 专家预测（简化：每个专家有一定准确率）
        expert_predictions = []
        for e in range(num_experts):
            pattern_idx = t % len(expert_skills[e])
            skill = expert_skills[e][pattern_idx]
            pred = 1 if random.random() < skill else 0
            expert_predictions.append(pred)
        
        # 计算损失
        true = true_outcomes[t]
        
        for e in range(num_experts):
            loss = 0 if expert_predictions[e] == true else 1
            ftl.update(e, loss)
        
        ftl_predictions.append(leader)
    
    # 结果分析
    best_expert, best_loss = ftl.get_best_static_expert()
    ftl_total_loss = ftl.expert_losses[ftl.get_leader()]
    
    print("结果:")
    print(f"  FTL领导者总损失: {ftl_total_loss:.1f}")
    print(f"  最佳专家 #{best_expert}: 损失={best_loss:.1f}")
    print(f"  遗憾度: {ftl.regret():.1f}")
    print(f"  理论遗憾上界: {ftl.get_regret_bound():.1f}")
    print(f"  领导者切换次数: {len(leader_changes)}")


def demo_regret_analysis():
    """遗憾度分析"""
    print("\n=== 遗憾度分析 ===\n")
    
    print("遗憾度定义:")
    print("  regret(T) = Σ L_algo(t) - min_e Σ L_e(t)")
    print()
    
    print("不同设置下的遗憾界:")
    print("| 设置           | 遗憾界        | 备注       |")
    print("|----------------|---------------|------------|")
    print("| 确定性FTL      | O(√T)         | 经典结果   |")
    print("| FTRL          | O(√T log T)   | 权重平均   |")
    print("| Exponential F | O(√T log K)   | K个专家   |")
    print("| Online Mirror | O(√T)         | 一般凸    |")
    
    print("\n平均遗憾度（每轮）:")
    print("  regret(T) / T = O(1/√T) → 0 当 T → ∞")
    print("  这称为\"渐近无遗憾\"")


def demo_expert_prediction():
    """演示专家预测"""
    print("\n=== 专家预测演示 ===\n")
    
    # 专家类型
    def make_trend_expert(e_id):
        """趋势专家"""
        predictions = []
        trend = 1 if e_id % 2 == 0 else 0
        for _ in range(20):
            predictions.append(trend)
        return PredictionExpert(e_id, f"Trend_{e_id}", predictions)
    
    def make_random_expert(e_id):
        """随机专家"""
        predictions = [random.randint(0, 1) for _ in range(20)]
        return PredictionExpert(e_id, f"Random_{e_id}", predictions)
    
    # 创建专家
    expert_makers = []
    for i in range(3):
        expert_makers.append(lambda i=i: make_trend_expert(i))
    for i in range(3, 5):
        expert_makers.append(lambda i=i: make_random_expert(i))
    
    framework = ExpertFramework(expert_makers)
    
    print("专家:")
    for e in framework.experts:
        print(f"  {e.name}: {[e.predictions[i] for i in range(5)]}...")
    
    print("\n运行:")
    for t in range(10):
        pred = framework.round_predict()
        print(f"  Round {t}: 预测={pred}")
        
        # 假设专家0是正确专家
        true = framework.experts[0].predictions[t]
        
        # 更新所有专家的损失
        for i, e in enumerate(framework.experts):
            loss = 0 if e.predictions[t] == true else 1
            framework.round_update(i, loss)
    
    print("\n最终损失:")
    for i, loss in enumerate(framework.expert_losses):
        print(f"  专家{i}: {loss}")


def demo_ftl_vs_ftrl():
    """对比FTL和FTRL"""
    print("\n=== FTL vs FTRL 对比 ===\n")
    
    num_experts = 5
    num_rounds = 200
    
    # FTL
    ftl = FTLFramework(num_experts)
    
    # FTRL
    ftrl = FTLWithRandomization(num_experts, learning_rate=0.1)
    
    print(f"专家数: {num_experts}, 轮数: {num_rounds}")
    print()
    
    # 运行两种算法
    for t in range(num_rounds):
        # 真实情况
        true = random.randint(0, 1)
        
        # FTL
        ftl_pred = ftl.predict_with_leader()
        ftl_loss = 0 if ftl_pred == true else 1
        
        # 更新（这里简化处理）
        for e in range(num_experts):
            expert_pred = random.randint(0, 1)
            loss = 0 if expert_pred == true else 1
            ftl.update(e, loss)
        
        # FTRL
        ftrl_pred = ftrl.predict()
        for e in range(num_experts):
            expert_pred = random.randint(0, 1)
            loss = 0 if expert_pred == true else 1
            ftrl.update(e, loss)
    
    print("结果:")
    print(f"  FTL 总损失: {ftl.expert_losses[ftl.get_leader()]:.1f}")
    print(f"  FTRL 总损失: {ftrl.expert_losses[ftrl.get_best_expert()]:.1f}")
    print(f"  FTL 遗憾: {ftl.regret():.1f}")


if __name__ == "__main__":
    print("=" * 60)
    print("Follow the Leader (FTL) 在线学习算法")
    print("=" * 60)
    
    # 基本模拟
    simulate_ftl()
    
    # 遗憾度分析
    demo_regret_analysis()
    
    # 专家预测
    demo_expert_prediction()
    
    # FTL vs FTRL
    demo_ftl_vs_ftrl()
    
    print("\n" + "=" * 60)
    print("FTL核心原理:")
    print("=" * 60)
    print("""
1. 算法步骤:
   1. 维护每个专家的累积损失
   2. 选择损失最低的专家（领导者）
   3. 使用领导者进行预测
   4. 根据结果更新专家损失

2. 遗憾度分析:
   - T轮后，遗憾度 = O(√T)
   - 平均每轮遗憾 = O(1/√T) → 0

3. 优点:
   - 简单直观
   - 不需要调参
   - 渐近无遗憾

4. 缺点:
   - 可能过早锁定在某个专家
   - 对噪声敏感
   - 最坏情况可能较差

5. 改进方向:
   - FTRL：加权平均而非单一选择
   - 多个领导者
   - 扰动技术
""")
