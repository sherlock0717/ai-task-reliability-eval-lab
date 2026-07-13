from __future__ import annotations

# Case 数据直接存放在 docs/data，GitHub Pages 与 Python 注册表读取同一份文件。
# 该脚本保留为兼容入口，避免旧命令失效。

from creative_agent_eval.registry import validate_registry


def main() -> None:
    summary = validate_registry()
    print(f"case data ready: {summary['case_count']} cases")


if __name__ == "__main__":
    main()
