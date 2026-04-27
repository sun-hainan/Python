# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / cw_attack

本文件实现 cw_attack 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class CWAttackL2:
    """
    C&W L2范数攻击

    通过优化找到最小L2范数扰动使模型误分类
    """

    def __init__(self, model, targeted=False, c=1.0, kappa=0, max_iter=1000, learning_rate=0.01):
        """
        参数:
            model: 目标分类模型
            targeted: 是否为有目标攻击
            c: 损失函数中常量，用于平衡分类损失和扰动范数
            kappa: 置信度参数，迫使攻击达到一定置信度
            max_iter: 最大迭代次数
            learning_rate: 优化器学习率
        """
        self.model = model
        self.targeted = targeted
        self.c = c
        self.kappa = kappa
        self.max_iter = max_iter
        self.lr = learning_rate

    def _attack_variable(self, original_images):
        """
        创建可学习的扰动变量

        参数:
            original_images: 原始图像 [B, C, H, W]

        返回:
            delta: 扰动变量（参数化后在tanh空间）
        """
        batch_size = original_images.size(0)
        device = next(self.model.parameters()).device

        # 在tanh空间参数化，避免裁剪操作
        delta = torch.zeros_like(original_images).uniform_(-1e-4, 1e-4).to(device)
        delta = nn.Parameter(delta)
        return delta

    def _logits_to_loss(self, logits, labels):
        """
        计算C&W损失函数

        公式: loss = ||delta||_2^2 + c * f(x+delta)
        其中f是精心设计的代理损失

        参数:
            logits: 模型输出的logits
            labels: 目标标签

        返回:
            loss: 损失值
        """
        num_classes = logits.size(1)

        # 计算目标logit和最大非目标logit
        one_hot_labels = torch.zeros_like(logits)
        one_hot_labels.scatter_(1, labels.unsqueeze(1), 1)

        # 有目标：所有非目标类别的最大值
        # 无目标：真实类别的logit
        if self.targeted:
            target_logits = (logits * (1 - one_hot_labels)).max(dim=1)[0]
            other_logits = (logits * one_hot_labels).sum(dim=1)
            diff = other_logits - target_logits
        else:
            real_logits = (logits * one_hot_labels).sum(dim=1)
            other_logits = (logits * (1 - one_hot_labels)).max(dim=1)[0]
            diff = other_logits - real_logits

        # 代理损失：满足置信度要求时为0
        f_loss = torch.clamp(diff + self.kappa, min=0)

        return f_loss

    def attack(self, images, labels):
        """
        执行C&W L2攻击

        参数:
            images: 原始图像
            labels: 真实标签（无目标）或目标标签（有目标）

        返回:
            adversarial_images: 对抗样本
        """
        device = next(self.model.parameters()).device
        images = images.to(device)
        labels = labels.to(labels)

        self.model.eval()

        # 初始化扰动变量
        delta = self._attack_variable(images)

        # 优化器：使用Adam
        optimizer = torch.optim.Adam([delta], lr=self.lr)

        for iteration in range(self.max_iter):
            optimizer.zero_grad()

            # 生成对抗样本（在tanh空间映射）
            adv_images = torch.tanh(delta) * 0.5 + 0.5  # [0,1]范围

            # 前向传播
            logits = self.model(adv_images)

            # 计算损失
            perturbation_loss = torch.sum(delta ** 2)
            classification_loss = self._logits_to_loss(logits, labels).sum()
            total_loss = perturbation_loss + self.c * classification_loss

            # 反向传播
            total_loss.backward()
            optimizer.step()

            # 检查是否攻击成功
            with torch.no_grad():
                predictions = torch.argmax(logits, dim=1)
                if self.targeted:
                    success = (predictions == labels).all()
                else:
                    success = (predictions != labels).all()

                if success and iteration > 10:
                    break

        # 返回最终对抗样本
        with torch.no_grad():
            adv_images = torch.tanh(delta) * 0.5 + 0.5

        return adv_images


def cw_attack_linf(model, images, labels, epsilon=0.03, c=1.0, max_iter=50):
    """
    C&W L-inf攻击

    参数:
        epsilon: L-inf扰动上界
        c: 损失权重系数
        max_iter: 迭代次数

    返回:
        adversarial_images: 对抗样本
    """
    device = next(model.parameters()).device
    images = images.to(device)
    labels = labels.to(labels)

    delta = torch.zeros_like(images).uniform_(-epsilon, epsilon).requires_grad_(True).to(device)

    optimizer = torch.optim.Adam([delta], lr=1e-3)

    for i in range(max_iter):
        optimizer.zero_grad()

        adv_images = torch.clamp(images + delta, 0, 1)
        logits = model(adv_images)

        # C&W L-inf损失
        one_hot = torch.zeros_like(logits).scatter_(1, labels.unsqueeze(1), 1)
        real_logit = (logits * one_hot).sum(dim=1)
        other_logit = (logits * (1 - one_hot)).max(dim=1)[0]
        f_loss = torch.clamp(other_logit - real_logit + 50, min=0).sum()

        loss = f_loss
        loss.backward()
        optimizer.step()

        # 投影到L-inf球内
        with torch.no_grad():
            delta.copy_(torch.clamp(delta, -epsilon, epsilon))

    return torch.clamp(images + delta, 0, 1)


def cw_attack_l0(model, images, labels, c=1.0, max_iter=1000):
    """
    C&W L0攻击：通过迭代减少修改的像素数量

    L0攻击通过依次固定不重要的像素来增加扰动的稀疏性。
    实现采用梯度下降结合像素重要性排序。

    参数:
        c: 损失权重
        max_iter: 最大迭代次数

    返回:
        adversarial_images: 对抗样本
    """
    device = next(model.parameters()).device
    images = images.to(device)
    labels = labels.to(labels)

    delta = torch.zeros_like(images).uniform_(-0.1, 0.1).requires_grad_(True).to(device)
    optimizer = torch.optim.Adam([delta], lr=0.01)

    for iteration in range(max_iter):
        optimizer.zero_grad()

        # 使用sigmoid将delta映射到[0,1]进行L0约束
        mask = torch.sigmoid(delta * 10)
        adv_images = torch.clamp(images + mask * torch.sign(delta), 0, 1)

        logits = model(adv_images)

        one_hot = torch.zeros_like(logits).scatter_(1, labels.unsqueeze(1), 1)
        real_logit = (logits * one_hot).sum(dim=1)
        other_logit = (logits * (1 - one_hot)).max(dim=1)[0]
        f_loss = torch.clamp(other_logit - real_logit + 50, min=0).sum()

        loss = f_loss + c * mask.sum()
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        mask = torch.sigmoid(delta * 10)
        adv_images = torch.clamp(images + mask * torch.sign(delta), 0, 1)

    return adv_images


if __name__ == "__main__":
    # 定义简单模型
    class SimpleModel(nn.Module):
        def __init__(self, num_classes=10):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv2d(1, 32, 3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d(1)
            )
            self.fc = nn.Linear(64, num_classes)

        def forward(self, x):
            x = self.conv(x)
            x = x.view(x.size(0), -1)
            return self.fc(x)

    device = torch.device("cpu")
    model = SimpleModel(num_classes=10).to(device)
    model.eval()

    torch.manual_seed(42)
    test_images = torch.rand(4, 1, 28, 28).to(device)
    test_labels = torch.tensor([3, 7, 2, 5]).to(device)

    print("=" * 50)
    print("C&W攻击测试")
    print("=" * 50)

    # 干净预测
    with torch.no_grad():
        clean_preds = torch.argmax(model(test_images), dim=1)
        print(f"原始预测: {clean_preds.cpu().numpy()}")

    # C&W L2攻击
    print("\n--- C&W L2 攻击 ---")
    cw_l2_attacker = CWAttackL2(model, targeted=False, c=1.0, kappa=0, max_iter=100)
    adv_images_l2 = cw_l2_attacker.attack(test_images, test_labels)

    with torch.no_grad():
        adv_preds_l2 = torch.argmax(model(adv_images_l2), dim=1)
        perturbation_l2 = torch.norm((adv_images_l2 - test_images).view(4, -1), dim=1, p=2)
        print(f"对抗预测: {adv_preds_l2.cpu().numpy()}")
        print(f"L2扰动范数: {perturbation_l2.cpu().numpy()}")

    # C&W L-inf攻击
    print("\n--- C&W L-inf 攻击 ---")
    adv_images_linf = cw_attack_linf(model, test_images, test_labels, epsilon=0.1, max_iter=30)

    with torch.no_grad():
        adv_preds_linf = torch.argmax(model(adv_images_linf), dim=1)
        perturbation_linf = torch.norm((adv_images_linf - test_images).view(4, -1), dim=1, p=float('inf'))
        print(f"对抗预测: {adv_preds_linf.cpu().numpy()}")
        print(f"L-inf扰动范数: {perturbation_linf.cpu().numpy()}")

    # 有目标攻击测试
    print("\n--- C&W 有目标攻击 ---")
    target_labels = torch.tensor([1, 1, 1, 1]).to(device)
    cw_targeted = CWAttackL2(model, targeted=True, c=1.0, kappa=0, max_iter=100)
    adv_images_targeted = cw_targeted.attack(test_images, target_labels)

    with torch.no_grad():
        targeted_preds = torch.argmax(model(adv_images_targeted), dim=1)
        print(f"目标标签: {target_labels.cpu().numpy()}")
        print(f"对抗预测: {targeted_preds.cpu().numpy()}")

    print("\n测试完成！")
