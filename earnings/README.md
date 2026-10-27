# 财报与会议 — 刷新方法
```
python3 -m venv /workspace/venv-earn && /workspace/venv-earn/bin/pip install yfinance
/workspace/venv-earn/bin/python earnings/scripts/refresh_earnings.py   # 日期+一致预期+最近财报 (Yahoo + Nasdaq)
python3 earnings/scripts/refresh_macro.py                              # 合并 ForexFactory 本周中美日历(预期/前值)
```
人工维护（无免费API）：`calendar.json` 中已公布宏观数据的实际值/对比、会议结果与市场预期；`earnings.json` 中 guidance/note/manual。
发布后用 Playwright 检查 1280/375/414 宽度。
