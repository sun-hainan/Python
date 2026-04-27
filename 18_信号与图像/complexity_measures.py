# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / complexity_measures



本文件实现 complexity_measures 相关的算法功能。

"""



import numpy as np



def sample_entropy(signal, m=2, r=0.2):

    n = len(signal)

    def _maxdist(xi, xj):

        return max(abs(a-b) for a,b in zip(xi,xj))

    def _phi(m):

        c = 0

        for i in range(n-m):

            for j in range(i+1, n-m):

                if _maxdist(signal[i:i+m], signal[j:j+m]) < r:

                    c += 1

        return c

    phi_m = _phi(m)

    phi_m1 = _phi(m+1)

    return -np.log(phi_m1/phi_m) if phi_m>0 and phi_m1>0 else 0



def lyapunov_exponent(signal, tau=1, max_dim=10):

    exponents = []

    for d in range(2, max_dim+1):

        N = len(signal) - d*tau

        if N < 10: break

        embedded = np.zeros((N, d))

        for i in range(d):

            embedded[:,i] = signal[i*tau:i*tau+N]

        cov = np.cov(embedded.T)

        eigenvalues = np.abs(np.linalg.eigvals(cov))

        eigenvalues = np.sort(eigenvalues)[::-1]

        le = np.log(eigenvalues[0]+1e-10)

        exponents.append(le)

    return np.mean(exponents) if exponents else 0



def correlation_dimension(signal, eps_range=None):

    if eps_range is None:

        eps_range = np.linspace(0.1, 2, 20)

    c = []

    for eps in eps_range:

        n = len(signal)

        count = 0

        for i in range(n):

            for j in range(i+1, n):

                if abs(signal[i]-signal[j]) < eps:

                    count += 1

        c.append(2*count/(n*(n-1)))

    log_eps = np.log(eps_range)

    log_c = np.log(np.maximum(c, 1e-10))

    from scipy.stats import linregress

    slope = linregress(log_eps, log_c).slope

    return slope



if __name__ == "__main__":

    np.random.seed(42)

    sig = np.sin(2*np.pi*0.1*np.arange(200)) + 0.1*np.random.randn(200)

    se = sample_entropy(sig)

    print(f"Sample entropy: {se:.4f}")

    print("\n复杂性度量测试完成!")

