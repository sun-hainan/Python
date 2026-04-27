# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / video_compression



本文件实现 video_compression 相关的算法功能。

"""



import numpy as np

import math





class FrameDifferencing:

    """

    帧差分压缩



    基础的时间冗余压缩方法。

    """



    def __init__(self, keyframe_interval=30):

        """

        初始化帧差分



        参数:

            keyframe_interval: 关键帧间隔

        """

        self.keyframe_interval = keyframe_interval

        self.previous_frame = None

        self.frame_count = 0



    def compress_frame(self, frame):

        """

        压缩单帧



        参数:

            frame: 当前帧

        返回:

            compressed: 压缩数据

        """

        if self.previous_frame is None or self.frame_count % self.keyframe_interval == 0:

            # 关键帧

            compressed = {

                'type': 'I',

                'data': frame.tobytes() if hasattr(frame, 'tobytes') else frame

            }

        else:

            # P 帧：差分

            diff = frame.astype(float) - self.previous_frame.astype(float)

            mse = np.mean(diff**2)

            compressed = {

                'type': 'P',

                'diff': diff,

                'mse': mse

            }



        self.previous_frame = frame.copy()

        self.frame_count += 1



        return compressed



    def decompress_frame(self, compressed, reference=None):

        """

        解压缩帧



        参数:

            compressed: 压缩数据

            reference: 参考帧

        返回:

            frame: 解压后帧

        """

        if compressed['type'] == 'I':

            if isinstance(compressed['data'], bytes):

                frame = np.frombuffer(compressed['data'], dtype=np.uint8).reshape(-1, -1)

            else:

                frame = compressed['data']

        else:

            frame = reference.astype(float) + compressed['diff']

            frame = np.clip(frame, 0, 255).astype(np.uint8)



        return frame





class BlockMotionEstimation:

    """

    块运动估计



    将帧划分为块，搜索最佳匹配块。

    """



    def __init__(self, block_size=16, search_range=16):

        """

        初始化运动估计



        参数:

            block_size: 块大小

            search_range: 搜索范围

        """

        self.block_size = block_size

        self.search_range = search_range



    def estimate(self, current_frame, reference_frame):

        """

        运动估计



        参数:

            current_frame: 当前帧

            reference_frame: 参考帧

        返回:

            motion_vectors: 运动矢量图

            residuals: 残差

        """

        h, w = current_frame.shape[:2]

        bs = self.block_size



        # 计算块数

        n_blocks_h = h // bs

        n_blocks_w = w // bs



        motion_vectors = np.zeros((n_blocks_h, n_blocks_w, 2), dtype=int)

        residuals = np.zeros_like(current_frame)



        for i in range(n_blocks_h):

            for j in range(n_blocks_w):

                # 当前块

                y = i * bs

                x = j * bs

                current_block = current_frame[y:y+bs, x:x+bs]



                # 搜索最佳匹配

                best_mv = (0, 0)

                best_mse = float('inf')



                for dy in range(-self.search_range, self.search_range + 1):

                    for dx in range(-self.search_range, self.search_range + 1):

                        ref_y = y + dy

                        ref_x = x + dx



                        if 0 <= ref_y < h - bs and 0 <= ref_x < w - bs:

                            ref_block = reference_frame[ref_y:ref_y+bs, ref_x:ref_x+bs]

                            mse = np.mean((current_block.astype(float) - ref_block.astype(float))**2)



                            if mse < best_mse:

                                best_mse = mse

                                best_mv = (dy, dx)



                motion_vectors[i, j] = best_mv



                # 计算残差

                ref_y, ref_x = y + best_mv[0], x + best_mv[1]

                ref_block = reference_frame[ref_y:ref_y+bs, ref_x:ref_x+bs]

                residuals[y:y+bs, x:x+bs] = current_block.astype(float) - ref_block.astype(float)



        return motion_vectors, residuals



    def compensate(self, reference_frame, motion_vectors):

        """

        运动补偿



        参数:

            reference_frame: 参考帧

            motion_vectors: 运动矢量

        返回:

            compensated: 运动补偿后的帧

        """

        h, w = reference_frame.shape[:2]

        bs = self.block_size



        compensated = np.zeros_like(reference_frame)



        for i in range(motion_vectors.shape[0]):

            for j in range(motion_vectors.shape[1]):

                y = i * bs

                x = j * bs

                dy, dx = motion_vectors[i, j]



                ref_y = y + dy

                ref_x = x + dx



                if 0 <= ref_y < h - bs and 0 <= ref_x < w - bs:

                    compensated[y:y+bs, x:x+bs] = reference_frame[ref_y:ref_y+bs, ref_x:ref_x+bs]



        return compensated





class DCTTransform:

    """

    DCT（离散余弦变换）



    视频编码中的空间频率变换。

    """



    @staticmethod

    def dct_2d(block):

        """

        2D DCT



        参数:

            block: 8x8 块

        返回:

            dct_block: DCT 系数

        """

        N = block.shape[0]

        dct_block = np.zeros_like(block, dtype=float)



        for u in range(N):

            for v in range(N):

                sum_val = 0

                for x in range(N):

                    for y in range(N):

                        cos1 = math.cos((2*x + 1) * u * math.pi / (2*N))

                        cos2 = math.cos((2*y + 1) * v * math.pi / (2*N))

                        sum_val += block[x, y] * cos1 * cos2



                cu = 1 if u == 0 else math.sqrt(2)

                cv = 1 if v == 0 else math.sqrt(2)

                dct_block[u, v] = 0.25 * cu * cv * sum_val



        return dct_block



    @staticmethod

    def idct_2d(dct_block):

        """

        2D 逆 DCT



        参数:

            dct_block: DCT 系数

        返回:

            block: 重建块

        """

        N = dct_block.shape[0]

        block = np.zeros_like(dct_block)



        for x in range(N):

            for y in range(N):

                sum_val = 0

                for u in range(N):

                    for v in range(N):

                        cu = 1 if u == 0 else math.sqrt(2)

                        cv = 1 if v == 0 else math.sqrt(2)

                        cos1 = math.cos((2*x + 1) * u * math.pi / (2*N))

                        cos2 = math.cos((2*y + 1) * v * math.pi / (2*N))

                        sum_val += cu * cv * dct_block[u, v] * cos1 * cos2



                block[x, y] = 0.25 * sum_val



        return block



    @staticmethod

    def quantize(dct_block, qp=10):

        """

        量化



        参数:

            dct_block: DCT 系数

            qp: 量化参数

        返回:

            quantized: 量化后系数

        """

        Q = np.ones_like(dct_block)

        for i in range(dct_block.shape[0]):

            for j in range(dct_block.shape[1]):

                Q[i, j] = 1 + (1 + i + j) * qp



        return np.round(dct_block / Q)



    @staticmethod

    def dequantize(quantized, qp=10):

        """逆量化"""

        Q = np.ones_like(quantized)

        for i in range(quantized.shape[0]):

            for j in range(quantized.shape[1]):

                Q[i, j] = 1 + (1 + i + j) * qp



        return quantized * Q





class VideoEncoder:

    """

    简单视频编码器



    整合帧差分、运动估计、DCT 变换。

    """



    def __init__(self, block_size=8, search_range=8, qp=10):

        self.block_size = block_size

        self.search_range = search_range

        self.qp = qp

        self.motion_est = BlockMotionEstimation(block_size, search_range)

        self.dct = DCTTransform()

        self.frame_diff = FrameDifferencing(keyframe_interval=10)

        self.reference_frames = []



    def encode_frame(self, frame):

        """编码帧"""

        if self.frame_diff.frame_count % 10 == 0:

            # 关键帧

            encoded = {'type': 'I', 'data': frame}

        else:

            # 运动估计 + DCT

            ref = self.reference_frames[-1] if self.reference_frames else frame

            mvs, residuals = self.motion_est.estimate(frame, ref)



            # DCT 变换

            dct_coeffs = []

            bs = self.block_size

            h, w = frame.shape



            for i in range(0, h - h % bs, bs):

                for j in range(0, w - w % bs, bs):

                    block = residuals[i:i+bs, j:j+bs]

                    dct_block = self.dct.dct_2d(block)

                    quantized = self.dct.quantize(dct_block, self.qp)

                    dct_coeffs.append(quantized)



            encoded = {

                'type': 'P',

                'motion_vectors': mvs,

                'dct_coeffs': dct_coeffs

            }



        # 更新参考帧

        compressed = self.frame_diff.compress_frame(frame)

        self.reference_frames.append(frame)



        return encoded



    def get_bitrate(self, encoded_frame, fps=30):

        """估算比特率"""

        if encoded_frame['type'] == 'I':

            return np.prod(encoded_frame['data'].shape) * 8 * fps

        else:

            return len(encoded_frame['motion_vectors']) * 4 * 8





if __name__ == "__main__":

    print("=== 视频压缩测试 ===")



    # 创建测试视频序列

    print("\n1. 创建测试视频序列")

    np.random.seed(42)

    frames = []

    for i in range(30):

        frame = np.zeros((64, 64), dtype=np.uint8)

        # 移动的方形

        x, y = 10 + i, 20

        if x + 20 < 64 and y + 20 < 64:

            frame[y:y+20, x:x+20] = 200

        # 添加噪声

        frame += np.random.randint(0, 20, (64, 64))

        frames.append(frame)



    print(f"帧数: {len(frames)}")

    print(f"每帧大小: {frames[0].shape}")



    # 帧差分压缩

    print("\n2. 帧差分压缩")

    fd = FrameDifferencing(keyframe_interval=10)

    compressed_frames = []

    for i, frame in enumerate(frames):

        comp = fd.compress_frame(frame)

        compressed_frames.append(comp)

        if comp['type'] == 'I':

            print(f"  帧 {i}: I帧 (关键帧)")

        else:

            print(f"  帧 {i}: P帧, MSE={comp['mse']:.2f}")



    # 运动估计

    print("\n3. 运动估计")

    me = BlockMotionEstimation(block_size=16, search_range=8)

    mvs, residuals = me.estimate(frames[5], frames[4])

    print(f"运动矢量形状: {mvs.shape}")

    nonzero_mv = np.sum(mvs != 0)

    print(f"非零运动矢量: {nonzero_mv}/{mvs.size}")



    # 运动补偿

    print("\n4. 运动补偿")

    compensated = me.compensate(frames[4], mvs)

    compensated_residual = frames[5].astype(float) - compensated.astype(float)

    print(f"补偿残差均值: {np.mean(np.abs(compensated_residual)):.2f}")



    # DCT 变换

    print("\n5. DCT 变换")

    block = frames[0][:8, :8].astype(float)

    dct_block = DCTTransform.dct_2d(block)

    quantized = DCTTransform.quantize(dct_block, qp=10)

    print(f"DCT 块范围: [{np.min(np.abs(dct_block)):.2f}, {np.max(np.abs(dct_block)):.2f}]")

    print(f"量化后范围: [{np.min(np.abs(quantized)):.0f}, {np.max(np.abs(quantized)):.0f}]")



    # 视频编码器

    print("\n6. 视频编码器")

    encoder = VideoEncoder()

    for i, frame in enumerate(frames[:5]):

        encoded = encoder.encode_frame(frame)

        bitrate = encoder.get_bitrate(encoded)

        print(f"  帧 {i}: {encoded['type']}帧, 估算比特率={bitrate} bits")



    # 压缩率估算

    print("\n7. 压缩率估算")

    original_bits = 30 * 64 * 64 * 8

    print(f"原始大小: {original_bits} bits")

    i_frame_bits = 10 * 64 * 64 * 8

    p_frame_bits = 20 * (64 * 64 // 256) * 8  # 简化估计

    compressed_bits = i_frame_bits + p_frame_bits

    print(f"压缩后估计: {compressed_bits} bits")

    print(f"压缩比: {original_bits / compressed_bits:.1f}x")



    print("\n视频压缩测试完成!")

