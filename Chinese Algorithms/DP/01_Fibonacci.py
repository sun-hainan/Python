"""
Fibonacci - 斐波那契数列
==========================================

【数列定义】
F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)

【时间复杂度】O(n)
【空间复杂度】O(1)

【应用场景】
- 兔子繁殖问题
- 黄金分割比例
- 动态规划入门示例
- 网页动态加载延迟

【何时使用】
- 学习递归/动态规划
- 斐波那契相关数学问题
"""

class Fibonacci:
    """
    斐波那契数列计算器(缓存优化)
    """
    def __init__(self):
        self.cache = [0, 1]
    
    def get_nth(self, n):
        while len(self.cache) <= n:
            self.cache.append(self.cache[-1] + self.cache[-2])
        return self.cache[n]
    
    def get_sequence(self, n):
        self.get_nth(n - 1)
        return self.cache[:n]
