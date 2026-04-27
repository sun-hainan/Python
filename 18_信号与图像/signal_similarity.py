# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / signal_similarity



本文件实现 signal_similarity 相关的算法功能。

"""



import numpy as np



def euclidean_distance(s1, s2):

    return np.linalg.norm(np.array(s1) - np.array(s2))



def cosine_similarity(s1, s2):

    a,b = np.array(s1), np.array(s2)

    return np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-10)



def dynamic_time_warping(s1, s2):

    n,m = len(s1), len(s2)

    dtw = np.full((n+1,m+1), np.inf)

    dtw[0,0] = 0

    for i in range(1,n+1):

        for j in range(1,m+1):

            cost = abs(s1[i-1]-s2[j-1])

            dtw[i,j] = cost + min(dtw[i-1,j], dtw[i,j-1], dtw[i-1,j-1])

    return dtw[n,m]



def pearson_correlation(s1, s2):

    a,b = np.array(s1), np.array(s2)

    am, bm = a.mean(), b.mean()

    centered_a, centered_b = a-am, b-bm

    denom = np.sqrt((centered_a**2).sum()*(centered_b**2).sum())

    return (centered_a*centered_b).sum()/denom if denom>0 else 0



if __name__ == "__main__":

    np.random.seed(42)

    s1 = np.sin(np.linspace(0,2*np.pi,100))

    s2 = np.sin(np.linspace(0,2*np.pi,100)) + 0.1*np.random.randn(100)

    print(f"Cosine sim: {cosine_similarity(s1,s2):.4f}")

    print(f"DTW dist: {dynamic_time_warping(s1,s2):.2f}")

    print("\n相似性度量测试完成!")

