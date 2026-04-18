"""
Kruskal - 最小生成树
==========================================

【算法原理】
贪心 + 并查集：
1. 将所有边按权重排序
2. 依次选择最小边(不成环)
3. 直到选中V-1条边

【时间复杂度】O(E log E)
【空间复杂度】O(V)

【应用场景】
- 与Prim相同
- 边稀疏的图更高效

【何时使用】
- 边稀疏的图（E远小于V^2）
- 边已排序的场景
- 并查集操作更高效

【实际案例】
# 航空公司航线规划
# 如何用最少的航线连接所有城市
routes = [
    ("北京", "上海", 1000),
    ("北京", "广州", 2000),
    ("上海", "深圳", 800),
    ("广州", "深圳", 600),
    ("上海", "成都", 1500),
    ("深圳", "成都", 900)
]
# Kruskal找出最小生成树
"""

def kruskal(num_nodes, edges):
    """
    Kruskal最小生成树
    
    Args:
        num_nodes: 顶点数
        edges: 边列表 [(起点, 终点, 权重)]
        
    Returns:
        MST的总权重
    """
    edges = sorted(edges, key=lambda x: x[2])
    parent = list(range(num_nodes))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    result = 0
    for u, v, w in edges:
        pu, pv = find(u), find(v)
        if pu != pv:
            parent[pu] = pv
            result += w
    
    return result
