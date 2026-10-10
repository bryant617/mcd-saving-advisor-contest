# 贡献指南

感谢你对「麦麦省钱参谋（mcd-saving-advisor）」的兴趣！

## 如何贡献

1. **Fork 本仓库** 到你的个人 GitHub 账号。
2. **创建分支**：`git checkout -b feature/your-idea`
3. **提交改动**：`git commit -m "feat: 描述你的改动"`
4. **推送分支**：`git push origin feature/your-idea`
5. **发起 Pull Request**。

## 提交规范

- 不要提交任何真实 Token、密钥、账号凭证或个人敏感信息。
- 保持 `mcp-config.example.json` 中仅使用环境变量占位符。
- 新增代码尽量附带 fixtures 数据，方便离线测试。
- 涉及麦当劳 MCP 工具调用的改动，请在 `MCP_INTEGRATION.md` 同步更新工具清单与流程说明。

## 本地测试

```bash
cd scripts
python rank_combos.py --input ../fixtures/sample_candidates.json --top 3
python price_calculator.py --fixtures ../fixtures/sample_menu.json
```

## 安全与合规

- 领券 / 下单等高风险操作必须保留确认闸门。
- 错误码如实报告，不假装成功。
- 不预置任何门店码、商品码、券码。

## 联系我们

如有问题或建议，欢迎通过 GitHub Issues 讨论。
