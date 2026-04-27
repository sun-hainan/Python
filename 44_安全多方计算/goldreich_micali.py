# -*- coding: utf-8 -*-

"""

算法实现：安全多方计算 / goldreich_micali



本文件实现 goldreich_micali 相关的算法功能。

"""



import random

from typing import List, Tuple





class GMWProtocol:

    """GMW多方计算协议"""



    def __init__(self, n_parties: int):

        """

        参数：

            n_parties: 参与方数量

        """

        self.n = n_parties

        self.shares = [[] for _ in range(n_parties)]



    def share_secret(self, secret: int) -> List[int]:

        """

        秘密分享



        参数：

            secret: 秘密值



        返回：分享列表

        """

        shares = []



        # 生成 n-1 个随机数

        random_shares = [random.randint(0, 1000000) for _ in range(self.n - 1)]



        # 最后一个是秘密减去其他

        last_share = secret - sum(random_shares)

        random_shares.append(last_share)



        # 打乱顺序

        random.shuffle(random_shares)



        return random_shares



    def reconstruct(self, shares: List[int]) -> int:

        """

        重构秘密



        返回：秘密值

        """

        return sum(shares) % (10**6)  # 简化模运算



    def local_add(self, shares1: List[int], shares2: List[int]) -> List[int]:

        """

        本地加法



        返回：结果分享

        """

        return [(s1 + s2) % (10**6) for s1, s2 in zip(shares1, shares2)]



    def secure_compare(self, a_shares: List[int], b_shares: List[int]) -> List[int]:

        """

        安全比较（简化）



        返回：结果分享

        """

        # 简化：计算差值

        diff = [(s_a - s_b) % (10**6) for s_a, s_b in zip(a_shares, b_shares)]



        return diff





def gmw_properties():

    """GMW性质"""

    print("=== GMW协议性质 ===")

    print()

    print("安全性：")

    print("  - 诚实多数安全")

    print("  - 需要 > n/2 参与者诚实")

    print()

    print("效率：")

    print("  - 加法：本地")

    print("  - 乘法：需要通信 O(n)")

    print()

    print("应用：")

    print("  - 通用MPC")

    print("  - 安全函数计算")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== GMW协议测试 ===\n")



    # 创建3方协议

    gmw = GMWProtocol(3)



    # 秘密分享

    secret = 42



    shares = gmw.share_secret(secret)



    print(f"秘密: {secret}")

    print(f"分享: {[s % 10 for s in shares]}")  # 显示简化后的分享

    print()



    # 重构

    reconstructed = gmw.reconstruct(shares)

    print(f"重构: {reconstructed}")

    print(f"正确: {'✅' if reconstructed == secret else '❌'}")

    print()



    # 加法

    a_shares = gmw.share_secret(10)

    b_shares = gmw.share_secret(20)



    result_shares = gmw.local_add(a_shares, b_shares)

    result = gmw.reconstruct(result_shares)



    print(f"加法: 10 + 20 = {result}")



    print()

    gmw_properties()



    print()

    print("说明：")

    print("  - GMW是MPC的经典协议")

    print("  - 基于秘密共享")

    print("  - 适合半诚实的多数参与者")

