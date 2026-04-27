# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / bandit_recommendation

本文件实现 bandit_recommendation 相关的算法功能。
"""

if __name__ == '__main__':
    print('=== Bandit Recommendation test ===')
    np.random.seed(42)
    true_rewards = np.array([0.3, 0.5, 0.7, 0.4, 0.6])
    n_rounds = 500
    print(f'True rewards: {true_rewards}')
    print(f'Optimal arm: {np.argmax(true_rewards)}')
    ucb = UCB1(n_arms=5, c=2.0)
    reward_ucb = simulate_bandit(ucb, n_rounds, true_rewards)
    print(f'UCB total reward: {reward_ucb}')
    ts = ThompsonSampling(n_arms=5)
    reward_ts = simulate_bandit(ts, n_rounds, true_rewards)
    print(f'Thomson total reward: {reward_ts}')
