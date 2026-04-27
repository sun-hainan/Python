# -*- coding: utf-8 -*-

"""

算法实现：区块链算法 / transaction_validation



本文件实现 transaction_validation 相关的算法功能。

"""



import hashlib

import time

from typing import List, Dict, Optional

from dataclasses import dataclass



@dataclass

class Transaction:

    """交易"""

    tx_id: str

    sender: str

    receiver: str

    amount: int

    fee: int

    timestamp: float

    signature: str

    nonce: int



class UTXO:

    """未花费交易输出"""

    def __init__(self, tx_id: str, output_index: int, owner: str, amount: int):

        self.tx_id = tx_id

        self.output_index = output_index

        self.owner = owner

        self.amount = amount

        self.spent = False



class TransactionValidator:

    """

    交易验证

    

    验证交易的:

    1. 签名有效性

    2. 余额充足

    3. 双花检查

    4. 格式正确性

    """

    

    def __init__(self):

        self.utxo_set: Dict[str, UTXO] = {}  # utxo_id -> UTXO

        self.nonces: Dict[str, int] = {}  # address -> nonce

    

    def add_utxo(self, tx_id: str, output_index: int, owner: str, amount: int):

        """添加UTXO到集合"""

        utxo_id = f"{tx_id}:{output_index}"

        self.utxo_set[utxo_id] = UTXO(tx_id, output_index, owner, amount)

    

    def verify_signature(self, tx: Transaction) -> bool:

        """

        验证交易签名

        

        简化实现: 检查签名格式和长度

        """

        # 实际应使用ECDSA验证

        if not tx.signature:

            return False

        

        # 简化: 签名应为64字节十六进制

        if len(tx.signature) != 128:

            return False

        

        return True

    

    def verify_balance(self, sender: str, amount: int, fee: int) -> bool:

        """

        验证发送者余额是否充足

        

        Args:

            sender: 发送者地址

            amount: 发送金额

            fee: 交易费用

        

        Returns:

            是否充足

        """

        total_balance = 0

        for utxo in self.utxo_set.values():

            if utxo.owner == sender and not utxo.spent:

                total_balance += utxo.amount

        

        return total_balance >= (amount + fee)

    

    def verify_nonce(self, sender: str, nonce: int) -> bool:

        """

        验证nonce

        

        防止重放攻击

        """

        expected_nonce = self.nonces.get(sender, 0)

        return nonce == expected_nonce

    

    def check_double_spend(self, tx: Transaction) -> bool:

        """

        检查双花

        

        检查同一UTXO是否被多次花费

        """

        # 简化实现

        return False  # 无双花

    

    def validate_transaction(self, tx: Transaction) -> tuple:

        """

        完整交易验证

        

        Returns:

            (是否有效, 错误信息)

        """

        errors = []

        

        # 1. 签名验证

        if not self.verify_signature(tx):

            errors.append("无效的签名")

        

        # 2. 金额验证

        if tx.amount <= 0:

            errors.append("金额必须为正")

        

        if tx.fee < 0:

            errors.append("费用不能为负")

        

        # 3. 余额验证

        if not self.verify_balance(tx.sender, tx.amount, tx.fee):

            errors.append("余额不足")

        

        # 4. Nonce验证

        if not self.verify_nonce(tx.sender, tx.nonce):

            errors.append("nonce错误")

        

        # 5. 时间戳验证

        current_time = time.time()

        if abs(current_time - tx.timestamp) > 3600:  # 1小时

            errors.append("时间戳过于老旧")

        

        return (len(errors) == 0, errors)

    

    def mark_utxo_spent(self, tx_id: str, output_index: int):

        """标记UTXO为已花费"""

        utxo_id = f"{tx_id}:{output_index}"

        if utxo_id in self.utxo_set:

            self.utxo_set[utxo_id].spent = True



if __name__ == "__main__":

    print("=== 交易验证测试 ===")

    

    validator = TransactionValidator()

    

    # 添加一些UTXO

    validator.add_utxo("tx001", 0, "alice", 100000000)

    validator.add_utxo("tx002", 0, "alice", 50000000)

    validator.add_utxo("tx003", 0, "bob", 200000000)

    

    print("UTXO集合:")

    for utxo_id, utxo in validator.utxo_set.items():

        print(f"  {utxo_id}: {utxo.owner} = {utxo.amount} satoshis")

    

    # 创建测试交易

    tx = Transaction(

        tx_id="tx004",

        sender="alice",

        receiver="bob",

        amount=80000000,

        fee=1000,

        timestamp=time.time(),

        signature="a" * 128,  # 假签名

        nonce=0

    )

    

    print(f"\n交易: {tx.sender} -> {tx.receiver}: {tx.amount} satoshis")

    

    # 验证交易

    is_valid, errors = validator.validate_transaction(tx)

    

    print(f"\n验证结果: {'有效' if is_valid else '无效'}")

    if errors:

        print(f"错误: {errors}")

    

    # 模拟余额不足

    print("\n=== 余额不足测试 ===")

    tx2 = Transaction(

        tx_id="tx005",

        sender="alice",

        receiver="bob",

        amount=200000000,  # 超过alice的余额

        fee=1000,

        timestamp=time.time(),

        signature="b" * 128,

        nonce=1

    )

    

    is_valid2, errors2 = validator.validate_transaction(tx2)

    print(f"交易2验证结果: {'有效' if is_valid2 else '无效'}")

    print(f"错误: {errors2}")

    

    # Nonce测试

    print("\n=== Nonce测试 ===")

    tx3 = Transaction(

        tx_id="tx006",

        sender="alice",

        receiver="bob",

        amount=10000000,

        fee=1000,

        timestamp=time.time(),

        signature="c" * 128,

        nonce=0  # 重复nonce

    )

    

    # 先处理tx，再验证tx3

    validator.nonces["alice"] = 1  # alice的nonce已经变成1

    is_valid3, errors3 = validator.validate_transaction(tx3)

    print(f"Nonce测试结果: {'有效' if is_valid3 else '无效'}")

    print(f"错误: {errors3}")

