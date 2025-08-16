# src/run_dynamic_astar_gui.py
from algorithms.configuration.configuration import Configuration
from algorithms.classic.graph_based.dynamic_a_star import DynamicAStar
from algorithms.classic.testing.dynamic_a_star_testing import DynamicAStarTesting
from simulator.simulator import Simulator
from simulator.services.services import Services
from simulator.services.debug import DebugLevel

# 先用临时 Services 只为读取地图
_tmp = Services(Configuration())
dyn_map = _tmp.resources.maps_dir.load("my_dynamic_demo")  # 你之前生成的动态地图 pickle 名

# 配置：显式开启图形
config = Configuration()
config.simulator_graphics = True                         # 开图形
config.simulator_write_debug_level = DebugLevel.BASIC    # 想安静点用 DebugLevel.NONE
config.simulator_initial_map = dyn_map                   # 用你的动态地图
config.simulator_algorithm_type = DynamicAStar
config.simulator_testing_type = DynamicAStarTesting

# 正式跑模拟器（有图形）
services = Services(config)
sim = Simulator(services)
sim.start()  # 图形模式/无图形模式的选择取决于 config.simulator_graphics 和状态文件
