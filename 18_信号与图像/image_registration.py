# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / image_registration



本文件实现 image_registration 相关的算法功能。

"""



import numpy as np

import math





# ncc_match 算法

def ncc_match(img1, img2):

    """归一化互相关"""

    m1, m2 = np.mean(img1), np.mean(img2)

    s1, s2 = np.std(img1), np.std(img2)

    if s1 < 1e-10 or s2 < 1e-10:

        return 0

    return np.mean((img1-m1)*(img2-m2))/(s1*s2)





# template_match 算法

def template_match(img, template, method='ncc'):

    """模板匹配"""

    th, tw = template.shape

    ih, iw = img.shape

    best = (0, 0, -1e9)



    for y in range(ih-th):

        for x in range(iw-tw):

            patch = img[y:y+th, x:x+tw]

            score = ncc_match(patch, template)

            if score > best[2]:

                best = (y, x, score)

    return best[:2], best[2]





# ransac_transform 算法

def ransac_transform(src, dst, n_iter=100, threshold=3.0):

    """RANSAC 变换估计"""

    n = min(len(src), len(dst), 4)

    best_inliers = 0

    best_model = np.eye(3)



    for _ in range(n_iter):

        idx = np.random.choice(len(src), n, replace=False)

        s, d = src[idx], dst[idx]

        if len(s) < 3:

            continue

        A = []

        b = []

        for (x,y),(u,v) in zip(s,d):

            A.append([x,y,1,0,0,0]); b.append(u)

            A.append([0,0,0,x,y,1]); b.append(v)

        try:

            params = np.linalg.lstsq(np.array(A), b, rcond=None)[0]

            inliers = 0

            for (x,y),(u,v) in zip(src,dst):

                pred = np.array([x,y,1]) @ params.reshape(2,3)

                if math.sqrt((pred[0]-u)**2+(pred[1]-v)**2) < threshold:

                    inliers += 1

            if inliers > best_inliers:

                best_inliers = inliers

                best_model = params.reshape(2,3)

        except:

            pass

    return best_model, best_inliers





if __name__ == "__main__":

    np.random.seed(42)

    img = np.zeros((50,50))

    img[20:30,20:30] = 200



    template = img[22:28,22:28]

    (y,x), score = template_match(img, template)

    print(f"最佳匹配: ({y},{x}), NCC={score:.4f}")

    print("\n图像配准测试完成!")

