# -*- coding: utf-8 -*-

"""

算法实现：推荐系统 / sequence_recommendation



本文件实现 sequence_recommendation 相关的算法功能。

"""



if __name__ == '__main__':

    print('=== Sequence Recommendation test ===')

    np.random.seed(42)

    sessions = [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6], [1, 3, 5, 7]]

    n_items = 10

    gru = GRU4Rec(n_items=n_items, embedding_dim=8, hidden_dim=16)

    for session in sessions[:2]:

        recs = gru.predict_next_item(session, top_k=3)

        print(f'  Sequence {session} -> {recs}')

    mc = MarkovChainRecommender(n_items=n_items)

    mc.fit(sessions)

    for item in [1, 2, 3]:

        recs = mc.predict(item, top_k=3)

        print(f'  Current {item} -> {recs}')

