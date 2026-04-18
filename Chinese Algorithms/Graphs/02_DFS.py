"""
DFS - 深度优先搜索
==========================================

【算法原理】
使用栈(或递归)，一条路走到黑，再回溯探索其他路径。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 迷宫求解
- 路径搜索
- 连通分量检测
- 拓扑排序

【何时使用】
- 找所有可能路径
- 迷宫问题
- 连通分量分析
- 需要回溯的搜索

【实际案例】
# 走迷宫 - 找到从起点到终点的路径
maze = [
    [0, 1, 0, 0],
    [0, 1, 0, 1],
    [0, 0, 0, 0],
    [1, 1, 0, 0]
]
# DFS找到从(0,0)到(3,3)的路径

# 文件系统遍历
# 递归遍历文件夹所有文件
file_system = {
    "根": ["文件夹A", "文件夹B"],
    "文件夹A": ["文件1.txt", "文件2.txt"],
    "文件夹B": ["文件夹C", "文件3.txt"],
    "文件夹C": ["文件4.txt"]
}
dfs(file_system, "根")  # 遍历所有文件

# 数独求解器
# DFS + 回溯尝试每个数字
"""

def dfs(graph, start, visited=None):
    """
    深度优先搜索(递归版)
    
    Args:
        graph: 邻接表 {顶点: [邻接顶点]}
        start: 起始顶点
        visited: 已访问顶点集合
        
    Returns:
        从start可达的所有顶点
    """
    if visited is None:
        visited = set()
    
    visited.add(start)
    result = [start]
    
    for neighbor in graph.get(start, []):
        if neighbor not in visited:
            result.extend(dfs(graph, neighbor, visited))
    
    return result
