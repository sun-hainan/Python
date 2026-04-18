"""
斐波那契数列 (Fibonacci) - 中文注释版
==========================================

算法原理：
    斐波那契数列是最经典的动态规划入门问题。
    数列定义：F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)（n>=2）
    即每个数是前两个数之和。

    普通递归会重复计算相同的子问题，导致指数级时间复杂度。
    动态规划通过保存已计算的结果（记忆化），将时间复杂度降为线性。

动态规划思想：
    1. 自底向上：从小问题逐步计算到大问题
    2. 记忆化：保存已计算的结果，避免重复计算

时间复杂度：
    - 普通递归：O(2^n)（指数级，不推荐）
    - 记忆化递归 / 迭代 DP：O(n)（线性）

空间复杂度：
    - 迭代（只保留前两个数）：O(1)
    - 记忆化（保留整个序列）：O(n）
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
