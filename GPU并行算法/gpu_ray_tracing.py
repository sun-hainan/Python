# -*- coding: utf-8 -*-

"""

算法实现：GPU并行算法 / gpu_ray_tracing



本文件实现 gpu_ray_tracing 相关的算法功能。

"""



import numpy as np

from numba import cuda

import numba

import math





@cuda.jit

def gpu_ray_triangle_kernel(origins, directions, vertices, indices, 

                            output_color, width, height, num_rays):

    """

    GPU光线-三角形相交检测内核

    

    光线投射（Ray Casting）：

    - 每个像素发射一条光线

    - 找到光线与场景的最近交点

    - 根据法线计算颜色

    

    参数:

        origins: 光线起点数组

        directions: 光线方向数组

        vertices: 三角形顶点

        indices: 三角形索引

        output_color: 输出颜色

        width, height: 图像尺寸

        num_rays: 光线数量

    """

    # 每个线程处理一个像素/光线

    pixel_x = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x

    pixel_y = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y

    

    if pixel_x >= width or pixel_y >= height:

        return

    

    # 计算全局光线索引

    ray_idx = pixel_y * width + pixel_x

    if ray_idx >= num_rays:

        return

    

    # 获取光线参数

    ox = origins[ray_idx * 3 + 0]

    oy = origins[ray_idx * 3 + 1]

    oz = origins[ray_idx * 3 + 2]

    

    dx = directions[ray_idx * 3 + 0]

    dy = directions[ray_idx * 3 + 1]

    dz = directions[ray_idx * 3 + 2]

    

    # 光线-场景相交检测

    t_min = 1e10

    hit_normal_x = 0.0

    hit_normal_y = 1.0

    hit_normal_z = 0.0

    

    # 简化的平面相交（假设场景是地面+几个球体）

    # 地面: y = -1

    if abs(dy) > 1e-6:

        t = (-1.0 - oy) / dy

        if t > 0 and t < t_min:

            hit_x = ox + dx * t

            hit_z = oz + dz * t

            # 棋盘格纹理

            if (int(hit_x) + int(hit_z)) % 2 == 0:

                t_min = t

                hit_normal_y = 1.0

    

    # 球体: 简化为距离检验

    # 球体1: 中心(0, 0, 3), 半径1

    sphere_x, sphere_y, sphere_z = 0.0, 0.0, 3.0

    sphere_r = 1.0

    

    # 光线-球体相交

    oc_x = ox - sphere_x

    oc_y = oy - sphere_y

    oc_z = oz - sphere_z

    

    a = dx * dx + dy * dy + dz * dz

    b = 2.0 * (oc_x * dx + oc_y * dy + oc_z * dz)

    c = oc_x * oc_x + oc_y * oc_y + oc_z * oc_z - sphere_r * sphere_r

    

    discriminant = b * b - 4 * a * c

    if discriminant > 0:

        t = (-b - math.sqrt(discriminant)) / (2.0 * a)

        if t > 0 and t < t_min:

            t_min = t

            hit_x = ox + dx * t

            hit_y = oy + dy * t

            hit_z = oz + dz * t

            hit_normal_x = (hit_x - sphere_x) / sphere_r

            hit_normal_y = (hit_y - sphere_y) / sphere_r

            hit_normal_z = (hit_z - sphere_z) / sphere_r

    

    # 计算颜色

    if t_min < 1e10:

        # 光照计算

        light_x, light_y, light_z = 5.0, 10.0, 5.0

        lx = light_x - (ox + dx * t_min)

        ly = light_y - (oy + dy * t_min)

        lz = light_z - (oz + dz * t_min)

        llen = math.sqrt(lx * lx + ly * ly + lz * lz)

        lx /= llen

        ly /= llen

        lz /= llen

        

        # 法线与光线点积

        nx = hit_normal_x

        ny = hit_normal_y

        nz = hit_normal_z

        

        diffuse = max(0.0, nx * lx + ny * ly + nz * lz)

        

        # 环境光 + 漫反射

        color = 0.1 + 0.9 * diffuse

        

        # 阴影

        shadow_origin_x = ox + dx * t_min + nx * 1e-4

        shadow_origin_y = oy + dy * t_min + ny * 1e-4

        shadow_origin_z = oz + dz * t_min + nz * 1e-4

        

        # 简单阴影检测

        shadow_t = -1.0

        if abs(ly) > 1e-6:

            shadow_t = (-1.0 - shadow_origin_y) / ly

        

        if shadow_t > 0 and shadow_t < llen:

            color *= 0.5

        

        output_color[ray_idx * 3 + 0] = color

        output_color[ray_idx * 3 + 1] = color

        output_color[ray_idx * 3 + 2] = color

    else:

        # 背景色（渐变蓝）

        output_color[ray_idx * 3 + 0] = 0.3

        output_color[ray_idx * 3 + 1] = 0.5

        output_color[ray_idx * 3 + 2] = 0.9





@cuda.jit

def gpu_ambient_occlusion_kernel(hit_points, normals, ao_values, num_points, samples):

    """

    GPU环境光遮蔽计算

    

    环境光遮蔽（AO）：

    - 估算某点被环境光照射的程度

    - 在凹陷区域减少光照

    - 提高真实感

    

    参数:

        hit_points: 命中点位置

        normals: 命中点法线

        ao_values: AO结果输出

        num_points: 点的数量

        samples: 采样数量

    """

    point_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x

    

    if point_idx >= num_points:

        return

    

    px = hit_points[point_idx * 3 + 0]

    py = hit_points[point_idx * 3 + 1]

    pz = hit_points[point_idx * 3 + 2]

    

    nx = normals[point_idx * 3 + 0]

    ny = normals[point_idx * 3 + 1]

    nz = normals[point_idx * 3 + 2]

    

    occluded = 0

    

    # 简化的AO计算

    for i in range(samples):

        # 随机方向（简化）

        theta = float(i) / float(samples) * 2.0 * 3.14159

        phi = float(i * 3) / float(samples) * 2.0 * 3.14159

        

        dir_x = math.sin(theta) * math.cos(phi)

        dir_y = math.cos(theta)

        dir_z = math.sin(theta) * math.sin(phi)

        

        # 检查是否在法线同侧

        if dir_x * nx + dir_y * ny + dir_z * nz > 0:

            # 简化的遮挡检测

            # 假设地面在y=-1

            if abs(dir_y) > 1e-6:

                t = (-1.0 - py) / dir_y

                if t > 0 and t < 10.0:

                    hit_x = px + dir_x * t

                    hit_z = pz + dir_z * t

                    # 检查是否在某个物体附近

                    if hit_x * hit_x + hit_z * hit_z < 10.0:

                        occluded += 1

    

    ao_values[point_idx] = 1.0 - float(occluded) / float(samples)





def cpu_ray_tracer_simple(width, height, camera_x, camera_y, camera_z):

    """

    CPU光线追踪（简化版本，用于对比）

    

    参数:

        width, height: 图像尺寸

        camera_x/y/z: 相机位置

    

    返回:

        图像数据

    """

    image = np.zeros((height, width, 3), dtype=np.float32)

    

    for py in range(height):

        for px in range(width):

            # 计算光线方向

            dx = (px / width) * 2 - 1

            dy = (py / height) * 2 - 1

            dz = 1.0

            

            # 简化的着色

            image[py, px, 0] = 0.3 + 0.1 * (1 - dy)

            image[py, px, 1] = 0.5 + 0.1 * (1 - dy)

            image[py, px, 2] = 0.9 - 0.2 * (1 - dy)

    

    return image





def gpu_ray_tracer(width, height):

    """

    GPU光线追踪主函数

    

    参数:

        width, height: 图像尺寸

    

    返回:

        渲染图像

    """

    num_pixels = width * height

    

    # 光线起点（相机位置）

    origins = np.zeros(num_pixels * 3, dtype=np.float32)

    for i in range(num_pixels):

        origins[i * 3 + 0] = 0.0  # x

        origins[i * 3 + 1] = 0.0  # y

        origins[i * 3 + 2] = 0.0  # z

    

    # 光线方向（从每个像素出发）

    directions = np.zeros(num_pixels * 3, dtype=np.float32)

    for py in range(height):

        for px in range(width):

            idx = py * width + px

            # 归一化方向

            dx = (px / width) * 2 - 1

            dy = (py / height) * 2 - 1

            dz = 1.0

            dlen = math.sqrt(dx * dx + dy * dy + dz * dz)

            directions[idx * 3 + 0] = dx / dlen

            directions[idx * 3 + 1] = dy / dlen

            directions[idx * 3 + 2] = dz / dlen

    

    # 输出颜色

    output_color = np.zeros(num_pixels * 3, dtype=np.float32)

    

    # 三角形顶点和索引（简化）

    num_vertices = 3

    vertices = np.zeros(num_vertices * 3, dtype=np.float32)

    indices = np.zeros(3, dtype=np.int32)

    

    # 传输到GPU

    d_origins = cuda.to_device(origins)

    d_directions = cuda.to_device(directions)

    d_vertices = cuda.to_device(vertices)

    d_indices = cuda.to_device(indices)

    d_output = cuda.to_device(output_color)

    

    # 配置grid和block

    threads = (16, 16)

    blocks = ((width + threads[0] - 1) // threads[0],

              (height + threads[1] - 1) // threads[1])

    

    # 执行内核

    gpu_ray_triangle_kernel[blocks, threads](

        d_origins, d_directions, d_vertices, d_indices,

        d_output, width, height, num_pixels

    )

    

    # 复制结果

    output_color = d_output.copy_to_host()

    

    # 重排为图像格式

    image = np.zeros((height, width, 3), dtype=np.float32)

    for py in range(height):

        for px in range(width):

            idx = py * width + px

            image[py, px, 0] = output_color[idx * 3 + 0]

            image[py, px, 1] = output_color[idx * 3 + 1]

            image[py, px, 2] = output_color[idx * 3 + 2]

    

    return image





def run_demo():

    """运行光线追踪演示"""

    print("=" * 60)

    print("GPU并行算法：光线追踪渲染")

    print("=" * 60)

    

    # 渲染设置

    width, height = 64, 64

    

    print(f"\n渲染设置: {width}×{height} 像素")

    

    # GPU渲染

    print("\n[GPU光线追踪]")

    try:

        import time

        start = time.time()

        image_gpu = gpu_ray_tracer(width, height)

        gpu_time = time.time() - start

        print(f"  渲染时间: {gpu_time:.4f}秒")

        print(f"  输出形状: {image_gpu.shape}")

        print(f"  像素值范围: [{np.min(image_gpu):.2f}, {np.max(image_gpu):.2f}]")

    except Exception as e:

        print(f"  GPU渲染失败: {e}")

    

    # CPU对比

    print("\n[CPU光线追踪（简化）]")

    start = time.time()

    image_cpu = cpu_ray_tracer_simple(width, height, 0, 0, 0)

    cpu_time = time.time() - start

    print(f"  渲染时间: {cpu_time:.4f}秒")

    

    # 性能对比

    if 'gpu_time' in dir() and gpu_time > 0:

        speedup = cpu_time / gpu_time if gpu_time > 0 else float('inf')

        print(f"\n[性能对比]")

        print(f"  GPU时间: {gpu_time:.4f}秒")

        print(f"  CPU时间: {cpu_time:.4f}秒")

        print(f"  加速比: {speedup:.2f}x")

    

    print("\n" + "=" * 60)

    print("光线追踪核心概念:")

    print("  1. 光线投射: 从眼睛通过每个像素发射光线")

    print("  2. 光线-物体相交: 找到最近交点")

    print("  3. 着色模型: 环境光+漫反射+镜面反射")

    print("  4. GPU并行: 每个像素独立计算")

    print("  5. 优化: 包围盒、空间分割、共享内存缓存")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

