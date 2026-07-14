# Agent Instructions

本仓库维护 AUTO-MAS 的 HSR 插件工作区。

- `packages/` 下每个目录是独立 Python distribution；项目名、公开 entry point 和包路径不得随意变更。
- `automas-script-hsr` 是 HSR 编排和契约的唯一拥有者；SRA、三月七适配器只能依赖它，不能互相依赖。
- 插件通过稳定的 DTO 或 JSON 兼容字典跨包协作，不能将某个适配器的内部模型作为另一个包的契约。
- 代码使用 AUTO-MAS 主程序提供的 `app` 插件接口时，应保持与宿主兼容，不把宿主实现复制进本仓库。
- 修改包的代码或发行契约时，同步更新对应测试、版本和内部依赖下限。
- 提交前运行 `uv run python -m unittest discover -s tests -v` 和 `uv run python scripts/build_all.py`。
- 不提交 `dist/`、`build/`、`*.egg-info`、虚拟环境或 Python 缓存。
