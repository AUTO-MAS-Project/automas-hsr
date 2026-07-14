# AUTO-MAS HSR Plugins

AUTO-MAS 的星穹铁道插件工作区。仓库统一维护 HSR 调度、StarRailAssistant 和三月七助手的适配代码；每个目录仍独立构建并发布为一个 Python distribution。

## Packages

- `automas-script-hsr`：HSR 脚本入口、配置模型、调度和公共契约。
- `automas-hsr-adapter-sra`：StarRailAssistant 适配器。
- `automas-hsr-adapter-m7a`：三月七助手适配器。

## Development

```powershell
uv sync --all-packages --group dev
uv run python -m unittest discover -s tests -v
uv run python scripts/build_all.py
```

## Publishing

通过 GitHub Actions 的 `Publish` 手动工作流发布单个 distribution。发布使用 PyPI Trusted Publishing，不保存长期 PyPI token。
