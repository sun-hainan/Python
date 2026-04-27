# -*- coding: utf-8 -*-

"""

算法实现：对抗机器学习 / pgd_attack



本文件实现 pgd_attack 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F





def pgd_attack(model, images, labels, epsilon=0.03, alpha=0.001, num_iter=40, random_start=True):

    """

    PGD对抗攻击核心函数



    参数:

        model: 目标分类模型

        images: 原始输入图像 [B, C, H, W]

        labels: 真实标签 [B]

        epsilon: 扰动上界（L无穷范数约束）

        alpha: 每步迭代的学习率（步长）

        num_iter: 迭代次数

        random_start: 是否在约束球内随机初始化扰动



    返回:

        adversarial_images: 对抗样本

    """

    device = next(model.parameters()).device

    images = images.to(device)

    labels = labels.to(device)



    # 扰动下界和上界（相对于原始图像）

    lower_bound = torch.clamp(images - epsilon, 0.0, 1.0)

    upper_bound = torch.clamp(images + epsilon, 0.0, 1.0)



    # 随机初始化扰动（在epsilon约束球内）

    if random_start:

        init_noise = torch.zeros_like(images).uniform_(-epsilon, epsilon)

        adversarial_images = torch.clamp(images + init_noise, 0.0, 1.0).detach()

    else:

        adversarial_images = images.clone().detach()



    # 迭代梯度上升

    for i in range(num_iter):

        adversarial_images.requires_grad = True



        # 前向传播

        outputs = model(adversarial_images)

        loss = F.cross_entropy(outputs, labels)



        # 反向传播获取梯度

        model.zero_grad()

        loss.backward()



        # 一步梯度上升：沿梯度方向小步移动

        grad = adversarial_images.grad.data

        adv_images_next = adversarial_images + alpha * torch.sign(grad)



        # 投影回约束集：确保在epsilon球内且像素值在[0,1]内

        adversarial_images = torch.clamp(adv_images_next, lower_bound, upper_bound).detach()



    return adversarial_images





def pgd_targeted_attack(model, images, target_labels, epsilon=0.03, alpha=0.001, num_iter=40, random_start=True):

    """

    有目标的PGD攻击



    参数:

        model: 目标模型

        images: 原始图像

        target_labels: 目标标签

        epsilon: 扰动上界

        alpha: 步长

        num_iter: 迭代次数

        random_start: 随机初始化



    返回:

        adversarial_images: 对抗样本

    """

    device = next(model.parameters()).device

    images = images.to(device)

    target_labels = target_labels.to(device)



    lower_bound = torch.clamp(images - epsilon, 0.0, 1.0)

    upper_bound = torch.clamp(images + epsilon, 0.0, 1.0)



    if random_start:

        init_noise = torch.zeros_like(images).uniform_(-epsilon, epsilon)

        adversarial_images = torch.clamp(images + init_noise, 0.0, 1.0).detach()

    else:

        adversarial_images = images.clone().detach()



    for i in range(num_iter):

        adversarial_images.requires_grad = True

        outputs = model(adversarial_images)



        # 有目标攻击：最小化目标类损失

        loss = F.cross_entropy(outputs, target_labels)

        model.zero_grad()

        loss.backward()



        # 有目标攻击沿负梯度方向

        grad = adversarial_images.grad.data

        adv_images_next = adversarial_images - alpha * torch.sign(grad)

        adversarial_images = torch.clamp(adv_images_next, lower_bound, upper_bound).detach()



    return adversarial_images





def pgd_attack_with_restarts(model, images, labels, epsilon=0.03, alpha=0.001, num_iter=40, num_restarts=5):

    """

    带随机重启的PGD攻击：多次运行取最强攻击效果



    参数:

        model: 目标模型

        images: 原始图像

        labels: 真实标签

        epsilon: 扰动上界

        alpha: 步长

        num_iter: 每次PGD的迭代次数

        num_restarts: 重启次数



    返回:

        best_adversarial: 攻击效果最好的对抗样本

    """

    device = next(model.parameters()).device

    images = images.to(device)

    labels = labels.to(device)



    # 记录每个样本的损失（用于选择最强攻击）

    best_loss = torch.zeros(len(images)).to(device) - float('inf')

    best_adversarial = images.clone()



    for restart in range(num_restarts):

        # 每次重启使用不同的随机起点

        adv_images = pgd_attack(

            model, images, labels,

            epsilon=epsilon, alpha=alpha,

            num_iter=num_iter, random_start=True

        )



        # 计算对抗样本的损失

        with torch.no_grad():

            outputs = model(adv_images)

            losses = F.cross_entropy(outputs, labels, reduction='none')



        # 更新每个样本的最强攻击

        improved_mask = losses > best_loss

        best_loss[improved_mask] = losses[improved_mask]

        best_adversarial[improved_mask] = adv_images[improved_mask]



    return best_adversarial





def pgd_attack_L2(model, images, labels, epsilon=0.5, alpha=0.01, num_iter=40):

    """

    L2范数约束的PGD攻击：扰动在L2球内



    参数:

        epsilon: L2范数上界

        alpha: 步长



    返回:

        adversarial_images: 对抗样本

    """

    device = next(model.parameters()).device

    images = images.to(device)

    labels = labels.to(device)



    # 随机初始化

    init_noise = torch.randn_like(images)

    init_noise = epsilon * 0.5 * init_noise / torch.norm(init_noise.view(len(images), -1), dim=1, p=2).view(-1, 1, 1, 1)

    adversarial_images = torch.clamp(images + init_noise, 0.0, 1.0).detach()



    for i in range(num_iter):

        adversarial_images.requires_grad = True

        outputs = model(adversarial_images)

        loss = F.cross_entropy(outputs, labels)



        model.zero_grad()

        loss.backward()



        grad = adversarial_images.grad.data

        grad_flat = grad.view(len(images), -1)



        # L2归一化梯度

        grad_norm = torch.norm(grad_flat, dim=1, p=2).view(-1, 1, 1, 1)

        grad_normalized = grad / (grad_norm + 1e-10)



        # 梯度上升步

        adv_images_next = adversarial_images + alpha * grad_normalized



        # 投影到L2球内

        delta = adv_images_next - images

        delta_flat = delta.view(len(images), -1)

        delta_norm = torch.norm(delta_flat, dim=1, p=2).view(-1, 1, 1, 1)



        # 裁剪超过epsilon的部分

        mask = (delta_norm > epsilon).squeeze()

        if mask.any():

            delta_flat[mask] = delta_flat[mask] * epsilon / delta_norm[mask].view(-1, 1)



        adversarial_images = torch.clamp(images + delta_flat.view_as(delta), 0.0, 1.0).detach()



    return adversarial_images





if __name__ == "__main__":

    # 定义简单CNN用于测试

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



    # 随机测试数据

    torch.manual_seed(123)

    test_images = torch.rand(8, 1, 28, 28).to(device)

    test_labels = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7]).to(device)



    print("=" * 50)

    print("PGD攻击测试")

    print("=" * 50)



    # 干净准确率

    with torch.no_grad():

        clean_preds = torch.argmax(model(test_images), dim=1)

        print(f"原始预测: {clean_preds.cpu().numpy()}")

        print(f"真实标签: {test_labels.cpu().numpy()}")



    # PGD攻击

    epsilon = 0.1

    alpha = 0.01

    num_iter = 20



    adv_images = pgd_attack(model, test_images, test_labels, epsilon=epsilon, alpha=alpha, num_iter=num_iter)



    with torch.no_grad():

        adv_preds = torch.argmax(model(adv_images), dim=1)

        print(f"PGD对抗预测: {adv_preds.cpu().numpy()}")



    # 统计攻击成功率

    correct_mask = (clean_preds == test_labels)

    attack_success = (adv_preds != test_labels) & correct_mask

    success_rate = attack_success.sum().item() / correct_mask.sum().item()

    print(f"攻击成功率: {success_rate:.2%}")



    # 测试L2版本

    adv_images_l2 = pgd_attack_L2(model, test_images, test_labels, epsilon=1.0, alpha=0.05, num_iter=20)



    with torch.no_grad():

        adv_preds_l2 = torch.argmax(model(adv_images_l2), dim=1)

        print(f"L2-PGD对抗预测: {adv_preds_l2.cpu().numpy()}")



    # 测试随机重启

    adv_images_restart = pgd_attack_with_restarts(

        model, test_images, test_labels,

        epsilon=epsilon, alpha=alpha, num_iter=num_iter, num_restarts=3

    )



    with torch.no_grad():

        adv_preds_restart = torch.argmax(model(adv_images_restart), dim=1)

        print(f"PGD-重启对抗预测: {adv_preds_restart.cpu().numpy()}")



    print("\n测试完成！")

