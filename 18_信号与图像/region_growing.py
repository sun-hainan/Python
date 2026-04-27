# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / region_growing



本文件实现 region_growing 相关的算法功能。

"""



import numpy as np

from collections import deque



def region_growing(image, seed, threshold=20):

    h,w = image.shape

    visited = np.zeros_like(image, dtype=bool)

    seed_value = image[seed[1],seed[0]]

    queue = deque([seed])

    region = []

    while queue:

        y,x = queue.popleft()

        if visited[y,x]: continue

        if abs(int(image[y,x]) - int(seed_value)) > threshold: continue

        visited[y,x] = True

        region.append((x,y))

        for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:

            ny,nx = y+dy,x+dx

            if 0<=ny<h and 0<=nx<w and not visited[ny,nx]:

                queue.append((ny,nx))

    return region



def flood_fill(image, seed, new_val=255):

    h,w = image.shape

    filled = image.copy()

    seed_val = image[seed[1],seed[0]]

    queue = deque([seed])

    while queue:

        y,x = queue.popleft()

        if filled[y,x] != seed_val: continue

        filled[y,x] = new_val

        for dy,dx in [(-1,0),(1,0),(0,-1),(0,1)]:

            ny,nx = y+dy,x+dx

            if 0<=ny<h and 0<=nx<w and filled[ny,nx]==seed_val:

                queue.append((ny,nx))

    return filled



if __name__ == "__main__":

    np.random.seed(42)

    img = np.zeros((40,40))

    img[15:30,15:30] = 200

    img += np.random.randint(0,20,(40,40))

    seeds = [(20,20)]

    region = region_growing(img, seeds[0], 25)

    print(f"Region size: {len(region)} pixels")

    print("\n区域生长测试完成!")

