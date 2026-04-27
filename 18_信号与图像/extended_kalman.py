# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / extended_kalman



本文件实现 extended_kalman 相关的算法功能。

"""



import numpy as np





# ekf_predict 算法

def ekf_predict(x, P, f, F_jac, Q, u=None):

    """EKF 预测步骤"""

    x_pred = f(x, u)

    F = F_jac(x, u)

    P_pred = F @ P @ F.T + Q

    return x_pred, P_pred





# ekf_update 算法

def ekf_update(x, P, z, h, H_jac, R):

    """EKF 更新步骤"""

    H = H_jac(x)

    y = z - h(x)

    S = H @ P @ H.T + R

    K = P @ H.T @ np.linalg.inv(S)

    x_new = x + K @ y

    P_new = (np.eye(len(x)) - K @ H) @ P

    return x_new, P_new





# EKFSimple 类

class EKFSimple:

    """简化 EKF"""



# __init__ 算法

    def __init__(self, state_dim):

        self.x = np.zeros(state_dim)

        self.P = np.eye(state_dim)



# step 算法

    def step(self, z, f, h, F_jac, H_jac, Q, R, u=None):

        self.x, self.P = ekf_predict(self.x, self.P, f, F_jac, Q, u)

        self.x, self.P = ekf_update(self.x, self.P, z, h, H_jac, R)

        return self.x, self.P





if __name__ == "__main__":

    ekf = EKFSimple(2)

# f 算法

    def f(x, u): return np.array([x[0]+x[1]*0.1, x[1]+0.01])

# h 算法

    def h(x): return np.array([x[0]])

# Fj 算法

    def Fj(x, u): return np.array([[1, 0.1], [0, 1]])

# Hj 算法

    def Hj(x): return np.array([[1, 0]])

    Q = np.eye(2)*0.01

    R = np.array([[0.5]])



    for i in range(10):

        z = np.array([i*0.1]) + np.random.randn(1)*0.2

        ekf.step(z, f, h, Fj, Hj, Q, R)

        print(f"Step {i+1}: estimate={ekf.x.round(3)}")

    print("\nExtended Kalman Filter 测试完成!")

