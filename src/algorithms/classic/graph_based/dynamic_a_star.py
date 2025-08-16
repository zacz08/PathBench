from typing import Optional
from algorithms.algorithm import Algorithm
from algorithms.classic.graph_based.a_star import AStar
from algorithms.classic.testing.dynamic_a_star_testing import DynamicAStarTesting
from simulator.views.map.display.entities_map_display import EntitiesMapDisplay
from simulator.views.map.display.online_lstm_map_display import OnlineLSTMMapDisplay

class DynamicAStar(Algorithm):
    def __init__(self, services, testing: Optional[DynamicAStarTesting] = None,
                 max_steps: int = 2000):
        super().__init__(services, testing or DynamicAStarTesting(services))
        self._max_steps = max_steps
        self.mem = None

    def set_display_info(self):
        # 先拿父类的，再追加：网格显示 + 实体显示
        return super().set_display_info() + [
            OnlineLSTMMapDisplay(self._services),  # 画整张栅格地图
            EntitiesMapDisplay(self._services)     # 画 agent/goal
        ]

    def _find_path_internal(self):
        dyn_map = self._get_grid()
        max_outer_steps = 500
        step = 0
        inner_astar = None

        while step < max_outer_steps and not dyn_map.is_agent_in_goal_radius():
            # 内层 A*：直接 new，不挂载到 self._services.algorithm.instance
            inner_astar = AStar(self._services, None)
            self._services.last_inner_astar = inner_astar

            # 调用它自己的内部搜索，不触发 testing
            inner_astar._find_path_internal()

            # 保存 trace
            path = getattr(inner_astar, "trace", [])
            if not path or len(path) < 2:
                break

            # 走下一步
            next_pos = path[1]
            self.move_agent(next_pos)
            self.key_frame()

            # 推进动态障碍
            if hasattr(dyn_map, "advance"):
                dyn_map.advance_
