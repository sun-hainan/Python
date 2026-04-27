# -*- coding: utf-8 -*-
"""
算法实现：局部可解码码 / locally_recoverable

本文件实现 locally_recoverable 相关的算法功能。
"""

import random
from typing import List, Tuple


class LocallyRecoverableCode:
    """局部可恢复编码"""

    def __init__(self, n: int, k: int, r: int):
        """
        参数：
            n: 码字长度
            k: 信息位
            r: 局部校验位数
        """
        self.n = n
        self.k = k
        self.r = r
        self.local_groups = self._build_local_groups()

    def _build_local_groups(self) -> List[List[int]]:
        """构建局部组"""
        groups = []
        # 将n个位置分成若干组，每组有r个本地校验位
        group_size = (self.n - self.k) // (r + 1)

        for i in range(0, self.n - self.k, group_size):
            group = list(range(i, min(i + group_size, self.n)))
            groups.append(group)

        return groups

    def encode(self, data: List[int]) -> List[int]:
        """
        编码

        参数：
            data: 信息位

        返回：码字
        """
        # 添加全局校验位（简化）
        global_parity = sum(data) % 2
        codeword = data + [global_parity]

        # 添加本地校验位
        for group in self.local_groups:
            parity = sum(codeword[i] for i in group if i < len(codeword)) % 2
            codeword.append(parity)

        return codeword

    def recover_local(self, codeword: List[int], erased_positions: List[int]) -> List[int]:
        """
        本地恢复

        参数：
            codeword: 码字
            erased_positions: 损坏位置列表

        返回：恢复后的码字
        """
        recovered = codeword.copy()

        for pos in erased_positions:
            if pos < len(recovered):
                # 在同一个本地组中找到未损坏的位置
                for group in self.local_groups:
                    if pos in group:
                        # 找到同组的其他位置
                        others = [i for i in group if i != pos and i < len(recovered)]
                        if others:
                            # 用奇偶校验恢复
                            parity = sum(recovered[i] for i in others) % 2
                            recovered[pos] = parity
                        break

        return recovered

    def decode(self, received: List[int]) -> List[int]:
        """
        译码

        返回：信息位
        """
        # 简化：返回前k位
        return received[:self.k]


def lrc_vs_raid():
    """LRC vs RAID"""
    print("=== LRC vs RAID ===")
    print()
    print("RAID 5/6：")
    print("  - 需要读取多块才能恢复")
    print("  - 网络带宽大")
    print()
    print("LRC：")
    print("  - 单块本地恢复")
    print("  - 减少网络使用")
    print("  - 略微增加存储开销")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 局部可恢复编码测试 ===\n")

    # 创建LRC
    n = 10  # 总长度
    k = 6   # 信息位
    r = 2   # 每组本地校验位

    lrc = LocallyRecoverableCode(n, k, r)

    print(f"LRC参数: n={n}, k={k}, r={r}")
    print(f"本地组数: {len(lrc.local_groups)}")
    print(f"本地组: {lrc.local_groups}")
    print()

    # 编码
    data = [1, 0, 1, 1, 0, 1]
    codeword = lrc.encode(data)

    print(f"信息: {data}")
    print(f"码字: {codeword}")
    print(f"码字长度: {len(codeword)}")
    print()

    # 模拟损坏
    erased = [3]  # 位置3损坏
    corrupted = codeword.copy()
    corrupted[3] = -1

    print(f"损坏位置: {erased}")

    # 本地恢复
    recovered = lrc.recover_local(corrupted, erased)

    print(f"恢复后: {recovered}")
    print(f"恢复正确: {'✅' if recovered == codeword else '❌'}")

    print()
    lrc_vs_raid()

    print()
    print("说明：")
    print("  - LRC用于分布式存储")
    print("  - Azure、Meta使用")
    print("  - 平衡可靠性和效率")
