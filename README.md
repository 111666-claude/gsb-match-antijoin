# match-antijoin

匹配防连坐：按真实时间冷却窗口挑对手，并受评分差上限、每 tick 配对预算与撤销窗口约束；
场景用 `scenarios/*.json` 回放，输出一行 JSON 报告，只用 Python 标准库。

```
python3 -m antijoin.replay --scenario scenarios/cooldown.json
python3 -m antijoin.replay --scenario scenarios/gap.json
python3 -m antijoin.replay --scenario scenarios/budget.json
python3 -m antijoin.replay --scenario scenarios/undo.json
python3 -m antijoin.replay --sample cooldown
python3 -m antijoin.replay --sample gap
python3 -m antijoin.replay --sample budget
python3 -m antijoin.replay --sample undo
python3 -m antijoin.replay --sample work
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **冷却窗口**：同一对玩家（不分先后）距上次成功且未撤销的配对不满 `cooldown_ms` 才禁止再配；
  正好等于冷却时长算已过冷却。冷却记录必须按时间回收，判定不许全扫历史。
- **评分差**：只有评分差不超过 `max_gap` 的两名玩家能配到一起。
- **每 tick 预算**：一次 `fill` 最多配成 `budget_per_tick` 场，没轮上的留在队列里并计入 `deferred`。
- **撤销**：`undo` 只接受配成时刻起 `confirm_ms` 内的请求，撤销后这场不计入冷却；超出窗口返回 false。
- **幂等**：同一 `match_id` 只结算一次；同一玩家重复入队只保留最早那条。
- **不变量**：队列里玩家不重复；已配成的玩家离开队列；冷却只由成功且未撤销的配对产生。
- **报告**：一行 JSON，含 `pairs`、`deferred`、`undone`、`waiting`、`work`；`work` 不随历史条数乘判定次数增长。

## 输出契约（不改格式）

```
{"pairs": .., "deferred": .., "undone": .., "waiting": .., "work": ..}
```

## 目录

```
antijoin/engine.py     冷却索引、评分差、预算与撤销
antijoin/replay.py     场景回放入口
scenarios/*.json       回放剧本
tests/test_engine.py   unittest 用例
```
