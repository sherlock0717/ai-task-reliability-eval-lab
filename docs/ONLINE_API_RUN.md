# 在线与本地API运行

## 密钥处理

不要把DeepSeek API Key写入聊天、代码、Issue、PR、日志或普通配置文件。

线上运行使用GitHub Environment Secret：

1. 打开仓库 `Settings`；
2. 进入 `Environments`，创建 `deepseek-eval`；
3. 在该环境中添加Secret：`DEEPSEEK_API_KEY`；
4. 可选：为环境增加人工批准规则；
5. 在 `Actions` 中手动运行 `Run DeepSeek API smoke`。

工作流只运行一个Case，并把Trace保存为Artifact。它不会在push或pull request时自动调用API。

未配置Secret时，工作流会显示提示并正常结束，不发送API请求，也不会因为缺少密钥产生失败邮件。真实API调用、认证错误或接口错误仍会按失败处理。

## 本地运行

在本地终端设置环境变量，再调用同一CLI：

```bash
export DEEPSEEK_API_KEY='...'
creative-agent-eval run-api \
  --case-id B04 \
  --model deepseek-v4-flash \
  --thinking enabled \
  --reasoning-effort high \
  --out outputs/api_smoke/B04.json
```

Windows PowerShell：

```powershell
$env:DEEPSEEK_API_KEY='...'
creative-agent-eval run-api `
  --case-id B04 `
  --model deepseek-v4-flash `
  --thinking enabled `
  --reasoning-effort high `
  --out outputs/api_smoke/B04.json
```

## 当前范围

当前API入口覆盖L0单次生成和单Case运行，用于验证认证、模型响应、用量字段和Trace落盘。L1—L3的离线执行已经可用；真实工具调用、多Loop API跑批和正式统计仍留到后续阶段。
