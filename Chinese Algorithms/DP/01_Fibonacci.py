"""
Fibonacci - 斐波那契数列
==========================================

【数列定义】
F(0) = 0, F(1) = 1
F(n) = F(n-1) + F(n-2)

【时间复杂度】O(n)
【空间复杂度】O(1)

【应用场景】
- 递归可视化教学
- 动态规划入门
- 兔子繁殖问题
- 黄金分割相关

【何时使用】
- 学习递归思想
- 斐波那契相关的数学问题
- 验证递归改动态规划

【实际案例】
# 兔子繁殖问题
# 第n个月的兔子对数 = F(n)
# 1月: 1对 → 2月: 1对 → 3月: 2对 → 4月: 3对 → ...

# 计算任意月份的兔子数量
fib = Fibonacci()
month_12_rabbits = fib.get_nth(12)  # 第12个月有多少对兔子

# 网页动态加载（斐波那契数列作为延迟时间）
# 越往后加载越慢，形成优雅的加载节奏
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
