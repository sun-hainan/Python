# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / causal_representation



本文件实现 causal_representation 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

from typing import List, Tuple, Optional

from collections import defaultdict





class CausalRepresentation(nn.Module):

    """

    因果表示学习网络

    

    学习数据的因果表示

    """

    

    def __init__(self, input_dim: int, latent_dim: int, hidden_dim: int = 64):

        super().__init__()

        

        self.input_dim = input_dim

        self.latent_dim = latent_dim

        

        # 编码器

        self.encoder = nn.Sequential(

            nn.Linear(input_dim, hidden_dim),

            nn.ReLU(),

            nn.Linear(hidden_dim, hidden_dim),

            nn.ReLU(),

            nn.Linear(hidden_dim, latent_dim * 2)  # mean + logvar

        )

        

        # 解码器

        self.decoder = nn.Sequential(

            nn.Linear(latent_dim, hidden_dim),

            nn.ReLU(),

            nn.Linear(hidden_dim, hidden_dim),

            nn.ReLU(),

            nn.Linear(hidden_dim, input_dim)

        )

        

        # 因果机制（每个潜在变量一个）

        self.causal_mechanisms = nn.ModuleList([

            nn.Sequential(

                nn.Linear(latent_dim, hidden_dim),

                nn.ReLU(),

                nn.Linear(hidden_dim, 1)

            ) for _ in range(latent_dim)

        ])

    

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:

        """编码到潜在空间"""

        h = self.encoder(x)

        mean = h[:, :self.latent_dim]

        logvar = h[:, self.latent_dim:]

        return mean, logvar

    

    def reparameterize(self, mean: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:

        """重参数化"""

        std = torch.exp(0.5 * logvar)

        eps = torch.randn_like(std)

        return mean + eps * std

    

    def decode(self, z: torch.Tensor) -> torch.Tensor:

        """从潜在空间解码"""

        return self.decoder(z)

    

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:

        """前向传播"""

        mean, logvar = self.encode(x)

        z = self.reparameterize(mean, logvar)

        x_recon = self.decode(z)

        return z, x_recon, mean, logvar





class CausalVAE(CausalRepresentation):

    """

    因果变分自编码器 (CausalVAE)

    

    结合VAE和因果结构

    """

    

    def __init__(self, input_dim: int, latent_dim: int, 

                 causal_adj: np.ndarray = None, hidden_dim: int = 64):

        super().__init__(input_dim, latent_dim, hidden_dim)

        

        self.latent_dim = latent_dim

        

        # 因果邻接矩阵

        if causal_adj is None:

            # 完全连接的先验

            self.causal_adj = torch.ones(latent_dim, latent_dim) - torch.eye(latent_dim)

        else:

            self.causal_adj = torch.FloatTensor(causal_adj)

        

        # 每个因果机制的参数

        self.causal_params = nn.Parameter(torch.randn(latent_dim, latent_dim))

    

    def sample_from_scm(self, n_samples: int, noise_std: float = 0.1) -> torch.Tensor:

        """

        从结构因果模型采样

        

        Returns:

            潜在变量样本

        """

        z_samples = []

        

        for i in range(self.latent_dim):

            if i == 0:

                # 根节点：无父节点

                z_i = torch.randn(n_samples, 1) * noise_std

            else:

                # 非根节点：取决于父节点

                parents = torch.where(self.causal_adj[i] > 0)[0]

                

                if len(parents) > 0:

                    # 从父节点传递因果效应

                    parent_vals = torch.stack([z_samples[p] for p in parents], dim=1)

                    # 简单线性SCM

                    weight = self.causal_params[i, parents].unsqueeze(0)

                    z_i = (parent_vals * weight).sum(dim=1, keepdim=True)

                    z_i += torch.randn(n_samples, 1) * noise_std

                else:

                    z_i = torch.randn(n_samples, 1) * noise_std

            

            z_samples.append(z_i)

        

        return torch.cat(z_samples, dim=1)





class DisentangledRepresentation(nn.Module):

    """

    解耦表示学习

    

    学习独立的潜在因素

    """

    

    def __init__(self, input_dim: int, n_factors: int, hidden_dim: int = 128):

        super().__init__()

        

        self.n_factors = n_factors

        

        # β-VAE风格的编码器

        self.encoder = nn.Sequential(

            nn.Linear(input_dim, hidden_dim),

            nn.ReLU(),

            nn.BatchNorm1d(hidden_dim),

            nn.Linear(hidden_dim, hidden_dim),

            nn.ReLU(),

            nn.Linear(hidden_dim, n_factors * 2)  # mean + logvar per factor

        )

        

        # 解码器

        self.decoder = nn.Sequential(

            nn.Linear(n_factors, hidden_dim),

            nn.ReLU(),

            nn.Linear(hidden_dim, hidden_dim),

            nn.ReLU(),

            nn.Linear(hidden_dim, input_dim)

        )

        

        # 每个因子的独立编码器

        self.factor_encoders = nn.ModuleList([

            nn.Sequential(

                nn.Linear(input_dim, hidden_dim // 4),

                nn.ReLU(),

                nn.Linear(hidden_dim // 4, 2)

            ) for _ in range(n_factors)

        ])

    

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:

        """编码"""

        h = self.encoder(x)

        mean = h[:, :self.n_factors]

        logvar = h[:, self.n_factors:]

        return mean, logvar

    

    def decode(self, z: torch.Tensor) -> torch.Tensor:

        """解码"""

        return self.decoder(z)

    

    def reparameterize(self, mean: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:

        """重参数化"""

        std = torch.exp(0.5 * logvar)

        eps = torch.randn_like(std)

        return mean + eps * std





def demo_causal_vae():

    """演示因果VAE"""

    print("=== 因果VAE演示 ===\n")

    

    # 模拟数据生成

    np.random.seed(42)

    torch.manual_seed(42)

    

    n_samples = 1000

    input_dim = 10

    latent_dim = 3

    

    # 生成因果相关数据

    # z1, z2, z3 是潜在因果变量

    z1 = np.random.randn(n_samples)

    z2 = np.sin(z1) + np.random.randn(n_samples) * 0.1

    z3 = 0.5 * z1 + 0.5 * z2 + np.random.randn(n_samples) * 0.1

    

    Z = np.stack([z1, z2, z3], axis=1)

    

    # 混合到观测空间

    mixing_matrix = np.random.randn(3, 10)

    X = Z @ mixing_matrix + np.random.randn(n_samples, 10) * 0.1

    

    print(f"数据形状: {X.shape}")

    print(f"潜在维度: {latent_dim}")

    

    # 创建模型

    device = torch.device('cpu')

    

    model = CausalVAE(

        input_dim=input_dim,

        latent_dim=latent_dim,

        hidden_dim=32

    ).to(device)

    

    # 优化器

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    

    # 训练

    X_tensor = torch.FloatTensor(X)

    

    print("\n训练因果VAE:")

    for epoch in range(100):

        optimizer.zero_grad()

        

        z, x_recon, mean, logvar = model(X_tensor)

        

        # 重构损失

        recon_loss = nn.functional.mse_loss(x_recon, X_tensor)

        

        # KL散度

        kl_loss = -0.5 * torch.sum(1 + logvar - mean.pow(2) - logvar.exp())

        kl_loss = kl_loss / n_samples

        

        # 总损失

        loss = recon_loss + 0.1 * kl_loss

        

        loss.backward()

        optimizer.step()

        

        if epoch % 20 == 0:

            print(f"  Epoch {epoch}: loss={loss.item():.4f}")

    

    # 分析学到的表示

    print("\n学到的因果表示:")

    with torch.no_grad():

        z_samples = model.sample_from_scm(10)

        print(f"  SCM样本形状: {z_samples.shape}")





def demo_disentanglement():

    """演示解耦表示"""

    print("\n=== 解耦表示演示 ===\n")

    

    print("解耦表示的目标:")

    print("  - 每个潜在维度对应一个独立的生成因子")

    print("  - 改变一个维度不影响其他维度")

    print()

    

    print("β-VAE损失:")

    print("  L = L_recon + β * L_KL")

    print()

    print("  β > 1: 更强的解耦")

    print("  β < 1: 更好的重构")





def demoSCM_in_latent_space():

    """演示潜在空间中的SCM"""

    print("\n=== 潜在空间中的SCM ===\n")

    

    print("因果结构学习:")

    print("  1. 学习潜在表示 z = f(x)")

    print("  2. 在z空间发现因果结构")

    print("  3. 建模 p(z) = ∏ p(z_i | Pa(z_i))")

    print()

    

    print("示例因果图:")

    print("  z1: 根节点（无父节点）")

    print("  z2 <- z1: z2由z1引起")

    print("  z3 <- z1, z2: z3由z1和z2引起")

    print()

    

    print("线性SCM示例:")

    print("  z1 = ε1")

    print("  z2 = a * z1 + ε2")

    print("  z3 = b * z1 + c * z2 + ε3")





def demo_causal_discovery_vae():

    """演示因果发现+VAE"""

    print("\n=== 因果发现+VAE ===\n")

    

    print("算法流程:")

    print()

    print("1. VAE学习表示")

    print("   - encoder: x -> z")

    print("   - decoder: z -> x")

    print()

    

    print("2. 因果结构发现")

    print("   - 在z空间应用PC算法")

    print("   - 学习因果邻接矩阵")

    print()

    

    print("3. 因果表示精炼")

    print("   - 加入因果损失项")

    print("   - 促进因果解耦")

    print()

    

    print("损失函数:")

    print("  L_total = L_recon + λ * L_KL + γ * L_causal")

    print()

    print("  L_causal: 因果结构的正则化")





def demo_applications():

    """演示应用"""

    print("\n=== 应用场景 ===\n")

    

    print("1. 图像因果解耦:")

    print("   - 分离形状、颜色、位置等因子")

    print("   - 可解释的生成模型")

    print()

    

    print("2. 视频因果表示:")

    print("   - 分离运动和外观")

    print("   - 时序因果分析")

    print()

    

    print("3. 多模态学习:")

    print("   - 图像-文本因果关联")

    print("   - 跨模态因果迁移")





if __name__ == "__main__":

    print("=" * 60)

    print("因果表示学习")

    print("=" * 60)

    

    # 因果VAE

    demo_causal_vae()

    

    # 解耦表示

    demo_disentanglement()

    

    # 潜在空间SCM

    demoSCM_in_latent_space()

    

    # 因果发现+VAE

    demo_causal_discovery_vae()

    

    # 应用

    demo_applications()

    

    print("\n" + "=" * 60)

    print("核心概念:")

    print("=" * 60)

    print("""

1. 因果表示学习目标:

   - 学习解耦的潜在表示

   - 同时发现因果结构

   - 支持反事实推理



2. CausalVAE:

   - VAE + 因果先验

   - SCM在潜在空间

   - 支持因果干预



3. 解耦表示:

   - β-VAE变体

   - 独立因子学习

   - 可解释性



4. 挑战:

   - 识别性 (Identifiability)

   - 计算复杂度

   - 非线性因果

""")

