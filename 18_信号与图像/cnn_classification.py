# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / cnn_classification



本文件实现 cnn_classification 相关的算法功能。

"""



# Part 1 - 构建 CNN 模型



import numpy as np



# 导入 Keras 库和子模块

import tensorflow as tf

from keras import layers, models





# ==========================================================

# 主程序入口

# ==========================================================

if __name__ == "__main__":

    # 初始化 CNN（Sequential：逐层堆叠模型）

    classifier = models.Sequential()



    # Step 1 - 卷积层（Convolution）

    # 添加 32 个 3x3 卷积核，输入形状 64x64x3（RGB 图像）

    # 激活函数 ReLU：将负值置零

    classifier.add(

        layers.Conv2D(32, (3, 3), input_shape=(64, 64, 3), activation="relu")

    )



    # Step 2 - 池化层（Pooling）

    # 2x2 池化窗口，减少特征图尺寸

    classifier.add(layers.MaxPooling2D(pool_size=(2, 2)))



    # 添加第二个卷积-池化块

    classifier.add(layers.Conv2D(32, (3, 3), activation="relu"))

    classifier.add(layers.MaxPooling2D(pool_size=(2, 2)))



    # Step 3 - 展平层（Flattening）

    # 将 2D 特征图转换为 1D 向量

    classifier.add(layers.Flatten())



    # Step 4 - 全连接层（Full Connection）

    # 128 个神经元，ReLU 激活

    classifier.add(layers.Dense(units=128, activation="relu"))

    # 输出层：1 个神经元，Sigmoid 分类（TB / Normal）

    classifier.add(layers.Dense(units=1, activation="sigmoid"))



    # 编译 CNN：Adam 优化器，二元交叉熵损失

    classifier.compile(

        optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]

    )



    # Part 2 - 训练模型



    # 数据增强：训练数据生成器

    # rescale：归一化像素值到 [0,1]

    # shear_range/zoom_range/horizontal_flip：数据增强

    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(

        rescale=1.0 / 255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True

    )



    # 测试数据生成器（仅归一化）

    test_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1.0 / 255)



    # 从目录加载训练数据

    # 目标尺寸 64x64，批量大小 32，二分类

    training_set = train_datagen.flow_from_directory(

        "dataset/training_set", target_size=(64, 64), batch_size=32, class_mode="binary"

    )



    # 从目录加载测试数据

    test_set = test_datagen.flow_from_directory(

        "dataset/test_set", target_size=(64, 64), batch_size=32, class_mode="binary"

    )



    # 训练模型：5 个 epoch，每 epoch 若干步

    classifier.fit_generator(

        training_set, steps_per_epoch=5, epochs=30, validation_data=test_set

    )



    # 保存训练好的模型

    classifier.save("cnn.h5")



    # Part 3 - 预测新图像



    # 加载待预测图像

    test_image = tf.keras.preprocessing.image.load_img(

        "dataset/single_prediction/image.png", target_size=(64, 64)

    )

    test_image = tf.keras.preprocessing.image.img_to_array(test_image)

    test_image = np.expand_dims(test_image, axis=0)

    

    # 执行预测

    result = classifier.predict(test_image)

    

    # 输出预测结果

    # class_indices: {'NORMAL': 0, 'ABNORMALITY': 1}

    if result[0][0] == 0:

        prediction = "Normal"

    if result[0][0] == 1:

        prediction = "Abnormality detected"

    

    print(f"预测结果: {prediction}")

