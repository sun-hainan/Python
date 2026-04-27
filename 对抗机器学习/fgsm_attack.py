# -*- coding: utf-8 -*-

"""

算法实现：对抗机器学习 / fgsm_attack



本文件实现 fgsm_attack 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





def fgsm_attack(model, images, labels, epsilon=0.03):

    """

    FGSM对抗攻击核心函数



    参数:

        model: 目标分类模型

        images: 原始输入图像 [B, C, H, W]

        labels: 真实标签 [B]

        epsilon: 扰动上界（范数约束）



    返回:

        adversarial_images: 对抗样本

    """

    # 将模型切换到评估模式，但需要梯度以计算扰动

    model.eval()

    images.requires_grad = True



    # 前向传播获取logits

    outputs = model(images)

    loss = F.cross_entropy(outputs, labels)



    # 反向传播获取梯度

    model.zero_grad()

    loss.backward()



    # 计算梯度并取sign，得到扰动方向

    grad = images.grad.data

    perturbation = epsilon * torch.sign(grad)



    # 生成对抗样本：原始图像 + 扰动，并裁剪到[0,1]范围

    adversarial_images = torch.clamp(images + perturbation, 0.0, 1.0)



    return adversarial_images





def fgsm_targeted_attack(model, images, target_labels, epsilon=0.03):

    """

    有目标的FGSM攻击：使模型将对抗样本误分类到指定目标标签



    参数:

        model: 目标模型

        images: 原始图像

        target_labels: 攻击者指定的目标标签

        epsilon: 扰动上界



    返回:

        adversarial_images: 对抗样本

    """

    images.requires_grad = True

    outputs = model(images)



    # 有目标攻击：最小化目标类的损失（即最大化负损失）

    loss = F.cross_entropy(outputs, target_labels)

    model.zero_grad()

    loss.backward()



    grad = images.grad.data

    # 有目标攻击沿梯度负方向（减小目标类损失）

    perturbation = -epsilon * torch.sign(grad)

    adversarial_images = torch.clamp(images + perturbation, 0.0, 1.0)



    return adversarial_images





def compute_adversarial_success_rate(model, images, labels, epsilon=0.03):

    """

    计算FGSM攻击成功率



    参数:

        model: 模型

        images: 原始图像批次

        labels: 真实标签

        epsilon: 扰动大小



    返回:

        success_rate: 对抗样本使模型分类错误的比例

    """

    model.eval()

    device = next(model.parameters()).device



    # 原始图像的预测结果

    with torch.no_grad():

        clean_preds = torch.argmax(model(images.to(device)), dim=1)



    # 生成对抗样本

    adversarial_images = fgsm_attack(model, images.to(device), labels.to(device), epsilon)



    # 对抗样本的预测结果

    with torch.no_grad():

        adv_preds = torch.argmax(model(adversarial_images), dim=1)



    # 统计攻击成功率（原始分类正确但对抗样本分类错误的比例）

    correct_mask = (clean_preds == labels.to(device))

    attacked_successfully = (adv_preds != labels.to(device)) & correct_mask



    success_rate = attacked_successfully.sum().item() / correct_mask.sum().item()



    return success_rate





if __name__ == "__main__":

    # 使用简单的CNN模型进行测试

    class SimpleCNN(nn.Module):

        """用于测试的简单卷积神经网络"""



        def __init__(self, num_classes=10):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)

            self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)

            self.fc1 = nn.Linear(64 * 7 * 7, 128)

            self.fc2 = nn.Linear(128, num_classes)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            x = self.fc2(x)

            return x



    # 初始化模型并移到CPU

    device = torch.device("cpu")

    model = SimpleCNN(num_classes=10).to(device)

    model.eval()



    # 生成随机测试图像（模拟MNIST格式：batch_size=4, 1x28x28）

    torch.manual_seed(42)

    test_images = torch.rand(4, 1, 28, 28).to(device)

    test_labels = torch.tensor([3, 7, 2, 9]).to(device)



    # 测试FGSM攻击

    print("=" * 50)

    print("FGSM攻击测试")

    print("=" * 50)



    # 干净样本准确率

    with torch.no_grad():

        clean_outputs = model(test_images)

        clean_preds = torch.argmax(clean_outputs, dim=1)

        print(f"原始预测: {clean_preds.cpu().numpy()}")

        print(f"真实标签: {test_labels.cpu().numpy()}")



    # 生成对抗样本

    epsilon = 0.1

    adv_images = fgsm_attack(model, test_images, test_labels, epsilon=epsilon)



    # 对抗样本预测

    with torch.no_grad():

        adv_outputs = model(adv_images)

        adv_preds = torch.argmax(adv_outputs, dim=1)

        print(f"对抗预测: {adv_preds.cpu().numpy()}")



    # 计算扰动大小

    perturbation = adv_images - test_images

    perturbation_norm = torch.norm(perturbation.view(perturbation.size(0), -1), p=float('inf'), dim=1)

    print(f"实际扰动L-inf范数: {perturbation_norm.cpu().numpy()}")



    # 攻击成功率

    success_rate = compute_adversarial_success_rate(model, test_images, test_labels, epsilon=epsilon)

    print(f"攻击成功率: {success_rate:.2%}")



    # 测试有目标攻击

    target_labels = torch.tensor([1, 1, 1, 1]).to(device)

    targeted_adv_images = fgsm_targeted_attack(model, test_images, target_labels, epsilon=epsilon)



    with torch.no_grad():

        targeted_preds = torch.argmax(model(targeted_adv_images), dim=1)

        print(f"\n有目标攻击（目标=1）: {targeted_preds.cpu().numpy()}")

        target_success = (targeted_preds == target_labels).sum().item()

        print(f"命中目标数量: {target_success}/{len(target_labels)}")



    print("\n测试完成！")

