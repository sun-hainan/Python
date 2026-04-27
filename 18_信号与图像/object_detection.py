# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / object_detection



本文件实现 object_detection 相关的算法功能。

"""



import numpy as np



def sliding_window(image, window_size, step=1):

    h,w = image.shape

    wy,wx = window_size

    windows = []

    positions = []

    for y in range(0, h-wy+1, step):

        for x in range(0, w-wx+1, step):

            windows.append(image[y:y+wy, x:x+wx])

            positions.append((y,x))

    return windows, positions



def non_max_suppression(boxes, scores, threshold=0.3):

    if len(boxes)==0: return []

    indices = np.argsort(scores)[::-1]

    keep = []

    while len(indices)>0:

        i = indices[0]

        keep.append(i)

        indices = [j for j in indices[1:] if np.max(np.abs(boxes[i]-boxes[j])) < threshold]

    return [boxes[i] for i in keep]



if __name__ == "__main__":

    np.random.seed(42)

    img = np.random.randint(0,256,(60,60))

    wins,pos = sliding_window(img, (15,15), step=5)

    print(f"Generated {len(wins)} windows")

    boxes = [(10,10,30,30),(12,12,28,28),(50,50,60,60)]

    scores = [0.9, 0.8, 0.7]

    suppressed = non_max_suppression(boxes, scores, 5)

    print(f"After NMS: {len(suppressed)} boxes")

    print("\n目标检测测试完成!")

