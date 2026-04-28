"""
视觉问答模块 (VQA) - 图像问答基础实现

本模块实现基础的视觉问答系统，结合图像特征和文本问题进行问答。
使用预训练的视觉编码器提取图像特征，通过多模态融合回答问题。

核心组件：
1. 图像编码器：CNN/ResNet提取视觉特征
2. 问题编码器：LSTM/Transformer编码问题
3. 多模态融合：图像-文本注意力交互
4. 答案预测：基于融合特征预测答案
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class ImageEncoder(nn.Module):
    """图像编码器：使用卷积神经网络提取视觉特征"""

    def __init__(self, in_channels=3, hidden_dim=256, num_layers=4):
        super().__init__()
        # 简单的CNN特征提取器（实际应使用预训练的ResNet/ViT）
        self.conv_layers = nn.ModuleList()
        channels = [in_channels, 64, 128, 256, hidden_dim]

        for i in range(num_layers):
            self.conv_layers.append(nn.Conv2d(
                in_channels=channels[i],
                out_channels=channels[i + 1],
                kernel_size=3,
                padding=1
            ))
            self.conv_layers.append(nn.BatchNorm2d(channels[i + 1]))
            self.conv_layers.append(nn.ReLU(inplace=True))
            self.conv_layers.append(nn.MaxPool2d(2, 2))

    def forward(self, images):
        """
        前向传播
        :param images: 图像张量 [batch, channels, height, width]
        :return: 特征图 [batch, hidden_dim, h', w']
        """
        x = images
        for layer in self.conv_layers:
            if isinstance(layer, nn.Conv2d):
                x = layer(x)
            else:
                x = layer(x)
        return x


class QuestionEncoder(nn.Module):
    """问题编码器：LSTM编码文本问题"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256, num_layers=1, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, question_tokens):
        """
        前向传播
        :param question_tokens: 问题token ids [batch, seq_len]
        :return: 问题表示 [batch, hidden_dim*2]
        """
        embedded = self.dropout(self.embedding(question_tokens))
        outputs, (h_n, _) = self.lstm(embedded)
        # 双向最后隐藏状态拼接
        h_combined = torch.cat([h_n[0], h_n[1]], dim=-1)
        return h_combined


class ImageTextAttention(nn.Module):
    """图像-文本注意力：融合图像特征和问题表示"""

    def __init__(self, image_dim, question_dim, hidden_dim):
        super().__init__()
        # 图像特征变换
        self.image_transform = nn.Linear(image_dim, hidden_dim)
        # 问题特征变换
        self.question_transform = nn.Linear(question_dim, hidden_dim)
        # 注意力评分
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, image_features, question_repr):
        """
        计算图像-问题注意力
        :param image_features: 图像特征 [batch, num_regions, image_dim]
        :param question_repr: 问题表示 [batch, question_dim]
        :return: 融合表示, 注意力权重
        """
        batch_size, num_regions, _ = image_features.size()

        # 变换特征
        img_transformed = self.image_transform(image_features)  # [batch, num_regions, hidden]
        q_transformed = self.question_transform(question_repr)   # [batch, hidden]

        # 扩展问题向量以匹配图像区域数
        q_expanded = q_transformed.unsqueeze(1).expand(-1, num_regions, -1)

        # 拼接计算注意力
        combined = torch.cat([img_transformed, q_expanded], dim=-1)
        scores = self.attention(combined).squeeze(-1)  # [batch, num_regions]

        # softmax归一化
        attn_weights = F.softmax(scores, dim=-1)

        # 加权求和
        context = torch.bmm(attn_weights.unsqueeze(1), img_transformed)
        context = context.squeeze(1)  # [batch, hidden]

        return context, attn_weights


class VQAModel(nn.Module):
    """完整的VQA模型"""

    def __init__(self, vocab_size, num_answers, embed_dim=128,
                 image_dim=256, hidden_dim=256, dropout=0.3):
        super().__init__()
        # 图像编码器
        self.image_encoder = ImageEncoder(in_channels=3, hidden_dim=image_dim)
        # 问题编码器
        self.question_encoder = QuestionEncoder(vocab_size, embed_dim, hidden_dim)
        # 图像-文本注意力
        self.attention = ImageTextAttention(image_dim, hidden_dim * 2, hidden_dim)
        # 答案预测器
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2 + hidden_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, num_answers)
        )

    def forward(self, images, question_tokens):
        """
        前向传播
        :param images: 图像张量 [batch, 3, H, W]
        :param question_tokens: 问题token ids [batch, seq_len]
        :return: 答案分数 [batch, num_answers]
        """
        # 图像特征
        image_features = self.image_encoder(images)
        batch_size, c, h, w = image_features.size()
        image_features = image_features.view(batch_size, c, -1).transpose(1, 2)  # [batch, h*w, c]

        # 问题特征
        question_repr = self.question_encoder(question_tokens)  # [batch, hidden*2]

        # 图像-问题注意力融合
        fused, attn_weights = self.attention(image_features, question_repr)

        # 拼接融合特征和问题表示
        combined = torch.cat([fused, question_repr], dim=-1)

        # 预测答案
        logits = self.classifier(combined)

        return logits, attn_weights


class LateFusionVQA(nn.Module):
    """后融合VQA：图像和问题分别编码后融合"""

    def __init__(self, vocab_size, num_answers, embed_dim=128, hidden_dim=256):
        super().__init__()
        # 问题编码器
        self.question_encoder = QuestionEncoder(vocab_size, embed_dim, hidden_dim)
        # 图像编码器（简化）
        self.image_fc = nn.Linear(512, hidden_dim)  # 假设预提取的图像特征
        # 融合分类器
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_answers)
        )

    def forward(self, image_features, question_tokens):
        """
        前向传播
        :param image_features: 预提取的图像特征 [batch, 512]
        :param question_tokens: 问题token ids [batch, seq_len]
        :return: 答案分数
        """
        # 编码问题
        q_repr = self.question_encoder(question_tokens)  # [batch, hidden*2]
        # 编码图像
        img_repr = self.image_fc(image_features)  # [batch, hidden]

        # 简单拼接融合
        combined = torch.cat([q_repr, img_repr], dim=-1)

        # 预测
        logits = self.classifier(combined)

        return logits


class BottomUpTopDownAttention(nn.Module):
    """自底向上自顶向下注意力机制（常用VQA方法）"""

    def __init__(self, hidden_dim, attention_dim=256):
        super().__init__()
        # 图像区域特征投影
        self.image投影 = nn.Linear(hidden_dim, attention_dim)
        # 问题嵌入投影
        self.question投影 = nn.Linear(hidden_dim, attention_dim)
        # 注意力归一化
        self.attention_norm = nn.Linear(attention_dim, 1)

    def forward(self, image_features, question_repr, num_objects):
        """
        计算每个区域的注意力
        :param image_features: 图像特征 [batch, num_regions, hidden]
        :param question_repr: 问题表示 [batch, hidden]
        :param num_objects: 每个样本的对象数量
        :return: 加权后的图像特征
        """
        batch_size = image_features.size(0)

        # 投影到注意力空间
        img_proj = self.image投影(image_features)  # [batch, num_regions, attention]
        q_proj = self.question投影(question_repr)  # [batch, attention]

        # 扩展问题向量
        q_expanded = q_proj.unsqueeze(1).expand(-1, image_features.size(1), -1)

        # 计算注意力分数
        combined = torch.tanh(img_proj + q_expanded)
        scores = self.attention_norm(combined).squeeze(-1)  # [batch, num_regions]

        # softmax归一化
        attn_weights = F.softmax(scores, dim=-1)

        # 加权求和
        gated_image = torch.bmm(attn_weights.unsqueeze(1), image_features)
        gated_image = gated_image.squeeze(1)

        return gated_image, attn_weights


def vqa_accuracy(predictions, targets):
    """
    计算VQA准确率
    :param predictions: 预测答案索引 [batch]
    :param targets: 真实答案索引 [batch]
    :return: 准确率
    """
    correct = (predictions == targets).float()
    accuracy = correct.mean()
    return accuracy.item()


def demo():
    """VQA模型演示"""
    batch_size = 2
    vocab_size = 1000
    num_answers = 500
    image_size = 224

    # 初始化模型
    model = VQAModel(vocab_size=vocab_size, num_answers=num_answers)
    model.train()

    # 构造假数据
    images = torch.randn(batch_size, 3, image_size, image_size)
    question_tokens = torch.randint(1, vocab_size, (batch_size, 15))

    # 前向传播
    logits, attn_weights = model(images, question_tokens)

    print(f"[视觉问答演示]")
    print(f"  图像尺寸: {images.shape}")
    print(f"  问题长度: {question_tokens.shape[1]}")
    print(f"  答案分数形状: {logits.shape}")
    print(f"  注意力权重形状: {attn_weights.shape}")
    print(f"  预测答案: {logits.argmax(dim=1)}")
    print(f"  模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # 后融合模型演示
    late_fusion = LateFusionVQA(vocab_size, num_answers)
    image_features = torch.randn(batch_size, 512)
    late_logits = late_fusion(image_features, question_tokens)
    print(f"  后融合模型输出: {late_logits.shape}")

    print("  ✅ 视觉问答演示通过！")


if __name__ == "__main__":
    demo()
