# AUTO-MAS HSR Plugins

AUTO-MAS 的崩坏：星穹铁道插件工作区，也是 HSR 插件及其引擎适配器的唯一源码仓库。

主程序不内置本仓库源码，也不把 HSR 脚本随主程序捆绑安装。完整体验可一键安装
`automas-hsr`；只使用单个引擎时，也可在 AUTO-MAS 插件市场单独选择 SRA 或
三月七助手适配器，适配器依赖会自动安装 HSR 核心包。

## Packages

- `automas-hsr`：一键安装 HSR 核心包与两个引擎适配器的 meta-package。
- `automas-script-hsr`：HSR 脚本入口、配置模型、调度和公共契约。
- `automas-hsr-adapter-sra`：StarRailAssistant 适配器。
- `automas-hsr-adapter-m7a`：三月七助手适配器。

每个目录独立构建为一个 Python distribution。`automas-hsr` 不包含运行时代码或
插件 entry point；适配器依赖 `automas-script-hsr`，适配器之间互不依赖。

## Development

```powershell
uv sync --locked --all-packages --group dev
uv run python -m unittest discover -s tests -v
uv run python scripts/build_all.py
uv run twine check dist/*/*
uv run python scripts/smoke_wheels.py dist --mode local-adapter-resolution
uv run python scripts/smoke_wheels.py dist --mode local-meta-resolution
```

## Publishing

发行只通过 GitHub Actions 和 PyPI Trusted Publishing 完成，不保存长期 PyPI
token，也不从开发机直接上传。完整配置与首发流程见 [docs/release.md](docs/release.md)。
