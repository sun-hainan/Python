# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / fxaa



本文件实现 fxaa 相关的算法功能。

"""



import numpy as np





class FXAA:

    """

    Fast Approximate Anti-Aliasing



    参数:

        span_max: 边缘检测的最大距离（像素）

        reduce_min: 最小减少量

        reduce_mul: 减少乘数

    """



    def __init__(self, span_max=8.0, reduce_min=1.0/128.0, reduce_mul=1.0/8.0):

        """

        初始化 FXAA



        参数:

            span_max: 边缘搜索范围

            reduce_min: 最小步进

            reduce_mul: 步进乘数

        """

        self.span_max = span_max

        self.reduce_min = reduce_min

        self.reduce_mul = reduce_mul



    def luminance(self, pixel):

        """

        计算像素亮度



        使用 ITU-R BT.709 系数：

        L = 0.2126*R + 0.7152*G + 0.0722*B



        参数:

            pixel: RGB 颜色 [R, G, B]

        返回:

            luma: 亮度值

        """

        return 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]



    def get_luma_range(self, image, x, y, radius=1):

        """

        获取局部亮度范围



        参数:

            image: 输入图像 (H, W, 3)

            x, y: 中心坐标

            radius: 搜索半径

        返回:

            luma_min, luma_max, luma_center

        """

        h, w = image.shape[:2]

        luma_min = float('inf')

        luma_max = -float('inf')

        luma_center = self.luminance(image[y, x])



        for dy in range(-radius, radius + 1):

            for dx in range(-radius, radius + 1):

                nx, ny = x + dx, y + dy

                if 0 <= nx < w and 0 <= ny < h:

                    luma = self.luminance(image[ny, nx])

                    luma_min = min(luma_min, luma)

                    luma_max = max(luma_max, luma)



        return luma_min, luma_max, luma_center



    def apply_fxaa(self, image):

        """

        对整个图像应用 FXAA



        参数:

            image: 输入图像 (H, W, 3)，RGB

        返回:

            output: 抗锯齿后的图像

        """

        h, w = image.shape[:2]

        output = image.copy()



        for y in range(1, h - 1):

            for x in range(1, w - 1):

                output[y, x] = self._fxaa_pixel(image, x, y)



        return output



    def _fxaa_pixel(self, image, x, y):

        """

        对单个像素应用 FXAA



        参数:

            image: 输入图像

            x, y: 像素坐标

        返回:

            RGB: 平滑后的颜色

        """

        # 获取 3x3 邻域的亮度

        luma = []

        for dy in range(-1, 2):

            for dx in range(-1, 2):

                luma.append(self.luminance(image[y + dy, x + dx]))



        # 布局：

        #   [0] [1] [2]

        #   [3] [4] [5]

        #   [6] [7] [8]

        luma_center = luma[4]

        luma_N = luma[1]

        luma_S = luma[7]

        luma_E = luma[5]

        luma_W = luma[3]



        # 计算亮度梯度

        gradient_N = abs(luma_N - luma_center)

        gradient_S = abs(luma_S - luma_center)

        gradient_E = abs(luma_E - luma_center)

        gradient_W = abs(luma_W - luma_center)



        # 确定主边缘方向

        is_horizontal = gradient_N + gradient_S > gradient_E + gradient_W



        # 边缘强度

        edge_strength = max(gradient_N, gradient_S, gradient_E, gradient_W)



        # 如果不是边缘，直接返回

        if edge_strength < 0.02:

            return image[y, x]



        # 确定搜索方向

        if is_horizontal:

            # 水平边缘，沿垂直方向搜索

            edge_sign = 1.0 if luma_S > luma_N else -1.0

            gradient = gradient_N + gradient_S

        else:

            # 垂直边缘，沿水平方向搜索

            edge_sign = 1.0 if luma_E > luma_W else -1.0

            gradient = gradient_E + gradient_W



        # 计算步进方向

        if is_horizontal:

            x_off = 1

            y_off = 0

            length_sign = image.shape[1]  # 水平方向更长

        else:

            x_off = 0

            y_off = 1

            length_sign = image.shape[0]  # 垂直方向更长



        # 计算初始步进

        gradient *= edge_sign

        pixel_pos = x + x_off, y + y_off

        pixel_neg = x - x_off, y - y_off



        # 沿边缘方向搜索最大亮度变化

        luma_neg = 0.5 * (luma_center + self.luminance(image[pixel_neg[1], pixel_neg[0]]))

        luma_pos = 0.5 * (luma_center + self.luminance(image[pixel_pos[1], pixel_pos[0]]))



        gradient_scaled = max(0.0, gradient) * self.reduce_mul

        span_length = (luma_neg + luma_pos) * 0.5

        span_length = max(span_length, self.reduce_min)



        # 检测端点

        should_terminate = False

        if (luma_neg < span_length) != (luma_pos < span_length):

            should_terminate = True



        if not should_terminate:

            # 继续搜索

            step = self.reduce_mul

            for i in range(int(self.span_max)):

                if gradient_scaled < 1.0 / float(i + 1):

                    break



                pixel_pos = (x + x_off * (i + 1), y + y_off * (i + 1))

                luma_pos = self.luminance(image[pixel_pos[1], pixel_pos[0]])



                if (luma_neg < span_length) != (luma_pos < span_length):

                    break



                pixel_neg = (x - x_off * (i + 1), y - y_off * (i + 1))

                luma_neg = self.luminance(image[pixel_neg[1], pixel_neg[0]])



                if (luma_neg < span_length) != (luma_pos < span_length):

                    break



        # 计算亚像素偏移

        if is_horizontal:

            offset_mul = abs(luma_S - luma_center)

            offset_denom = gradient_N + gradient_S + 2 * abs(luma_center - 0.5 * (luma_N + luma_S))

        else:

            offset_mul = abs(luma_E - luma_center)

            offset_denom = gradient_E + gradient_W + 2 * abs(luma_center - 0.5 * (luma_E + luma_W))



        if offset_denom > 0:

            offset_mul = min(offset_mul, offset_denom)



        offset = offset_mul / max(offset_denom, 1e-10) * edge_sign * 0.5



        # 最终采样位置

        fx = x + offset * x_off

        fy = y + offset * y_off



        # 双线性插值采样

        fx_i = int(fx)

        fy_i = int(fy)

        fx_f = fx - fx_i

        fy_f = fy - fy_i



        fx_i = max(0, min(fx_i, image.shape[1] - 1))

        fy_i = max(0, min(fy_i, image.shape[0] - 1))

        fx_i1 = min(fx_i + 1, image.shape[1] - 1)

        fy_i1 = min(fy_i + 1, image.shape[0] - 1)



        # 双线性插值

        c00 = image[fy_i, fx_i]

        c10 = image[fy_i, fx_i1]

        c01 = image[fy_i1, fx_i]

        c11 = image[fy_i1, fx_i1]



        c0 = c00 * (1 - fx_f) + c10 * fx_f

        c1 = c01 * (1 - fx_f) + c11 * fx_f

        result = c0 * (1 - fy_f) + c1 * fy_f



        return np.clip(result, 0, 1)





class SimpleEdgeDetection:

    """简单的边缘检测（用于验证）"""



    def __init__(self, threshold=0.1):

        self.threshold = threshold



    def detect_edges(self, image):

        """

        检测边缘



        参数:

            image: 灰度图像或 RGB

        返回:

            edges: 边缘掩码

        """

        if len(image.shape) == 3:

            # RGB 转灰度

            gray = 0.2126 * image[:, :, 0] + 0.7152 * image[:, :, 1] + 0.0722 * image[:, :, 2]

        else:

            gray = image



        h, w = gray.shape

        edges = np.zeros_like(gray)



        # Sobel 算子

        for y in range(1, h - 1):

            for x in range(1, w - 1):

                gx = (-gray[y-1, x-1] - 2*gray[y, x-1] - gray[y+1, x-1] +

                      gray[y-1, x+1] + 2*gray[y, x+1] + gray[y+1, x+1])

                gy = (-gray[y-1, x-1] - 2*gray[y-1, x] - gray[y-1, x+1] +

                      gray[y+1, x-1] + 2*gray[y+1, x] + gray[y+1, x+1])

                magnitude = np.sqrt(gx**2 + gy**2)

                if magnitude > self.threshold:

                    edges[y, x] = magnitude



        return edges





def create_test_image(size=64):

    """

    创建测试图像（带有锯齿边缘）



    参数:

        size: 图像大小

    返回:

        image: 测试图像

    """

    image = np.zeros((size, size, 3))



    # 白色背景

    image[:] = [1.0, 1.0, 1.0]



    # 黑色斜线（会产生锯齿）

    for y in range(size):

        x = int(y * 0.7)

        if x < size:

            image[y, x:x+2] = [0, 0, 0]



    # 圆形

    cx, cy = size // 2, size // 2

    radius = size // 3

    for y in range(size):

        for x in range(size):

            dist = np.sqrt((x - cx)**2 + (y - cy)**2)

            if abs(dist - radius) < 1.5:

                image[y, x] = [0, 0, 0]



    # 棋盘格（高频率细节）

    checker_size = 4

    for y in range(size):

        for x in range(size):

            if ((x // checker_size) + (y // checker_size)) % 2 == 0:

                image[y, x] = [0, 0, 0]



    return image





def measure_aliasing(image):

    """

    测量图像的锯齿程度



    通过计算相邻像素的亮度差异。

    """

    gray = 0.2126 * image[:, :, 0] + 0.7152 * image[:, :, 1] + 0.0722 * image[:, :, 2]



    total_variation = 0.0

    count = 0



    for y in range(1, gray.shape[0] - 1):

        for x in range(1, gray.shape[1] - 1):

            # 水平变化

            h_diff = abs(gray[y, x] - gray[y, x + 1])

            # 垂直变化

            v_diff = abs(gray[y, x] - gray[y + 1, x])

            total_variation += h_diff + v_diff

            count += 2



    return total_variation / count if count > 0 else 0.0





if __name__ == "__main__":

    print("=== FXAA 测试 ===")



    # 创建测试图像

    print("\n1. 创建测试图像")

    test_image = create_test_image(64)

    print(f"图像尺寸: {test_image.shape}")



    aliasing_before = measure_aliasing(test_image)

    print(f"处理前锯齿程度: {aliasing_before:.4f}")



    # 应用 FXAA

    print("\n2. 应用 FXAA")

    fxaa = FXAA(span_max=8.0)

    result = fxaa.apply_fxaa(test_image)



    aliasing_after = measure_aliasing(result)

    print(f"处理后锯齿程度: {aliasing_after:.4f}")

    print(f"改善: {(aliasing_before - aliasing_after) / aliasing_before * 100:.1f}%")



    # 边缘检测验证

    print("\n3. 边缘检测验证")

    detector = SimpleEdgeDetection(threshold=0.05)

    edges_before = detector.detect_edges(test_image)

    edges_after = detector.detect_edges(result)

    print(f"处理前边缘像素数: {np.sum(edges_before > 0.1)}")

    print(f"处理后边缘像素数: {np.sum(edges_after > 0.1)}")



    # 不同参数测试

    print("\n4. 不同参数测试")

    for span_max in [4.0, 8.0, 12.0]:

        fxaa_test = FXAA(span_max=span_max)

        result_test = fxaa_test.apply_fxaa(test_image)

        aliasing_test = measure_aliasing(result_test)

        print(f"  span_max={span_max}: 锯齿程度={aliasing_test:.4f}")



    # 单像素测试

    print("\n5. 单像素 FXAA 处理示例")

    center_pixel = test_image[32, 32]

    center_neighbors = test_image[30:33, 30:33]

    print(f"中心像素 RGB: {center_pixel}")

    print(f"3x3 邻域亮度: {fxaa.luminance(center_neighbors)}")



    luma_min, luma_max, luma_c = fxaa.get_luma_range(test_image, 32, 32)

    print(f"局部亮度范围: [{luma_min:.3f}, {luma_max:.3f}], center={luma_c:.3f}")



    # 性能测试

    print("\n6. 性能测试")

    import time



    sizes = [64, 128, 256]

    for size in sizes:

        img = create_test_image(size)

        fxaa_test = FXAA()



        start = time.time()

        result_test = fxaa_test.apply_fxaa(img)

        elapsed = time.time() - start



        print(f"  {size}x{size}: {elapsed*1000:.2f}ms ({elapsed/img.size*1e6:.2f}us/像素)")



    print("\nFXAA 测试完成!")

