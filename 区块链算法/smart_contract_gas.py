# -*- coding: utf-8 -*-

"""

算法实现：区块链算法 / smart_contract_gas



本文件实现 smart_contract_gas 相关的算法功能。

"""



from typing import Dict, Callable, List



class GasCalculator:

    """

    智能合约Gas优化计算器

    

    估算以太坊交易的Gas消耗

    """

    

    # 基本操作Gas成本

    GAS_COSTS = {

        "add": 3,

        "sub": 3,

        "mul": 5,

        "div": 5,

        "mod": 5,

        "sstore": 20000,

        "sload": 800,

        "jump": 8,

        "push": 3,

        "pop": 2,

        "call": 2500,

        "create": 32000,

        "memory_per_byte": 16,

    }

    

    def __init__(self):

        self.execution_trace: List[dict] = []

    

    def calculate_storage_write(self, cold_access: bool = True) -> int:

        """计算SSTORE Gas成本"""

        if cold_access:

            return 20000  # 首次写入

        return 5000  # 更新已有值

    

    def calculate_storage_read(self, cold_access: bool = True) -> int:

        """计算SLOAD Gas成本"""

        if cold_access:

            return 2100  # 冷读取

        return 100  # 热读取

    

    def calculate_memory_gas(self, memory_size: int) -> int:

        """计算内存Gas成本（扩展内存）"""

        # memory_size in bytes, quadratic cost

        if memory_size <= 724:

            return 0

        words = (memory_size + 31) // 32

        return words * 3

    

    def calculate_call_gas(self, value: int, new_contract: bool = False) -> int:

        """计算CALL Gas成本"""

        base = 700

        if value > 0:

            base += 9000

        if new_contract:

            base += 25000

        return base

    

    def estimate_contract_gas(self, num_storage_reads: int, 

                            num_storage_writes: int,

                            num_calls: int,

                            memory_kb: int = 0,

                            computation_steps: int = 0) -> Dict:

        """

        估算合约Gas消耗

        

        Args:

            num_storage_reads: 存储读取次数

            num_storage_writes: 存储写入次数

            num_calls: 调用次数

            memory_kb: 内存使用（KB）

            computation_steps: 计算步骤数

        

        Returns:

            Gas估算结果

        """

        gas_used = 21000  # 基础交易Gas

        gas_used += self.calculate_storage_read(num_storage_reads)

        gas_used += self.calculate_storage_write(num_storage_writes)

        gas_used += self.calculate_call_gas(0, False) * num_calls

        gas_used += self.calculate_memory_gas(memory_kb * 1024)

        gas_used += computation_steps * 1

        

        return {

            "total_gas": gas_used,

            "breakdown": {

                "base_transaction": 21000,

                "storage_reads": self.calculate_storage_read(num_storage_reads),

                "storage_writes": self.calculate_storage_write(num_storage_writes),

                "calls": self.calculate_call_gas(0, False) * num_calls,

                "memory": self.calculate_memory_gas(memory_kb * 1024),

                "computation": computation_steps

            }

        }

    

    def optimize_batch_storage_writes(self, num_writes: int) -> int:

        """

        批量存储写入优化

        

        合并多个存储操作为单个操作以节省Gas

        """

        # 非优化：每个写入都需要SSTORE

        naive_cost = num_writes * self.calculate_storage_write()

        

        # 优化：使用单个映射批量写入

        # 实际上需要使用更高效的数据结构

        optimized_cost = 21000 + num_writes * 500 + 5000

        

        return optimized_cost

    

    def estimate_transaction_fee(self, gas_used: int, gas_price_gwei: int = 30) -> Dict:

        """估算交易费用"""

        gas_cost_wei = gas_used * gas_price_gwei * 10**9

        gas_cost_eth = gas_cost_wei / 10**18

        

        return {

            "gas_used": gas_used,

            "gas_price_gwei": gas_price_gwei,

            "cost_wei": gas_cost_wei,

            "cost_eth": gas_cost_eth,

            "cost_usd_approx": gas_cost_eth * 2000  # 假设ETH=$2000

        }



if __name__ == "__main__":

    print("=== 智能合约Gas优化测试 ===")

    

    calculator = GasCalculator()

    

    # 简单ETH转账

    print("\n=== ETH转账 ===")

    simple_tx_gas = 21000

    fee = calculator.estimate_transaction_fee(simple_tx_gas)

    print(f"Gas消耗: {simple_tx_gas}")

    print(f"费用: {fee['cost_eth']:.6f} ETH (${fee['cost_usd_approx']:.2f})")

    

    # ERC20代币转账（估算）

    print("\n=== ERC20代币转账 ===")

    erc20_gas = calculator.estimate_contract_gas(

        num_storage_reads=2,

        num_storage_writes=2,

        num_calls=1,

        memory_kb=0,

        computation_steps=100

    )

    print(f"Gas估算: {erc20_gas}")

    

    fee = calculator.estimate_transaction_fee(erc20_gas['total_gas'])

    print(f"费用: {fee['cost_eth']:.6f} ETH (${fee['cost_usd_approx']:.2f})")

    

    # DEX交易（估算）

    print("\n=== DEX交易（Uniswap风格） ===")

    dex_gas = calculator.estimate_contract_gas(

        num_storage_reads=5,

        num_storage_writes=8,

        num_calls=3,

        memory_kb=4,

        computation_steps=1000

    )

    print(f"Gas估算: {dex_gas}")

    

    fee = calculator.estimate_transaction_fee(dex_gas['total_gas'])

    print(f"费用: {fee['cost_eth']:.6f} ETH (${fee['cost_usd_approx']:.2f})")

    

    # 批量写入优化

    print("\n=== 批量存储写入优化 ===")

    for num_writes in [1, 5, 10, 20]:

        naive = num_writes * calculator.calculate_storage_write()

        optimized = calculator.optimize_batch_storage_writes(num_writes)

        savings = naive - optimized

        print(f"  {num_writes}次写入: 原始{naive}, 优化后{optimized}, 节省{savings} ({savings/naive*100:.1f}%)")

    

    # Gas价格影响

    print("\n=== Gas价格影响 ===")

    for price in [10, 30, 100, 200]:

        fee = calculator.estimate_transaction_fee(150000, price)

        print(f"  Gas价格{price} gwei: {fee['cost_eth']:.6f} ETH (${fee['cost_usd_approx']:.2f})")

