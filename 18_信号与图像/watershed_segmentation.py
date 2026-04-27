# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / watershed_segmentation



本文件实现 watershed_segmentation 相关的算法功能。

"""



import numpy as np

from collections import deque





class Watershed:

    """

    分水岭分割

    """



    # 标记

    MASK = -2  # 未访问

    WSHED = 0  # 分水岭

    INIT = -1  # 初始

    INQUEUE = -3  # 在队列中



    def __init__(self):

        self.label = None

        self.distance = None

        self.output = None



    def watershed(self, image):

        """

        分水岭分割



        参数:

            image: 输入图像（灰度）

        返回:

            labels: 分割标签

        """

        image = np.array(image, dtype=float)

        h, w = image.shape



        # 初始化

        self.output = np.zeros((h, w), dtype=int)

        self.label = np.zeros((h, w), dtype=int)

        self.distance = np.zeros((h, w), dtype=float)



        # 队列

        queue = deque()



        # 按灰度排序像素

        indices = np.argsort(image.flatten()).reshape(h, w)



        # 第一遍：初始化

        for idx in indices:

            y, x = np.where(indices == idx)

            y, x = y[0], x[0]

            pixel = image[y, x]

            neighbors = self._get_neighbors(y, x, h, w)



            # 检查是否是邻域中有更高灰度的像素

            has_higher = False

            for ny, nx in neighbors:

                if image[ny, nx] > pixel:

                    has_higher = True

                    break



            if has_higher:

                # 标记为分水岭候选

                self.label[y, x] = self.WSHED

            else:

                self.label[y, x] = self.INIT



        # 按灰度升高处理

        current_label = 0

        current_distance = 1



        for idx in range(len(indices.flatten())):

            y, x = np.unravel_index(indices.flatten()[idx], (h, w))

            pixel = image[y, x]

            self.label[y, x] = self.MASK



            # 检查邻域中是否有标签的像素

            labeled_neighbors = []

            for ny, nx in self._get_neighbors(y, x, h, w):

                if self.label[ny, nx] > 0:

                    labeled_neighbors.append((ny, nx, self.label[ny, nx]))



            if labeled_neighbors:

                # 有标签邻居

                # 分配标签

                min_label = min(n[2] for n in labeled_neighbors)

                self.label[y, x] = min_label



                # 检查是否需要创建新标签

                unique_labels = set(n[2] for n in labeled_neighbors)

                if len(unique_labels) > 1:

                    # 分水岭脊线

                    for ny, nx, l in labeled_neighbors:

                        if l != min_label:

                            # 这两个标签会分开

                            pass



        return self.label



    def watershed_marker(self, image, markers):

        """

        标记控制分水岭



        参数:

            image: 输入图像

            markers: 标记图像（种子点）

        返回:

            labels: 分割结果

        """

        image = np.array(image, dtype=float)

        markers = np.array(markers, dtype=int)

        h, w = image.shape



        # 初始化

        labels = np.zeros((h, w), dtype=int)

        queue = deque()



        # 初始化标记

        current_label = 1

        for y in range(h):

            for x in range(w):

                if markers[y, x] > 0:

                    labels[y, x] = current_label

                    queue.append((y, x))

                    current_label += 1



        # BFS 洪水填充

        while queue:

            y, x = queue.popleft()

            current_label = labels[y, x]

            current_val = image[y, x]



            for ny, nx in self._get_neighbors(y, x, h, w):

                if labels[ny, nx] == 0 and abs(image[ny, nx] - current_val) < 10:

                    # 相邻且灰度接近

                    labels[ny, nx] = current_label

                    queue.append((ny, nx))



        return labels



    def _get_neighbors(self, y, x, h, w):

        """获取4邻域"""

        neighbors = []

        if y > 0: neighbors.append((y - 1, x))

        if y < h - 1: neighbors.append((y + 1, x))

        if x > 0: neighbors.append((y, x - 1))

        if x < w - 1: neighbors.append((y, x + 1))

        return neighbors





class DistanceTransform:

    """

    距离变换



    计算每个像素到最近零像素的距离。

    """



    @staticmethod

    def euclidean(image):

        """

        欧几里得距离变换



        参数:

            image: 二值图像（0=背景，1=前景）

        返回:

            distance: 距离图像

        """

        h, w = image.shape

        distance = np.zeros_like(image, dtype=float)



        # 两遍扫描

        # 第一遍：从左上到右下

        for y in range(h):

            for x in range(w):

                if image[y, x] == 0:

                    d = 0

                else:

                    d = float('inf')

                    if y > 0:

                        d = min(d, distance[y - 1, x] + 1)

                    if x > 0:

                        d = min(d, distance[y, x - 1] + 1)

                distance[y, x] = d



        # 第二遍：从右下到左上

        for y in range(h - 1, -1, -1):

            for x in range(w - 1, -1, -1):

                d = distance[y, x]

                if y < h - 1:

                    d = min(d, distance[y + 1, x] + 1)

                if x < w - 1:

                    d = min(d, distance[y, x + 1] + 1)

                distance[y, x] = d



        return distance





def find_local_maxima(image, threshold=0.5):

    """

    找到局部最大值（用于种子点检测）



    参数:

        image: 输入图像

        threshold: 阈值（0-1，相对于最大值）

    返回:

        maxima: 局部最大值位置

    """

    image = np.array(image, dtype=float)

    h, w = image.shape



    max_val = np.max(image)

    threshold_val = threshold * max_val



    maxima = []

    for y in range(1, h - 1):

        for x in range(1, w - 1):

            if image[y, x] >= threshold_val:

                is_max = True

                for ny in range(y - 1, y + 2):

                    for nx in range(x - 1, x + 2):

                        if (ny, nx) != (y, x) and image[ny, nx] > image[y, x]:

                            is_max = False

                            break

                    if not is_max:

                        break

                if is_max:

                    maxima.append((y, x, image[y, x]))



    # 按强度排序

    maxima.sort(key=lambda x: x[2], reverse=True)

    return maxima





def create_markers_from_seeds(image, seeds):

    """

    从种子点创建标记图像



    参数:

        image: 输入图像

        seeds: 种子点列表 [(y, x, label), ...]

    返回:

        markers: 标记图像

    """

    h, w = image.shape

    markers = np.zeros((h, w), dtype=int)



    for y, x, label in seeds:

        if 0 <= y < h and 0 <= x < w:

            markers[y, x] = label



    return markers





def apply_watershed(image, seeds):

    """

    完整的分水岭分割流程



    参数:

        image: 输入图像

        seeds: 种子点列表

    返回:

        segments: 分割结果

    """

    ws = Watershed()



    # 创建标记

    markers = create_markers_from_seeds(image, seeds)



    # 分水岭

    segments = ws.watershed_marker(image, markers)



    return segments





if __name__ == "__main__":

    print("=== 分水岭分割测试 ===")



    # 创建测试图像

    print("\n1. 创建测试图像")

    image = np.zeros((50, 50))

    image[10:20, 10:20] = 100

    image[30:40, 30:40] = 150

    image[15:35, 15:35] = 200

    print(f"图像尺寸: {image.shape}")

    print(f"灰度范围: [{np.min(image):.0f}, {np.max(image):.0f}]")



    # 分水岭分割

    print("\n2. 分水岭分割")

    ws = Watershed()



    # 定义种子点

    seeds = [

        (15, 15, 1),  # 第一个区域种子

        (35, 35, 2),  # 第二个区域种子

    ]



    markers = create_markers_from_seeds(image, seeds)

    print(f"种子点: {len(seeds)}")

    print(f"标记值: {np.unique(markers)}")



    segments = ws.watershed_marker(image, markers)

    print(f"分割区域数: {len(np.unique(segments)) - (1 if 0 in segments else 0)}")



    # 距离变换

    print("\n3. 距离变换")

    binary = (image > 100).astype(int)

    dist = DistanceTransform.euclidean(binary)

    print(f"距离范围: [{np.min(dist):.2f}, {np.max(dist):.2f}]")



    # 局部最大值

    print("\n4. 局部最大值检测")

    maxima = find_local_maxima(dist, threshold=0.5)

    print(f"找到 {len(maxima)} 个局部最大值")

    for i, (y, x, val) in enumerate(maxima[:5]):

        print(f"  极大值 {i+1}: 位置=({y}, {x}), 值={val:.2f}")



    # 标记控制分水岭

    print("\n5. 标记控制分水岭")

    seeds_from_maxima = [(y, x, i+1) for i, (y, x, _) in enumerate(maxima[:3])]

    if seeds_from_maxima:

        markers2 = create_markers_from_seeds(image, seeds_from_maxima)

        segments2 = ws.watershed_marker(image, markers2)

        print(f"分割区域数: {len(np.unique(segments2)) - (1 if 0 in segments2 else 0)}")



    # 分割结果统计

    print("\n6. 分割结果统计")

    for label in np.unique(segments2):

        mask = segments2 == label

        count = np.sum(mask)

        print(f"  区域 {label}: {count} 像素")



    print("\n分水岭分割测试完成!")

