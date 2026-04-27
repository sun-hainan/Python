# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / advanced_attacks

本文件实现 advanced_attacks 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class AutoAttack:
    """
    AutoAttack 组合攻击

    组合FGSM, PGD, APGD, Square等多种攻击方法
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.model.to(device)
        self.model.eval()

    def fgsm_attack(self, images, labels, epsilon=0.03):
        """FGSM攻击"""
        images.requires_grad = True
        outputs = self.model(images)
        loss = F.cross_entropy(outputs, labels)

        self.model.zero_grad()
        loss.backward()

        grad = images.grad.data
        perturbation = epsilon * torch.sign(grad)

        return torch.clamp(images + perturbation, 0, 1).detach()

    def pgd_attack(self, images, labels, epsilon=0.03, alpha=0.001, num_iter=40):
        """PGD攻击"""
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
            adversarial = torch.clamp(adversarial + alpha * torch.sign(grad), lower, upper).detach()

        return adversarial

    def apgd_attack(self, images, labels, epsilon=0.03, num_iter=100):
        """APGD (Adaptive PGD) 攻击"""
        # 简化的APGD实现
        lower = torch.clamp(images - epsilon, 0, 1)
        upper = torch.clamp(images + epsilon, 0, 1)

        adversarial = images.clone().detach()
        adversarial.requires_grad = True

        for i in range(num_iter):
            # 自适应步长
            alpha = epsilon / 10 if i < num_iter // 2 else epsilon / 5

            outputs = self.model(adversarial)
            loss = F.cross_entropy(outputs, labels)

            self.model.zero_grad()
            loss.backward()

            grad = adversarial.grad.data
            adversarial = torch.clamp(adversarial + alpha * torch.sign(grad), lower, upper).detach()
            adversarial.requires_grad = True

        return adversarial.detach()

    def square_attack(self, images, labels, epsilon=0.03, n_iter=5000):
        """
        Square Attack

        随机添加稀疏的方形扰动
        """
        adversarial = images.clone().detach()

        batch_size = images.size(0)
        side = int(np.sqrt(images.size(2) * images.size(3) * 0.1))  # 10%面积

        for _ in range(n_iter):
            # 随机选择位置
            x = np.random.randint(0, images.size(2) - side)
            y = np.random.randint(0, images.size(3) - side)

            # 随机扰动
            delta = torch.zeros_like(images)
            delta[:, :, x:x+side, y:y+side] = torch.randn(batch_size, 1, side, side, device=self.device) * epsilon

            # 接受或拒绝
            candidate = torch.clamp(adversarial + delta, 0, 1)

            with torch.no_grad():
                outputs = self.model(candidate)
                preds = torch.argmax(outputs, dim=1)
                current_preds = torch.argmax(self.model(adversarial), dim=1)

                # 如果攻击成功或置信度降低，接受扰动
                if (preds != labels).any() or (F.softmax(outputs, dim=1).max(dim=1)[0] < F.softmax(self.model(adversarial), dim=1).max(dim=1)[0]).any():
                    adversarial = candidate

        return adversarial

    def attack(self, images, labels, verbose=False):
        """
        运行组合攻击

        返回最强的对抗样本
        """
        attacks = {
            'fgsm': self.fgsm_attack(images, labels, epsilon=0.03),
            'pgd': self.pgd_attack(images, labels, epsilon=0.03, num_iter=20),
        }

        best_adversarial = None
        best_loss = float('-inf')

        for name, adv in attacks.items():
            with torch.no_grad():
                outputs = self.model(adv)
                loss = F.cross_entropy(outputs, labels)

                if loss > best_loss:
                    best_loss = loss
                    best_adversarial = adv

                if verbose:
                    preds = torch.argmax(outputs, dim=1)
                    success = (preds != labels).float().mean().item()
                    print(f"  {name}: 成功率={success:.2%}")

        return best_adversarial


class SPSAAttack:
    """
    SPSA (Simultaneous Perturbation Stochastic Approximation) 攻击

    使用双向随机扰动估计梯度
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def attack(self, images, labels, epsilon=0.03, num_iter=100, gamma=0.01, delta=0.01):
        """
        SPSA攻击

        参数:
            delta: 扰动幅度
        """
        images = images.to(self.device)
        labels = labels.to(self.device)

        adversarial = images.clone().detach()

        for i in range(num_iter):
            # 生成双向扰动
            delta_plus = torch.randn_like(images) * delta
            delta_minus = -delta_plus

            # 估计梯度
            with torch.no_grad():
                # f(x + delta)
                adv_plus = torch.clamp(images + delta_plus, 0, 1)
                loss_plus = F.cross_entropy(self.model(adv_plus), labels)

                # f(x - delta)
                adv_minus = torch.clamp(images + delta_minus, 0, 1)
                loss_minus = F.cross_entropy(self.model(adv_minus), labels)

            # 梯度估计
            grad_estimate = (loss_plus - loss_minus) / (2 * delta_plus) * delta_plus.sign()

            # 更新
            alpha = gamma / (i + 1)
            adversarial = torch.clamp(adversarial - alpha * grad_estimate.sign(), images - epsilon, images + epsilon)
            adversarial = torch.clamp(adversarial, 0, 1)

        return adversarial.detach()


class CWL2AttackSimplified:
    """
    简化的C&W L2攻击实现
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def attack(self, images, labels, epsilon=0.5, max_iter=100, learning_rate=0.01):
        """
        C&W L2攻击
        """
        images = images.to(self.device)

        # 参数化扰动
        delta = torch.zeros_like(images).uniform_(-epsilon, epsilon).requires_grad_(True).to(self.device)
        optimizer = torch.optim.Adam([delta], lr=learning_rate)

        for i in range(max_iter):
            optimizer.zero_grad()

            adversarial = torch.tanh(delta) * 0.5 + 0.5

            outputs = self.model(adversarial)

            # C&W损失
            one_hot = torch.zeros_like(outputs).scatter_(1, labels.unsqueeze(1), 1)
            real = (outputs * one_hot).sum(dim=1)
            other = (outputs * (1 - one_hot)).max(dim=1)[0]

            loss = -torch.clamp(other - real + 50, min=0).sum()

            # L2正则化
            perturbation = adversarial - images
            loss = loss + torch.sum(perturbation ** 2)

            loss.backward()
            optimizer.step()

        with torch.no_grad():
            adversarial = torch.tanh(delta) * 0.5 + 0.5

        return adversarial.detach()


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

    torch.manual_seed(42)
    test_images = torch.rand(4, 1, 28, 28).to(device)
    test_labels = torch.tensor([0, 1, 2, 3]).to(device)

    print("=" * 50)
    print("高级对抗攻击测试")
    print("=" * 50)

    # AutoAttack
    print("\n--- AutoAttack ---")
    aa = AutoAttack(model, device)
    adv = aa.attack(test_images, test_labels, verbose=True)

    # SPSA
    print("\n--- SPSA ---")
    spsa = SPSAAttack(model, device)
    adv_spsa = spsa.attack(test_images, test_labels, epsilon=0.1, num_iter=50)

    with torch.no_grad():
        print(f"SPSA成功率: {(torch.argmax(model(adv_spsa), dim=1) != test_labels).float().mean():.2%}")

    print("\n测试完成！")
