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
