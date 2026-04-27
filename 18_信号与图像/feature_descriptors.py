# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / feature_descriptors



本文件实现 feature_descriptors 相关的算法功能。

"""



import numpy as np



def hu_moments(image):

    from scipy import ndimage

    m = ndimage.moments(image.astype(float), order=3)

    cr = m[0,0]

    nu = np.zeros(7)

    for p in range(7):

        for q in range(7):

            if p+q <= 3 and (p+q)>=2:

                nu[p+q] = m[p,q] / (cr**((p+q)/2+1))

    return nu



def hog_descriptor(image, cell_size=8, n_bins=9):

    from scipy.ndimage import gradient

    gx, gy = gradient(image)

    magnitude = np.sqrt(gx**2 + gy**2)

    orientation = np.arctan2(gy, gx) * 180 / np.pi

    h, w = image.shape

    n_cells_y = h // cell_size

    n_cells_x = w // cell_size

    histograms = np.zeros((n_cells_y, n_cells_x, n_bins))

    for cy in range(n_cells_y):

        for cx in range(n_cells_x):

            cell_mag = magnitude[cy*cell_size:(cy+1)*cell_size, cx*cell_size:(cx+1)*cell_size]

            cell_ori = orientation[cy*cell_size:(cy+1)*cell_size, cx*cell_size:(cx+1)*cell_size]

            for my, mx in zip(cell_mag.ravel(), cell_ori.ravel()):

                bin_idx = int((mx + 180) / 180 * n_bins) % n_bins

                histograms[cy,cx,bin_idx] += my

    return histograms



def lbp_simple(image, radius=1):

    h,w = image.shape

    lbp = np.zeros((h-2*radius,w-2*radius))

    for y in range(radius,h-radius):

        for x in range(radius,w-radius):

            center = image[y,x]

            code = 0

            for dy,dx in [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]:

                if image[y+dy,x+dx] >= center:

                    code |= 1

                code >>= 1

            lbp[y-radius,x-radius] = code

    return lbp



if __name__ == "__main__":

    np.random.seed(42)

    img = np.random.randint(0,256,(64,64))

    hu = hu_moments(img)

    hog = hog_descriptor(img)

    lbp = lbp_simple(img)

    print(f"HOG shape: {hog.shape}, LBP max: {np.max(lbp)}")

    print("\n特征描述子测试完成!")

