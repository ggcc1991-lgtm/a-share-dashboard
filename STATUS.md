# 推进清单（壳层）

## 已完成（本地）
- [x] 彭博壳：纯黑底 + 琥珀 `#FFA028`（`theme.css`）
- [x] 总览抄底密表 + 头栏「文案上 / 进度条下」（`index.html` + `.bb-ind*`）
- [x] 顶栏五栏含「政策产业」→ `/policy/`
- [x] `/policy/` 读 `policy/snapshot.json`（v1）；真快照已在目录
- [x] 图表壳色去掉偏蓝灰（`shell.js` DashTheme）
- [x] `/bottom/` 重建为真壳页（非 fat wrap；fetch `data/bottom.json` + `.bb-ind*`）

## 线上待合（相对 Pages）
- [ ] 强调色仍为 `#ff6400` → 推 `#FFA028`
- [ ] 头栏仍为三列挤字 → 推当前 `.bb-ind-top` / `.bb-ind-top-main`
- [ ] `policy/snapshot.json` 线上 404 → 随 `policy/` 整目录推
- [ ] 线上 `data/policy.json` 仍是 4 条假数据（可留作废弃或删）

## 他人负责
- 政策产业观察：页面内容已在本地 `policy/index.html`（可再迭代）
- ETF / feed / bottom 子页内容：各助手
- github助手：推送与 Pages
