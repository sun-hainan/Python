# -*- coding: utf-8 -*-

"""

算法实现：物理仿真 / particle_system



本文件实现 particle_system 相关的算法功能。

"""



import random

import math





class Particle:

    """粒子"""



    def __init__(self, x: float, y: float, vx: float, vy: float,

                 lifetime: float = 1.0, size: float = 1.0, color=None):

        self.x = x

        self.y = y

        self.vx = vx

        self.vy = vy

        self.lifetime = lifetime  # 总生命周期

        self.age = 0.0           # 已存活时间

        self.size = size

        self.color = color or (random.randint(150, 255), random.randint(100, 200), random.randint(50, 100))

        self.alive = True



    def update(self, dt: float, gravity: float = 0):

        """更新粒子状态"""

        if not self.alive:

            return



        # 位置更新（欧拉积分）

        self.x += self.vx * dt

        self.y += self.vy * dt



        # 应用重力

        self.vy += gravity * dt



        # 生命周期衰减

        self.age += dt

        if self.age >= self.lifetime:

            self.alive = False



    def is_alive(self) -> bool:

        return self.alive



    def get_alpha(self) -> float:

        """获取透明度（随年龄衰减）"""

        return max(0.0, 1.0 - self.age / self.lifetime)





class Emitter:

    """粒子发射器"""



    def __init__(self, x: float, y: float):

        self.x = x

        self.y = y

        self.rate = 10          # 每秒发射粒子数

        self.lifetime_min = 0.5  # 生命周期范围

        self.lifetime_max = 2.0

        self.speed_min = 1.0

        self.speed_max = 5.0

        self.spread_angle = math.pi  # 发射角度范围

        self.gravity = -9.8



    def emit(self) -> Particle:

        """生成一个新粒子"""

        # 随机方向

        angle = random.uniform(-self.spread_angle / 2, self.spread_angle / 2)

        # 随机速度大小

        speed = random.uniform(self.speed_min, self.speed_max)

        vx = math.cos(angle) * speed

        vy = math.sin(angle) * speed



        # 随机生命周期

        lifetime = random.uniform(self.lifetime_min, self.lifetime_max)



        return Particle(self.x, self.y, vx, vy, lifetime)





class ParticleSystem:

    """粒子系统管理器"""



    def __init__(self, max_particles: int = 10000):

        self.particles = []

        self.emitters = []

        self.max_particles = max_particles



    def add_emitter(self, emitter: Emitter):

        self.emitters.append(emitter)



    def update(self, dt: float):

        """更新所有粒子"""

        # 发射新粒子

        for emitter in self.emitters:

            # 按发射率发射

            n_new = emitter.rate * dt

            for _ in range(int(n_new)):

                if len(self.particles) < self.max_particles:

                    self.particles.append(emitter.emit())



        # 更新所有粒子

        for p in self.particles:

            p.update(dt, gravity=0)  # 发射器自己处理重力



        # 移除死亡粒子

        self.particles = [p for p in self.particles if p.is_alive()]



    def get_active_count(self) -> int:

        return len(self.particles)





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 粒子系统测试 ===\n")



    ps = ParticleSystem(max_particles=1000)



    # 创建发射器（喷泉效果）

    emitter1 = Emitter(x=5, y=10)

    emitter1.rate = 50

    emitter1.lifetime_min = 1.0

    emitter1.lifetime_max = 3.0

    emitter1.speed_min = 3

    emitter1.speed_max = 8

    emitter1.spread_angle = math.pi / 4

    emitter1.gravity = -9.8

    ps.add_emitter(emitter1)



    print("运行 3 秒仿真...")

    print("每秒发射约 50 个粒子\n")



    for sec in range(3):

        for frame in range(60):  # 60 FPS

            dt = 1.0 / 60.0

            ps.update(dt)



            if frame % 30 == 0:  # 每秒输出几次

                print(f"  t={sec:.1f}s, 粒子数: {ps.get_active_count()}")



    print(f"\n最终活跃粒子: {ps.get_active_count()}")

    print("模拟完成")

