# 七乐彩选号技能

为 OpenClaw 添加七乐彩选号、复盘能力。

## 触发条件

用户提到以下内容时触发：
- "七乐彩选号"
- "七乐彩推荐"
- "七乐彩复盘"
- "今天七乐彩"
- "周一/三/五买什么彩票"

## 可用命令

### 生成选号
```bash
python3 /home/Jaben/.openclaw/workspace-finnace-bot/lottery-qlc/scripts/generate_qlc.py
```

输出：
- 5 注单式推荐（每注 2 元，共 10 元）
- 1 注 8+1 复式推荐（16 元）
- JSON 和 Markdown 格式输出到 `outputs/` 目录

### 开奖复盘
```bash
python3 /home/Jaben/.openclaw/workspace-finnace-bot/lottery-qlc/scripts/review_qlc.py
```

功能：
- 读取最新开奖结果
- 对比上期选号
- 输出命中情况和奖金
- 提供规则优化建议

### 更新历史数据
```bash
python3 /home/Jaben/.openclaw/workspace-finnace-bot/lottery-qlc/scripts/update_qlc_history.py
```

⚠️ 当前数据接口待完善，需手动导入历史数据。

## 七乐彩规则

- **开奖日期**：每周一、三、五 21:15
- **玩法规则**：从 01-30 选 7 个红球 + 从 01-16 选 1 个特别号
- **单注成本**：2 元
- **奖级设置**：7 个奖级（一等奖到七等奖）

## 输出示例

生成选号后，向用户展示：
1. 单式推荐（5 注）
2. 复式推荐（8+1）
3. 总成本
4. 下次开奖日期

复盘时展示：
1. 开奖号码
2. 命中情况（每注）
3. 总奖金
4. 最好表现
5. 规则优化建议

## 文件位置

- **工作目录**：`/home/Jaben/.openclaw/workspace-finnace-bot/lottery-qlc/`
- **脚本目录**：`scripts/`
- **数据目录**：`data/qlc_history.csv`
- **输出目录**：`outputs/`
- **配置文件**：`config.json`
- **策略文档**：`docs/strategy.md`

## 与双色球系统关系

- 独立目录维护：`lottery-qlc/` vs `lottery-ssq/`
- 脚本结构相同，参数不同
- 可共用 OpenClaw 技能框架

---

*理性购彩，量力而行。本技能仅供娱乐参考。*
