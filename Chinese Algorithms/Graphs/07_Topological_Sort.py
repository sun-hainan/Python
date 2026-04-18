"""
Topological Sort - 拓扑排序
==========================================

【问题定义】
对有向无环图(DAG)进行线性排序，
使得所有有向边(u,v)中，u都在v之前。

【时间复杂度】O(V + E)
【空间复杂度】O(V)

【应用场景】
- 课程先修关系（数据结构课需要先学编程）
- 项目任务调度
- Makefile依赖解析
- 编译器符号表构建
- 食谱/做菜顺序

【何时使用】
- 有依赖关系的任务排序
- DAG遍历
- 任务调度

【实际案例】
# 大学课程先修关系
courses = {
    "编程": [],
    "数据结构": ["编程"],
    "算法": ["数据结构"],
    "机器学习": ["算法", "概率论"],
    "人工智能": ["机器学习"]
}
topological_sort(courses)  # 得出选课顺序

# 项目开发任务调度
tasks = {
    "需求分析": [],
    "系统设计": ["需求分析"],
    "编码": ["系统设计"],
    "测试": ["编码"],
    "上线": ["测试", "系统设计"]
}
topological_sort(tasks)  # 得出任务执行顺序

# 早餐制作顺序
breakfast = {
    "烤面包": [],
    "煎蛋": ["烤面包"],
    "冲咖啡": [],
    "摆盘": ["烤面包", "煎蛋"]
}
topological_sort(breakfast)  # 得出做早餐顺序
"""

from collections import deque

def topological_sort(graph):
    """
    拓扑排序 - Kahn算法(BFS)
    
    Args:
        graph: 邻接表 {顶点: [邻接顶点]}
        
    Returns:
        拓扑排序结果
    """
    in_degree = {v: 0 for v in graph}
    for v in graph:
        for neighbor in graph[v]:
            in_degree[neighbor] += 1
    
    queue = deque([v for v in graph if in_degree[v] == 0])
    result = []
    
    while queue:
        vertex = queue.popleft()
        result.append(vertex)
        
        for neighbor in graph[vertex]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return result
