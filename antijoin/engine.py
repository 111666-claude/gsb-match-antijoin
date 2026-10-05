"""匹配防连坐：按真实时间冷却窗口挑对手，外加评分差上限、每 tick 配对预算与撤销窗口。

缺陷：冷却记录从不回收（永久冷却）、挑对手不看评分差上限、每次配对数不受预算约束、
同一个玩家重复入队、撤销接口直接返回失败（冷却也不清）、判定全扫历史。
"""


class Engine:
    """配对引擎。"""

    def __init__(self, cooldown_ms, max_gap, budget_per_tick, confirm_ms):
        self.cooldown_ms = cooldown_ms
        self.max_gap = max_gap
        self.budget = budget_per_tick
        self.confirm_ms = confirm_ms
        self.queue = []
        self.history = []
        self.deferred = 0
        self.work = 0

    def enqueue(self, player, rating, at_ms):
        """把玩家放进队列，返回是否成功。缺陷：同一玩家重复入队也照收。"""
        self.queue.append((player, rating, at_ms))
        return True

    def waiting(self):
        return len(self.queue)

    def cooldown_ok(self, a, b, now_ms):
        """判断这对玩家现在能不能配。缺陷：只要历史上出现过就永久冷却。"""
        for _, left, right, _, _ in self.history:
            if {left, right} == {a, b}:
                return False
        return True

    def fill(self, now_ms):
        """为队首玩家挑对手配对，返回本次配成的 (match_id, a, b)。

        缺陷：不看评分差上限、不限每 tick 预算、不查重复入队、全扫历史。
        """
        out = []
        taken = set()
        for index, (player, rating, at) in enumerate(self.queue):
            if player in taken:
                continue
            for other_index in range(index + 1, len(self.queue)):
                other, other_rating, _ = self.queue[other_index]
                if other in taken:
                    continue
                self.work += len(self.history)
                if not self.cooldown_ok(player, other, now_ms):
                    continue
                match_id = "%s-%s-%d" % (player, other, len(out))
                self.history.append((match_id, player, other, now_ms, True))
                taken.add(player)
                taken.add(other)
                out.append((match_id, player, other))
                break
        self.queue = [item for item in self.queue if item[0] not in taken]
        return out

    def undo(self, match_id, now_ms):
        """在确认窗口内撤销一次配对。缺陷：直接返回失败，冷却也不清。"""
        return False

    def work_count(self):
        return self.work
