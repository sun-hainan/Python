# -*- coding: utf-8 -*-

"""

算法实现：08_位运算 / bitmap_index



本文件实现 bitmap_index 相关的算法功能。

"""



# BitmapIndex 类

class BitmapIndex:

    """位图索引，每个比特对应一个整数的存在性"""



# __init__ 算法

    def __init__(self, max_val: int):

        # 计算所需比特数，向上取整到字节边界

        self.size = (max_val + 63) // 64  # 64位ulong数组

        self.bits = [0] * self.size



# set 算法

    def set(self, val: int):

        """设置第val位为1"""

        idx = val // 64

        offset = val % 64

        self.bits[idx] |= (1 << offset)



# unset 算法

    def unset(self, val: int):

        """清除第val位"""

        idx = val // 64

        offset = val % 64

        self.bits[idx] &= ~(1 << offset)



    def test(self, val: int) -> bool:

        """测试第val位是否存在"""

        idx = val // 64

        offset = val % 64

        return (self.bits[idx] >> offset) & 1 == 1



    def union(self, other: "BitmapIndex") -> "BitmapIndex":

        """并集：按位OR"""

        result = BitmapIndex.__new__(BitmapIndex)

        result.size = self.size

        result.bits = [a | b for a, b in zip(self.bits, other.bits)]

        return result



    def intersect(self, other: "BitmapIndex") -> "BitmapIndex":

        """交集：按位AND"""

        result = BitmapIndex.__new__(BitmapIndex)

        result.size = self.size

        result.bits = [a & b for a, b in zip(self.bits, other.bits)]

        return result



    def difference(self, other: "BitmapIndex") -> "BitmapIndex":

        """差集：self & ~other"""

        result = BitmapIndex.__new__(BitmapIndex)

        result.size = self.size

        result.bits = [a & ~b for a, b in zip(self.bits, other.bits)]

        return result



    def cardinality(self) -> int:

        """计算1的个数"""

        total = 0

        for block in self.bits:

            while block:

                total += 1

                block &= block - 1  # Brian Kernighan

        return total



    def to_list(self) -> list[int]:

        """导出所有为1的位置"""

        result = []

        for i, block in enumerate(self.bits):

            offset = 0

            while block:

                lsb = block & -block

                pos = i * 64 + (lsb.bit_length() - 1)

                result.append(pos)

                block &= block - 1

        return result





if __name__ == "__main__":

    # 示例：用户兴趣标签索引

    user1 = BitmapIndex(128)

    for tag in [3, 7, 12, 45, 67]:

        user1.set(tag)



    user2 = BitmapIndex(128)

    for tag in [7, 20, 45, 88]:

        user2.set(tag)



    print("用户1标签:", user1.to_list())

    print("用户2标签:", user2.to_list())



    shared = user1.intersect(user2)

    print("共同标签:", shared.to_list())



    union = user1.union(user2)

    print("全部标签:", union.to_list())



    print(f"用户1标签数: {user1.cardinality()}")

    print(f"用户2标签数: {user2.cardinality()}")

    print(f"共同标签数: {shared.cardinality()}")

