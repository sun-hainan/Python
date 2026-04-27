# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / robust_optimization

本文件实现 robust_optimization 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import copy


class PGDAdversarialTrainer:
    """
    PGD对抗训练器

    在每个训练步骤中：
    1. 对当前batch的样本生成对抗样本
    2. 用对抗样本计算损失并更新模型参数
    """

    def __init__(self, model, optimizer, device='cpu', epsilon=0.03, alpha=0.001, num_iter=7):
        """
        参数:
            model: 待训练的模型
            optimizer: 优化器
            device: 计算设备
            epsilon: 对抗扰动上界
            alpha: PGD步长
            num_iter: PGD迭代次数
        """
        self.model = model
        self.optimizer = optimizer
        self.device = device
        self.epsilon = epsilon
        self.alpha = alpha
        self.num_iter = num_iter

    def pgd_attack_train(self, images, labels):
        """
        生成PGD对抗样本用于训练

        参数:
            images: 原始图像
            labels: 真实标签

        返回:
            adversarial_images: 对抗样本
        """
        images = images.to(self.device)
        labels = labels.to(self.device)

        # 备份原始图像
        original_images = images.clone().detach()

        # 随机初始化（在epsilon球内）
        images = images + torch.zeros_like(images).uniform_(-self.epsilon, self.epsilon)
        images = torch.clamp(images, 0, 1).detach()
        images.requires_grad = True

        # PGD迭代
        for i in range(self.num_iter):
            outputs = self.model(images)
            loss = F.cross_entropy(outputs, labels)

            self.model.zero_grad()
            loss.backward()

            grad = images.grad.data
            images = images.detach() + self.alpha * torch.sign(grad)
            images = torch.clamp(images, original_images - self.epsilon, original_images + self.epsilon)
            images = torch.clamp(images, 0, 1).detach()
            images.requires_grad = True

        return images.detach()

    def train_epoch(self, dataloader, epoch_num=None):
        """
        执行一个epoch的对抗训练

        参数:
            dataloader: 训练数据加载器
            epoch_num: 当前epoch编号（用于打印）

        返回:
            avg_loss: 平均训练损失
            clean_acc: 干净样本准确率
            adv_acc: 对抗样本准确率
        """
        self.model.train()
        total_loss = 0.0
        total_clean_correct = 0
        total_adv_correct = 0
        total_samples = 0

        for batch_idx, (images, labels) in enumerate(dataloader):
            images = images.to(self.device)
            labels = labels.to(self.device)

            # 生成对抗样本
            adversarial_images = self.pgd_attack_train(images, labels)

            # 干净样本前向
            clean_outputs = self.model(images)
            clean_loss = F.cross_entropy(clean_outputs, labels)
            clean_correct = (torch.argmax(clean_outputs, dim=1) == labels).sum().item()

            # 对抗样本前向
            adv_outputs = self.model(adversarial_images)
            adv_loss = F.cross_entropy(adv_outputs, labels)
            adv_correct = (torch.argmax(adv_outputs, dim=1) == labels).sum().item()

            # 组合损失：干净损失 + 对抗损失
            loss = clean_loss + adv_loss

            # 反向传播并更新
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            # 统计
            total_loss += loss.item() * len(labels)
            total_clean_correct += clean_correct
            total_adv_correct += adv_correct
            total_samples += len(labels)

        avg_loss = total_loss / total_samples
        clean_acc = total_clean_correct / total_samples
        adv_acc = total_adv_correct / total_samples

        if epoch_num is not None:
            print(f"Epoch {epoch_num}: Loss={avg_loss:.4f}, Clean Acc={clean_acc:.2%}, Adv Acc={adv_acc:.2%}")

        return avg_loss, clean_acc, adv_acc


class FreeAdversarialTraining:
    """
    Free Adversarial Training（自由对抗训练）

    通过复用梯度计算来加速对抗训练。
    核心思想：在同一个minibatch上轮流计算干净样本和对抗样本的梯度，
    多次扰动但只进行一次前向传播。

    参考文献：Shafahi et al. "Free Adversarial Training" (2020)
    """

    def __init__(self, model, optimizer, device='cpu', epsilon=0.03, num_replays=4):
        """
        参数:
            num_replays: 每个样本的对抗扰动次数
        """
        self.model = model
        self.optimizer = optimizer
        self.device = device
        self.epsilon = epsilon
        self.num_replays = num_replays

    def train_epoch(self, dataloader, epoch_num=None):
        """
        执行Free对抗训练的一个epoch
        """
        self.model.train()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0

        for images, labels in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            batch_size = len(labels)
            images.requires_grad = True

            # 累积梯度
            cumulative_grad = None

            for replay in range(self.num_replays):
                outputs = self.model(images)
                loss = F.cross_entropy(outputs, labels)

                self.optimizer.zero_grad()
                loss.backward()

                if cumulative_grad is None:
                    cumulative_grad = [p.grad.clone() for p in self.model.parameters() if p.grad is not None]
                else:
                    for i, p in enumerate([p for p in self.model.parameters() if p.grad is not None]):
                        cumulative_grad[i] += p.grad

                # 更新图像（生成新的对抗样本）
                if replay < self.num_replays - 1:
                    grad = images.grad.data
                    images = images.detach() + self.epsilon * torch.sign(grad)
                    images = torch.clamp(images, 0, 1).detach()
                    images.requires_grad = True

            # 应用累积梯度
            self.optimizer.zero_grad()
            for p, g in zip([p for p in self.model.parameters() if p.grad is not None], cumulative_grad):
                p.grad = g

            self.optimizer.step()

            # 统计
            total_loss += loss.item() * batch_size
            total_correct += (torch.argmax(outputs, dim=1) == labels).sum().item()
            total_samples += batch_size

        avg_loss = total_loss / total_samples
        acc = total_correct / total_samples

        if epoch_num is not None:
            print(f"Free Epoch {epoch_num}: Loss={avg_loss:.4f}, Acc={acc:.2%}")

        return avg_loss, acc


class TradesAdversarialTraining:
    """
    TRADES对抗训练

    TRADES (TRAditional vs. Distillation) 通过KL散度使干净样本和对抗样本的
    输出分布一致，从而提升泛化能力。

    参考文献：Zhang et al. "Theoretically Principled Trade-off" (ICML 2019)
    """

    def __init__(self, model, optimizer, device='cpu', epsilon=0.03, alpha=1.0, num_iter=7):
        """
        参数:
            alpha: KL散度损失的权重
        """
        self.model = model
        self.optimizer = optimizer
        self.device = device
        self.epsilon = epsilon
        self.alpha = alpha
        self.num_iter = num_iter

    def pgd_attack(self, images):
        """为TRADES生成对抗样本"""
        original_images = images.clone().detach()
        images = images + torch.zeros_like(images).uniform_(-self.epsilon, self.epsilon)
        images = torch.clamp(images, 0, 1).detach()
        images.requires_grad = True

        for _ in range(self.num_iter):
            outputs = self.model(images)
            self.model.zero_grad()
            outputs.backward(gradient=torch.ones_like(outputs[:, 0]))
            grad = images.grad.data

            images = images.detach() + 0.007 * torch.sign(grad)
            images = torch.clamp(images, original_images - self.epsilon, original_images + self.epsilon)
            images = torch.clamp(images, 0, 1).detach()
            images.requires_grad = True

        return images.detach()

    def train_epoch(self, dataloader, epoch_num=None):
        """执行TRADES训练的一个epoch"""
        self.model.train()
        total_loss = 0.0
        total_correct = 0
        total_samples = 0

        for images, labels in dataloader:
            images = images.to(self.device)
            labels = labels.to(self.device)

            # 干净样本的预测
            clean_outputs = self.model(images)

            # 生成对抗样本
            adversarial_images = self.pgd_attack(images)
            adv_outputs = self.model(adversarial_images)

            # TRADES损失：分类损失 + alpha * KL(clean || adv)
            ce_loss = F.cross_entropy(clean_outputs, labels)
            kl_loss = F.kl_div(
                F.log_softmax(adv_outputs, dim=1),
                F.softmax(clean_outputs, dim=1),
                reduction='batchmean'
            )

            loss = ce_loss + self.alpha * kl_loss

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            # 统计
            total_loss += loss.item() * len(labels)
            total_correct += (torch.argmax(clean_outputs, dim=1) == labels).sum().item()
            total_samples += len(labels)

        avg_loss = total_loss / total_samples
        acc = total_correct / total_samples

        if epoch_num is not None:
            print(f"TRADES Epoch {epoch_num}: Loss={avg_loss:.4f}, Acc={acc:.2%}")

        return avg_loss, acc


if __name__ == "__main__":
    # 定义简单模型和数据
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

    # 创建虚拟数据
    torch.manual_seed(42)
    device = torch.device("cpu")

    # 模拟数据加载器
    class DummyDataset:
        def __init__(self, size=100):
            self.size = size

        def __iter__(self):
            for _ in range(self.size):
                images = torch.rand(32, 1, 28, 28)
                labels = torch.randint(0, 10, (32,))
                yield images, labels

        def __len__(self):
            return self.size

    model = SimpleCNN(num_classes=10).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    print("=" * 50)
    print("PGD对抗训练测试")
    print("=" * 50)

    # PGD对抗训练
    trainer = PGDAdversarialTrainer(model, optimizer, device, epsilon=0.1, alpha=0.01, num_iter=5)

    print("\n--- PGD Adversarial Training ---")
    for epoch in range(3):
        trainer.train_epoch(DummyDataset(10), epoch_num=epoch + 1)

    # Free对抗训练
    model2 = SimpleCNN(num_classes=10).to(device)
    optimizer2 = torch.optim.Adam(model2.parameters(), lr=0.001)
    free_trainer = FreeAdversarialTraining(model2, optimizer2, device, epsilon=0.1, num_replays=4)

    print("\n--- Free Adversarial Training ---")
    for epoch in range(3):
        free_trainer.train_epoch(DummyDataset(10), epoch_num=epoch + 1)

    # TRADES
    model3 = SimpleCNN(num_classes=10).to(device)
    optimizer3 = torch.optim.Adam(model3.parameters(), lr=0.001)
    trades_trainer = TradesAdversarialTraining(model3, optimizer3, device, epsilon=0.1, alpha=1.0, num_iter=5)

    print("\n--- TRADES Training ---")
    for epoch in range(3):
        trades_trainer.train_epoch(DummyDataset(10), epoch_num=epoch + 1)

    print("\n测试完成！")
