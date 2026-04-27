# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / deep_sweep

本文件实现 deep_sweep 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class DeepSweepDefense:
    """
    DeepSweep权重扰动防御

    通过分析梯度的方向性，在权重空间中找到最能提升鲁棒性的扰动方向
    """

    def __init__(self, model, device='cpu'):
        """
        参数:
            model: 待防御的模型
            device: 计算设备
        """
        self.model = model
        self.device = device
        self.model.to(device)

    def compute_weight_sensitivity(self, dataloader, loss_fn=F.cross_entropy):
        """
        计算权重敏感度：衡量每个权重参数对损失的影响程度

        参数:
            dataloader: 数据加载器
            loss_fn: 损失函数

        返回:
            sensitivities: 每个参数的敏感度字典
        """
        self.model.eval()
        sensitivities = {}

        # 累积梯度平方作为敏感度指标
        for images, labels in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            for name, param in self.model.named_parameters():
                if param.requires_grad:
                    param.requires_grad = True

            outputs = self.model(images)
            loss = loss_fn(outputs, labels)

            self.model.zero_grad()
            loss.backward()

            for name, param in self.model.named_parameters():
                if param.grad is not None:
                    # 使用梯度绝对值作为敏感度
                    sens = param.grad.abs().mean().item()
                    if name not in sensitivities:
                        sensitivities[name] = []
                    sensitivities[name].append(sens)

        # 计算平均敏感度
        avg_sensitivities = {k: np.mean(v) for k, v in sensitivities.items()}

        return avg_sensitivities

    def apply_weight_perturbation(self, perturbation_dict):
        """
        应用权重扰动

        参数:
            perturbation_dict: 扰动字典 {param_name: perturbation_tensor}
        """
        with torch.no_grad():
            for name, perturbation in perturbation_dict.items():
                # 找到对应参数并应用扰动
                for param_name, param in self.model.named_parameters():
                    if param_name == name:
                        param.add_(perturbation)

    def find_adversarial_weight_direction(self, images, labels, loss_fn=F.cross_entropy):
        """
        找到能最大提升对抗鲁棒性的权重扰动方向

        通过分析损失对权重的梯度，找到使模型在对抗扰动下损失增大的方向

        参数:
            images: 输入图像
            labels: 标签
            loss_fn: 损失函数

        返回:
            perturbation_dict: 权重扰动方向字典
        """
        self.model.train()

        outputs = self.model(images)
        loss = loss_fn(outputs, labels)

        self.model.zero_grad()
        loss.backward()

        perturbation_dict = {}

        for name, param in self.model.named_parameters():
            if param.grad is not None:
                # 沿梯度方向扰动
                perturbation_dict[name] = param.grad.clone()

        return perturbation_dict

    def sweep_weight_perturbation(self, images, labels, epsilon=0.01, num_directions=10):
        """
        在多个权重方向上进行"扫荡"，找到最佳扰动

        参数:
            images: 测试图像
            labels: 测试标签
            epsilon: 扰动幅度
            num_directions: 探索的方向数

        返回:
            best_direction: 最佳扰动方向
            best_loss: 对抗样本的最小损失
        """
        self.model.eval()

        # 生成多个随机扰动方向
        best_direction = None
        best_loss = float('inf')

        for i in range(num_directions):
            # 记录当前权重
            original_weights = {}
            for name, param in self.model.named_parameters():
                original_weights[name] = param.clone()

            # 生成随机扰动
            perturbation_dict = {}
            for name, param in self.model.named_parameters():
                noise = torch.randn_like(param) * epsilon
                perturbation_dict[name] = noise
                param.add_(noise)

            # 评估扰动后的模型
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(images)
                # 对抗样本评估（简化：用PGD）
                adv_images = self.pgd_attack_simple(images, labels)
                adv_outputs = self.model(adv_images)
                adv_loss = F.cross_entropy(adv_outputs, labels).item()

            if adv_loss > best_loss:
                best_loss = adv_loss
                best_direction = {k: v.clone() for k, v in perturbation_dict.items()}

            # 恢复权重
            with torch.no_grad():
                for name, param in self.model.named_parameters():
                    param.copy_(original_weights[name])

        return best_direction, best_loss

    def pgd_attack_simple(self, images, labels, epsilon=0.03, alpha=0.001, num_iter=10):
        """简化版PGD攻击"""
        lower_bound = torch.clamp(images - epsilon, 0, 1)
        upper_bound = torch.clamp(images + epsilon, 0, 1)

        adversarial = images.clone().uniform_(-epsilon, epsilon)
        adversarial = torch.clamp(adversarial, lower_bound, upper_bound).detach()

        for _ in range(num_iter):
            adversarial.requires_grad = True
            outputs = self.model(adversarial)
            loss = F.cross_entropy(outputs, labels)

            self.model.zero_grad()
            loss.backward()

            grad = adversarial.grad.data
            adversarial = torch.clamp(adversarial + alpha * torch.sign(grad), lower_bound, upper_bound).detach()

        return adversarial


class WeightNoiseDefense:
    """
    权重噪声防御

    通过向权重添加Gaussian噪声来提升对对抗攻击的鲁棒性。
    这是一种随机化防御方法，类似于输入随机化。
    """

    def __init__(self, model, sigma=0.01, device='cpu'):
        """
        参数:
            model: 原始模型
            sigma: 噪声标准差
            device: 计算设备
        """
        self.model = model
        self.sigma = sigma
        self.device = device

    def forward_with_noise(self, x):
        """带权重噪声的前向传播"""
        # 保存原始权重
        original_weights = {}
        for name, param in self.model.named_parameters():
            original_weights[name] = param.clone()

            # 添加噪声
            noise = torch.randn_like(param) * self.sigma
            param.add_(noise)

        # 前向传播
        with torch.no_grad():
            output = self.model(x)

        # 恢复原始权重
        with torch.no_grad():
            for name, param in self.model.named_parameters():
                param.copy_(original_weights[name])

        return output

    def predict_with_noise(self, x, num_samples=10):
        """
        多次采样噪声并平均预测

        参数:
            x: 输入
            num_samples: 采样次数

        返回:
            averaged_logits: 平均后的logits
        """
        all_outputs = []

        for _ in range(num_samples):
            output = self.forward_with_noise(x)
            all_outputs.append(output)

        return torch.stack(all_outputs).mean(dim=0)


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

    # 虚拟数据加载器
    class DummyDataset:
        def __init__(self, size=5):
            self.size = size

        def __iter__(self):
            for _ in range(self.size):
                images = torch.rand(8, 1, 28, 28)
                labels = torch.randint(0, 10, (8,))
                yield images, labels

    print("=" * 50)
    print("DeepSweep权重扰动防御测试")
    print("=" * 50)

    # DeepSweep测试
    deepsweep = DeepSweepDefense(model, device)

    test_images = torch.rand(4, 1, 28, 28).to(device)
    test_labels = torch.tensor([0, 1, 2, 3]).to(device)

    # 权重敏感度分析
    print("\n--- 权重敏感度分析 ---")
    sensitivities = deepsweep.compute_weight_sensitivity(DummyDataset(3))
    sorted_sens = sorted(sensitivities.items(), key=lambda x: x[1], reverse=True)[:5]
    print("Top 5敏感权重:")
    for name, sens in sorted_sens:
        print(f"  {name}: {sens:.6f}")

    # 找最佳扰动方向
    print("\n--- 权重扰动方向搜索 ---")
    best_dir, best_loss = deepsweep.sweep_weight_perturbation(
        test_images, test_labels, epsilon=0.001, num_directions=5
    )
    print(f"最佳扰动方向损失: {best_loss:.4f}")

    # 权重噪声防御测试
    print("\n--- 权重噪声防御 ---")
    noise_defense = WeightNoiseDefense(model, sigma=0.01, device=device)

    with torch.no_grad():
        clean_output = model(test_images)
        clean_pred = torch.argmax(clean_output, dim=1)
        print(f"原始预测: {clean_pred.cpu().numpy()}")

    # 带噪声预测
    noisy_output = noise_defense.forward_with_noise(test_images)
    noisy_pred = torch.argmax(noisy_output, dim=1)
    print(f"带噪声预测: {noisy_pred.cpu().numpy()}")

    # 多次采样平均
    averaged_output = noise_defense.predict_with_noise(test_images, num_samples=5)
    averaged_pred = torch.argmax(averaged_output, dim=1)
    print(f"噪声平均预测: {averaged_pred.cpu().numpy()}")

    print("\n测试完成！")
