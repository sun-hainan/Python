# -*- coding: utf-8 -*-
"""
算法实现：对抗机器学习 / deepfool_attack

本文件实现 deepfool_attack 相关的算法功能。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def deepfool_attack(model, images, labels, num_classes=10, max_iter=50, overshoot=0.02, device='cpu'):
    """
    DeepFool无目标攻击

    通过迭代方式找到最小范数扰动使样本跨越决策边界

    参数:
        model: 分类模型
        images: 原始图像 [B, C, H, W]
        labels: 真实标签
        num_classes: 类别总数
        max_iter: 最大迭代次数
        overshoot: 过冲参数，用于加速收敛
        device: 计算设备

    返回:
        adversarial_images: 对抗样本
        perturbations: 扰动张量
    """
    model.eval()
    images = images.to(device)
    labels = labels.to(device)

    batch_size = images.size(0)
    adversarial_images = images.clone().detach()
    perturbations = torch.zeros_like(images)

    for idx in range(batch_size):
        image = images[idx:idx + 1].clone().detach()
        original_label = labels[idx].item()
        current_image = image.clone()

        for iteration in range(max_iter):
            current_image.requires_grad = True
            outputs = model(current_image)

            # 获取当前预测类别
            current_pred = torch.argmax(outputs, dim=1).item()

            # 如果已经分类错误，则停止
            if current_pred != original_label:
                break

            # 计算所有类别的梯度
            grads = []
            for class_idx in range(num_classes):
                if class_idx == original_label:
                    continue

                # 对每个非真实类计算梯度
                model.zero_grad()
                output = outputs[0, class_idx]
                output.backward(retain_graph=True)
                grads.append(current_image.grad.data.clone())

            # 找最小范数的扰动方向
            if len(grads) == 0:
                break

            # 将梯度堆叠并计算最优扰动
            grads_tensor = torch.cat(grads, dim=0)  # [num_classes-1, C, H, W]

            # 计算扰动（简化版本：使用第一个非真实类梯度）
            # 完整版本需要计算决策边界法向量
            perturbation = grads_tensor[0]

            # 归一化扰动
            pert_norm = torch.norm(perturbation.view(-1), p=2)
            if pert_norm > 1e-8:
                perturbation = perturbation / pert_norm

            # 计算攻击强度
            output_real = outputs[0, original_label]
            output_other = outputs[0, (original_label + 1) % num_classes]
            diff = output_other - output_real

            if diff.item() > 1e-8:
                alpha = (diff.item() + 1e-8) / (torch.norm(grads_tensor[0].view(-1), p=2) ** 2 + 1e-8)
            else:
                alpha = 0.1

            # 更新图像
            perturbation = perturbation * alpha * (1 + overshoot)
            current_image = current_image.detach() - perturbation

            # 投影回[0,1]范围
            current_image = torch.clamp(current_image, 0, 1)

        adversarial_images[idx] = current_image.detach()
        perturbations[idx] = current_image - image

    return adversarial_images, perturbations


def deepfool_targeted_attack(model, images, target_labels, num_classes=10, max_iter=50, device='cpu'):
    """
    DeepFool有目标攻击：使图像被分类到目标类别

    参数:
        model: 分类模型
        images: 原始图像
        target_labels: 目标标签
        num_classes: 类别数
        max_iter: 最大迭代次数
        device: 计算设备

    返回:
        adversarial_images: 对抗样本
    """
    model.eval()
    images = images.to(device)
    target_labels = target_labels.to(device)

    batch_size = images.size(0)
    adversarial_images = images.clone().detach()

    for idx in range(batch_size):
        image = images[idx:idx + 1].clone().detach()
        target_label = target_labels[idx].item()
        current_image = image.clone()

        for iteration in range(max_iter):
            current_image.requires_grad = True
            outputs = model(current_image)

            current_pred = torch.argmax(outputs, dim=1).item()

            # 如果已成功分类到目标类，停止
            if current_pred == target_label:
                break

            # 计算目标类和其他类之间的梯度差
            model.zero_grad()

            # 获取目标类logit
            target_logit = outputs[0, target_label]

            # 计算目标类相对于其他类的梯度
            best_perturbation = None
            best_norm = float('inf')

            for class_idx in range(num_classes):
                if class_idx == target_label:
                    continue

                other_logit = outputs[0, class_idx]
                diff = target_logit - other_logit

                if diff.item() < 0.1:  # 目标类logit不够高
                    model.zero_grad()
                    diff.backward(retain_graph=True)

                    grad = current_image.grad.data.clone()
                    grad_norm = torch.norm(grad.view(-1), p=2)

                    if grad_norm > 1e-8:
                        # 计算达到目标所需步长
                        step = (0.1 - diff.item() + 1e-8) / (grad_norm ** 2 + 1e-8)
                        perturbation = grad / (grad_norm + 1e-8) * step

                        if torch.norm(perturbation.view(-1), p=2) < best_norm:
                            best_norm = torch.norm(perturbation.view(-1), p=2).item()
                            best_perturbation = perturbation

            if best_perturbation is None:
                best_perturbation = torch.zeros_like(current_image)

            current_image = current_image.detach() + best_perturbation
            current_image = torch.clamp(current_image, 0, 1)

        adversarial_images[idx] = current_image.detach()

    return adversarial_images


def compute_deepfool_perturbation_norm(adversarial_images, original_images):
    """
    计算DeepFool扰动的平均范数

    参数:
        adversarial_images: 对抗样本
        original_images: 原始图像

    返回:
        mean_l2_norm: 平均L2范数
    """
    perturbations = adversarial_images - original_images
    norms = torch.norm(perturbations.view(len(perturbations), -1), dim=1, p=2)
    return norms.mean().item()


if __name__ == "__main__":
    # 定义简单CNN
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
    model.eval()

    # 生成测试数据
    torch.manual_seed(99)
    test_images = torch.rand(6, 1, 28, 28).to(device)
    test_labels = torch.tensor([0, 1, 2, 3, 4, 5]).to(device)

    print("=" * 50)
    print("DeepFool攻击测试")
    print("=" * 50)

    # 干净预测
    with torch.no_grad():
        clean_preds = torch.argmax(model(test_images), dim=1)
        print(f"原始预测: {clean_preds.cpu().numpy()}")
        print(f"真实标签: {test_labels.cpu().numpy()}")

    # DeepFool攻击
    adv_images, perturbations = deepfool_attack(
        model, test_images, test_labels,
        num_classes=10, max_iter=30, device=device
    )

    with torch.no_grad():
        adv_preds = torch.argmax(model(adv_images), dim=1)
        print(f"DeepFool预测: {adv_preds.cpu().numpy()}")

    # 计算扰动范数
    pert_norms = compute_deepfool_perturbation_norm(adv_images, test_images)
    print(f"平均L2扰动范数: {pert_norms:.6f}")

    # 攻击成功率
    correct_mask = (clean_preds == test_labels)
    success = (adv_preds != test_labels) & correct_mask
    success_rate = success.sum().item() / correct_mask.sum().item()
    print(f"攻击成功率: {success_rate:.2%}")

    # 测试有目标攻击
    print("\n--- DeepFool有目标攻击 ---")
    target_labels = torch.tensor([9, 8, 7, 6, 5, 4]).to(device)
    adv_images_targeted = deepfool_targeted_attack(
        model, test_images, target_labels,
        num_classes=10, max_iter=30, device=device
    )

    with torch.no_grad():
        targeted_preds = torch.argmax(model(adv_images_targeted), dim=1)
        print(f"目标标签: {target_labels.cpu().numpy()}")
        print(f"对抗预测: {targeted_preds.cpu().numpy()}")
        hit_rate = (targeted_preds == target_labels).float().mean()
        print(f"目标命中率: {hit_rate:.2%}")

    print("\n测试完成！")
