# mcd-mcp 工具速查（麦麦省钱参谋专用）

本文件是 SKILL.md 的配套参考，给出各工具的字段细节、传参范例与确认闸门判定。字段以 mcd-mcp 实际 schema 为准，本文档标注易错点。

## 1. 取餐场景映射（所有价格/下单工具的根基）

`calculate-price` 与 `create-order` 都要求 `storeCode` + `orderType` + `beType`，且部分场景要求 `beCode`：

| beType | 名称 | orderType | beCode | beCode 来源工具 |
|--------|------|-----------|--------|----------------|
| 1 | 到店自取 | 1 | 不传 | — |
| 2 | 麦乐送到家（外送） | 2 | 必传 | `delivery-query-stores` |
| 5 | 得来速（DT 车道） | 1 | 必传 | `query-nearby-stores` |
| 6 | 企业团餐 | 2 | 必传 | `delivery-query-stores` |

- `storeCode`：门店编码，永远必填。
- `beCode`：与 `storeCode` 配对使用，来自门店查询工具返回，不得手填。
- `reservationDate`：仅预约场景传，格式 `yyyy-MM-dd HH:mm`；非预约不传。

## 2. 各工具字段要点

### available_coupons（查可领券，只读）
- 入参：无。
- 返回：券名称、图片、状态、促销标签。展示给用户，作为后续用券依据。

### auto_bind_coupons（一键领券，确认闸门）
- 入参：无（自动领全部可领券）。
- 风险：消耗「可领券额度」，属确认闸门——先展示 `available_coupons` 清单，用户说「领券」再调用。

### query_meals（查在售餐品，只读）
- 必填：`storeCode`、`orderType`、`beType`；外送/团餐补 `beCode`。
- 返回：餐品列表 + `productCode`（算价/下单的必填主键）。

### query_promotions（查团餐促销，只读，仅 beType=6）
- 必填：`storeCode`、`orderType=2`、`beType=6`，外送/团餐补 `beCode`。
- 返回促销规则原始数据，每条含：
  - `promotionType`：31=满额减，33=订单折扣
  - `ruleCategory`：30=满折/折扣，40=满减
  - `products`：适用餐品，`type`=1 包含 / 2 不包含 / 3 全部；`productCode` 为餐品编码
  - `ruleDetail`：具体满减/折扣门槛与力度
  - `startTime`/`endTime`：已过滤掉过期/未开始
- 工具只给原始规则，由本技能解读并计算凑单方案，不做推荐。

### calculate-price（算价试券，只读）
- 必填：`storeCode`、`orderType`、`beType`；外送/团餐补 `beCode`。
- `items[]`（数组，必填至少一项）：
  - `productCode`：必填
  - `quantity`：必填，≥1
  - `couponId` / `couponCode`：选填，用券时填（来自 available_coupons 或已领券）
  - `modification.values[]`：特制选项（`code`/`key`/`quantity`），key 规则见 §4
  - `roundList[]`：套餐子项（`round` + `comboItemList[]`，子项同样有 `code`/`quantity`/`modification`）
- `withOrder`：随单购（来自 query_meals），选填，可享随单购优惠
- `needTableware`：是否需要餐具费（bool）
- `gmServiceCode`：团餐助餐服务码
- **返回价格单位为「分」**，展示 ÷100 → 元。
- 返回含 `data.takeWayList[]`（到店/得来速取餐方式），其 `.code` 是下单 `takeWayCode` 来源。**注意：takeWayList 因门店而异**，不同门店返回的取值（如堂食/外带/取餐柜等）可能不同，下单前务必以「本次」算价返回的选项为准，禁止硬编码——任何门店码/取餐码都从实时返回读取，不写死。

### create-order（创建订单，确认闸门）
- 必填：`storeCode`、`orderType`、`beType`。
- `beCode`：得来速/外送/团餐必传。
- `takeWayCode`：到店/得来速（orderType=1）必传，取自算价返回 `data.takeWayList[].code`；外送/团餐（orderType=2）不传。
- `addressId`：外送/团餐必填（配送地址 ID）。来源：`delivery-query-addresses`（查已存地址列表）或 `delivery-create-address`（新建，必填 city/address/addressDetail/contactName/phone，gender 可选）。
- `items[]`：与算价一致，含 `productCode`/`quantity`，用券带 `couponId`/`couponCode`，套餐用 `roundList`，特制用 `modification`。
- `remark`：仅外送场景引导用户填（≤50 字）。
- `reservationDate`：预约场景传。
- 成功后引导支付，并请用户回复「支付完成 / 支付失败」以查订单状态。

### 麦乐送地址获取流程（外送前置，易错点）
- 先 `delivery-query-addresses`（无参，只读）查用户已存地址；若已有匹配地址，取其 `addressId` 直接用。
- 若无，需 `delivery-create-address` 新建，**必填** `city`/`address`/`addressDetail`/`contactName`/`phone`（11 位纯数字），`gender` 建议传。这是**写操作**（往用户账号加地址），按闸门先向用户确认缺失字段再创建，不得编造联系人/电话。
- 拿到 `addressId` 后，`delivery-query-stores(beType=2, addressId)` 取该地址可配送门店 + `beCode`。
- 注意：创建地址与下单都涉及用户账号/资金状态，均须走确认闸门。

## 3. 价格单位换算（最高频错误）

`calculate-price` 返回的 `totalPrice` / 各项金额字段单位为**分**。
- 展示：`金额(元) = 金额(分) ÷ 100`，保留两位小数，前缀 `¥`。
- 例：返回 `3990` → 展示 `¥39.90`；返回 `12500` → `¥125.00`。
- 对比表、推荐语中的所有金额都用「元」呈现，禁止直接把分当元展示。

## 4. 特制选项（modification）key 规则

来自 `query-meal-detail` 的特制项，传 `modification.values[]` 时：
- 选中的项：`key = selectedKey`。
- 未选中的项：若该组 `unselectedKey` 非空，**也必须传入**，`key = unselectedKey`。
- 含 `unselectedKey` 的特制组 = 组内所有项都要传（选中用 selectedKey，未选中用 unselectedKey）。
- 套餐 `roundList[].comboItemList[]` 内商品同样适用。

## 5. 确认闸门判定清单

| 动作 | 工具 | 触发条件 | 闸门 |
|------|------|---------|------|
| 领券 | `auto_bind_coupons` | 用户明确「领券/一键领券」 | 先展示 available_coupons 清单 |
| 下单 | `create-order` | 用户明确「下单/创建订单/就这个」 | 先展示方案+金额+用券，逐项确认 |

- 用户仅浏览/询问 → 只用只读工具，不领券不下单。
- 金额、门店、商品、用券任一项不符用户意图 → 先纠正，不擅自执行。
- 不得在「展示方案」的同一轮对话里顺带调用写工具。

## 6. 调用范例（JSON 片段）

算价（到店自取，无券基准）：
```json
{
  "storeCode": "A1234",
  "orderType": 1,
  "beType": 1,
  "items": [
    { "productCode": "P_BURGER_01", "quantity": 2 }
  ]
}
```

算价（同一单带券试算）：
```json
{
  "storeCode": "A1234",
  "orderType": 1,
  "beType": 1,
  "items": [
    { "productCode": "P_BURGER_01", "quantity": 2, "couponId": "C_xxx", "couponCode": "20261010" }
  ]
}
```

下单（到店自取，取算价返回的 takeWayCode）：
```json
{
  "storeCode": "A1234",
  "orderType": 1,
  "beType": 1,
  "takeWayCode": "TW_001",
  "items": [
    { "productCode": "P_BURGER_01", "quantity": 2, "couponId": "C_xxx", "couponCode": "20261010" }
  ]
}
```
