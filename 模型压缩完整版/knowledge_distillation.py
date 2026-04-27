# -*- coding: utf-8 -*-
"""
算法实现：模型压缩完整版 / knowledge_distillation

本文件实现 knowledge_distillation 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import copy


class KnowledgeDistiller:
    """
    基础知识蒸馏器

    使用软标签和硬标签的组合进行蒸馏
    """

    def __init__(self, teacher_model, student_model, device='cpu', temperature=4.0, alpha=0.7):
        """
        参数:
            teacher_model: 教师模型（大型模型）
            student_model: 学生模型（小型模型）
            temperature: 温度参数，用于软化概率分布
            alpha: 硬标签损失的权重，软标签权重为(1-alpha)
        """
        self.teacher_model = teacher_model
        self.student_model = student_model
        self.device = device
        self.temperature = temperature
        self.alpha = alpha

        self.teacher_model.to(device)
        self.teacher_model.eval()
        self.student_model.to(device)

    def compute_soft_target_loss(self, student_logits, teacher_logits):
        """
        计算软目标损失（KL散度）

        使用温度缩放后的softmax计算KL散度

        参数:
            student_logits: 学生模型的logits
            teacher_logits: 教师模型的logits

        返回:
            kl_loss: KL散度损失
        """
        # 温度缩放
        student_soft = F.log_softmax(student_logits / self.temperature, dim=1)
        teacher_soft = F.softmax(teacher_logits / self.temperature, dim=1)

        # KL散度：T^2是补偿温度缩放带来的梯度缩小
        kl_loss = F.kl_div(student_soft, teacher_soft, reduction='batchmean') * (self.temperature ** 2)

        return kl_loss

    def compute_hard_target_loss(self, student_logits, labels):
        """
        计算硬目标损失（交叉熵）
        """
        return F.cross_entropy(student_logits, labels)

    def distill(self, images, labels):
        """
        执行一步蒸馏

        总损失 = alpha * hard_loss + (1-alpha) * soft_loss

        参数:
            images: 输入图像
            labels: 真实标签

        返回:
            total_loss: 总损失
            hard_loss: 硬目标损失
            soft_loss: 软目标损失
        """
        images = images.to(self.device)
        labels = labels.to(self.device)

        # 教师模型前向（不需要梯度）
        with torch.no_grad():
            teacher_logits = self.teacher_model(images)

        # 学生模型前向
        student_logits = self.student_model(images)

        # 计算损失
        hard_loss = self.compute_hard_target_loss(student_logits, labels)
        soft_loss = self.compute_soft_target_loss(student_logits, teacher_logits)

        total_loss = self.alpha * hard_loss + (1 - self.alpha) * soft_loss

        return total_loss, hard_loss.item(), soft_loss.item()

    def train_step(self, images, labels, optimizer):
        """训练步骤"""
        total_loss, hard_loss, soft_loss = self.distill(images, labels)

        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        return total_loss.item(), hard_loss, soft_loss


class TemperatureScaledDistiller:
    """
    温度缩放蒸馏器

    研究不同温度对蒸馏效果的影响
    """

    def __init__(self, teacher_model, student_model, device='cpu'):
        self.teacher_model = teacher_model
        self.student_model = student_model
        self.device = device

    def softmax_with_temperature(self, logits, temperature):
        """带温度的softmax"""
        return F.softmax(logits / temperature, dim=1)

    def compute_distillation_loss(self, student_logits, teacher_logits, temperature):
        """计算指定温度下的蒸馏损失"""
        student_soft = F.log_softmax(student_logits / temperature, dim=1)
        teacher_soft = F.softmax(teacher_logits / temperature, dim=1)

        kl_loss = F.kl_div(student_soft, teacher_soft, reduction='batchmean') * (temperature ** 2)

        return kl_loss

    def search_optimal_temperature(self, dataloader, temp_range=[1, 2, 4, 8, 16, 32]):
        """
        搜索最优温度

        参数:
            dataloader: 数据加载器
            temp_range: 温度候选范围

        返回:
            best_temp: 最优温度
            best_acc: 对应准确率
        """
        best_temp = 1.0
        best_acc = 0.0

        for temp in temp_range:
            total_correct = 0
            total = 0

            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                with torch.no_grad():
                    teacher_logits = self.teacher_model(images)

                student_logits = self.student_model(images)

                loss = self.compute_distillation_loss(student_logits, teacher_logits, temp)

                # 简单评估：使用学生模型预测准确率
                preds = torch.argmax(student_logits, dim=1)
                total_correct += (preds == labels).sum().item()
                total += len(labels)

            acc = total_correct / total
            print(f"Temperature={temp}: Accuracy={acc:.4f}")

            if acc > best_acc:
                best_acc = acc
                best_temp = temp

        return best_temp, best_acc


class LabelSmoothingDistiller:
    """
    标签平滑蒸馏器

    结合标签平滑和知识蒸馏
    """

    def __init__(self, teacher_model, student_model, device='cpu', smoothing=0.1, temperature=4.0):
        self.teacher_model = teacher_model
        self.student_model = student_model
        self.device = device
        self.smoothing = smoothing
        self.temperature = temperature

    def smooth_labels(self, labels, num_classes):
        """
        平滑标签

        参数:
            labels: 原始标签
            num_classes: 类别数

        返回:
            smoothed: 平滑后的标签分布
        """
        confidence = 1.0 - self.smoothing
        smoothed = torch.zeros(len(labels), num_classes, device=self.device)
        smoothed.scatter_(1, labels.unsqueeze(1), confidence)
        smoothed += self.smoothing / num_classes

        return smoothed

    def compute_loss(self, student_logits, labels, num_classes):
        """计算组合损失"""
        # 软标签损失
        with torch.no_grad():
            teacher_logits = self.teacher_model(labels)
            teacher_probs = F.softmax(teacher_logits / self.temperature, dim=1)

        student_log_probs = F.log_softmax(student_logits / self.temperature, dim=1)
        soft_loss = F.kl_div(student_log_probs, teacher_probs, reduction='batchmean') * (self.temperature ** 2)

        # 平滑硬标签损失
        smoothed_labels = self.smooth_labels(labels, num_classes)
        hard_loss = -(smoothed_labels * F.log_softmax(student_logits, dim=1)).sum(dim=1).mean()

        return soft_loss + hard_loss


class DKLDivergenceDistiller:
    """
    DKL散度蒸馏器

    使用双向KL散度进行蒸馏
    """

    def __init__(self, teacher_model, student_model, device='cpu', temperature=4.0):
        self.teacher_model = teacher_model
        self.student_model = student_model
        self.device = device
        self.temperature = temperature

    def bidirectional_kl_divergence(self, student_logits, teacher_logits):
        """
        双向KL散度

        DKL(P||Q) + DKL(Q||P) = H(P,Q) + H(Q,P) - 2*H(P,Q)
        这鼓励学生和教师分布互相接近
        """
        student_soft = F.log_softmax(student_logits / self.temperature, dim=1)
        teacher_soft = F.softmax(teacher_logits / self.temperature, dim=1)

        # KL(student || teacher)
        kl_student_teacher = F.kl_div(student_soft, teacher_soft, reduction='batchmean')

        # KL(teacher || student)
        teacher_log_soft = F.log_softmax(teacher_logits / self.temperature, dim=1)
        student_soft_raw = F.softmax(student_logits / self.temperature, dim=1)
        kl_teacher_student = F.kl_div(teacher_log_soft, student_soft_raw, reduction='batchmean')

        return kl_student_teacher + kl_teacher_student

    def compute_loss(self, images, labels):
        """计算蒸馏损失"""
        with torch.no_grad():
            teacher_logits = self.teacher_model(images)

        student_logits = self.student_model(images)

        # 双向KL散度
        bidir_kl = self.bidirectional_kl_divergence(student_logits, teacher_logits) * (self.temperature ** 2)

        # 硬标签损失
        hard_loss = F.cross_entropy(student_logits, labels)

        return bidir_kl + 0.5 * hard_loss


class DeepHierarchicalDistillation:
    """
    深度分层蒸馏

    不仅蒸馏最终输出，还蒸馏中间层表示
    """

    def __init__(self, teacher_model, student_model, device='cpu', temperature=4.0):
        self.teacher_model = teacher_model
        self.student_model = student_model
        self.device = device
        self.temperature = temperature
        self.layer_mappings = []

    def register_hooks(self):
        """注册hook获取中间层输出"""
        self.teacher_features = []
        self.student_features = []

        def teacher_hook(module, input, output):
            self.teacher_features.append(output.detach())

        def student_hook(module, input, output):
            self.student_features.append(output.detach())

        # 为教师模型的每一层注册hook
        teacher_handles = []
        for module in self.teacher_model.modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                handle = module.register_forward_hook(teacher_hook)
                teacher_handles.append(handle)

        # 为学生模型的每一层注册hook
        student_handles = []
        for module in self.student_model.modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                handle = module.register_forward_hook(student_hook)
                student_handles.append(handle)

        return teacher_handles, student_handles

    def compute_layer_loss(self):
        """计算各层特征的蒸馏损失"""
        total_loss = 0.0

        for t_feat, s_feat in zip(self.teacher_features, self.student_features):
            # 匹配维度
            if t_feat.shape != s_feat.shape:
                # 使用自适应池化匹配
                t_feat = F.adaptive_avg_pool2d(t_feat, s_feat.shape[2:]) if t_feat.dim() == 4 else t_feat
                if t_feat.shape != s_feat.shape:
                    t_feat = t_feat.reshape(s_feat.shape[0], -1)

            # MSE损失
            total_loss += F.mse_loss(s_feat, t_feat)

        return total_loss / len(self.teacher_features)

    def distill(self, images, labels, alpha=0.5):
        """
        执行分层蒸馏

        参数:
            alpha: 最终损失中分层损失的权重
        """
        images = images.to(self.device)
        labels = labels.to(self.device)

        # 清空特征
        self.teacher_features = []
        self.student_features = []

        # 前向传播（触发hook）
        teacher_logits = self.teacher_model(images)
        student_logits = self.student_model(images)

        # 最终损失
        final_loss = F.cross_entropy(student_logits, labels)
        layer_loss = self.compute_layer_loss()

        total_loss = (1 - alpha) * final_loss + alpha * layer_loss

        return total_loss, final_loss.item(), layer_loss.item()


if __name__ == "__main__":
    # 定义教师和学生模型
    class TeacherCNN(nn.Module):
        def __init__(self, num_classes=10):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 64, 3, padding=1)
            self.conv2 = nn.Conv2d(64, 128, 3, padding=1)
            self.conv3 = nn.Conv2d(128, 256, 3, padding=1)
            self.fc1 = nn.Linear(256 * 3 * 3, 256)
            self.fc2 = nn.Linear(256, num_classes)

        def forward(self, x):
            x = F.relu(F.max_pool2d(self.conv1(x), 2))
            x = F.relu(F.max_pool2d(self.conv2(x), 2))
            x = F.relu(F.max_pool2d(self.conv3(x), 2))
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    class StudentCNN(nn.Module):
        def __init__(self, num_classes=10):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
            self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
            self.fc1 = nn.Linear(32 * 7 * 7, 64)
            self.fc2 = nn.Linear(64, num_classes)

        def forward(self, x):
            x = F.relu(F.max_pool2d(self.conv1(x), 2))
            x = F.relu(F.max_pool2d(self.conv2(x), 2))
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    device = torch.device("cpu")

    # 创建模型
    teacher = TeacherCNN(num_classes=10).to(device)
    student = StudentCNN(num_classes=10).to(device)

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
    print("知识蒸馏测试")
    print("=" * 50)

    # 基础蒸馏
    print("\n--- 基础知识蒸馏 ---")
    distiller = KnowledgeDistiller(teacher, student, device, temperature=4.0, alpha=0.7)
    optimizer = torch.optim.Adam(student.parameters(), lr=0.001)

    for epoch in range(5):
        total_loss_sum = 0
        for images, labels in DummyDataset(10):
            loss, hard, soft = distiller.train_step(images, labels, optimizer)
            total_loss_sum += loss

        print(f"Epoch {epoch + 1}: Total={total_loss_sum / 320:.4f}")

    # DKL散度蒸馏
    print("\n--- DKL散度蒸馏 ---")
    student2 = StudentCNN(num_classes=10).to(device)
    dkl_distiller = DKLDivergenceDistiller(teacher, student2, device, temperature=4.0)
    optimizer2 = torch.optim.Adam(student2.parameters(), lr=0.001)

    for epoch in range(5):
        for images, labels in DummyDataset(10):
            images, labels = images.to(device), labels.to(device)
            loss = dkl_distiller.compute_loss(images, labels)

            optimizer2.zero_grad()
            loss.backward()
            optimizer2.step()

        print(f"Epoch {epoch + 1}: DKL Loss={loss.item():.4f}")

    # 分层蒸馏
    print("\n--- 深度分层蒸馏 ---")
    student3 = StudentCNN(num_classes=10).to(device)
    hier_distiller = DeepHierarchicalDistillation(teacher, student3, device, temperature=4.0)
    optimizer3 = torch.optim.Adam(student3.parameters(), lr=0.001)

    hier_distiller.register_hooks()

    for epoch in range(3):
        for images, labels in DummyDataset(5):
            images, labels = images.to(device), labels.to(device)

            loss, final, layer = hier_distiller.distill(images, labels, alpha=0.5)

            optimizer3.zero_grad()
            loss.backward()
            optimizer3.step()

        print(f"Epoch {epoch + 1}: Total={loss.item():.4f}, Final={final:.4f}, Layer={layer:.4f}")

    print("\n测试完成！")
