# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / superscalar_ipc

本文件实现 superscalar_ipc 相关的算法功能。
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PipelineType(Enum):
    """流水线类型"""
    BASIC = "basic"                    # 基本5级流水线
    SUPER = "super"                    # 超级流水线
    SUPERSCALAR = "superscalar"        # 超标量


@dataclass
class PipelineConfig:
    """流水线配置"""
    pipeline_type: PipelineType
    stages: int                         # 流水线级数
    issue_width: int = 1                # 发射宽度
    alu_units: int = 1                 # ALU数量
    branch_penalty: int = 3             # 分支预测失败惩罚
    fetch_width: int = 1               # 取指宽度


class SuperPipelineStage:
    """超级流水线阶段"""

    def __init__(self, stage_id: int, name: str):
        self.stage_id = stage_id
        self.name = name
        self.instruction: Optional[any] = None
        self.busy: bool = False


class SuperPipeline:
    """
    超级流水线

    将基本流水线分成更深的阶段。
    例如，Intel Pentium 4的流水线深度达到31级。
    """

    def __init__(self, num_stages: int = 10):
        self.num_stages = num_stages
        self.stages: List[SuperPipelineStage] = [
            SuperPipelineStage(i, f"Stage_{i}") for i in range(num_stages)
        ]

        # 指令队列
        self.instruction_queue: List[any] = []

        # 统计
        self.total_instructions: int = 0
        self.total_cycles: int = 0

    def get_pipeline_depth(self) -> int:
        """获取流水线深度"""
        return self.num_stages

    def get_theoretical_latency(self) -> int:
        """获取指令的理论延迟（周期数）"""
        return self.num_stages

    def get_initiation_interval(self) -> int:
        """获取发射间隔（理想情况）"""
        return 1  # 理想情况下每个周期可以发射一条


class IssueUnit:
    """发射单元"""

    def __init__(self, width: int, alu_count: int):
        self.width = width
        self.alu_count = alu_count

        # 已分配的FU
        self.allocated_alu: List[int] = []
        self.allocated_load: List[int] = []
        self.allocated_store: List[int] = []

        # 待发射指令
        self.pending_instructions: List[any] = []

    def can_issue(self, instr_type: str) -> bool:
        """检查是否可以发射某种类型的指令"""
        if instr_type == 'ALU':
            return len(self.allocated_alu) < self.alu_count
        return True  # 简化

    def issue(self, instr: any) -> bool:
        """发射指令"""
        if not self.can_issue(instr.type):
            return False

        if len(self.pending_instructions) >= self.width:
            return False

        self.pending_instructions.append(instr)
        return True

    def step(self):
        """每个周期重置分配"""
        self.allocated_alu.clear()
        self.allocated_load.clear()
        self.allocated_store.clear()


class RetireUnit:
    """退役单元"""

    def __init__(self, width: int):
        self.width = width
        self.robb_entries: List[any] = []
        self.head: int = 0

    def can_retire(self) -> bool:
        """检查是否可以退役"""
        if not self.robb_entries:
            return False
        head_entry = self.robb_entries[self.head % len(self.robb_entries)]
        return head_entry and head_entry.get('completed', False)

    def retire(self) -> Optional[any]:
        """退役指令"""
        if not self.can_retire():
            return None
        entry = self.robb_entries[self.head % len(self.robb_entries)]
        self.head += 1
        return entry


class IPCAnalyzer:
    """
    IPC分析器

    分析影响IPC的因素，计算实际IPC。
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.total_instructions: int = 0
        self.total_cycles: int = 0

        # 停顿统计
        self.branch_stalls: int = 0
        self.hazard_stalls: int = 0
        self.cache_stalls: int = 0
        self.frontend_stalls: int = 0

    def calculate_ideal_ipc(self) -> float:
        """计算理想IPC（无任何停顿）"""
        return float(self.config.issue_width)

    def calculate_actual_ipc(self) -> float:
        """计算实际IPC"""
        if self.total_cycles == 0:
            return 0.0
        return self.total_instructions / self.total_cycles

    def get_stall_cycles(self) -> int:
        """计算总停顿周期数"""
        return (self.branch_stalls + self.hazard_stalls +
                self.cache_stalls + self.frontend_stalls)

    def get_CPI(self) -> float:
        """计算CPI (Cycles Per Instruction)"""
        if self.total_instructions == 0:
            return 0.0
        return self.total_cycles / self.total_instructions

    def get_IPC(self) -> float:
        """获取IPC"""
        return self.calculate_actual_ipc()

    def analyze_pipeline_efficiency(self) -> Dict:
        """分析流水线效率"""
        ideal_ipc = self.calculate_ideal_ipc()
        actual_ipc = self.calculate_actual_ipc()
        efficiency = actual_ipc / ideal_ipc if ideal_ipc > 0 else 0

        return {
            'ideal_ipc': ideal_ipc,
            'actual_ipc': actual_ipc,
            'efficiency': efficiency * 100,  # 百分比
            'total_instructions': self.total_instructions,
            'total_cycles': self.total_cycles,
            'total_stalls': self.get_stall_cycles(),
            'branch_stalls': self.branch_stalls,
            'hazard_stalls': self.hazard_stalls,
            'cache_stalls': self.cache_stalls,
        }


class BranchPredictorImpact:
    """分支预测器对IPC的影响"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.mispredict_rate: float = 0.05  # 假设5%错误率

    def calculate_branch_overhead(self, num_branches: int,
                                  mispredict_rate: float = None) -> int:
        """
        计算分支预测失败的开销
        """
        if mispredict_rate is None:
            mispredict_rate = self.mispredict_rate

        penalty = self.config.branch_penalty
        return int(num_branches * mispredict_rate * penalty)

    def calculate_ipc_with_branch(self, base_ipc: float,
                                  num_branches: int,
                                  num_instructions: int) -> float:
        """
        计算有分支预测影响后的IPC
        """
        mispredicts = int(num_branches * self.mispredict_rate)
        total_penalty = mispredicts * self.config.branch_penalty

        # 总周期 = 基本周期 + 分支惩罚
        base_cycles = num_instructions / base_ipc
        total_cycles = base_cycles + total_penalty

        return num_instructions / total_cycles


class CacheMissImpact:
    """缓存未命中对IPC的影响"""

    def __init__(self, config: PipelineConfig):
        self.config = config

    def calculate_cache_overhead(self, num_loads: int,
                                miss_rate: float,
                                miss_penalty: int) -> int:
        """计算缓存未命中的开销"""
        return int(num_loads * miss_rate * miss_penalty)

    def calculate_ipc_with_cache(self, base_ipc: float,
                                num_instructions: int,
                                num_loads: int,
                                miss_rate: float = 0.05,
                                miss_penalty: int = 10) -> float:
        """计算有缓存影响后的IPC"""
        total_penalty = self.calculate_cache_overhead(num_loads, miss_rate, miss_penalty)
        base_cycles = num_instructions / base_ipc
        total_cycles = base_cycles + total_penalty
        return num_instructions / total_cycles


class HazardImpact:
    """数据hazard对IPC的影响"""

    def __init__(self):
        self.raw_stalls: int = 0
        self.war_stalls: int = 0
        self.waw_stalls: int = 0

    def calculate_hazard_overhead(self) -> int:
        """计算hazard导致的停顿"""
        return self.raw_stalls + self.war_stalls + self.waw_stalls

    def estimate_hazard_stalls(self, num_instructions: int,
                              dependency_density: float = 0.2) -> int:
        """
        估算hazard停顿
        dependency_density: 依赖密度（平均多少指令有一个依赖）
        """
        return int(num_instructions * dependency_density * 0.5)  # 简化估算


class SuperscalarAnalyzer:
    """
    超标量处理器分析器
    """

    def __init__(self, issue_width: int = 4, alu_units: int = 2):
        self.issue_width = issue_width
        self.alu_units = alu_units

        # 资源使用统计
        self.alu_utilization: List[int] = []
        self.load_store_utilization: List[int] = []

        # 指令统计
        self.total_instructions: int = 0
        self.alu_instructions: int = 0
        self.load_instructions: int = 0
        self.store_instructions: int = 0
        self.branch_instructions: int = 0

    def calculate_theoretical_peak_ipc(self) -> float:
        """计算理论峰值IPC"""
        return float(self.issue_width)

    def calculate_sustained_ipc(self, resource_limit_factor: float = 0.8) -> float:
        """
        计算持续IPC（考虑资源限制）
        """
        return self.calculate_theoretical_peak_ipc() * resource_limit_factor

    def analyze_instruction_mix(self, instructions: List[Dict]) -> Dict:
        """分析指令混合"""
        total = len(instructions)
        if total == 0:
            return {}

        type_counts = {}
        for instr in instructions:
            t = instr.get('type', 'UNKNOWN')
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            'total': total,
            'alu_percent': type_counts.get('ALU', 0) / total * 100,
            'load_percent': type_counts.get('LOAD', 0) / total * 100,
            'store_percent': type_counts.get('STORE', 0) / total * 100,
            'branch_percent': type_counts.get('BRANCH', 0) / total * 100,
        }


def simulate_superpipeline_superscalar():
    """
    模拟超级流水线和超标量架构，分析IPC
    """
    print("=" * 60)
    print("超级流水线与超标量 IPC 分析")
    print("=" * 60)

    # 流水线配置
    configs = [
        PipelineConfig(PipelineType.BASIC, stages=5, issue_width=1),
        PipelineConfig(PipelineType.SUPER, stages=10, issue_width=1),
        PipelineConfig(PipelineType.SUPER, stages=20, issue_width=1),
        PipelineConfig(PipelineType.SUPERSCALAR, stages=5, issue_width=2),
        PipelineConfig(PipelineType.SUPERSCALAR, stages=5, issue_width=4),
    ]

    print("\n流水线配置对比:")
    print("-" * 60)
    print(f"{'类型':<15} {'深度':<8} {'发射宽度':<10} {'理想IPC':<10}")
    print("-" * 60)

    for config in configs:
        ideal_ipc = float(config.issue_width)
        print(f"{config.pipeline_type.value:<15} {config.stages:<8} {config.issue_width:<10} {ideal_ipc:<10}")

    # IPC分析
    print("\n" + "=" * 60)
    print("IPC 分析")
    print("=" * 60)

    # 创建分析器
    config = PipelineConfig(PipelineType.SUPERSCALAR, stages=5, issue_width=4)
    analyzer = IPCAnalyzer(config)

    analyzer.total_instructions = 1000
    analyzer.total_cycles = 350  # 实际运行了350个周期

    analysis = analyzer.analyze_pipeline_efficiency()

    print(f"\n基本IPC分析 (发射宽度={config.issue_width}):")
    print(f"  理想IPC: {analysis['ideal_ipc']:.2f}")
    print(f"  实际IPC: {analysis['actual_ipc']:.2f}")
    print(f"  流水线效率: {analysis['efficiency']:.1f}%")

    # 分支预测影响
    print("\n" + "-" * 40)
    print("分支预测影响")
    print("-" * 40)

    branch_analyzer = BranchPredictorImpact(config)
    num_branches = 150  # 假设150条分支指令
    base_ipc = 4.0

    ipc_with_branch = branch_analyzer.calculate_ipc_with_branch(
        base_ipc, num_branches, 1000
    )
    print(f"  分支指令数: {num_branches}")
    print(f"  错误预测率: {branch_analyzer.mispredict_rate * 100:.1f}%")
    print(f"  分支惩罚: {config.branch_penalty} cycles")
    print(f"  考虑分支后的IPC: {ipc_with_branch:.2f}")

    # 缓存影响
    print("\n" + "-" * 40)
    print("缓存未命中影响")
    print("-" * 40)

    cache_analyzer = CacheMissImpact(config)
    num_loads = 250
    ipc_with_cache = cache_analyzer.calculate_ipc_with_cache(
        ipc_with_branch, 1000, num_loads,
        miss_rate=0.05, miss_penalty=10
    )
    print(f"  LOAD指令数: {num_loads}")
    print(f"  未命中率: 5%")
    print(f"  未命中惩罚: 10 cycles")
    print(f"  考虑缓存后的IPC: {ipc_with_cache:.2f}")

    # 超标量分析
    print("\n" + "-" * 40)
    print("超标量资源利用")
    print("-" * 40)

    superscalar = SuperscalarAnalyzer(issue_width=4, alu_units=2)

    # 模拟指令序列
    instructions = [
        {'type': 'ALU'}, {'type': 'ALU'}, {'type': 'LOAD'}, {'type': 'ALU'},
        {'type': 'STORE'}, {'type': 'ALU'}, {'type': 'ALU'}, {'type': 'LOAD'},
    ] * 10  # 重复

    mix = superscalar.analyze_instruction_mix(instructions)
    print(f"  指令混合分析:")
    print(f"    ALU: {mix['alu_percent']:.1f}%")
    print(f"    LOAD: {mix['load_percent']:.1f}%")
    print(f"    STORE: {mix['store_percent']:.1f}%")
    print(f"    分支: {mix.get('branch_percent', 0):.1f}%")
    print(f"  理论峰值IPC: {superscalar.calculate_theoretical_peak_ipc():.2f}")
    print(f"  持续IPC (80%利用率): {superscalar.calculate_sustained_ipc(0.8):.2f}")

    # 最终总结
    print("\n" + "=" * 60)
    print("IPC 影响因素总结")
    print("=" * 60)

    print(f"\n初始IPC (理想): 4.00")
    print(f"  - 分支预测失败: -> {ipc_with_branch:.2f} (影响 {-((4.0 - ipc_with_branch) / 4.0 * 100):.1f}%)")
    print(f"  - 缓存未命中: -> {ipc_with_cache:.2f} (累计影响 {-((4.0 - ipc_with_cache) / 4.0 * 100):.1f}%)")
    print(f"  - 数据hazard: -> ~{ipc_with_cache * 0.95:.2f} (估计)")
    print(f"\n最终实际IPC: ~{ipc_with_cache * 0.95:.2f}")


if __name__ == "__main__":
    simulate_superpipeline_superscalar()
