"""匹配防连坐：短时间内不再把同一对玩家配到一起。

缺陷：冷却记录从不回收（窗口不滑）、自己和自己也能配对、同一个 match_id 重复结算、
每次判定全扫历史配对。
"""


class Engine:
    """配对台账。"""

    def __init__(self, cooldown_ms):
        self.cooldown_ms = cooldown_ms
        self.history = []
        self.work = 0

    def pair(self, match_id, a, b, at_ms):
        """返回这对玩家是否允许配对。缺陷：只看发生过、不看时间、自匹配放行、无幂等、全扫。"""
        self.work += len(self.history)
        for left, right, _ in self.history:
            if {left, right} == {a, b}:
                return False
        self.history.append((a, b, at_ms))
        return True

    def work_count(self):
        return self.work
