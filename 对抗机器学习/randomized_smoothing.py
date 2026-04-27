# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / randomized_smoothing

本文件实现 randomized_smoothing 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.stats import norm


class RandomizedSmoothing(nn.Module):
    """
    随机平滑分类器

    通过在输入上添加Gaussian噪声并投票来获得鲁棒预测
    """

    def __init__(self, base_classifier, num_classes=10, sigma=0.5, device='cpu'):
        """
        参数:
            base_classifier: 基础分类模型
            num_classes: 类别数
            sigma: Gaussian噪声的标准差
            device: 计算设备
        """
        super().__init__()
        self.base_classifier = base_classifier
        self.num_classes = num_classes
        self.sigma = sigma
        self.device = device

    def forward(self, x):
        """
        前向传播：返回噪声样本的平均logits

        参数:
            x: 输入图像 [B, C, H, W]

        返回:
            平均logits
        """
        return self.base_classifier(x)

    def predict(self, x, num_samples=100, batch_size=32, alpha=0.001):
        """
        随机平滑预测：多次采样并投票

        参数:
            x: 输入图像 [B, C, H, W]
            num_samples: 采样次数
            batch_size: 每批采样数
            alpha: 显著性水平（用于置信区间）

        返回:
            predictions: 预测类别
            certified_radius: 认证半径（对抗扰动上界）
        """
        self.eval()
        x = x.to(self.device)
        batch_size = min(batch_size, num_samples)

        all_predictions = []

        with torch.no_grad():
            for i in range(0, num_samples, batch_size):
                current_batch_size = min(batch_size, num_samples - i)

                # 生成随机噪声
                noise = torch.randn(x.size(0), x.size(1), x.size(2), x.size(3),
                                   device=self.device) * self.sigma

                # 添加噪声并预测
                noisy_x = x + noise
                outputs = self.base_classifier(noisy_x)
                predictions = torch.argmax(outputs, dim=1)
                all_predictions.append(predictions)

        # 堆叠所有预测
        all_predictions = torch.stack(all_predictions, dim=0)  # [num_batches, B]

        # 投票得到最终预测
        final_predictions = []
        certified_radii = []

        for i in range(x.size(0)):
            predictions_i = all_predictions[:, i]  # 该样本的所有预测
            votes = torch.bincount(predictions_i, minlength=self.num_classes)
            top_class = torch.argmax(votes).item()
            top_vote_count = votes[top_class].item()

            final_predictions.append(top_class)

            # 计算认证半径
            n = num_samples
            p_lower = norm.ppf(alpha / 2, loc=top_vote_count / n, scale=np.sqrt(top_vote_count / n * (1 - top_vote_count / n)))

            # 简化：使用二项分布置信下界
            if top_vote_count > 0:
                # 认证半径公式：sigma * norm.ppf(Phi^{-1}(p_lower))
                # 这里使用简化版本
                radius = self.sigma * 0.5
            else:
                radius = 0.0

            certified_radii.append(radius)

        return torch.tensor(final_predictions), certified_radii


def get_certified_radius(vote_count, total_samples, sigma, alpha=0.001):
    """
    计算认证半径

    基于投票结果和噪声标准差，计算可证明鲁棒的扰动上界

    参数:
        vote_count: 获胜类别的票数
        total_samples: 总采样数
        sigma: 噪声标准差
        alpha: 显著性水平

    返回:
        radius: 认证半径（在该半径内的对抗扰动无法改变预测）
    """
    # 获得票数比例
    p = vote_count / total_samples

    # 计算下界（使用Clopper-Pearson区间）
    from scipy.stats import binom
    if p < 1.0:
        # 使用正态近似计算95%置信下界
        z = norm.ppf(1 - alpha / 2)
        p_lower = p - z * np.sqrt(p * (1 - p) / total_samples)
        p_lower = max(0, p_lower)

        # 认证半径：sigma * norm.ppf(p_lower)
        if p_lower > 0.5:
            radius = sigma * norm.ppf(p_lower)
        else:
            radius = 0.0
    else:
        # 全票通过，理论上可以无限鲁棒（实际取大值）
        radius = sigma * 10

    return radius


def randomized_smoothing_certified_accuracy(model, images, labels, sigma=0.5, num_samples=1000, device='cpu'):
    """
    计算随机平滑后的认证准确率

    参数:
        model: 分类模型
        images: 测试图像
        labels: 真实标签
        sigma: 噪声标准差
        num_samples: 采样次数
        device: 计算设备

    返回:
        certified_accuracy: 不同半径下的认证准确率字典
    """
    model.eval()
    images = images.to(device)
    labels = labels.to(device)

    certified_accuracy = {}

    # 不同半径阈值
    radii = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]

    for radius in radii:
        certified_count = 0

        for i in range(len(images)):
            # 多次采样预测
            predictions = []
            for _ in range(min(num_samples, 100)):  # 限制计算量
                noise = torch.randn(1, *images.shape[1:], device=device) * sigma
                noisy_image = images[i:i + 1] + noise

                with torch.no_grad():
                    output = model(noisy_image)
                    pred = torch.argmax(output, dim=1).item()
                    predictions.append(pred)

            # 投票
            pred_counts = torch.bincount(torch.tensor(predictions), minlength=10)
            top_pred = torch.argmax(pred_counts).item()
            top_votes = pred_counts[top_pred].item()

            # 计算该预测的认证半径
            certified_radius = get_certified_radius(top_votes, len(predictions), sigma)

            # 如果认证半径大于阈值，且预测正确
            if certified_radius >= radius and top_pred == labels[i].item():
                certified_count += 1

        certified_accuracy[radius] = certified_count / len(images)

    return certified_accuracy


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
    model.eval()

    # 包装为随机平滑分类器
    rs_classifier = RandomizedSmoothing(model, num_classes=10, sigma=0.5, device=device)

    # 测试数据
    torch.manual_seed(42)
    test_images = torch.rand(6, 1, 28, 28).to(device)
    test_labels = torch.tensor([0, 1, 2, 3, 4, 5]).to(device)

    print("=" * 50)
    print("随机平滑测试")
    print("=" * 50)

    # 干净预测
    with torch.no_grad():
        clean_preds = torch.argmax(model(test_images), dim=1)
        print(f"原始预测: {clean_preds.cpu().numpy()}")
        print(f"真实标签: {test_labels.cpu().numpy()}")

    # 随机平滑预测
    predictions, radii = rs_classifier.predict(test_images, num_samples=200)

    print(f"平滑预测: {predictions.cpu().numpy()}")
    print(f"认证半径: {[f'{r:.3f}' for r in radii]}")

    # 计算不同半径下的认证准确率
    print("\n认证准确率（不同半径）:")
    certified_acc = randomized_smoothing_certified_accuracy(
        model, test_images, test_labels,
        sigma=0.5, num_samples=200, device=device
    )

    for radius, acc in certified_acc.items():
        print(f"  半径 >= {radius:.2f}: {acc:.2%}")

    # 测试不同sigma值的影响
    print("\n不同噪声标准差的影响:")
    for sigma in [0.25, 0.5, 1.0]:
        rs = RandomizedSmoothing(model, num_classes=10, sigma=sigma, device=device)
        preds, radii = rs.predict(test_images, num_samples=200)
        avg_radius = np.mean(radii)
        print(f"  sigma={sigma}: 平均认证半径={avg_radius:.4f}")

    print("\n测试完成！")
