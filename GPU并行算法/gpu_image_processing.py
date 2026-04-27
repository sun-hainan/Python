# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_image_processing

本文件实现 gpu_image_processing 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba


def cpu_convolution_2d(image, kernel):
    """
    CPU 2D卷积（基准）
    
    参数:
        image: 输入图像
        kernel: 卷积核
    
    返回:
        卷积结果
    """
    kh, kw = kernel.shape
    ih, iw = image.shape
    out_h = ih - kh + 1
    out_w = iw - kw + 1
    
    result = np.zeros((out_h, out_w), dtype=np.float32)
    
    for i in range(out_h):
        for j in range(out_w):
            total = 0.0
            for ki in range(kh):
                for kj in range(kw):
                    total += image[i + ki, j + kj] * kernel[ki, kj]
            result[i, j] = total
    
    return result


@cuda.jit
def gpu_convolution_2d_kernel(image, kernel, result, kh, kw, out_h, out_w):
    """
    GPU 2D卷积内核
    
    参数:
        image: 输入图像
        kernel: 卷积核
        result: 输出结果
        kh, kw: 卷积核尺寸
        out_h, out_w: 输出尺寸
    """
    # 共享内存：缓存图像块
    # 每个block处理一块图像
    block_h = cuda.blockDim.y
    block_w = cuda.blockDim.x
    
    # 共享内存大小需要足够容纳整个tile
    shared_image = cuda.shared.array((18, 18), dtype=np.float32)
    
    # 线程在block内的坐标
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    
    # 线程对应的全局坐标
    global_x = cuda.blockIdx.x * block_w + tx
    global_y = cuda.blockIdx.y * block_h + ty
    
    # 加载图像到共享内存（带边界处理）
    if global_y < image.shape[0] and global_x < image.shape[1]:
        shared_image[ty, tx] = image[global_y, global_x]
    else:
        shared_image[ty, tx] = 0.0
    
    cuda.syncthreads()
    
    # 计算卷积（只让输出像素的线程参与）
    if global_y < out_h and global_x < out_w:
        total = 0.0
        
        # 卷积核应用
        for ki in range(kh):
            for kj in range(kw):
                # 需要从共享内存中读取
                img_y = ty + ki
                img_x = tx + kj
                
                # 边界检查
                if img_y < block_h + kh - 1 and img_x < block_w + kw - 1:
                    total += shared_image[img_y, img_x] * kernel[ki, kj]
        
        result[global_y, global_x] = total


@cuda.jit
def gpu_gaussian_blur_kernel(image, result, image_h, image_w):
    """
    GPU高斯模糊内核
    
    使用3x3高斯核:
    [1, 2, 1]
    [2, 4, 2] / 16
    [1, 2, 1]
    
    参数:
        image: 输入图像
        result: 输出图像
        image_h, image_w: 图像尺寸
    """
    shared_data = cuda.shared.array(18, dtype=numba.float32)
    
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    bx = cuda.blockIdx.x
    by = cuda.blockIdx.y
    
    # 每个block处理8x8的输出
    block_out_h = 8
    block_out_w = 8
    
    # 全局输出位置
    out_x = bx * block_out_w + tx
    out_y = by * block_out_h + ty
    
    # 加载数据到共享内存
    # 需要加载9x9的窗口
    shared_h = block_out_h + 2
    shared_w = block_out_w + 2
    
    if out_x < image_w and out_y < image_h:
        shared_data[ty * shared_w + tx] = image[out_y, out_x]
    
    cuda.syncthreads()
    
    # 应用高斯核
    if out_x < image_w - 1 and out_y < image_h - 1 and out_x > 0 and out_y > 0:
        # 高斯核权重
        total = (shared_data[(ty) * shared_w + tx] * 4.0 +
                 shared_data[(ty - 1) * shared_w + tx] * 2.0 +
                 shared_data[(ty + 1) * shared_w + tx] * 2.0 +
                 shared_data[ty * shared_w + tx - 1] * 2.0 +
                 shared_data[ty * shared_w + tx + 1] * 2.0 +
                 shared_data[(ty - 1) * shared_w + tx - 1] * 1.0 +
                 shared_data[(ty - 1) * shared_w + tx + 1] * 1.0 +
                 shared_data[(ty + 1) * shared_w + tx - 1] * 1.0 +
                 shared_data[(ty + 1) * shared_w + tx + 1] * 1.0) / 16.0
        
        result[out_y, out_x] = total


@cuda.jit
def gpu_edge_detection_kernel(image, result, image_h, image_w):
    """
    GPU边缘检测（Sobel算子）
    
    Sobel X方向:
    [-1, 0, 1]
    [-2, 0, 2]
    [-1, 0, 1]
    
    Sobel Y方向:
    [-1, -2, -1]
    [ 0,  0,  0]
    [ 1,  2,  1]
    
    参数:
        image: 输入灰度图像
        result: 输出边缘图像
        image_h, image_w: 图像尺寸
    """
    shared_data = cuda.shared.array(18, dtype=numba.float32)
    
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    bx = cuda.blockIdx.x
    by = cuda.blockIdx.y
    
    block_out_h = 8
    block_out_w = 8
    
    out_x = bx * block_out_w + tx
    out_y = by * block_out_h + ty
    
    shared_h = block_out_h + 2
    shared_w = block_out_w + 2
    
    # 加载数据
    if out_x < image_w and out_y < image_h:
        shared_data[ty * shared_w + tx] = image[out_y, out_x]
    
    cuda.syncthreads()
    
    # Sobel边缘检测
    if out_x > 0 and out_x < image_w - 1 and out_y > 0 and out_y < image_h - 1:
        gx = (-shared_data[(ty - 1) * shared_w + tx - 1] +
              shared_data[(ty - 1) * shared_w + tx + 1] +
              -2 * shared_data[ty * shared_w + tx - 1] +
              2 * shared_data[ty * shared_w + tx + 1] +
              -shared_data[(ty + 1) * shared_w + tx - 1] +
              shared_data[(ty + 1) * shared_w + tx + 1])
        
        gy = (-shared_data[(ty - 1) * shared_w + tx - 1] +
              -2 * shared_data[(ty - 1) * shared_w + tx] +
              -shared_data[(ty - 1) * shared_w + tx + 1] +
              shared_data[(ty + 1) * shared_w + tx - 1] +
              2 * shared_data[(ty + 1) * shared_w + tx] +
              shared_data[(ty + 1) * shared_w + tx + 1])
        
        result[out_y, out_x] = np.sqrt(gx * gx + gy * gy)


@cuda.jit
def gpu_histogram_equalization_kernel(image, hist, cdf, result, image_h, image_w, num_bins):
    """
    GPU直方图均衡化内核
    
    参数:
        image: 输入图像
        hist: 直方图
        cdf: 累积分布函数
        result: 输出图像
        image_h, image_w: 图像尺寸
        num_bins: bin数量
    """
    global_x = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    global_y = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    
    if global_x < image_w and global_y < image_h:
        pixel = image[global_y, global_x]
        
        # 找到对应的bin
        bin_idx = int(pixel * num_bins)
        if bin_idx >= num_bins:
            bin_idx = num_bins - 1
        if bin_idx < 0:
            bin_idx = 0
        
        # 使用CDF进行均衡化
        cdf_min = cdf[0]
        result[global_y, global_x] = (cdf[bin_idx] - cdf_min) / (image_h * image_w - cdf_min)


def run_demo():
    """运行图像处理演示"""
    print("=" * 60)
    print("GPU图像处理 - 卷积、滤波与直方图")
    print("=" * 60)
    
    # 创建测试图像
    image_h, image_w = 64, 64
    image = np.random.rand(image_h, image_w).astype(np.float32)
    
    # 定义卷积核（锐化）
    sharpen_kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ], dtype=np.float32)
    
    # CPU卷积基准
    print("\n[演示1] 卷积操作（锐化）:")
    cpu_result = cpu_convolution_2d(image, sharpen_kernel)
    print(f"  输入图像形状: {image.shape}")
    print(f"  卷积核形状: {sharpen_kernel.shape}")
    print(f"  CPU结果形状: {cpu_result.shape}")
    print(f"  CPU结果前5x5:\n{cpu_result[:5, :5]}")
    
    # GPU卷积
    d_image = cuda.to_device(image)
    d_kernel = cuda.to_device(sharpen_kernel)
    out_h = image_h - 3 + 1
    out_w = image_w - 3 + 1
    d_result = cuda.to_device(np.zeros((out_h, out_w), dtype=np.float32))
    
    threads = (8, 8)
    blocks = ((out_w + threads[1] - 1) // threads[1],
              (out_h + threads[0] - 1) // threads[0])
    
    gpu_convolution_2d_kernel[blocks, threads](d_image, d_kernel, d_result, 3, 3, out_h, out_w)
    gpu_result = d_result.copy_to_host()
    
    print(f"  GPU结果前5x5:\n{gpu_result[:5, :5]}")
    print(f"  最大误差: {np.max(np.abs(cpu_result - gpu_result)):.6f}")
    
    # 高斯模糊
    print("\n[演示2] 高斯模糊:")
    d_result = cuda.to_device(np.zeros((image_h, image_w), dtype=np.float32))
    threads = (8, 8)
    blocks = ((image_w + threads[1] - 1) // threads[1],
              (image_h + threads[0] - 1) // threads[0])
    gpu_gaussian_blur_kernel[blocks, threads](d_image, d_result, image_h, image_w)
    blur_result = d_result.copy_to_host()
    print(f"  模糊后图像均值: {np.mean(blur_result):.4f}")
    print(f"  原始图像均值: {np.mean(image):.4f}")
    
    # 边缘检测
    print("\n[演示3] Sobel边缘检测:")
    d_result = cuda.to_device(np.zeros((image_h, image_w), dtype=np.float32))
    gpu_edge_detection_kernel[blocks, threads](d_image, d_result, image_h, image_w)
    edge_result = d_result.copy_to_host()
    print(f"  边缘图像均值: {np.mean(edge_result):.4f}")
    print(f"  检测到边缘像素数: {np.sum(edge_result > 0.5)}")
    
    print("\n" + "=" * 60)
    print("GPU图像处理核心概念:")
    print("  1. 卷积: 共享内存缓存图像块，减少全局内存访问")
    print("  2. 滤波: 局域操作，适合GPU并行")
    print("  3. 直方图: 原子操作或局部聚合")
    print("  4. 优化: tile化处理，边界处理，共享内存复用")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
