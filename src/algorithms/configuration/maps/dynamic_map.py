# src/algorithms/configuration/maps/dynamic_map.py
from typing import List, Tuple, Callable, Optional
import copy
import numpy as np

from algorithms.configuration.maps.dense_map import DenseMap
from structures import Point, Size
# 可选：仅做类型提示，避免循环导入
try:
    from simulator.services.services import Services
except Exception:
    Services = None

# ---- 动态障碍基类 ----
class DynamicObstacle:
    """每个 step 调用 update(t)，然后 rasterize(grid_shape) 返回应当置为 WALL 的像素坐标列表"""
    def update(self, t: int) -> None:
        pass

    def rasterize(self, grid_shape: Tuple[int, int]) -> List[Tuple[int, int]]:
        return []
    
    @property
    def position(self) -> Point:
        # 默认用 (self.x, self.y)，子类必须保证 update() 里更新过
        return Point(int(round(getattr(self, "x", 0))), int(round(getattr(self, "y", 0))))
    
    

# ---- 圆形匀速移动 ----
class MovingCircle(DynamicObstacle):
    def __init__(self, center: Tuple[float, float], radius: float, vel: Tuple[float, float]):
        self.cx, self.cy = center
        self.r = radius
        self.vx, self.vy = vel
        # 初始化当前位置，避免第一次 rasterize 前没 x/y
        self.x, self.y = self.cx, self.cy

    def update(self, t: int) -> None:
        self.x = self.cx + self.vx * t
        self.y = self.cy + self.vy * t

    def rasterize(self, grid_shape: Tuple[int, int]) -> List[Tuple[int, int]]:
        H, W = grid_shape
        r2 = self.r * self.r
        x0 = max(0, int(np.floor(self.x - self.r)))
        x1 = min(W - 1, int(np.ceil(self.x + self.r)))
        y0 = max(0, int(np.floor(self.y - self.r)))
        y1 = min(H - 1, int(np.ceil(self.y + self.r)))
        cells = []
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                if (xx - self.x) ** 2 + (yy - self.y) ** 2 <= r2:
                    cells.append((yy, xx))
        return cells

# ---- 直线往返（Ping-Pong）条带 ----
class PingPongSegment(DynamicObstacle):
    """沿 start->end 往返运动的线段条带（宽度为 w，像素距离）"""
    def __init__(self, start: Tuple[float, float], end: Tuple[float, float], period: int, width: int = 1):
        self.sx, self.sy = start
        self.ex, self.ey = end
        self.period = max(1, int(period))
        self.w = max(1, int(width))
        # 初始位置
        self.x, self.y = self.sx, self.sy

    def update(self, t: int) -> None:
        # 0..period/2 去，period/2..period 回
        p2 = self.period // 2
        mod = t % self.period
        if mod <= p2:
            alpha = mod / max(1, p2)
        else:
            alpha = (self.period - mod) / max(1, p2)
        self.x = self.sx + (self.ex - self.sx) * alpha
        self.y = self.sy + (self.ey - self.sy) * alpha

    def rasterize(self, grid_shape: Tuple[int, int]) -> List[Tuple[int, int]]:
        # 把当前位置附近 w 的正方形涂墙，简单粗暴够用
        H, W = grid_shape
        cells = []
        x0 = max(0, int(np.floor(self.x - self.w)))
        x1 = min(W - 1, int(np.ceil(self.x + self.w)))
        y0 = max(0, int(np.floor(self.y - self.w)))
        y1 = min(H - 1, int(np.ceil(self.y + self.w)))
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                cells.append((yy, xx))
        return cells


class DynamicMap(DenseMap):
    """
    基于 DenseMap 的动态地图。
    - 持有 static_walls（静态墙 mask）
    - 每帧重新绘制：静态墙 + 动态障碍 -> grid
    重要：构造函数签名需兼容 DenseMap(grid, services=None, transpose=True)
    """
    def __init__(self, grid: np.ndarray, services: Optional['Services'] = None, transpose: bool = True,
                 obstacles: Optional[List[DynamicObstacle]] = None):
        # 兼容 DenseMap 的签名，避免 deepcopy/import 时传参不匹配
        super().__init__(grid, services=services, transpose=transpose)
        self.t = 0
        self.obstacles: List[DynamicObstacle] = obstacles or []

        # 记录静态墙（不包含 Agent / Goal）
        self._static_walls = (self.grid == self.WALL_ID).copy()

    def add_obstacle(self, obst: DynamicObstacle) -> None:
        self.obstacles.append(obst)

    def _rebuild_grid(self):
        # 以“静态墙”为底重新绘制动态墙；保留 agent / goal 位置
        H, W = self.grid.shape[:2]
        # 清空到 CLEAR
        self.grid[:] = self.CLEAR_ID
        # 静态墙
        self.grid[self._static_walls] = self.WALL_ID

        # 动态墙
        for obst in self.obstacles:
            for (yy, xx) in obst.rasterize((H, W)):
                self.grid[yy, xx] = self.WALL_ID

        # 重新标记 agent / goal
        a = self.agent.position
        g = self.goal.position
        if 0 <= a.y < H and 0 <= a.x < W:
            self.grid[a.y, a.x] = self.AGENT_ID
        if 0 <= g.y < H and 0 <= g.x < W:
            self.grid[g.y, g.x] = self.GOAL_ID

    def advance(self, dt: int = 1) -> None:
        """
        该方法用于在仿真每步中更新地图环境。
        用法：在算法每步动作前/后调用 map.advance(1)
        """
        self.t += dt
        for obst in self.obstacles:
            obst.update(self.t)
        self._rebuild_grid()

    def __deepcopy__(self, memo):
        """
        兼容框架在 AlgorithmRunner 里的 deepcopy 行为。
        DenseMap.__deepcopy__ 会用 self.__class__(grid_copy, services=self.services, transpose=False)
        这里保持相同签名并拷贝动态字段。
        """
        new_obj = type(self)(
            copy.deepcopy(self.grid, memo),
            services=self.services,
            transpose=False,  # 避免重复转置
            obstacles=copy.deepcopy(self.obstacles, memo)
        )
        # 复制基础实体
        new_obj.agent = copy.deepcopy(self.agent, memo)
        new_obj.goal = copy.deepcopy(self.goal, memo)
        # 复制静态墙和时间
        new_obj._static_walls = copy.deepcopy(self._static_walls, memo)
        new_obj.t = self.t
        return new_obj
