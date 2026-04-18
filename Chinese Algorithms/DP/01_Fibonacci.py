"""
Fibonacci - 斐波那契数列
==========================================

【数列定义】
F(0) = 0, F(1) = 1
F(n) = F(n-1) + F(n-2)

【应用场景】
- 递归可视化
- 动态规划入门
- 黄金分割比例
"""

class Fibonacci:
    """
    斐波那契数列计算器(使用缓存优化)
    """
    
    def __init__(self):
        self.cache = [0, 1]
    
    def get_nth(self, n):
        """
        获取第n个斐波那契数
        
        Args:
            n: 位置(从0开始)
            
        Returns:
            第n个斐波那契数
        """
        while len(self.cache) <= n:
            self.cache.append(self.cache[-1] + self.cache[-2])
        return self.cache[n]
    
    def get_sequence(self, n):
        """获取前n个斐波那契数"""
        self.get_nth(n - 1)
        return self.cache[:n]
