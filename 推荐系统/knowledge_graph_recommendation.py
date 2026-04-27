# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / knowledge_graph_recommendation

本文件实现 knowledge_graph_recommendation 相关的算法功能。
"""

if __name__ == '__main__':
    print('=== Knowledge Graph Recommendation test ===')
    np.random.seed(42)
    kg = KnowledgeGraph()
    triples = [(10, 1, 20), (11, 1, 21), (12, 1, 20), (10, 2, 30)]
    for h, r, t in triples:
        kg.add_triple(h, r, t)
    print(f'Triples: {len(kg.triples)}')
    ripple = RippleNet(n_entities=100, n_relations=10, n_items=20, embedding_dim=16, n_hops=2)
    user_history = [10, 11]
    ripple_sets = ripple.ripple_set_expansion(user_history, kg)
    print(f'Ripple set hops: {len(ripple_sets)}')
    recs = ripple.recommend(user_history, kg, k=5)
    print(f'Recommendations: {recs}')
