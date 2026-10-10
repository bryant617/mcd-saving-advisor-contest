# MCP 集成说明

## 麦当劳 MCP Server

| 项目 | 说明 |
|------|------|
| Server 名称 | `mcd-mcp` |
| 提供方 | 麦当劳中国官方 |
| 接入方式 | streamable-http |
| URL | `https://mcp.mcd.cn`（或 `https://mcp.mcd.cn/mcp-servers/mcd-mcp`） |
| 鉴权 | `Authorization: Bearer YOUR_MCP_TOKEN` |
| Token 获取 | 访问 [https://open.mcd.cn/mcp](https://open.mcd.cn/mcp) → 手机号登录 → 控制台 → 激活 → 复制 Token |

配置示例见 `mcp-config.example.json`。该文件**仅允许使用环境变量占位符 `${MCD_MCP_TOKEN}`**，禁止写入真实 Token；真实 Token 通过系统环境变量注入，具体方法见 [`README.md`](./README.md) 的「安装方法」章节。

## 实际调用的 Tool 清单

本 Skill 按「省钱决策工作流」调用以下麦当劳 MCP Tool：

### 只读查询类

| Tool | 作用 | 在工作流中的位置 |
|------|------|-----------------|
| `available_coupons` | 查询用户当前可领取的麦麦省优惠券 | 步骤 1：查券 |
| `query_meals` | 查询指定门店在售餐品及 `productCode` | 步骤 2：选品 |
| `query_promotions` | 查询企业团餐满减/满折规则（仅 beType=6） | 步骤 2：团餐凑单 |
| `calculate-price` | 计算商品总价、折扣、到手价（可带券试算） | 步骤 3：比价 |
| `query-nearby-stores` | 到店/得来速场景取 `storeCode` + `beCode` | 步骤 0：定位门店 |
| `delivery-query-stores` | 外送/团餐场景取配送门店 + `beCode` | 步骤 0：外送定位 |
| `delivery-query-addresses` | 查询用户已存配送地址列表 | 步骤 0：外送地址 |

### 写操作类（受确认闸门约束）

| Tool | 作用 | 风险 | 触发条件 |
|------|------|------|---------|
| `auto_bind_coupons` | 一键领取全部可领券 | 消耗券额度 | 用户明确说「领券 / 一键领券」 |
| `create-order` | 创建订单并生成支付链接 | 真实资金 | 用户明确说「下单 / 就这个」 |
| `delivery-create-address` | 新建配送地址 | 写入账号 | 外送无地址且用户确认后 |

## 调用流程

```
用户输入
   │
   ▼
确认场景（到店 / 麦乐送 / 得来速 / 团餐）
   │
   ├─→ 到店/得来速：query-nearby-stores(beType=1/5) → storeCode(+beCode)
   ├─→ 麦乐送/团餐：delivery-query-addresses → delivery-query-stores(beType=2/6) → storeCode+beCode
   │
   ▼
available_coupons（查券）
   │
   ▼
用户说「领券」？ ──是──▶ auto_bind_coupons（确认闸门）
   │否
   ▼
query_meals（选品） + query_promotions（团餐可选）
   │
   ▼
calculate-price（无券基准价）
   │
   ▼
calculate-price（带券试算）
   │
   ▼
输出对比表 → 用户确认
   │
   ▼
用户说「下单」？ ──是──▶ create-order（确认闸门）
   │否
   ▼
结束
```

## 业务价值

1. **降低决策成本**：用户不再需要打开 App 手动翻券、算价、凑满减，一句话即可获得「最省方案」。
2. **减少优惠浪费**：自动提示可领券、临期券、适用场景，避免「有券没用上」。
3. **团餐效率提升**：企业团餐场景下快速解读满减规则、测算凑单，节省订餐人时间。
4. **安全合规兜底**：敏感操作（领券/下单/新建地址）必须用户显式确认，防止误操作与资金损失。

## 关键约束与错误码

| 错误码 | 含义 | 处理建议 |
|--------|------|---------|
| `600012` | 券不适用该商品 | 券与商品为严格一一绑定，换券或换商品后重试 |
| `60006` | 商品已售罄或不可售 | 沙箱/测试环境常见；建议换商品、换门店、搭配主餐或改外送 |
| beCode 缺失 | 得来速/外送/团餐未传 beCode | 先从门店查询工具取配对编码 |
| 价格单位 | 接口返回「分」 | 展示时 ÷100 转「元」，保留两位小数 |

## 与其他参赛作品的差异

- **定位更窄**：只做「省钱决策」，不做营养、不做每日播报、不做积分商城。
- **约束写死**：把「券↔商品绑定」「确认闸门」「分→元」「60006 边界」等实测硬约束写进 Skill，避免 AI 在沙箱里乱套券、乱下单。
- **零硬编码运行数据**：不预置任何具体城市、门店码、商品码、券码，所有参数来自用户输入或 MCP 实时返回，方便他人直接使用。
