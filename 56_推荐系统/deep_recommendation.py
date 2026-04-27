# -*- coding: utf-8 -*-

"""

算法实现：推荐系统 / deep_recommendation



本文件实现 deep_recommendation 相关的算法功能。

"""



if __name__ == '__main__':

    print('=== Deep Recommendation test ===')

    np.random.seed(42)

    n_samples, n_features = 100, 20

    X = np.random.rand(n_samples, n_features)

    y = np.random.randint(0, 2, n_samples)

    print(f'Data: {X.shape}')

    wnd = WideAndDeep(n_features)

    pred_wnd = wnd.forward(X)

    print(f'WideAndDeep pred range: [{pred_wnd.min():.4f}, {pred_wnd.max():.4f}]')

    dfm = DeepFM(n_features, n_factors=5, hidden_dims=[16, 8])

    pred_dfm = dfm.forward(X)

    print(f'DeepFM pred range: [{pred_dfm.min():.4f}, {pred_dfm.max():.4f}]')

