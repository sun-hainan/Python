# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / pos_staking

本文件实现 pos_staking 相关的算法功能。
"""

import random
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Validator:
    """验证者"""
    validator_id: str
    stake: int
    uptime: float

class ProofOfStake:
    """
    PoS权益证明机制
    
    验证者被选中出块的概率与其质押的代币数量成正比
    """
    
    def __init__(self):
        self.validators: Dict[str, Validator] = {}
        self.total_stake = 0
        self.rewards: Dict[str, float] = {}
    
    def add_validator(self, validator_id: str, stake: int, uptime: float = 1.0):
        """添加验证者"""
        self.validators[validator_id] = Validator(validator_id, stake, uptime)
        self.total_stake += stake
        self.rewards[validator_id] = 0.0
    
    def remove_validator(self, validator_id: str):
        """移除验证者"""
        if validator_id in self.validators:
            self.total_stake -= self.validators[validator_id].stake
            del self.validators[validator_id]
    
    def select_validator(self, random_seed: int) -> Optional[str]:
        """选择下一个验证者（加权随机）"""
        if not self.validators:
            return None
        
        weights = []
        for vid, validator in self.validators.items():
            weight = validator.stake * validator.uptime
            weights.append((vid, weight))
        
        total_weight = sum(w for _, w in weights)
        rand_val = random.Random(random_seed).random() * total_weight
        
        cumulative = 0
        for vid, weight in weights:
            cumulative += weight
            if cumulative >= rand_val:
                return vid
        
        return weights[-1][0]
    
    def distribute_rewards(self, block_reward: float):
        """分配区块奖励"""
        for vid, validator in self.validators.items():
            share = (validator.stake / self.total_stake) * block_reward
            self.rewards[vid] += share
    
    def get_validator_info(self, validator_id: str) -> Optional[Dict]:
        """获取验证者信息"""
        if validator_id not in self.validators:
            return None
        v = self.validators[validator_id]
        return {
            "id": v.validator_id,
            "stake": v.stake,
            "uptime": v.uptime,
            "rewards": self.rewards[validator_id],
            "probability": v.stake / self.total_stake if self.total_stake > 0 else 0
        }

if __name__ == "__main__":
    print("=== PoS权益证明测试 ===")
    
    pos = ProofOfStake()
    
    # 添加验证者
    validators = [
        ("alice", 1000, 1.0),
        ("bob", 2000, 0.95),
        ("charlie", 500, 1.0),
        ("david", 1500, 0.9),
    ]
    
    for vid, stake, uptime in validators:
        pos.add_validator(vid, stake, uptime)
    
    print("验证者信息:")
    for vid, _, _ in validators:
        info = pos.get_validator_info(vid)
        print(f"  {vid}: stake={info['stake']}, 概率={info['probability']:.2%}")
    
    print(f"\n总质押: {pos.total_stake}")
    
    print("\n=== 验证者选择模拟 ===")
    selection_counts = {vid: 0 for vid, _, _ in validators}
    num_blocks = 1000
    
    for i in range(num_blocks):
        selected = pos.select_validator(i)
        if selected:
            selection_counts[selected] += 1
    
    print(f"模拟{num_blocks}个区块的验证者选择:")
    for vid, count in selection_counts.items():
        expected = pos.validators[vid].stake / pos.total_stake * num_blocks
        print(f"  {vid}: 选中{count}次 (期望约{expected:.0f}次)")
    
    print("\n=== 奖励分配 ===")
    pos.distribute_rewards(10.0)
    for vid, _, _ in validators:
        info = pos.get_validator_info(vid)
        print(f"  {vid}: 获得奖励 = {info['rewards']:.4f}")
