# 发布准备

本仓库发布三个独立 distribution：

- `automas-script-hsr`
- `automas-hsr-adapter-sra`
- `automas-hsr-adapter-m7a`

发布顺序必须先核心包，再发布两个适配器。

## GitHub 设置

1. 在 `AUTO-MAS-Project` 组织创建 `automas-hsr` 仓库，并将本地仓库推送到 `main`。
2. 创建三个 GitHub Environments：`pypi-script-hsr`、`pypi-adapter-sra`、`pypi-adapter-m7a`。
3. 为每个环境设置 Required reviewers，至少包含发布维护者。不要在仓库或环境中保存长期 PyPI token。

## PyPI Trusted Publishing

对三个项目分别添加 pending publisher。每条配置均使用 GitHub Actions：

| PyPI 项目 | Owner | Repository | Workflow | Environment |
| --- | --- | --- | --- | --- |
| `automas-script-hsr` | `AUTO-MAS-Project` | `automas-hsr` | `publish.yml` | `pypi-script-hsr` |
| `automas-hsr-adapter-sra` | `AUTO-MAS-Project` | `automas-hsr` | `publish.yml` | `pypi-adapter-sra` |
| `automas-hsr-adapter-m7a` | `AUTO-MAS-Project` | `automas-hsr` | `publish.yml` | `pypi-adapter-m7a` |

PyPI 的 pending publisher 能在首次 OIDC 发布时创建项目；配置与工作流环境名必须完全一致。

官方说明：

- <https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/>
- <https://docs.pypi.org/trusted-publishers/adding-a-publisher/>

## 发布步骤

1. 合并通过 CI 的版本变更。
2. 从 GitHub Actions 手动运行 `Publish`，先选择 `automas-script-hsr`。
3. 发布成功后依次运行两个适配器包。
4. 在干净环境安装并检查 entry points；随后更新 AUTO-MAS 主仓的插件 bootstrap 版本并进行集成测试。
