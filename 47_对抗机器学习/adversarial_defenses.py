# -*- coding: utf-8 -*-

"""

算法实现：对抗机器学习 / adversarial_defenses



本文件实现 adversarial_defenses 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F

from scipy.ndimage import gaussian_filter





class InputPurification:

    """

    输入净化防御



    通过预处理输入图像来去除对抗扰动

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def jpeg_compression(self, images, quality=75):

        """

        JPEG压缩净化



        通过JPEG压缩去除高频对抗扰动

        注意：简化实现，实际需要libjpeg



        参数:

            images: 输入图像 [B, C, H, W]

            quality: JPEG质量（越小压缩越强）



        返回:

            purified: 净化后的图像

        """

        # 简化版：使用高斯模糊模拟JPEG去噪效果

        purified = []

        for img in images:

            # 对每个通道应用模糊

            img_np = img.cpu().numpy()

            blurred = gaussian_filter(img_np, sigma=1.0)

            purified.append(torch.from_numpy(blurred))



        return torch.stack(purified).to(self.device)



    def bit_depth_reduction(self, images, num_bits=4):

        """

        比特深度压缩



        将图像量化为较少比特，减少扰动影响



        参数:

            num_bits: 保留的比特数



        返回:

            quantized: 量化后的图像

        """

        # 归一化到[0, 1]

        images = torch.clamp(images, 0, 1)



        # 量化

        scale = (2 ** num_bits - 1)

        quantized = torch.round(images * scale) / scale



        return quantized



    def image_denoising(self, images, kernel_size=3):

        """

        中值滤波去噪



        使用中值滤波去除椒盐噪声类型的对抗扰动



        参数:

            kernel_size: 滤波核大小



        返回:

            denoised: 去噪后的图像

        """

        # 简化实现：使用均值滤波

        pad = kernel_size // 2

        padded = F.pad(images, (pad, pad, pad, pad), mode='replicate')

        unfolded = F.unfold(padded, kernel_size).transpose(1, 2)

        denoised = unfolded.mean(dim=2).view_as(images)



        return denoised



    def feature_squeeze(self, images):

        """

        特征压缩（Feature Squeezing）



        同时使用多种压缩方法，选择差异最大的结果



        参数:

            images: 输入图像



        返回:

            squeezed_output: 压缩后模型的预测

            difference: 原始与压缩输出的差异

        """

        # 原始预测

        with torch.no_grad():

            original_output = self.model(images)



        # 多种压缩方法

        compressed_images = []



        # 1. 比特深度压缩

        bit_reduced = self.bit_depth_reduction(images, num_bits=4)

        compressed_images.append(bit_reduced)



        # 2. 高斯模糊

        blurred = F.avg_pool2d(images, kernel_size=3, stride=1, padding=1)

        compressed_images.append(blurred)



        # 3. 中值滤波

        denoised = self.image_denoising(images)

        compressed_images.append(denoised)



        # 计算与原始输出的差异

        differences = []

        for comp_img in compressed_images:

            with torch.no_grad():

                comp_output = self.model(comp_img)

                diff = torch.abs(original_output - comp_output).max().item()

                differences.append(diff)



        # 返回平均预测

        all_outputs = [original_output] + [

            self.model(comp) for comp in compressed_images

        ]

        avg_output = torch.stack(all_outputs).mean(dim=0)



        return avg_output, differences



    def randomized_smoothing_defense(self, images, num_samples=10, sigma=0.1):

        """

        随机平滑防御



        对输入添加随机噪声并多次预测取平均



        参数:

            num_samples: 采样次数

            sigma: 噪声标准差



        返回:

            avg_output: 平均预测

        """

        all_outputs = []



        for _ in range(num_samples):

            noise = torch.randn_like(images) * sigma

            noisy_images = torch.clamp(images + noise, 0, 1)



            with torch.no_grad():

                output = self.model(noisy_images)

                all_outputs.append(output)



        return torch.stack(all_outputs).mean(dim=0)





class FeatureDenoising:

    """

    特征去噪防御



    通过去噪中间层特征或平滑特征空间来防御对抗攻击

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def channel_attention_denoise(self, features, reduction=16):

        """

        通道注意力去噪



        使用通道注意力机制识别重要通道并抑制噪声



        参数:

            features: 特征张量 [B, C, H, W]

            reduction: 注意力机制的降维比



        返回:

            denoised: 去噪后的特征

        """

        B, C, H, W = features.shape



        # 全局平均池化

        gap = F.adaptive_avg_pool2d(features, 1).view(B, C)



        # 全局最大池化

        gmp = F.adaptive_max_pool2d(features, 1).view(B, C)



        # 共享MLP

        fc = nn.Sequential(

            nn.Linear(C, C // reduction, bias=False),

            nn.ReLU(inplace=True),

            nn.Linear(C // reduction, C, bias=False)

        ).to(self.device)



        # 注意力权重

        gap_attn = torch.sigmoid(fc(gap))

        gmp_attn = torch.sigmoid(fc(gmp))

        attention = (gap_attn + gmp_attn) / 2



        # 应用注意力

        return features * attention.view(B, C, 1, 1)



    def temporal_smoothing(self, features, momentum=0.9):

        """

        时序平滑（用于RNN场景）



        通过移动平均平滑特征



        参数:

            momentum: 动量因子

        """

        # 简化实现

        return features



    def high_frequency_filter(self, features, threshold=0.5):

        """

        高频滤波



        去除特征中的高频成分（可能为对抗噪声）



        参数:

            threshold: 频率阈值

        """

        # 在频域中滤波

        fft = torch.fft.fft2(features)

        magnitude = torch.abs(fft)



        # 低频保留，高频衰减

        mask = (magnitude < threshold).float()

        filtered_fft = fft * mask



        return torch.real(torch.fft.ifft2(filtered_fft))





class GradientMasking:

    """

    梯度屏蔽防御



    通过各种技术使攻击者难以获取有效梯度来生成对抗样本

    """



    def __init__(self, model, device='cpu'):

        self.model = model

        self.device = device



    def add_gradient_noise(self, grad, noise_scale=0.1):

        """

        梯度噪声



        向梯度添加随机噪声，使攻击者无法获取精确梯度



        参数:

            grad: 原始梯度

            noise_scale: 噪声强度

        """

        noise = torch.randn_like(grad) * noise_scale

        return grad + noise



    def gradient_sparsification(self, grad, sparsity=0.9):

        """

        梯度稀疏化



        只传递梯度中最大的部分，模拟二值化梯度效果



        参数:

            sparsity: 置零比例

        """

        k = int(grad.numel() * (1 - sparsity))

        if k == 0:

            return grad



        # 获取绝对值最大的k个位置

        flat_grad = grad.view(-1)

        threshold = torch.kthvalue(torch.abs(flat_grad), k)[0]

        mask = (torch.abs(grad) >= threshold).float()



        return grad * mask



    def defensive_quantization(self, grad, num_bits=8):

        """

        梯度量化防御



        量化梯度以阻止精确梯度攻击



        参数:

            num_bits: 量化比特数

        """

        scale = (2 ** num_bits - 1)

        quantized = torch.round(grad * scale) / scale



        return quantized



    def non_differentiable_defense(self, images):

        """

        不可微防御层



        在前向传播和反向传播之间引入不可微操作



        参数:

            images: 输入图像



        返回:

            defended: 添加了不可微操作的图像

        """

        # 随机路由：训练时使用真实掩码，推理时使用随机掩码

        if self.model.training:

            # 训练时使用确定性阈值

            threshold = 0.5

            mask = (images > threshold).float()

        else:

            # 推理时使用随机二值化

            mask = (torch.rand_like(images) < images).float()



        # 混合原始和二值化版本

        return images * 0.5 + mask * 0.5





if __name__ == "__main__":

    # 定义简单模型

    class SimpleCNN(nn.Module):

        def __init__(self, num_classes=10):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)

            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)

            self.fc1 = nn.Linear(64 * 7 * 7, 128)

            self.fc2 = nn.Linear(128, num_classes)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            return self.fc2(x)



    device = torch.device("cpu")

    model = SimpleCNN(num_classes=10).to(device)



    # 生成测试数据

    torch.manual_seed(42)

    test_images = torch.rand(8, 1, 28, 28).to(device)

    test_labels = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7]).to(device)



    # 模拟对抗图像（添加小扰动）

    adversarial_images = test_images + torch.randn_like(test_images) * 0.05

    adversarial_images = torch.clamp(adversarial_images, 0, 1)



    print("=" * 50)

    print("对抗样本防御测试")

    print("=" * 50)



    # 输入净化测试

    print("\n--- 输入净化防御 ---")

    purifier = InputPurification(model, device)



    # 干净样本预测

    with torch.no_grad():

        clean_pred = torch.argmax(model(test_images), dim=1)

        adv_pred_before = torch.argmax(model(adversarial_images), dim=1)

        print(f"干净预测: {clean_pred.cpu().numpy()}")

        print(f"对抗预测(净化前): {adv_pred_before.cpu().numpy()}")



    # 特征压缩

    squeezed_output, differences = purifier.feature_squeeze(adversarial_images)

    squeezed_pred = torch.argmax(squeezed_output, dim=1)

    print(f"特征压缩后预测: {squeezed_pred.cpu().numpy()}")

    print(f"各方法差异: {[f'{d:.4f}' for d in differences]}")



    # 随机平滑

    smooth_output = purifier.randomized_smoothing_defense(adversarial_images, num_samples=20, sigma=0.1)

    smooth_pred = torch.argmax(smooth_output, dim=1)

    print(f"随机平滑预测: {smooth_pred.cpu().numpy()}")



    # 特征去噪测试

    print("\n--- 特征去噪防御 ---")

    denoiser = FeatureDenoising(model, device)



    # 获取中间特征

    x = F.relu(F.max_pool2d(model.conv1(test_images), 2))

    x = F.relu(F.max_pool2d(model.conv2(x), 2))

    print(f"原始特征形状: {x.shape}")



    # 通道注意力去噪

    denoised_feat = denoiser.channel_attention_denoise(x)

    print(f"去噪后特征形状: {denoised_feat.shape}")



    # 梯度屏蔽测试

    print("\n--- 梯度屏蔽防御 ---")

    masker = GradientMasking(model, device)



    # 模拟梯度

    test_grad = torch.randn(8, 1, 28, 28).to(device)



    # 各种屏蔽方法

    noisy_grad = masker.add_gradient_noise(test_grad, noise_scale=0.5)

    sparse_grad = masker.gradient_sparsification(test_grad, sparsity=0.7)

    quantized_grad = masker.defensive_quantization(test_grad, num_bits=4)



    print(f"原始梯度范围: [{test_grad.min():.4f}, {test_grad.max():.4f}]")

    print(f"加噪梯度范围: [{noisy_grad.min():.4f}, {noisy_grad.max():.4f}]")

    print(f"稀疏化梯度非零比例: {(sparse_grad != 0).float().mean():.2%}")

    print(f"量化梯度唯一值数: {len(quantized_grad.unique())}")



    print("\n测试完成！")

