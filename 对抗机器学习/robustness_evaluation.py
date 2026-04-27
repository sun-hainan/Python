# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / robustness_evaluation

本文件实现 robustness_evaluation 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class RobustnessEvaluator:
    """
    鲁棒性综合评估器
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.model.to(device)
        self.model.eval()

    def evaluate_clean_accuracy(self, dataloader):
        """评估干净样本准确率"""
        correct = 0
        total = 0

        with torch.no_grad():
            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                preds = torch.argmax(outputs, dim=1)

                correct += (preds == labels).sum().item()
                total += len(labels)

        return correct / total

    def evaluate_adversarial_accuracy(self, dataloader, epsilon=0.03, attack='pgd', num_iter=20):
        """评估对抗鲁棒性"""
        correct = 0
        total = 0

        for images, labels in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            # 生成对抗样本
            adversarial = self._generate_adversarial(images, labels, epsilon, attack, num_iter)

            with torch.no_grad():
                outputs = self.model(adversarial)
                preds = torch.argmax(outputs, dim=1)

                correct += (preds == labels).sum().item()
                total += len(labels)

        return correct / total

    def _generate_adversarial(self, images, labels, epsilon, attack, num_iter):
        """生成对抗样本"""
        if attack == 'pgd':
            lower = torch.clamp(images - epsilon, 0, 1)
            upper = torch.clamp(images + epsilon, 0, 1)

            adversarial = images.clone().uniform_(-epsilon, epsilon)
            adversarial = torch.clamp(adversarial, lower, upper).detach()

            for _ in range(num_iter):
                adversarial.requires_grad = True
                outputs = self.model(adversarial)
                loss = F.cross_entropy(outputs, labels)

                self.model.zero_grad()
                loss.backward()

                grad = adversarial.grad.data
                adversarial = torch.clamp(adversarial + 0.01 * torch.sign(grad), lower, upper).detach()

            return adversarial

        elif attack == 'fgsm':
            images.requires_grad = True
            outputs = self.model(images)
            loss = F.cross_entropy(outputs, labels)

            self.model.zero_grad()
            loss.backward()

            grad = images.grad.data
            return torch.clamp(images + epsilon * torch.sign(grad), 0, 1).detach()

    def compute_local_lipschitz(self, images, labels, epsilon=0.1, num_samples=100):
        """
        计算局部Lipschitz常数

        使用有限差分法估计
        """
        lipschitz_estimates = []

        for i in range(min(len(images), num_samples)):
            img = images[i:i+1]
            label = labels[i:i+1]

            # 原始预测
            with torch.no_grad():
                out = self.model(img)
                pred = torch.argmax(out, dim=1).item()

            if pred != label.item():
                continue

            # 随机方向扰动
            max_ratio = 0.0

            for _ in range(10):
                direction = torch.randn_like(img)
                direction = direction / direction.norm()

                for dist in [0.01, 0.02, 0.05, 0.1]:
                    perturbed = img + direction * dist
                    perturbed = torch.clamp(perturbed, 0, 1)

                    with torch.no_grad():
                        pert_out = self.model(perturbed)
                        pert_pred = torch.argmax(pert_out, dim=1).item()

                        if pert_pred != pred:
                            ratio = dist
                            max_ratio = max(max_ratio, ratio)
                            break

            if max_ratio > 0:
                lipschitz_estimates.append(ratio)

        return np.mean(lipschitz_estimates) if lipschitz_estimates else 0.0

    def evaluate_certified_radius(self, images, labels, num_samples=100, sigma=0.5):
        """
        评估认证半径（随机平滑）

        参数:
            sigma: 噪声标准差
        """
        radii = []

        for i in range(len(images)):
            img = images[i:i+1]
            label = labels[i].item()

            # 多次采样
            predictions = []

            for _ in range(num_samples):
                noise = torch.randn_like(img) * sigma
                noisy = torch.clamp(img + noise, 0, 1)

                with torch.no_grad():
                    pred = torch.argmax(self.model(noisy), dim=1).item()
                    predictions.append(pred)

            # 投票
            from collections import Counter
            vote = Counter(predictions).most_common(1)[0][0]
            votes = Counter(predictions)[vote]

            # 估计认证半径
            if votes > num_samples * 0.5:
                radius = sigma * 0.5
            else:
                radius = 0.0

            radii.append(radius)

        return np.mean(radii)

    def generate_evaluation_report(self, dataloader, epsilon=0.03):
        """生成完整评估报告"""
        report = {}

        # 干净准确率
        report['clean_accuracy'] = self.evaluate_clean_accuracy(dataloader)

        # 对抗准确率
        report['adversarial_accuracy'] = self.evaluate_adversarial_accuracy(
            dataloader, epsilon=epsilon, attack='pgd', num_iter=20
        )

        # FGSM对抗准确率
        report['fgsm_accuracy'] = self.evaluate_adversarial_accuracy(
            dataloader, epsilon=epsilon, attack='fgsm'
        )

        return report


class BoundaryEdgeDetector:
    """
    决策边界与边缘检测
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def estimate_boundary_distance(self, images, labels, num_directions=20):
        """估计到决策边界的距离"""
        distances = []

        for i in range(len(images)):
            img = images[i:i+1]
            label = labels[i].item()

            min_dist = float('inf')

            for _ in range(num_directions):
                direction = torch.randn_like(img).view(1, -1)
                direction = direction / direction.norm()

                # 二分搜索
                low, high = 0.0, 1.0
                for _ in range(10):
                    mid = (low + high) / 2
                    perturbed = img + direction.view_as(img) * mid
                    perturbed = torch.clamp(perturbed, 0, 1)

                    with torch.no_grad():
                        pred = torch.argmax(self.model(perturbed), dim=1).item()

                    if pred != label:
                        high = mid
                    else:
                        low = mid

                min_dist = min(min_dist, (low + high) / 2)

            distances.append(min_dist)

        return np.array(distances)


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

    class DummyDataset:
        def __init__(self, size=5):
            self.size = size

        def __iter__(self):
            for _ in range(self.size):
                yield torch.rand(16, 1, 28, 28), torch.randint(0, 10, (16,))

    print("=" * 50)
    print("鲁棒性评估测试")
    print("=" * 50)

    evaluator = RobustnessEvaluator(model, device)

    report = evaluator.generate_evaluation_report(DummyDataset(5), epsilon=0.1)

    print("\n评估报告:")
    for key, value in report.items():
        print(f"  {key}: {value:.2%}")

    print("\n测试完成！")
