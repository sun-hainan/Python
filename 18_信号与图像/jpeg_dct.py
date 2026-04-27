# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / jpeg_dct

本文件实现 jpeg_dct 相关的算法功能。
"""

import numpy as np
import math
import struct


class JPEGQuantization:
    """
    JPEG 量化表和量化操作
    """

    # 标准亮度量化表
    LUMINANCE_QUANT_TABLE = np.array([
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99]
    ], dtype=float)

    # 色度量化表
    CHROMINANCE_QUANT_TABLE = np.array([
        [17, 18, 24, 47, 99, 99, 99, 99],
        [18, 21, 26, 66, 99, 99, 99, 99],
        [24, 26, 56, 99, 99, 99, 99, 99],
        [47, 66, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99]
    ], dtype=float)

    @staticmethod
    def quantize(block, quant_table, quality=50):
        """
        量化 DCT 系数

        参数:
            block: 8x8 DCT 系数
            quant_table: 量化表
            quality: 质量因子 1-100
        返回:
            quantized: 量化后系数
        """
        # 调整量化表
        if quality < 50:
            scale = 5000 / quality
        else:
            scale = 200 - 2 * quality

        Q = quant_table * (scale / 100)
        Q = np.clip(Q, 1, 255)

        return np.round(block / Q)

    @staticmethod
    def dequantize(quantized, quant_table, quality=50):
        """
        逆量化

        参数:
            quantized: 量化后系数
            quant_table: 量化表
            quality: 质量因子
        返回:
            block: DCT 系数
        """
        if quality < 50:
            scale = 5000 / quality
        else:
            scale = 200 - 2 * quality

        Q = quant_table * (scale / 100)
        Q = np.clip(Q, 1, 255)

        return quantized * Q


class JPEGDCT:
    """
    JPEG DCT 编码器
    """

    def __init__(self, quality=50):
        self.quality = quality
        self.quant = JPEGQuantization()

    def dct_2d(self, block):
        """
        8x8 块的 DCT 变换

        参数:
            block: 8x8 输入块
        返回:
            dct_block: 8x8 DCT 系数
        """
        dct_block = np.zeros((8, 8), dtype=float)

        for u in range(8):
            for v in range(8):
                sum_val = 0.0
                for x in range(8):
                    for y in range(8):
                        cos_x = math.cos((2*x + 1) * u * math.pi / 16)
                        cos_y = math.cos((2*y + 1) * v * math.pi / 16)
                        sum_val += (block[x, y] - 128) * cos_x * cos_y

                cu = 1.0 / math.sqrt(2) if u == 0 else 1.0
                cv = 1.0 / math.sqrt(2) if v == 0 else 1.0
                dct_block[u, v] = 0.25 * cu * cv * sum_val

        return dct_block

    def idct_2d(self, dct_block):
        """
        8x8 块的逆 DCT

        参数:
            dct_block: 8x8 DCT 系数
        返回:
            block: 重建块
        """
        block = np.zeros((8, 8), dtype=float)

        for x in range(8):
            for y in range(8):
                sum_val = 0.0
                for u in range(8):
                    for v in range(8):
                        cu = 1.0 / math.sqrt(2) if u == 0 else 1.0
                        cv = 1.0 / math.sqrt(2) if v == 0 else 1.0
                        cos_x = math.cos((2*x + 1) * u * math.pi / 16)
                        cos_y = math.cos((2*y + 1) * v * math.pi / 16)
                        sum_val += cu * cv * dct_block[u, v] * cos_x * cos_y

                block[x, y] = 0.25 * sum_val + 128

        return np.clip(block, 0, 255).astype(np.uint8)

    def zigzag_scan(self, block):
        """
        Z 字形扫描

        参数:
            block: 8x8 块
        返回:
            stream: 1D 系数流
        """
        zigzag = [
            (0,0), (0,1), (1,0), (2,0), (1,1), (0,2), (0,3), (1,2),
            (2,1), (3,0), (4,0), (3,1), (2,2), (1,3), (0,4), (0,5),
            (1,4), (2,3), (3,2), (4,1), (5,0), (6,0), (5,1), (4,2),
            (3,3), (2,4), (1,5), (0,6), (0,7), (1,6), (2,5), (3,4),
            (4,3), (5,2), (6,1), (7,0), (7,1), (6,2), (5,3), (4,4),
            (3,5), (2,6), (1,7), (2,7), (3,6), (4,5), (5,4), (6,3),
            (7,2), (7,3), (6,4), (5,5), (4,6), (3,7), (4,7), (5,6),
            (6,5), (7,4), (7,5), (6,6), (5,7), (6,7), (7,6), (7,7)
        ]

        stream = []
        for y, x in zigzag:
            stream.append(block[y, x])

        return np.array(stream)

    def run_length_encode(self, stream):
        """
        行程编码（RLE）

        参数:
            stream: Z 字形扫描后的系数流
        返回:
            rle: RLE 数据
        """
        rle = []
        zero_count = 0

        for i, val in enumerate(stream):
            if val == 0:
                zero_count += 1
            else:
                rle.append((zero_count, val))
                zero_count = 0

        # EOB
        if zero_count > 0:
            rle.append((0, 0))

        return rle

    def encode_block(self, block):
        """
        编码单个 8x8 块

        参数:
            block: 原始 8x8 块
        返回:
            encoded: 编码数据
        """
        # DCT
        dct_block = self.dct_2d(block)

        # 量化
        quantized = self.quant.quantize(
            dct_block,
            JPEGQuantization.LUMINANCE_QUANT_TABLE,
            self.quality
        )

        # Z 字形扫描
        stream = self.zigzag_scan(quantized)

        # RLE
        rle = self.run_length_encode(stream)

        return {
            'dct': dct_block,
            'quantized': quantized,
            'stream': stream,
            'rle': rle
        }

    def decode_block(self, quantized):
        """
        解码单个块

        参数:
            quantized: 量化系数
        返回:
            block: 重建块
        """
        # 逆量化
        dct_block = self.quant.dequantize(
            quantized,
            JPEGQuantization.LUMINANCE_QUANT_TABLE,
            self.quality
        )

        # 逆 DCT
        return self.idct_2d(dct_block)


def rgb_to_ycbcr(image):
    """
    RGB 到 YCbCr 颜色空间转换

    参数:
        image: RGB 图像
    返回:
        ycbcr: YCbCr 图像
    """
    image = image.astype(float)

    R, G, B = image[:,:,0], image[:,:,1], image[:,:,2]

    Y = 0.299 * R + 0.587 * G + 0.114 * B
    Cb = 128 - 0.168736 * R - 0.331264 * G + 0.5 * B
    Cr = 128 + 0.5 * R - 0.418688 * G - 0.081312 * B

    return np.stack([Y, Cb, Cr], axis=-1)


def ycbcr_to_rgb(ycbcr):
    """
    YCbCr 到 RGB 颜色空间转换
    """
    Y, Cb, Cr = ycbcr[:,:,0], ycbcr[:,:,1], ycbcr[:,:,2]

    R = Y + 1.402 * (Cr - 128)
    G = Y - 0.344136 * (Cb - 128) - 0.714136 * (Cr - 128)
    B = Y + 1.772 * (Cb - 128)

    return np.clip(np.stack([R, G, B], axis=-1), 0, 255).astype(np.uint8)


class SimpleJPEGEncoder:
    """
    简化 JPEG 编码器
    """

    def __init__(self, quality=50):
        self.quality = quality
        self.dct = JPEGDCT(quality)

    def encode_image(self, image):
        """
        编码完整图像

        参数:
            image: RGB 图像
        返回:
            encoded: 编码数据
        """
        # RGB 到 YCbCr
        ycbcr = rgb_to_ycbcr(image)

        h, w = ycbcr.shape[:2]

        # 填充到 8 的倍数
        h_pad = (8 - h % 8) % 8
        w_pad = (8 - w % 8) % 8
        ycbcr_pad = np.pad(ycbcr, ((0, h_pad), (0, w_pad), (0, 0)))

        # 编码 Y 分量
        encoded_blocks = []
        for i in range(0, ycbcr_pad.shape[0], 8):
            for j in range(0, ycbcr_pad.shape[1], 8):
                block = ycbcr_pad[i:i+8, j:j+8, 0]  # Y 分量
                encoded = self.dct.encode_block(block)
                encoded_blocks.append(encoded)

        return {
            'blocks': encoded_blocks,
            'shape': (h, w),
            'padded_shape': ycbcr_pad.shape[:2]
        }

    def decode_image(self, encoded):
        """
        解码图像

        参数:
            encoded: 编码数据
        返回:
            image: RGB 图像
        """
        h, w = encoded['shape']
        blocks = encoded['blocks']
        ph, pw = encoded['padded_shape']

        ycbcr_pad = np.zeros((ph, pw, 3))

        idx = 0
        for i in range(0, ph, 8):
            for j in range(0, pw, 8):
                block_data = blocks[idx]['quantized']
                decoded = self.dct.decode_block(block_data)
                ycbcr_pad[i:i+8, j:j+8, 0] = decoded
                idx += 1

        # 裁剪
        ycbcr = ycbcr_pad[:h, :w]

        # YCbCr 到 RGB
        return ycbcr_to_rgb(ycbcr)


if __name__ == "__main__":
    print("=== JPEG DCT 压缩测试 ===")

    # 创建测试图像
    print("\n1. 创建测试图像")
    np.random.seed(42)
    image = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)

    # 添加平滑区域
    image[20:44, 20:44] = 150

    print(f"图像尺寸: {image.shape}")
    print(f"原始图像均值: {np.mean(image):.2f}")

    # RGB 到 YCbCr
    print("\n2. 颜色空间转换")
    ycbcr = rgb_to_ycbcr(image)
    print(f"Y 分量均值: {np.mean(ycbcr[:,:,0]):.2f}")
    print(f"Cb 分量均值: {np.mean(ycbcr[:,:,1]):.2f}")
    print(f"Cr 分量均值: {np.mean(ycbcr[:,:,2]):.2f}")

    # DCT 编码
    print("\n3. DCT 编码")
    jpeg = JPEGDCT(quality=50)
    block = image[0:8, 0:8, 0].astype(float)
    encoded = jpeg.encode_block(block)

    print(f"DCT 块范围: [{np.min(np.abs(encoded['dct'])):.2f}, {np.max(np.abs(encoded['dct'])):.2f}")
    print(f"量化后范围: [{np.min(np.abs(encoded['quantized'])):.0f}, {np.max(np.abs(encoded['quantized'])):.0f}")
    print(f"Z 字形流长度: {len(encoded['stream'])}")
    print(f"RLE 项数: {len(encoded['rle'])}")

    # 解码
    print("\n4. DCT 解码")
    decoded_block = jpeg.dct.decode_block(encoded['quantized'])
    mse = np.mean((decoded_block.astype(float) - block.astype(float))**2)
    print(f"块 MSE: {mse:.4f}")

    # 完整图像编码
    print("\n5. 完整图像编码/解码")
    encoder = SimpleJPEGEncoder(quality=50)
    encoded_img = encoder.encode_image(image)
    decoded_img = encoder.decode_image(encoded_img)

    image_mse = np.mean((decoded_img.astype(float) - image.astype(float))**2)
    image_psnr = 10 * np.log10(255**2 / image_mse)

    print(f"编码块数: {len(encoded_img['blocks'])}")
    print(f"图像 MSE: {image_mse:.4f}")
    print(f"图像 PSNR: {image_psnr:.2f} dB")

    # 量化表
    print("\n6. 量化表分析")
    Q = JPEGQuantization.LUMINANCE_QUANT_TABLE
    print(f"量化表范围: [{np.min(Q):.0f}, {np.max(Q):.0f}]")

    # 不同质量对比
    print("\n7. 不同质量对比")
    for quality in [10, 30, 50, 80, 95]:
        enc = SimpleJPEGEncoder(quality=quality)
        encoded = enc.encode_image(image)
        decoded = enc.decode_image(encoded)
        mse = np.mean((decoded.astype(float) - image.astype(float))**2)
        psnr = 10 * np.log10(255**2 / mse) if mse > 0 else float('inf')
        nonzero = sum(np.count_nonzero(b['quantized']) for b in encoded['blocks'])
        print(f"  质量={quality}: PSNR={psnr:.2f}dB, 非零系数={nonzero}")

    print("\nJPEG DCT 压缩测试完成!")
