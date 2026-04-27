# -*- coding: utf-8 -*-
"""
算法实现：模型压缩完整版 / fine_tuning_after_pruning

本文件实现 fine_tuning_after_pruning 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import copy


class FineTuner:
    """
    剪枝后微调器
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.original_state = None

    def save_original(self):
        """保存原始状态"""
        self.original_state = copy.deepcopy(self.model.state_dict())

    def restore_original(self):
        """恢复到原始状态"""
        if self.original_state:
            self.model.load_state_dict(self.original_state)

    def fine_tune(self, dataloader, epochs=10, lr=0.001):
        """
        标准微调

        参数:
            dataloader: 数据加载器
            epochs: 微调轮数
            lr: 学习率
        """
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0

            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                loss = F.cross_entropy(outputs, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)
            print(f"Fine-tune Epoch {epoch + 1}: Loss={avg_loss:.4f}")

    def fine_tune_with_mask(self, dataloader, mask_dict, epochs=10, lr=0.001, mask_lr_ratio=0.1):
        """
        带掩码的微调

        只更新未被剪枝的权重
        """
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0

            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                loss = F.cross_entropy(outputs, labels)

                optimizer.zero_grad()
                loss.backward()

                # 只更新未掩码的梯度
                with torch.no_grad():
                    for name, param in self.model.named_parameters():
                        if name in mask_dict:
                            param.grad *= mask_dict[name]

                optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)
            print(f"Mask Fine-tune Epoch {epoch + 1}: Loss={avg_loss:.4f}")


class LayerwiseFineTuner:
    """
    分层微调器

    从输出层到输入层逐层微调
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def get_layer_groups(self):
        """获取分层结构"""
        groups = []
        current_group = []
        current_depth = 0

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                current_group.append((name, module))
                current_depth += 1

                # 每N层一组
                if current_depth % 3 == 0:
                    groups.append(current_group)
                    current_group = []

        if current_group:
            groups.append(current_group)

        return groups[::-1]  # 反转：从深层到浅层

    def layerwise_fine_tune(self, dataloader, epochs_per_layer=5, lr=0.001):
        """
        分层微调
        """
        groups = self.get_layer_groups()

        for group_idx, group in enumerate(groups):
            print(f"\n微调层组 {group_idx + 1}/{len(groups)}")

            # 只启用当前组的参数
            for name, param in self.model.named_parameters():
                param.requires_grad = False

            for name, module in group:
                for n, p in self.model.named_parameters():
                    if n.startswith(name.split('.')[0]):
                        p.requires_grad = True

            optimizer = torch.optim.Adam(
                [p for p in self.model.parameters() if p.requires_grad],
                lr=lr
            )

            for epoch in range(epochs_per_layer):
                self.model.train()
                total_loss = 0.0

                for images, labels in dataloader:
                    images = images.to(self.device)
                    labels = labels.to(self.device)

                    outputs = self.model(images)
                    loss = F.cross_entropy(outputs, labels)

                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                    total_loss += loss.item()

                avg_loss = total_loss / len(dataloader)
                print(f"  Epoch {epoch + 1}: Loss={avg_loss:.4f}")


class ProgressiveFineTuner:
    """
    渐进式微调

    逐步增加训练的层数
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device

    def progressive_fine_tune(self, dataloader, total_epochs=30, lr=0.001):
        """
        渐进式微调

        从最后几层开始，逐步放开更多层
        """
        num_layers = self._count_layers()
        stages = [0.2, 0.4, 0.6, 0.8, 1.0]  # 逐步增加训练比例

        for stage_idx, train_ratio in enumerate(stages):
            num_train_layers = max(1, int(num_layers * train_ratio))
            print(f"\n阶段 {stage_idx + 1}: 训练 {num_train_layers}/{num_layers} 层")

            # 冻结不训练的层
            self._freeze_layers(num_layers - num_train_layers)

            optimizer = torch.optim.Adam(
                [p for p in self.model.parameters() if p.requires_grad],
                lr=lr * (1 - stage_idx * 0.1)  # 逐步降低学习率
            )

            epochs_this_stage = max(3, total_epochs // len(stages))

            for epoch in range(epochs_this_stage):
                self.model.train()
                total_loss = 0.0

                for images, labels in dataloader:
                    images = images.to(self.device)
                    labels = labels.to(self.device)

                    outputs = self.model(images)
                    loss = F.cross_entropy(outputs, labels)

                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                    total_loss += loss.item()

                avg_loss = total_loss / len(dataloader)
                print(f"  Epoch {epoch + 1}: Loss={avg_loss:.4f}")

    def _count_layers(self):
        """计算层数"""
        count = 0
        for m in self.model.modules():
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                count += 1
        return count

    def _freeze_layers(self, num_frozen):
        """冻结前N层"""
        count = 0
        for param in self.model.parameters():
            param.requires_grad = True

        for m in self.model.modules():
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                if count < num_frozen:
                    for p in m.parameters():
                        p.requires_grad = False
                count += 1


class RewindFineTuner:
    """
    权重重绕微调（Weight Rewinding Fine-tuning）

    将剪枝后的权重重绕到训练早期的值，然后重新微调
    """

    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.checkpoints = {}

    def save_checkpoint(self, name):
        """保存检查点"""
        self.checkpoints[name] = copy.deepcopy(self.model.state_dict())

    def rewind_to(self, name):
        """重绕到指定检查点"""
        if name in self.checkpoints:
            self.model.load_state_dict(self.checkpoints[name])

    def rewind_fine_tune(self, dataloader, rewind_epoch=5, total_epochs=20, lr=0.001):
        """
        重绕微调

        参数:
            rewind_epoch: 重绕到的epoch
            total_epochs: 总微调epochs
        """
        # 先训练到重绕点（收集检查点）
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

        for epoch in range(rewind_epoch):
            self.model.train()
            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                loss = F.cross_entropy(outputs, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            if epoch == rewind_epoch - 1:
                self.save_checkpoint(f'epoch_{epoch}')

        # 重绕
        self.rewind_to(f'epoch_{rewind_epoch - 1}')

        # 重新微调
        print(f"重绕到epoch {rewind_epoch - 1}，开始微调")
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr * 0.1)

        for epoch in range(total_epochs):
            self.model.train()
            total_loss = 0.0

            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = self.model(images)
                loss = F.cross_entropy(outputs, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)
            print(f"Rewind Fine-tune Epoch {epoch + 1}: Loss={avg_loss:.4f}")


if __name__ == "__main__":
    # 定义简单模型
    class SimpleCNN(nn.Module):
        def __init__(self, num_classes=10):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
            self.bn1 = nn.BatchNorm2d(32)
            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
            self.bn2 = nn.BatchNorm2d(64)
            self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
            self.bn3 = nn.BatchNorm2d(128)
            self.fc1 = nn.Linear(128, 128)
            self.fc2 = nn.Linear(128, num_classes)

        def forward(self, x):
            x = F.relu(self.bn1(F.max_pool2d(self.conv1(x), 2)))
            x = F.relu(self.bn2(F.max_pool2d(self.conv2(x), 2)))
            x = F.relu(self.bn3(F.max_pool2d(self.conv3(x), 2)))
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    device = torch.device("cpu")
    model = SimpleCNN(num_classes=10).to(device)

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
    print("剪枝后微调测试")
    print("=" * 50)

    # 模拟剪枝后的模型
    # 随机置零一些权重
    for name, param in model.named_parameters():
        if 'weight' in name:
            mask = (torch.rand_like(param) > 0.3).float()
            param.data *= mask

    print("\n--- 标准微调 ---")
    tuner = FineTuner(model, device)
    tuner.fine_tune(DummyDataset(10), epochs=3)

    # 模拟分层微调
    print("\n--- 分层微调 ---")
    model2 = SimpleCNN(num_classes=10).to(device)
    for name, param in model2.named_parameters():
        if 'weight' in name:
            mask = (torch.rand_like(param) > 0.3).float()
            param.data *= mask

    layer_tuner = LayerwiseFineTuner(model2, device)
    layer_tuner.layerwise_fine_tune(DummyDataset(5), epochs_per_layer=2)

    # 重绕微调
    print("\n--- 权重重绕微调 ---")
    model3 = SimpleCNN(num_classes=10).to(device)
    rewind_tuner = RewindFineTuner(model3, device)
    rewind_tuner.rewind_fine_tune(DummyDataset(5), rewind_epoch=3, total_epochs=5)

    print("\n测试完成！")
