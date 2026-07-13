# Fixture层

`B04.json`保留为首个手工编写的Case级fixture。其余Case在运行时由题面、Gold、工具声明和自动检查生成确定性基线fixture。

生成全部36份fixture：

```bash
creative-agent-eval materialize-fixtures --out-dir outputs/materialized_fixtures
```

生成结果包含：

- 每题一份JSON；
- 工具白名单；
- Gold中的必须条件、禁止失败和可接受策略；
- 从题面抽取的资源清单；
- `manifest.json`覆盖摘要。

生成fixture用于工程连通性、工具白名单和回归测试。需要精确物理参数、语义关系或状态转移时，应增加手工Case级fixture覆盖基线数据。
