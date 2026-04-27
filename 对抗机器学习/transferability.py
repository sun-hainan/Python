# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / transferability

本文件实现 transferability 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class TransferabilityAnalyzer:
    """
    分析对抗样本迁移性的工具类
    """

    def __init__(self, source_model, target_models, device='cpu'):
        """
        参数:
            source_model: 源模型（生成对抗样本的模型）
            target_models: 目标模型列表（评估迁移性的模型）
            device: 计算设备
        """
        self.source_model = source_model
        self.target_models = target_models if isinstance(target_models, list) else [target_models]
        self.device = device

    def generate_adversarial(self, images, labels, method='pgd', epsilon=0.03, num_iter=20):
        """
        生成对抗样本

        参数:
            images: 原始图像
            labels: 真实标签
            method: 攻击方法 ('fgsm', 'pgd', 'mi-fgsm')
            epsilon: 扰动上界
            num_iter: 迭代次数
        """
        if method == 'fgsm':
            return self._fgsm(images, labels, epsilon)
        elif method == 'pgd':
            return self._pgd(images, labels, epsilon, num_iter)
        elif method == 'mi-fgsm':
            return self._mi_fgsm(images, labels, epsilon, num_iter)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _fgsm(self, images, labels, epsilon):
        """FGSM攻击"""
        images.requires_grad = True
        outputs = self.source_model(images)
        loss = F.cross_entropy(outputs, labels)

        self.source_model.zero_grad()
        loss.backward()

        grad = images.grad.data
        perturbation = epsilon * torch.sign(grad)

        return torch.clamp(images + perturbation, 0, 1).detach()

    def _pgd(self, images, labels, epsilon, num_iter, alpha=None):
        """PGD攻击"""
        if alpha is None:
            alpha = epsilon / 4

        lower = torch.clamp(images - epsilon, 0, 1)
        upper = torch.clamp(images + epsilon, 0, 1)

        adversarial = images.clone().uniform_(-epsilon, epsilon)
        adversarial = torch.clamp(adversarial, lower, upper).detach()

        for _ in range(num_iter):
            adversarial.requires_grad = True
            outputs = self.source_model(adversarial)
            loss = F.cross_entropy(outputs, labels)

            self.source_model.zero_grad()
            loss.backward()

            grad = adversarial.grad.data
            adversarial = torch.clamp(adversarial + alpha * torch.sign(grad), lower, upper).detach()

        return adversarial

    def _mi_fgsm(self, images, labels, epsilon, num_iter, decay=1.0):
        """
        MI-FGSM：带动量的FGSM

        通过累积梯度动量来生成更具迁移性的对抗样本
        """
        alpha = epsilon / 4
        momentum = torch.zeros_like(images)

        adversarial = images.clone().detach()

        for _ in range(num_iter):
            adversarial.requires_grad = True
            outputs = self.source_model(adversarial)
            loss = F.cross_entropy(outputs, labels)

            self.source_model.zero_grad()
            loss.backward()

            grad = adversarial.grad.data

            # 累积动量
            momentum = decay * momentum + grad / torch.norm(grad.view(len(grad), -1), dim=1, p=1).view(len(grad), 1, 1, 1)

            adversarial = torch.clamp(adversarial + alpha * torch.sign(momentum), 0, 1).detach()

        return adversarial

    def evaluate_transferability(self, adversarial_images, labels):
        """
        评估对抗样本在源模型和目标模型上的攻击效果

        返回:
            source_success: 源模型攻击成功率
            target_success: 各目标模型攻击成功率列表
        """
        labels = labels.to(self.device)

        # 源模型成功率
        with torch.no_grad():
            source_preds = torch.argmax(self.source_model(adversarial_images), dim=1)
            source_clean = torch.argmax(self.source_model(
                adversarial_images - (adversarial_images - adversarial_images)
            ), dim=1)

            # 原始预测正确的样本中，有多少被攻击成功
            source_success = ((source_preds != labels) & (source_clean == labels)).float().mean().item() if source_clean.sum() > 0 else 0

        # 目标模型成功率
        target_successes = []
        for target_model in self.target_models:
            target_model.eval()
            with torch.no_grad():
                target_preds = torch.argmax(target_model(adversarial_images), dim=1)
                target_success = (target_preds != labels).float().mean().item()
                target_successes.append(target_success)

        return source_success, target_successes


class EnsembleTransferAttack:
    """
    集成迁移攻击

    通过多个模型生成对抗样本，提升迁移成功率
    """

    def __init__(self, models, device='cpu'):
        """
        参数:
            models: 模型列表
            device: 计算设备
        """
        self.models = models
        self.device = device

    def ensemble_fgsm(self, images, labels, epsilon=0.03):
        """
        集成FGSM：聚合多个模型的梯度

        参数:
            images: 原始图像
            labels: 标签
            epsilon: 扰动上界
        """
        images.requires_grad = True
        total_grad = torch.zeros_like(images)

        for model in self.models:
            model.eval()
            outputs = model(images)
            loss = F.cross_entropy(outputs, labels)

            model.zero_grad()
            loss.backward()

            total_grad += images.grad.data

        # 平均梯度
        avg_grad = total_grad / len(self.models)
        perturbation = epsilon * torch.sign(avg_grad)

        return torch.clamp(images + perturbation, 0, 1).detach()

    def ensemble_pgd(self, images, labels, epsilon=0.03, num_iter=20):
        """
        集成PGD：使用多模型梯度平均
        """
        alpha = epsilon / 4
        lower = torch.clamp(images - epsilon, 0, 1)
        upper = torch.clamp(images + epsilon, 0, 1)

        adversarial = images.clone().uniform_(-epsilon, epsilon)
        adversarial = torch.clamp(adversarial, lower, upper).detach()

        for _ in range(num_iter):
            adversarial.requires_grad = True
            total_grad = torch.zeros_like(adversarial)

            for model in self.models:
                outputs = model(adversarial)
                loss = F.cross_entropy(outputs, labels)

                model.zero_grad()
                loss.backward()

                total_grad += adversarial.grad.data

            avg_grad = total_grad / len(self.models)
            adversarial = torch.clamp(adversarial + alpha * torch.sign(avg_grad), lower, upper).detach()

        return adversarial

    def diverse_input_ensemble(self, images, labels, epsilon=0.03, num_iter=20, input_diversity=True):
        """
        多样化输入集成

        对输入进行变换后集成攻击
        """
        alpha = epsilon / 4
        adversarial = images.clone().detach()

        for _ in range(num_iter):
            adversarial.requires_grad = True

            # 输入多样性：随机缩放和填充
            if input_diversity:
                scale = np.random.uniform(0.9, 1.1)
                pad = int(28 * (scale - 1) / 2)
                scaled = F.pad(adversarial, (pad, pad, pad, pad), mode='replicate')
                if scaled.shape[-1] > 28:
                    scaled = F.interpolate(scaled, size=(28, 28), mode='bilinear', align_corners=False)
            else:
                scaled = adversarial

            total_grad = torch.zeros_like(scaled)

            for model in self.models:
                outputs = model(scaled)
                loss = F.cross_entropy(outputs, labels)

                model.zero_grad()
                loss.backward()

                total_grad += scaled.grad.data

            avg_grad = total_grad / len(self.models)
            perturbation = alpha * torch.sign(avg_grad)

            # 反变换
            if input_diversity and scale != 1.0:
                # 简化的反变换
                pass

            adversarial = torch.clamp(adversarial + perturbation, 0, 1).detach()

        return adversarial


class TransferabilityEnhancer:
    """
    迁移性增强器

    研究和实现提高对抗样本迁移性的技术
    """

    def __init__(self, source_model, device='cpu'):
        self.source_model = source_model
        self.device = device

    def add_input_transformation(self, images, prob=0.5):
        """
        输入变换增强迁移性

        参数:
            images: 输入图像
            prob: 变换概率
        """
        transformed = []

        for img in images:
            t = img.clone()

            # 随机水平翻转
            if torch.rand(1) < prob:
                t = torch.flip(t, dims=[2])

            # 随机缩放
            if torch.rand(1) < prob:
                scale = np.random.uniform(0.9, 1.1)
                h, w = t.shape[1], t.shape[2]
                new_h, new_w = int(h * scale), int(w * scale)
                t = F.interpolate(t.unsqueeze(0), size=(new_h, new_w), mode='bilinear', align_corners=False).squeeze(0)

            transformed.append(t)

        return torch.stack(transformed).to(self.device)

    def randomization_layer(self, x, random_pad=4):
        """
        随机填充层：推理时添加随机性使决策边界更平滑

        参数:
            random_pad: 最大填充像素数
        """
        pad = np.random.randint(0, random_pad)
        if pad > 0:
            x = F.pad(x, (pad, pad, pad, pad), mode='replicate')
            # 随机裁剪回原大小
            h, w = x.shape[2], x.shape[3]
            start_h = np.random.randint(0, h - 28)
            start_w = np.random.randint(0, w - 28)
            x = x[:, :, start_h:start_h + 28, start_w:start_w + 28]

        return x


def compute_transferability_matrix(source_model, target_models, images, labels, method='pgd'):
    """
    计算迁移性矩阵

    返回:
        matrix: NxM矩阵，N为源模型数，M为目标模型数
    """
    results = {}

    for i, src_model in enumerate([source_model] if not isinstance(source_model, list) else source_model):
        row = []
        for j, tgt_model in enumerate(target_models):
            analyzer = TransferabilityAnalyzer(src_model, tgt_model)
            adv_images = analyzer.generate_adversarial(images, labels, method=method)
            _, target_success = analyzer.evaluate_transferability(adv_images, labels)
            row.append(target_success[0])

        results[f'source_{i}'] = row

    return results


if __name__ == "__main__":
    # 定义多个不同架构的模型
    class ModelA(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(),
                nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
                nn.AdaptiveAvgPool2d(1)
            )
            self.fc = nn.Linear(64, 10)

        def forward(self, x):
            x = self.conv(x)
            x = x.view(x.size(0), -1)
            return self.fc(x)

    class ModelB(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv2d(1, 64, 5, padding=2), nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),
                nn.AdaptiveAvgPool2d(1)
            )
            self.fc = nn.Linear(128, 10)

        def forward(self, x):
            x = self.conv(x)
            x = x.view(x.size(0), -1)
            return self.fc(x)

    class ModelC(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(),
                nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(),
                nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
                nn.AdaptiveAvgPool2d(1)
            )
            self.fc = nn.Linear(64, 10)

        def forward(self, x):
            x = self.conv(x)
            x = x.view(x.size(0), -1)
            return self.fc(x)

    device = torch.device("cpu")
    model_a = ModelA().to(device)
    model_b = ModelB().to(device)
    model_c = ModelC().to(device)

    torch.manual_seed(42)
    test_images = torch.rand(16, 1, 28, 28).to(device)
    test_labels = torch.randint(0, 10, (16,)).to(device)

    print("=" * 50)
    print("对抗样本迁移性分析")
    print("=" * 50)

    # 分析迁移性
    analyzer = TransferabilityAnalyzer(model_a, [model_b, model_c], device)

    # 在Model A上生成对抗样本
    print("\n--- 在 Model A 上生成对抗样本 ---")

    # MI-FGSM
    adv_mi = analyzer.generate_adversarial(test_images, test_labels, method='mi-fgsm', epsilon=0.1, num_iter=20)
    src_success, tgt_success = analyzer.evaluate_transferability(adv_mi, test_labels)
    print(f"MI-FGSM: 源成功率={src_success:.2%}, 迁移到Model B={tgt_success[0]:.2%}, Model C={tgt_success[1]:.2%}")

    # PGD
    adv_pgd = analyzer.generate_adversarial(test_images, test_labels, method='pgd', epsilon=0.1, num_iter=20)
    src_success, tgt_success = analyzer.evaluate_transferability(adv_pgd, test_labels)
    print(f"PGD: 源成功率={src_success:.2%}, 迁移到Model B={tgt_success[0]:.2%}, Model C={tgt_success[1]:.2%}")

    # 集成迁移攻击
    print("\n--- 集成迁移攻击 ---")
    ensemble = EnsembleTransferAttack([model_a, model_b], device)

    adv_ensemble = ensemble.ensemble_pgd(test_images, test_labels, epsilon=0.1, num_iter=20)

    analyzer_ab = TransferabilityAnalyzer(model_a, [model_b, model_c], device)
    _, tgt_success = analyzer_ab.evaluate_transferability(adv_ensemble, test_labels)
    print(f"集成A+B攻击: 迁移到Model B={tgt_success[0]:.2%}, Model C={tgt_success[1]:.2%}")

    # 全模型集成
    ensemble_all = EnsembleTransferAttack([model_a, model_b, model_c], device)
    adv_all = ensemble_all.ensemble_pgd(test_images, test_labels, epsilon=0.1, num_iter=20)

    analyzer_all = TransferabilityAnalyzer(model_a, [model_b, model_c], device)
    _, tgt_success = analyzer_all.evaluate_transferability(adv_all, test_labels)
    print(f"集成A+B+C攻击: 迁移到Model B={tgt_success[0]:.2%}, Model C={tgt_success[1]:.2%}")

    print("\n测试完成！")
