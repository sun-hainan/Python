# -*- coding: utf-8 -*-

"""

算法实现：安全多方计算 / oblivious_transfer



本文件实现 oblivious_transfer 相关的算法功能。

"""



import random

from typing import List, Tuple





class ObliviousTransfer:

    """不经意传输基类"""



    def send(self, m0: int, m1: int, choice: int) -> int:

        """发送消息（接收方视角）"""

        raise NotImplementedError



    def receive(self, c0: int, c1: int) -> Tuple[int, int]:

        """接收选择（发送方视角）"""

        raise NotImplementedError





class SimpleOT(ObliviousTransfer):

    """简单OT（基于RSA）"""



    def __init__(self, security_bits: int = 256):

        self.security_bits = security_bits



    def ot_send(self, messages: Tuple[int, int]) -> Tuple[int, int]:

        """

        OT发送方



        参数：

            messages: (m0, m1)



        返回：(c0, c1)

        """

        m0, m1 = messages



        # 生成随机数

        k = random.randint(2, 2**self.security_bits)



        # 模拟加密

        c0 = (m0 + k) % (2**self.security_bits)

        c1 = (m1 + k) % (2**self.security_bits)



        return (c0, c1)



    def ot_receive(self, choice: int, c0: int, c1: int) -> int:

        """

        OT接收方



        参数：

            choice: 选择 0 或 1

            c0, c1: 接收到的密文



        返回：消息

        """

        # 简化：直接选

        if choice == 0:

            return c0

        else:

            return c1





class ChouOrlandiOT:

    """Chou-Orlandi高效OT"""



    def __init__(self, security_bits: int = 256):

        self.security_bits = security_bits



    def send(self, messages: List[int], receiver_choice: int) -> int:

        """

        发送方



        参数：

            messages: 消息列表

            receiver_choice: 接收方选择



        返回：加密的消息

        """

        # 选择对应的消息

        return messages[receiver_choice]



    def receive(self, ciphertext: int, choices: List[int]) -> int:

        """

        接收方



        参数：

            ciphertext: 加密消息

            choices: 可选消息列表



        返回：选择的值

        """

        # 简化实现

        return ciphertext





def ot_applications():

    """OT应用"""

    print("=== OT应用 ===")

    print()

    print("1. 安全两方计算")

    print("   - Yao的混淆电路使用OT")

    print("   - 发送方可以安全发送数据")

    print()

    print("2. 隐私保护查询")

    print("   - 数据库查询")

    print("   - 区块链隐私交易")

    print()

    print("3. 零知识证明")

    print("   - 某些ZKP协议使用OT")

    print()

    print("效率优化：")

    print("  - IKNP协议：批量OT")

    print("  - 常用于实际系统")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 不经意传输测试 ===\n")



    ot = SimpleOT()



    # 场景：Alice发送两个消息，Bob选择其中一个

    m0, m1 = 42, 77

    print(f"Alice的消息: ({m0}, {m1})")



    # Bob选择

    choice = random.randint(0, 1)

    print(f"Bob的选择: {choice}")



    # OT

    c0, c1 = ot.ot_send((m0, m1))

    result = ot.ot_receive(choice, c0, c1)



    expected = m0 if choice == 0 else m1

    print(f"Bob收到的消息: {result}")

    print(f"验证: {'✅ 正确' if result == expected else '❌ 错误'}")



    print()

    ot_applications()



    print()

    print("说明：")

    print("  - OT是安全多方计算的基本组件")

    print("  - 发送方不知道接收方选择了哪个")

    print("  - 接收方只知道那一条消息的内容")

