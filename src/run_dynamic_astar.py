# scripts/run_dynamic_astar.py
from algorithms.configuration.configuration import Configuration
from algorithms.classic.graph_based.dynamic_a_star import DynamicAStar
from algorithms.classic.testing.dynamic_a_star_testing import DynamicAStarTesting
from simulator.simulator import Simulator
from simulator.services.services import Services
from utility.constants import DATA_PATH

import os
import pickle

# 1) 准备配置
config = Configuration()
config.simulator_graphics = False  # 无图形
# 如果你已经把动态图存成 pickle：比如 "my_dynamic_demo"
# 1) 直接从磁盘读，不走 resources.maps_dir.load（绕开 smart_unpickle）
pkl_path = os.path.join(DATA_PATH, "maps", "my_dynamic_demo.pickle")
with open(pkl_path, "rb") as f:
    dyn_map = pickle.load(f)

# 2) 关键：在“调用方”把算法/测试器塞进 config
config.simulator_initial_map = dyn_map
config.simulator_algorithm_type = DynamicAStar
config.simulator_testing_type = DynamicAStarTesting

# 3) 启动
services = Services(config)  # 用更新后的 config 重新构建 Services
testing = Simulator(services).start()
testing.print_results()
