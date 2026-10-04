# match-antijoin

匹配防连坐：按真实时间冷却窗口避免同一对玩家连续配到一起，场景以 JSON 剧本回放，只用 Python 标准库。

```
python3 -m antijoin.replay --scenario scenarios/cooldown.json
python3 -m antijoin.replay --scenario scenarios/self.json
python3 -m antijoin.replay --scenario scenarios/dup.json
python3 -m antijoin.replay --sample work
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **冷却窗口**：同一对玩家（不分先后）距上次配对不满 `cooldown_ms` 才禁止再配；
  正好等于冷却时长算已过冷却，可以再配。
- **自匹配**：`a` 等于 `b` 一律拒绝。
- **幂等**：同一个 `match_id` 只结算一次，重复出现按同一条处理。
- **窗口回收**：冷却窗口外的历史必须回收，判定不许全扫历史，`work_count()` 不随历史条数乘判定次数增长。
- **报告**：输出一行 JSON，含 `allowed`、`blocked`、`matches`、`work` 四个字段。

## 输出契约（不改格式）

```
{"allowed": .., "blocked": .., "work": .., "matches": ..}
```

## 目录

```
antijoin/engine.py     冷却窗口与配对判定
antijoin/replay.py     场景回放入口
scenarios/*.json       回放剧本
tests/test_engine.py   unittest 用例
```
