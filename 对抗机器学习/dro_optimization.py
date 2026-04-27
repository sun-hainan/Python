# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / dro_optimization

本文件实现 dro_optimization 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.optimize import minimize


class DistributionallyRobustOptimizer:
    """
    分布鲁棒优化器

    通过在参数空间扰动数据分布来找到更鲁棒的模型
    """

    def __init__(self, model, device='cpu', epsilon=0.1, num_samples=10):
        """
        参数:
            model: 待优化模型
            epsilon: 分布扰动半径
            num_samples: 分布采样数
        """
        self.model = model
        self.device = device
        self.epsilon = epsilon
        self.num_samples = num_samples

    def worst_case_loss(self, images, labels, loss_fn=F.cross_entropy):
        """
        计算最坏情况损失

        通过在输入上添加扰动来模拟分布扰动
        """
        worst_loss = 0.0

        for _ in range(self.num_samples):
            # 在输入空间采样扰动
            perturbation = torch.randn_like(images) * self.epsilon
            perturbed_images = torch.clamp(images + perturbation, 0, 1)

            # 计算损失
            outputs = self.model(perturbed_images)
            loss = loss_fn(outputs, labels)
            worst_loss = max(worst_loss, loss.item())

        return worst_loss

    def dro_train_step(self, images, labels, base_optimizer, lr=0.001):
        """
        DRO训练步骤

        参数:
            images: 输入图像
            labels: 标签
            base_optimizer: 基础优化器
            lr: 学习率

        返回:
            loss: 当前步的损失
        """
        self.model.train()

        # 计算干净损失
        outputs = self.model(images)
        clean_loss = F.cross_entropy(outputs, labels)

        # 计算对抗损失（最坏情况）
        adversarial_images = images + torch.randn_like(images) * self.epsilon
        adversarial_images = torch.clamp(adversarial_images, 0, 1).detach()
        adversarial_images.requires_grad = True

        adv_outputs = self.model(adversarial_images)
        adv_loss = F.cross_entropy(adv_outputs, labels)

        # 组合损失
        loss = clean_loss + adv_loss

        base_optimizer.zero_grad()
        loss.backward()
        base_optimizer.step()

        return loss.item()


class FGSMDRTraining:
    """
    基于FGSM的分布鲁棒训练

    通过在特征空间扰动来模拟分布变化
    """

    def __init__(self, model, device='cpu', epsilon=0.03):
        self.model = model
        self.device = device
        self.epsilon = epsilon

    def feature_perturbation(self, images, labels, target_layer='fc1'):
        """
        在中间层进行扰动

        这比在输入层扰动更能捕捉语义变化
        """
        # 注册hook获取中间特征
        features = {}

        def hook_fn(module, input, output):
            features['fc1'] = output

        handle = self.model.fc1.register_forward_hook(hook_fn)

        # 前向传播
        outputs = self.model(images)

        handle.remove()

        # 在特征空间添加扰动
        if 'fc1' in features:
            feat = features['fc1'].clone()
            feat.requires_grad = True

            # 计算对特征的梯度
            loss = F.cross_entropy(outputs, labels)
            self.model.zero_grad()
            loss.backward()

            if feat.grad is not None:
                # 沿梯度方向扰动
                feat_adv = feat + self.epsilon * torch.sign(feat.grad)
            else:
                feat_adv = feat
        else:
            feat_adv = features.get('fc1', torch.zeros_like(images.view(len(images), -1)))

        return feat_adv

    def dro_loss(self, images, labels):
        """
        计算DRO损失：在输入和特征空间同时扰动
        """
        # 干净损失
        clean_outputs = self.model(images)
        clean_loss = F.cross_entropy(clean_outputs, labels)

        # 输入空间对抗扰动
        images_adv = images + torch.randn_like(images) * self.epsilon
        images_adv = torch.clamp(images_adv, 0, 1).detach()
        images_adv.requires_grad = True

        adv_outputs = self.model(images_adv)
        adv_loss = F.cross_entropy(adv_outputs, labels)

        # 组合
        loss = clean_loss + adv_loss

        return loss


class CVaROptimizer:
    """
    CVaR（Conditional Value at Risk）优化器

    CVaR关注最坏情况的尾部风险，是比风险最大化更保守的度量
    CVaR_α = E[loss | loss >= VaR_α]
    """

    def __init__(self, model, device='cpu', alpha=0.05, num_samples=100):
        """
        参数:
            alpha: 风险水平（如0.05表示关注最差的5%样本）
            num_samples: 采样数
        """
        self.model = model
        self.device = device
        self.alpha = alpha
        self.num_samples = num_samples

    def compute_cvar_loss(self, images, labels, epsilon=0.03):
        """
        计算CVaR损失

        参数:
            epsilon: 扰动半径

        返回:
            cvar_loss: CVaR损失
            var_loss: VaR损失
        """
        losses = []

        for i in range(len(images)):
            img = images[i:i + 1]
            label = labels[i:i + 1]

            # 采样多个扰动
            img_losses = []
            for _ in range(self.num_samples):
                perturbation = torch.randn_like(img) * epsilon
                pert_img = torch.clamp(img + perturbation, 0, 1)

                with torch.no_grad():
                    output = self.model(pert_img)
                    loss = F.cross_entropy(output, label, reduction='none')
                    img_losses.append(loss.item())

            img_losses = torch.tensor(img_losses)
            losses.append(img_losses.mean())

        losses = torch.tensor(losses)

        # 计算VaR和CVaR
        sorted_losses, _ = torch.sort(losses)
        var_idx = int(len(sorted_losses) * self.alpha)
        var_loss = sorted_losses[var_idx] if var_idx < len(sorted_losses) else sorted_losses[-1]

        # CVaR = VaR以上的平均损失
        tail_losses = sorted_losses[var_idx:]
        cvar_loss = tail_losses.mean() if len(tail_losses) > 0 else sorted_losses.mean()

        return cvar_loss, var_loss


class GroupDRO:
    """
    Group Distributionally Robust Optimization

    考虑样本属于不同组的情况，优化最坏组性能
    """

    def __init__(self, model, num_groups, device='cpu', step_size=0.01):
        """
        参数:
            num_groups: 组数量
            step_size: 组权重更新步长
        """
        self.model = model
        self.num_groups = num_groups
        self.device = device
        self.step_size = step_size
        self.group_weights = torch.ones(num_groups) / num_groups

    def assign_groups(self, labels):
        """
        将样本分配到不同组

        这里按标签模数组数来简单分组
        """
        groups = (labels % self.num_groups).long()
        return groups

    def group_dro_loss(self, images, labels):
        """
        计算Group DRO损失

        返回:
            loss: 加权损失
            group_losses: 各组损失
        """
        groups = self.assign_groups(labels)
        group_losses = torch.zeros(self.num_groups, device=self.device)

        # 计算各组损失
        outputs = self.model(images)
        per_sample_loss = F.cross_entropy(outputs, labels, reduction='none')

        for g in range(self.num_groups):
            mask = (groups == g)
            if mask.sum() > 0:
                group_losses[g] = per_sample_loss[mask].mean()

        # 加权组合
        loss = (self.group_weights * group_losses).sum()

        return loss, group_losses

    def update_weights(self, group_losses):
        """
        更新组权重（增加高损失组的权重）
        """
        with torch.no_grad():
            # 指数更新
            self.group_weights = self.group_weights * torch.exp(self.step_size * group_losses.detach())
            # 归一化
            self.group_weights = self.group_weights / self.group_weights.sum()


class LagrangianDRO:
    """
    Lagrangian方法求解DRO

    通过拉格朗日乘子处理约束
    min_θ max_ρ E_ρ[L(θ)] subject to D(ρ||ρ_0) <= ε
    """

    def __init__(self, model, device='cpu', epsilon=0.1):
        self.model = model
        self.device = device
        self.epsilon = epsilon
        self.lambda_reg = 1.0  # 拉格朗日乘子

    def compute_augmented_loss(self, images, labels, gamma=0.1):
        """
        增广拉格朗日损失

        L_aug = E[L] + λ * (D_KL - ε) + γ/2 * (D_KL - ε)^2
        """
        # 干净损失
        outputs = self.model(images)
        empirical_loss = F.cross_entropy(outputs, labels)

        # KL散度惩罚（简化版：用扰动样本的损失差异近似）
        # 这里用一个简单的代理
        perturbed = images + torch.randn_like(images) * 0.01
        perturbed = torch.clamp(perturbed, 0, 1)

        with torch.no_grad():
            pert_outputs = self.model(perturbed)
            pert_loss = F.cross_entropy(pert_outputs, labels)

        # KL约束代理
        kl_penalty = torch.abs(pert_loss - empirical_loss)

        # 增广拉格朗日
        aug_loss = empirical_loss + self.lambda_reg * (kl_penalty - self.epsilon) + \
                   gamma / 2 * (kl_penalty - self.epsilon) ** 2

        return aug_loss

    def update_lambda(self, kl_value):
        """更新拉格朗日乘子"""
        self.lambda_reg += 0.01 * (kl_value - self.epsilon)
        self.lambda_reg = max(0, self.lambda_reg)  # 乘子非负


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
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # 虚拟数据
    class DummyDataset:
        def __init__(self, size=20):
            self.size = size

        def __iter__(self):
            for _ in range(self.size):
                images = torch.rand(32, 1, 28, 28)
                labels = torch.randint(0, 10, (32,))
                yield images, labels

    print("=" * 50)
    print("分布鲁棒优化（DRO）测试")
    print("=" * 50)

    # 基础DRO
    print("\n--- Distributionally Robust Optimizer ---")
    dro = DistributionallyRobustOptimizer(model, device, epsilon=0.1, num_samples=5)

    test_images = torch.rand(8, 1, 28, 28).to(device)
    test_labels = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7]).to(device)

    for epoch in range(3):
        loss = dro.dro_train_step(test_images, test_labels, optimizer)
        print(f"Epoch {epoch + 1}: DRO Loss={loss:.4f}")

    # CVaR优化
    print("\n--- CVaR Optimizer ---")
    cvar_opt = CVaROptimizer(model, device, alpha=0.1, num_samples=50)

    cvar_loss, var_loss = cvar_opt.compute_cvar_loss(test_images, test_labels, epsilon=0.05)
    print(f"CVaR Loss: {cvar_loss:.4f}, VaR Loss: {var_loss:.4f}")

    # Group DRO
    print("\n--- Group DRO ---")
    group_dro = GroupDRO(model, num_groups=5, device=device)

    for epoch in range(3):
        loss, group_losses = group_dro.group_dro_loss(test_images, test_labels)
        group_dro.update_weights(group_losses)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        print(f"Epoch {epoch + 1}: Loss={loss.item():.4f}, "
              f"Group Weights={[f'{w:.3f}' for w in group_dro.group_weights.tolist()]}")

    # Lagrangian DRO
    print("\n--- Lagrangian DRO ---")
    lag_dro = LagrangianDRO(model, device, epsilon=0.1)

    for epoch in range(3):
        aug_loss = lag_dro.compute_augmented_loss(test_images, test_labels)

        optimizer.zero_grad()
        aug_loss.backward()
        optimizer.step()

        print(f"Epoch {epoch + 1}: Aug Loss={aug_loss.item():.4f}, Lambda={lag_dro.lambda_reg:.4f}")

    print("\n测试完成！")
