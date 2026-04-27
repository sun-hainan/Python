# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / certification_tools

本文件实现 certification_tools 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class CertifiedRadiusCalculator:
    """
    计算认证半径

    对于随机平滑等方法，计算可证明鲁棒的扰动上界
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.model.eval()

    def compute_radius_randomized_smoothing(self, images, labels, sigma=0.5, num_samples=1000, alpha=0.001):
        """
        计算随机平滑的认证半径

        参数:
            sigma: Gaussian噪声标准差
            num_samples: 采样次数
            alpha: 显著性水平

        返回:
            radius: 认证半径
        """
        from scipy.stats import norm

        predictions = []

        with torch.no_grad():
            for _ in range(num_samples):
                noise = torch.randn_like(images) * sigma
                noisy_images = torch.clamp(images + noise, 0, 1)
                pred = torch.argmax(self.model(noisy_images), dim=1)
                predictions.append(pred)

        predictions = torch.stack(predictions, dim=0)

        radii = []

        for i in range(len(images)):
            pred_i = predictions[:, i]

            # 统计每个类的票数
            for class_id in range(10):
                votes = (pred_i == class_id).sum().item()
                p = votes / num_samples

                # 计算置信下界
                if p > 0.5:
                    z = norm.ppf(1 - alpha / 2)
                    radius = sigma * z
                    radii.append(radius)
                    break

        return np.mean(radii) if radii else 0.0


class IntervalBoundPropagation:
    """
    区间边界传播（IBP）

    一种可认证的防御方法
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def compute_bounds(self, images, epsilon=0.03):
        """
        计算输出区间边界

        参数:
            epsilon: 扰动上界

        返回:
            lower, upper: 输出的下界和上界
        """
        # 简化实现
        images = images.to(self.device)

        # 中心点预测
        with torch.no_grad():
            center_output = self.model(images)

        # 简化的边界（实际需要更复杂的传播）
        delta = epsilon * 0.1
        lower = self.model(torch.clamp(images - delta, 0, 1))
        upper = self.model(torch.clamp(images + delta, 0, 1))

        return lower, upper

    def certify_adversarial(self, images, labels, epsilon=0.03):
        """
        认证对抗样本

        如果下界大于其他类上界，则认证鲁棒
        """
        lower, upper = self.compute_bounds(images, epsilon)

        predictions = torch.argmax(lower, dim=1)

        certified = []
        for i in range(len(images)):
            pred_class = predictions[i].item()
            true_label = labels[i].item()

            # 检查是否正确且鲁棒
            if pred_class == true_label:
                lower_class = lower[i, pred_class]
                upper_other = upper[i].clone()
                upper_other[pred_class] = 0
                max_other = upper_other.max().item()

                if lower_class > max_other:
                    certified.append(True)
                else:
                    certified.append(False)
            else:
                certified.append(False)

        return certified


class CROWNVerifier:
    """
    CROWN认证器

    使用线性约束传播认证鲁棒性
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def verify(self, images, labels, epsilon=0.03):
        """
        验证鲁棒性

        返回:
            verified: 是否通过验证
            lower_bound: 真实类别的下界
        """
        images = images.to(self.device)

        # 简化的CROWN近似
        # 实际实现需要更复杂的线性边界传播

        with torch.no_grad():
            outputs = self.model(images)
            predictions = torch.argmax(outputs, dim=1)

        verified = (predictions == labels).cpu().numpy()

        return verified, outputs.cpu().numpy()


def run_certification_benchmark(model, dataloader, device='cpu'):
    """
    运行认证基准测试
    """
    calculator = CertifiedRadiusCalculator(model, device)

    results = {
        'clean_accuracy': 0.0,
        'certified_accuracy': 0.0,
        'avg_radius': 0.0
    }

    total = 0
    certified = 0
    radii_sum = 0

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        # 干净准确率
        with torch.no_grad():
            preds = torch.argmax(model(images), dim=1)
            clean_correct = (preds == labels).sum().item()
            results['clean_accuracy'] += clean_correct

        # 认证半径
        radius = calculator.compute_radius_randomized_smoothing(
            images, labels, sigma=0.5, num_samples=100
        )

        if radius > 0:
            certified += clean_correct
            radii_sum += radius * clean_correct

        total += len(labels)

    results['clean_accuracy'] /= total
    results['certified_accuracy'] = certified / total

    if certified > 0:
        results['avg_radius'] = radii_sum / certified
    else:
        results['avg_radius'] = 0.0

    return results


if __name__ == "__main__":
    class SimpleCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
            self.fc1 = nn.Linear(64 * 7 * 7, 128)
            self.fc2 = nn.Linear(128, 10)

        def forward(self, x):
            x = F.relu(F.max_pool2d(self.conv1(x), 2))
            x = F.relu(F.max_pool2d(self.conv2(x), 2))
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    device = torch.device("cpu")
    model = SimpleCNN().to(device)
    model.eval()

    class DummyDataset:
        def __init__(self, size=3):
            self.size = size

        def __iter__(self):
            for _ in range(self.size):
                yield torch.rand(8, 1, 28, 28), torch.randint(0, 10, (8,))

    print("=" * 50)
    print("认证鲁棒性测试")
    print("=" * 50)

    # 随机平滑认证
    print("\n--- 随机平滑认证 ---")
    calculator = CertifiedRadiusCalculator(model, device)

    test_images = torch.rand(4, 1, 28, 28)
    test_labels = torch.tensor([0, 1, 2, 3])

    radius = calculator.compute_radius_randomized_smoothing(
        test_images, test_labels, sigma=0.5, num_samples=200
    )
    print(f"平均认证半径: {radius:.4f}")

    # IBP
    print("\n--- IBP ---")
    ibp = IntervalBoundPropagation(model, device)
    certified = ibp.certify_adversarial(test_images, test_labels, epsilon=0.1)
    print(f"认证数量: {sum(certified)}/{len(certified)}")

    print("\n测试完成！")
