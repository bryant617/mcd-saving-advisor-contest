# 麦麦省钱参谋（mcd-saving-advisor）

[![WorkBuddy Skill](https://img.shields.io/badge/WorkBuddy-Skill-blue)](https://www.workbuddy.cn)
[![MCP](https://img.shields.io/badge/Powered%20by-MCP-orange)](https://modelcontextprotocol.io/)
[![McDonald's](https://img.shields.io/badge/McDonald's-中国-red)](https://www.mcdonalds.com.cn/)

基于麦当劳中国官方 MCP（`mcd-mcp`）的「省钱点餐」WorkBuddy Skill，参加 **2026 麦当劳程序员节创意开发大赛**。

> **一句话介绍**：把麦当劳的券、菜单、价格引擎串成一条「查券 → 领券 → 比价 → 选最省 → 确认后下单」的省钱决策工作流，让 AI 帮你少花钱、用对券。

---

## 目录

- [功能特性](#功能特性)
- [目标用户](#目标用户)
- [效果展示](#效果展示)
- [安装方法](#安装方法)
  - [方式一：WorkBuddy 中加载（推荐）](#方式一workbuddy-中加载推荐)
  - [方式二：本地运行参考脚本](#方式二本地运行参考脚本)
- [使用示例](#使用示例)
- [项目仓库结构](#项目仓库结构)
- [安全与合规](#安全与合规)
- [MCP 集成详情](#mcp-集成详情)
- [许可证](#许可证)
- [致谢](#致谢)

---

## 功能特性

| 场景 | 示例 | 能力 |
|------|------|------|
| 查可领券 | "现在有什么优惠券" | 调用 `available_coupons` 展示可领券 |
| 一键领券 | "帮我领券" | 确认后调用 `auto_bind_coupons` 领取全部可用券 |
| 用券比价 | "用券后多少钱" | 无券基准价 + 带券试算，输出对比表 |
| 团餐凑单 | "人均 30 怎么点" | 查菜单、算价、给搭配建议 |
| 确认下单 | "就这个，下单" | 展示方案逐项确认后 `create-order` |

核心设计亮点：

- **确认闸门**：领券、下单等涉及真实资金/券额度的动作，必须等用户明确说「领券 / 就这个 / 下单」后才执行。
- **券↔商品严格绑定**：把券名与菜单商品名近似对应，误配会报 `600012`，绝不硬凑。
- **分→元自动换算**：接口返回「分」，展示时 ÷100 并保留两位小数。
- **零硬编码运行数据**：不预置任何门店码、商品码、券码，全部来自用户输入或 MCP 实时返回，方便分享给别人用。
- **60006 边界处理**：沙箱/测试环境常见「商品已售罄或不可售」，如实报告并给出诊断方向，不假装成功。

---

## 目标用户

- 经常点麦当劳、想少花钱的学生 / 上班族。
- 部门 / 团队团餐负责人，需要快速凑满减、比出最省方案。
- 任何想用自然语言把麦当劳优惠用满的「麦门信徒」。
- 参加麦当劳 MCP 创新大赛、想参考一个完整 Skill 项目的开发者。

---

## 效果展示

> 由于涉及麦当劳账号与真实支付，本项目不提供线上实时演示截图。你可以在本地按下方「安装方法」配置自己的 MCP Token 后，对 WorkBuddy 说：
>
> ```
> 帮我查麦当劳优惠券
> 领券
> 帮我搭配一个最省的午餐
> 就这个，下单
> ```

本地离线脚本演示（无需 Token）：

```bash
cd scripts
python rank_combos.py --input ../fixtures/sample_candidates.json --top 3
```

```bash
python price_calculator.py --fixtures ../fixtures/sample_menu.json --yes
```

---

## 安装方法

### 方式一：WorkBuddy 中加载（推荐，可参与 WorkBuddy 专项奖励）

1. **配置 MCP 环境变量**

   本仓库的 `mcp-config.example.json` 使用占位符 `${MCD_MCP_TOKEN}`，禁止直接写入真实 Token。请在系统环境变量中设置：

   - **Windows（PowerShell）**

     ```powershell
     [Environment]::SetEnvironmentVariable("MCD_MCP_TOKEN", "你的麦当劳 MCP Token", "User")
     ```

   - **macOS / Linux**

     ```bash
     export MCD_MCP_TOKEN='你的麦当劳 MCP Token'
     ```

   Token 获取方式：访问 [https://open.mcd.cn/mcp](https://open.mcd.cn/mcp) → 手机号登录 → 控制台 → 激活 → 复制 Token。

2. **复制 MCP 配置**

   将 `mcp-config.example.json` 复制为 `mcp-config.json`，并确保其中仍然只有占位符：

   ```bash
   cp mcp-config.example.json mcp-config.json
   ```

   > 注意：`mcp-config.json` 已加入 `.gitignore`，不会被提交到 GitHub。

3. **安装 Skill**

   将本仓库的 `SKILL.md` 及 `references/` 复制到 WorkBuddy 用户技能目录：

   ```
   C:\Users\<你的用户名>\.workbuddy\skills\mcd-saving-advisor\
   ```

4. **启用 MCP 连接器**

   在 WorkBuddy 左侧【专家·技能·连接器】→【连接器】→ 右上角【自定义连接器】→【配置 MCP】中导入 `mcp-config.json`，保存并启用 `mcd-mcp`（首次需点「信任」）。

5. **开始对话**

   对 WorkBuddy 说：

   - "帮我查麦当劳优惠券"
   - "领券"
   - "怎么点最划算"
   - "就这个，下单"

### 方式二：本地运行参考脚本（无需 Token，离线可跑）

```bash
# 候选方案排序
cd scripts
python rank_combos.py --input ../fixtures/sample_candidates.json --top 3

# 模拟完整省钱工作流
python price_calculator.py --fixtures ../fixtures/sample_menu.json
```

---

## 使用示例

### 示例 1：查券并比价

```text
用户：帮我查麦当劳优惠券
AI：当前有 X 张可领券：...
用户：领券
AI：已领取 X 张券：...
用户：怎么用券最划算
AI：给出无券价 / 带券价对比表，推荐最省方案
```

### 示例 2：团餐凑单

```text
用户：部门 10 人，人均 30，怎么点最划算
AI：查询企业团餐促销 → 解读满减规则 → 给出 A/B/C 三套凑单方案 → 等用户确认
```

### 示例 3：确认后下单

```text
用户：就这个，下单
AI：展示最终方案（门店 / 商品 / 用券 / 金额 / 取餐方式），请用户确认
用户：确认，外带
AI：调用 create-order 生成订单并引导支付
```

---

## 项目仓库结构

```
mcd-saving-advisor/
├── README.md                 # 本文件：项目介绍、安装方法、使用示例
├── CONTEST_DECLARATION.md    # 参赛声明（官方模板，内容不可改动）
├── MCP_INTEGRATION.md        # 麦当劳 MCP Server / Tool / 调用流程 / 业务价值
├── SKILL.md                  # WorkBuddy Skill 核心定义（可直接加载）
├── workbuddy.md              # WorkBuddy 开发对话上下文导出
├── mcp-config.example.json   # 脱敏 MCP 配置示例（仅环境变量占位符）
├── .gitignore                # 忽略真实 Token 与本地配置文件
├── LICENSE                   # 开源许可证
├── scripts/                  # 可运行的参考代码 / 本地策略引擎
│   ├── rank_combos.py        # 本地候选方案排序（零依赖，可离线演示）
│   └── price_calculator.py   # 模拟算价 + 用券匹配 + 确认闸门（安全可运行）
├── fixtures/                 # 本地脚本示例数据
│   ├── sample_candidates.json
│   └── sample_menu.json
└── references/               # Skill 配套参考资料
    ├── mcd-tools.md          # mcd-mcp 工具字段速查
    └── saving-strategy.md    # 省钱策略与方法论
```

---

## 安全与合规

- **仓库内不包含任何真实 Token**；`mcp-config.example.json` 仅使用 `${MCD_MCP_TOKEN}` 环境变量占位符。
- **本地真实配置文件**（`mcp-config.json`）已加入 `.gitignore`，不会被提交到 GitHub。
- 领券 / 下单等资金/券消耗操作受**确认闸门**约束：必须用户明确说「领券 / 下单 / 就这个」后才执行。
- 错误码（如 `600012` 券不适用、`60006` 商品不可售）**如实报告**，不假装成功、不硬重试生成订单。
- 本项目不代表麦当劳官方背书；商标归权利人所有。详见 `CONTEST_DECLARATION.md`。

---

## MCP 集成详情

详见 [`MCP_INTEGRATION.md`](./MCP_INTEGRATION.md)。

快速概览：

| Server | 类型 | URL | 鉴权 |
|--------|------|-----|------|
| `mcd-mcp` | streamable-http | `https://mcp.mcd.cn` | `Authorization: Bearer ${MCD_MCP_TOKEN}` |

核心工具：`available_coupons`、`auto_bind_coupons`、`query_meals`、`calculate-price`、`create-order`、`query-nearby-stores`、`delivery-query-stores` 等。

---

## 许可证

本仓库以 [MIT](./LICENSE) 许可证开源，参赛作品以学习与比赛交流为目的。

使用麦当劳 MCP 须遵守麦当劳中国《使用条款》与 MCP 服务规则。

---

## 致谢

- 麦当劳中国官方 MCP Server 提供的数据与能力支持。
- WorkBuddy 平台提供的 Skill 开发与运行框架。
- 2026 麦当劳程序员节创意开发大赛组委会。
