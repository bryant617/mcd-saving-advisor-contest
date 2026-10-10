# WorkBuddy 开发对话上下文导出

> 本文件用于核验「麦麦省钱参谋（mcd-saving-advisor）」是否符合 WorkBuddy 专项奖励条件。
> 记录自 2026-10-10 在 WorkBuddy 中与用户的完整开发、验收、优化过程。

## 1. 项目发起

- 用户目标：基于已配置好的麦当劳 MCP（mcd-mcp），开发一个创新 Skill。
- 决策路径：先用「吐槽猎人」方法论做机会筛检，再落地高价值 Skill。
- 最终选定：**Skill 1 —— 麦麦省钱参谋**，定位「查券 → 领券 → 比价 → 选最省 → 确认后下单」。

## 2. 能力面探查（只读）

- 加载 mcd-mcp 工具 schema：`available_coupons`、`auto_bind_coupons`、`calculate-price`、`create-order`、`query_meals`、`query_promotions`、`query-nearby-stores`、`delivery-query-stores`、`delivery-query-addresses` 等。
- 实测只读接口：
  - `available_coupons`：返回 6~7 张可领券。
  - `list_nutrition_foods`：160 项结构化营养数据（用于后续 Skill 2/3 机会评估）。
  - `mall_points_products`：积分商城含派对/联名款/品鉴会。
  - `now_time_info`：服务器时间。
- 明确「能调用 ≠ 值得做」，砍掉纯下单机器人、附近门店查询等低空白度方向。

## 3. Skill 创建与打包

- 使用 `skill-creator` 的 `init_skill.py` 在用户级目录创建骨架：
  - `C:\Users\Administrator\.workbuddy\skills\mcd-saving-advisor\`
- 编写 `SKILL.md`：工作流、确认闸门、beType/orderType/beCode 映射、分→元换算、券↔商品绑定约束、`60006` 边界。
- 编写 `references/mcd-tools.md`、`references/saving-strategy.md`。
- 使用 `package_skill.py` 校验并打包为 `mcd-saving-advisor.zip`，校验通过。

## 4. 真实验收过程

### 4.1 查券
- 调用 `available_coupons` 成功返回可领券清单（厚松饼套餐券×4、免费脆薯饼、麦旋风买一送一、9.9元中杯冰美式等）。

### 4.2 领券（确认闸门）
- 用户明确说「领券」后调用 `auto_bind_coupons`。
- **7 张券全部领取成功，0 失败**，并返回真实 `couponId` / `couponCode`。

### 4.3 带券比价
- 使用真实门店（惠州水口东江 `1420829`）与上海人民广场店 `1450713` 分别验证。
- 关键约束实测：
  - ✅ 9.9元中杯冰美式券 ↔ 指定饮品商品 code 匹配成功，¥19.00 → ¥9.90。
  - ❌ 免费脆薯饼券、厚松饼套餐券、麦旋风买一送一券套到非专属商品 code 均报 `600012`。
- 结论：**券与商品严格一一编码绑定**，已写进 Skill。

### 4.4 真实下单尝试
- 用户确认「下单，外带」后调用 `create-order`。
- 结果：**失败**，返回 `60006 商品已售罄或不可售`，订单未生成、未扣款。
- 诊断过程：
  - 方案 A：去券、仅脆薯饼 → 仍 60006（排除券限制）。
  - 方案 B：换双层猪柳蛋麦满分 → 算价阶段即 60006。
  - 上海店探测：同一组合之前算价成功，后期也 60006。
- 最终结论：**mcd-mcp 沙箱/测试环境商品可售状态动态波动**，`60006` 是环境限制而非 Skill 逻辑错误。已把此边界写死进 Skill。

### 4.5 麦乐送链路探查
- 用户给配送地址「惠州水口东江」。
- 发现账号无已存地址，需 `delivery-create-address` 新建（需联系人/手机/门牌号）。
- 因用户不愿在通用 Skill 中硬编码真实个人信息，未继续创建地址；把正确链路写入 Skill。

## 5. 脱敏与通用化

- 用户要求：Skill 要分享给别人用，不能硬编码验收时的城市、门店码、商品码、券码、个人信息。
- 执行：
  - 清理 `SKILL.md`、`references/mcd-tools.md`、`references/saving-strategy.md` 中所有具体城市、门店码、商品码、真实券码、地名。
  - 新增「零硬编码运行数据」原则：所有运行参数来自用户输入或 MCP 实时返回。
  - 重新打包校验通过。

## 6. 按比赛要求优化为项目仓库

- 用户提供比赛报名要求截图，要求仓库包含：
  - `README.md`（必须）
  - `CONTEST_DECLARATION.md`（必须，官方模板）
  - `MCP_INTEGRATION.md`（必须）
  - 源代码（必须）
  - `workbuddy.md`（WorkBuddy 专项奖励必须）
- 执行：
  - 创建比赛仓库 `G:/MCD/mcd-saving-advisor-contest/`。
  - 从 GitHub 同类参赛项目拉取官方 `CONTEST_DECLARATION.md` 模板（内容一致，未改动）。
  - 编写 `README.md`、`MCP_INTEGRATION.md`。
  - 复制已脱敏的 `SKILL.md` 与 `references/`。
  - 编写 `scripts/rank_combos.py`、`scripts/price_calculator.py`（零依赖、可离线运行）。
  - 编写 `fixtures/sample_candidates.json`、`fixtures/sample_menu.json`。
  - 编写 `mcp-config.example.json`、`.gitignore`。
  - 本文件 `workbuddy.md`。

## 7. 再次按比赛要求优化（本次）

用户再次提供报名要求截图，要求按「将项目发布至个人 GitHub 公开仓库」的标准补充与优化。

- 优化项：
  - `mcp-config.example.json`：将 `YOUR_MCP_TOKEN` 改为环境变量占位符 `${MCD_MCP_TOKEN}`，并在 README/MCP_INTEGRATION 中说明注入方式。
  - `README.md`：重写为 GitHub 公开仓库首页风格，增加徽章、目录、环境变量配置、完整使用示例、效果展示、致谢等。
  - 新增 `LICENSE`（MIT）：明确开源许可。
  - 新增 `CONTRIBUTING.md`：贡献指南与安全合规要求。
  - 新增 `screenshots/README.md`：演示截图占位与引用说明。
  - `.gitignore`：已包含 `mcp-config.json`，防止真实 Token 误提交。
  - 验证：本地 Python 脚本可运行，仓库无真实 Token、无硬编码运行数据。

## 8. 关键交付物

- WorkBuddy Skill：`C:\Users\Administrator\.workbuddy\skills\mcd-saving-advisor\`
- 比赛项目仓库：`G:\MCD\mcd-saving-advisor-contest\`
- Skill 打包产物：`C:\Users\Administrator\.workbuddy\skills\mcd-saving-advisor.zip`

## 9. 可复现的验证命令

```bash
cd G:/MCD/mcd-saving-advisor-contest/scripts

# 候选方案排序（离线）
python rank_combos.py --input ../fixtures/sample_candidates.json --top 3

# 模拟完整省钱工作流（离线，自动确认模式）
python price_calculator.py --fixtures ../fixtures/sample_menu.json --yes
```
