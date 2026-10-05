"""匹配防连坐：按真实时间冷却窗口挑对手，外加评分差上限、每 tick 配对预算与撤销窗口。

冷却记录挂在按过期时间排序的堆索引上，判定只做 O(1) 查表并按时间惰性回收，不全扫历史。
"""

import heapq


class Engine:
    """配对引擎。"""

    def __init__(self, cooldown_ms, max_gap, budget_per_tick, confirm_ms):
        self.cooldown_ms = cooldown_ms
        self.max_gap = max_gap
        self.budget = budget_per_tick
        self.confirm_ms = confirm_ms
        self.queue = []
        self.queued = set()
        self.matches = {}
        self.cooldowns = {}
        self.expiry = []
        self.match_seq = 0
        self.deferred = 0
        self.work = 0

    @staticmethod
    def _pair_key(a, b):
        return (a, b) if a <= b else (b, a)

    def enqueue(self, player, rating, at_ms):
        """把玩家放进队列；同一玩家重复入队只保留最早那条。"""
        if player in self.queued:
            return False
        self.queue.append((player, rating, at_ms))
        self.queued.add(player)
        return True

    def waiting(self):
        return len(self.queue)

    def _reclaim(self, now_ms):
        """按时间回收已过期的冷却记录。"""
        while self.expiry and self.expiry[0][0] <= now_ms:
            _, key, match_id = heapq.heappop(self.expiry)
            if self.cooldowns.get(key) == match_id:
                del self.cooldowns[key]

    def cooldown_ok(self, a, b, now_ms):
        """同一对玩家距上次成功且未撤销的配对不满 cooldown_ms 才禁止；正好等于算已过。"""
        self._reclaim(now_ms)
        match_id = self.cooldowns.get(self._pair_key(a, b))
        if match_id is None:
            return True
        _, at_ms = self.matches[match_id]
        return now_ms - at_ms >= self.cooldown_ms

    def fill(self, now_ms):
        """按队列顺序挑对手配对，受评分差上限与每 tick 预算约束，返回配成的 (match_id, a, b)。"""
        self._reclaim(now_ms)
        out = []
        taken = set()
        matched = set()
        made = 0
        for index, (player, rating, at) in enumerate(self.queue):
            if player in taken:
                continue
            for other_index in range(index + 1, len(self.queue)):
                other, other_rating, _ = self.queue[other_index]
                if other in taken:
                    continue
                self.work += 1
                if abs(rating - other_rating) > self.max_gap:
                    continue
                if not self.cooldown_ok(player, other, now_ms):
                    continue
                taken.add(player)
                taken.add(other)
                if made < self.budget:
                    match_id = "%s-%s-%d" % (player, other, self.match_seq)
                    self.match_seq += 1
                    key = self._pair_key(player, other)
                    self.matches[match_id] = (key, now_ms)
                    self.cooldowns[key] = match_id
                    heapq.heappush(self.expiry, (now_ms + self.cooldown_ms, key, match_id))
                    matched.add(player)
                    matched.add(other)
                    made += 1
                    out.append((match_id, player, other))
                else:
                    self.deferred += 1
                break
        if matched:
            self.queue = [item for item in self.queue if item[0] not in matched]
            self.queued -= matched
        return out

    def undo(self, match_id, now_ms):
        """在确认窗口内撤销一次配对；撤销后不计入冷却，同一 match_id 只结算一次。"""
        match = self.matches.get(match_id)
        if match is None:
            return False
        key, at_ms = match
        if now_ms - at_ms > self.confirm_ms:
            return False
        del self.matches[match_id]
        if self.cooldowns.get(key) == match_id:
            del self.cooldowns[key]
        return True

    def work_count(self):
        return self.work
