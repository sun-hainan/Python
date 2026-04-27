# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / fibonacci

本文件实现 fibonacci 相关的算法功能。
"""

class Fibonacci:
    """
    斐波那契数列计算器（使用动态规划）
    """

    def __init__(self) -> None:
        # 初始化序列，包含已知的 F(0) 和 F(1)
        self.sequence = [0, 1]

    def get(self, index: int) -> list:
        """
        获取斐波那契数列的前 index 个数

        如果计算到指定位置所需的数不存在，则先计算缺失的数。

        参数:
            index: 需要的斐波那契数的个数

        返回:
            斐波那契数列的前 index 个数

        示例:
            >>> Fibonacci().get(10)
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
            >>> Fibonacci().get(5)
            [0, 1, 1, 2, 3]
        """
        # 如果当前序列不够长，则继续计算
        difference = index - (len(self.sequence) - 1)
        if difference >= 1:
            for _ in range(difference):
                # 每个新数 = 前两个数之和
                self.sequence.append(self.sequence[-1] + self.sequence[-2])

        return self.sequence[:index]


def main() -> None:
    print(
        "斐波那契数列 - 动态规划实现\n",
        "输入索引获取对应位置的斐波那契数（输入 exit 或 Ctrl-C 退出）\n",
        sep="",
    )
    fibonacci = Fibonacci()

    while True:
        prompt: str = input(">> ")
        if prompt in {"exit", "quit"}:
            break

        try:
            index: int = int(prompt)
        except ValueError:
            print("请输入数字或 'exit'")
            continue

        print(fibonacci.get(index))


if __name__ == "__main__":
    main()
