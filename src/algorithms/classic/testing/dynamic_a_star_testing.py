from typing import Dict, Any
from algorithms.basic_testing import BasicTesting
from simulator.services.debug import DebugLevel

class DynamicAStarTesting(BasicTesting):
    def get_results(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "fringe": 0.0,
            "search_space": 0.0,
            "total_search_space": 0.0,
            "trace": [],
        }

        inner_astar = getattr(self._services, "last_inner_astar", None)
        if inner_astar is not None and hasattr(inner_astar, "mem"):
            res["fringe"] = self.get_occupancy_percentage_size(
                self._services.algorithm.map.size,
                len(inner_astar.mem.priority_queue)
            )
            res["search_space"] = self.get_occupancy_percentage_size(
                self._services.algorithm.map.size,
                len(inner_astar.mem.visited)
            )
            res["total_search_space"] = self.get_occupancy_percentage_size(
                self._services.algorithm.map.size,
                len(inner_astar.mem.priority_queue) + len(inner_astar.mem.visited)
            )
            if hasattr(inner_astar, "trace"):
                res["trace"] = inner_astar.trace

        return res

    def print_results(self) -> None:
        results: Dict[str, Any] = self.get_results()
        self._services.debug.write(
            f"Search space percentage (no fringe): {results['search_space']:.2f}%",
            DebugLevel.BASIC
        )
        self._services.debug.write(
            f"Fringe percentage: {results['fringe']:.2f}%",
            DebugLevel.BASIC
        )
        self._services.debug.write(
            f"Total search space percentage: {results['total_search_space']:.2f}%",
            DebugLevel.BASIC
        )
