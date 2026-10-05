"""匹配防连坐：按真实时间冷却窗口挑对手，外加评分差上限、每 tick 配对预算与撤销窗口。

冷却记录用 pair -> (match_id, at_ms) 字典索引并按时间回收，判定 O(1) 不全扫历史；
同一玩家重复入队只保留最早那条；撤销只认 confirm_ms 窗口内的请求，成功后清掉对应冷却。
"""


def _pair_key(a, b):
    return (a, b) if a <= b else (b, a)


class Engine:
    """配对引擎。"""

    def __init__(self, cooldown_ms, max_gap, budget_per_tick, confirm_ms):
        self.cooldown_ms = cooldown_ms
        self.max_gap = max_gap
        self.budget = budget_per_tick
        self.confirm_ms = confirm_ms
        self.queue = []
        self.queued = set()
        self.cooldowns = {}
        self.matches = {}
        self.deferred = 0
        self.work = 0
        self._seq = 0

    def enqueue(self, player, rating, at_ms):
        """把玩家放进队列；同一玩家重复入队只保留最早那条。"""
        if player in self.queued:
            return False
        self.queue.append((player, rating, at_ms))
        self.queued.add(player)
        return True

    def waiting(self):
        return len(self.queue)

    def cooldown_ok(self, a, b, now_ms):
        """距上次成功且未撤销的配对不满 cooldown_ms 才禁止；正好等于算已过。"""
        key = _pair_key(a, b)
        record = self.cooldowns.get(key)
        if record is None:
            return True
        _, at_ms = record
        if now_ms - at_ms >= self.cooldown_ms:
            del self.cooldowns[key]
            return True
        return False

    def fill(self, now_ms):
        """为队列里的玩家挑对手配对，返回本次配成的 (match_id, a, b)。

        只配评分差不超过 max_gap 的两人；一次最多配成 budget_per_tick 场，
        超出预算但本可配成的计入 deferred 并留在队列。
        """
        out = []
        matched = set()
        counted = set()
        made = 0
        queue = self.queue
        for index in range(len(queue)):
            player, rating, _ = queue[index]
            if player in counted:
                continue
            for other_index in range(index + 1, len(queue)):
                other, other_rating, _ = queue[other_index]
                if other in counted:
                    continue
                self.work += 1
                if abs(rating - other_rating) > self.max_gap:
                    continue
                if not self.cooldown_ok(player, other, now_ms):
                    continue
                counted.add(player)
                counted.add(other)
                if made < self.budget:
                    match_id = "%s-%s-%d" % (player, other, self._seq)
                    self._seq += 1
                    self.matches[match_id] = [player, other, now_ms, True]
                    self.cooldowns[_pair_key(player, other)] = (match_id, now_ms)
                    matched.add(player)
                    matched.add(other)
                    out.append((match_id, player, other))
                    made += 1
                else:
                    self.deferred += 1
                break
        if matched:
            self.queue = [item for item in queue if item[0] not in matched]
            self.queued -= matched
        return out

    def undo(self, match_id, now_ms):
        """在确认窗口内撤销一次配对；同一 match_id 只结算一次，撤销后不计入冷却。"""
        record = self.matches.get(match_id)
        if record is None or not record[3]:
            return False
        left, right, at_ms, _ = record
        if now_ms - at_ms > self.confirm_ms:
            return False
        record[3] = False
        key = _pair_key(left, right)
        current = self.cooldowns.get(key)
        if current is not None and current[0] == match_id:
            del self.cooldowns[key]
        return True

    def work_count(self):
        return self.work
