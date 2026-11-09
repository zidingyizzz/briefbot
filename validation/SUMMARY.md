# BriefBot 3 天真实数据验证汇总（2026-10-19 ~ 10-21）

- 运行方式：系统调度器（launchd）每日定时运行，配置 `validation/real-world.yaml`，plain 模式（无 LLM key）。
- 任务：cn-tech-digest（sspai / solidot / V2EX / 开源中国 四源 RSS）、nextjs-stats-watch（GitHub API star/fork/issues 字段差分）、nextjs-release-watch（releases.atom 新发版）。
- 基线：2026-10-18 手动首跑（40 条入库 + 首次快照 stars=143062 / forks=35158 / issues=3696）；同日第二次运行零重复，验证去重正常。
- 原始证据：本目录 `day1-3-archive/`（logs/ + reports/ + real-world.yaml）。

## 与任务书的一处偏差（如实记录）

任务书写的是每天 **09:05** 运行，但实际 plist 的 `StartCalendarInterval` 为 **每天 18:00**（见 day1-3-archive 同批安装产物；三天报告时间戳均为 18:00:0x，与 plist 一致）。三天均在 18:00 实际成功运行，**无漏跑**；只是执行时刻与任务书描述不符，推测安装时为规避白天开机不确定而改到了 18:00。

## 逐日结果

| 日期 | cn-tech-digest | nextjs-stats-watch | nextjs-release-watch |
|---|---|---|---|
| 10-18（基线） | ok，40 条新入库 | ok，首快照（1 项变更） | ok，5 条新发版 |
| 10-19 | ok，32 条 | ok，3 项字段变化（stars +24 / forks +83 / issues +3） | skipped（无新发版，正常） |
| 10-20 | ok，34 条 | ok，3 项字段变化（stars +18 / forks +39 / issues +9） | ok，2 条（canary.19 / canary.18） |
| 10-21 | ok，33 条 | ok，3 项字段变化（stars −2 / forks −528 / issues +27） | ok，2 条（canary.21 / canary.20） |

三天（10-19/20/21）均有完整运行记录：`run-20261019.log`、`run-20261020.log`、`run-20261021.log` 及对应 reports 均存在，无缺失。

## 状态统计

- ok：cn-tech-digest 3/3、nextjs-stats-watch 3/3、nextjs-release-watch 2/3（10-19 skipped 属正常无事件，非故障）。
- error：**0 次**。三天 9 次任务执行无一报错，`launchd.log` 为空（无 stderr 输出）。
- 新增条目：RSS 摘要共 99 条（32+34+33）；新发版共 4 条；stats 每日 3 字段变化均被捕获。

## 发现的问题与异常

1. **调度时刻与任务书不符**（09:05 vs 实际 18:00）——见上，不影响验证有效性。
2. **10-21 forks 单日 −528（35280 → 34752）**：汇总当日（10-21 晚）直查 GitHub API 得 forks=34774，与抓到的 34752 同量级，说明回落是 GitHub 侧真实变化（疑似批量清理垃圾/封禁 fork），BriefBot 如实差分，非工具误报。stars −2 同理属正常小幅回落。
3. **源失败/反爬/网络干扰：零**。sspai、solidot、V2EX、开源中国 RSS 与 GitHub API（含未认证限额内）三天全部正常，未触发任何 SSL 拦截或限流（Day 0 曾遇到的 SSL 坑在验证期内未复现）。
4. 10-18 基线当天第二次运行三任务全部 skipped 且零重复输出，去重/幂等表现符合预期。

## 对发布清单「自跑 3 天真实数据」的结论

**达标。** 依据：

- 3 个任务 × 3 天 = 9 次调度全部有运行记录，0 error，无一天缺 log；
- 数据维度全覆盖：每日 RSS 新条目（99 条）、字段差分（每日 3 项）、新发版事件（含 skipped 无事件日，证明零噪音）；
- 异常数据（forks 骤降）经外部交叉验证为真实，工具行为正确；
- 原始日志与报告已归档于 `day1-3-archive/`，可审计。

`docs/GUMROAD_LISTING.md` 中标记 [DAY-2/3] 的两处（included 的「3 天真实验证报告」、gallery 第 4 张图）现在具备了填充材料。

## 下一步建议

1. 将 GUMROAD_LISTING 的 [DAY-2/3] 占位替换为指向本 SUMMARY 与 day1-3-archive 的表述；gallery 第 4 张图可用三张日报截图拼接或 forks 骤降事件图（差异化证据）。
2. 复核 zip 包在干净机器上的可复现性（发布前置项），plain 模式无需 key 是卖点之一，可明示。
3. 调度验证任务已停用并清理（窗口结束）；本地副本暂留作复测材料。
4. 若后续版本做 LLM 摘要模式，建议用同一配置补一轮 3 天 A/B（plain vs LLM 输出对比），可作 listing 的进阶证据。

_生成于 2026-10-21，由验证窗口收尾汇总任务产出。_
