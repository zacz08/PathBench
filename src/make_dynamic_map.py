# src/make_dynamic_map.py
from algorithms.configuration.configuration import Configuration
from simulator.services.services import Services

# 你实现的动态地图类（根据你的路径调整 import）
from algorithms.configuration.maps.dynamic_map import DynamicMap, PingPongSegment, MovingCircle

def main():
    cfg = Configuration()
    cfg.simulator_graphics = False
    srv = Services(cfg)

    # 方式 A：直接用路径
    base = srv.resources.maps_dir.load("house_10/0")   # 或者 "house_10/0.pickle"

    # 包成动态地图
    dyn = DynamicMap(base.grid.copy())
    H, W = base.grid.shape

    # 加一个往返移动的“条形障碍”
    dyn.add_obstacle(
        PingPongSegment(
            start=(int(W*0.2), int(H*0.5)),
            end  =(int(W*0.8), int(H*0.5)),
            period=60,   # 往返一圈 60 tick
            width=2
        )
    )
    dyn.add_obstacle(MovingCircle(center=(W*0.3, H*0.5), radius=2.5, vel=(0.2, 0.0)))

    # 同步 agent/goal
    dyn.agent.position = base.agent.position
    dyn.goal.position  = base.goal.position
    dyn.agent.radius   = base.agent.radius
    dyn.goal.radius    = base.goal.radius

    # 保存为新地图
    srv.resources.maps_dir.save("my_dynamic_demo", dyn)
    print("✅ Saved dynamic map as 'my_dynamic_demo'")

if __name__ == "__main__":
    main()

