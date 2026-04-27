# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / discrete_cosine_transform



本文件实现 discrete_cosine_transform 相关的算法功能。

"""



import numpy as np



def dct(image):

    N = image.shape[0]

    dct_matrix = np.zeros((N,N))

    for u in range(N):

        for v in range(N):

            for i in range(N):

                for j in range(N):

                    cu = 1/np.sqrt(2) if u==0 else 1

                    cv = 1/np.sqrt(2) if v==0 else 1

                    dct_matrix[u,v] += cu*cv*image[i,j]*np.cos(np.pi*u*(2*i+1)/(2*N))*np.cos(np.pi*v*(2*j+1)/(2*N))

    return 2*dct_matrix/N



def idct(D):

    N = D.shape[0]

    img = np.zeros((N,N))

    for i in range(N):

        for j in range(N):

            for u in range(N):

                for v in range(N):

                    cu = 1/np.sqrt(2) if u==0 else 1

                    cv = 1/np.sqrt(2) if v==0 else 1

                    img[i,j] += cu*cv*D[u,v]*np.cos(np.pi*u*(2*i+1)/(2*N))*np.cos(np.pi*v*(2*j+1)/(2*N))

    return 2*img/N



if __name__ == "__main__":

    np.random.seed(42)

    img = np.random.randint(0,256,(8,8))

    D = dct(img)

    rec = idct(D)

    print(f"DCT max coeff: {np.max(np.abs(D)):.2f}, Reconstruction error: {np.max(np.abs(rec-img)):.4f}")

    print("\nDCT 测试完成!")

