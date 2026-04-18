"""
LIS - 最长递增子序列
==========================================

【问题定义】
在一个序列中找出最长的递增子序列。
子序列可以不连续，但必须保持递增顺序。

【应用场景】
- 套娃信封问题
- 合唱队形问题
- 股票最长上涨区间
"""

def lis(arr):
    """
    最长递增子序列 - 动态规划解法
    
    Args:
        arr: 待处理列表
        
    Returns:
        LIS长度
    """
    if not arr:
        return 0
    
    n = len(arr)
    # dp[i] = 以arr[i]结尾的LIS长度
    dp = [1] * n
    
    for i in range(1, n):
        for j in range(i):
            if arr[j] < arr[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)


# ---------- BFS ----------
FILES['Chinese Algorithms/Graphs/01_BFS.py'] = 
BFS - 广度优先搜索
==========================================

【算法原理】
使用队列，按层次遍历图/树。
先访问近的节点，再访问远的节点。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 最短路径(无权图)
- 层次遍历
- 社交网络好友推荐
