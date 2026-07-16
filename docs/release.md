# 发布准备

本仓库发布四个独立 distribution：

- `automas-hsr`
- `automas-script-hsr`
- `automas-hsr-adapter-sra`
- `automas-hsr-adapter-m7a`

首次发布必须先发布核心包，再发布两个适配器，最后发布一键安装聚合包
`automas-hsr`。AUTO-MAS 主程序不内置这些源码；用户既可安装聚合包获得完整双引擎
体验，也可在插件市场只安装自己选择的适配器，适配器依赖会自动拉取核心包。

## GitHub Environments

在 `AUTO-MAS-Project/automas-hsr` 创建四个 environment：

- `pypi-hsr`
- `pypi-script-hsr`
- `pypi-adapter-sra`
- `pypi-adapter-m7a`

每个 environment 应配置 required reviewers，并限制部署来源：允许 `main` 用于首次
手动发布，允许对应的包版本 tag 用于后续自动发布。仓库和 environment 都不保存
PyPI 用户名、密码或长期 token。

## PyPI Trusted Publishing

在 PyPI 的 Publishing 页面为三个项目分别创建 pending publisher：

| PyPI 项目 | Owner | Repository | Workflow | Environment |
| --- | --- | --- | --- | --- |
| `automas-hsr` | `AUTO-MAS-Project` | `automas-hsr` | `publish.yml` | `pypi-hsr` |
| `automas-script-hsr` | `AUTO-MAS-Project` | `automas-hsr` | `publish.yml` | `pypi-script-hsr` |
| `automas-hsr-adapter-sra` | `AUTO-MAS-Project` | `automas-hsr` | `publish.yml` | `pypi-adapter-sra` |
| `automas-hsr-adapter-m7a` | `AUTO-MAS-Project` | `automas-hsr` | `publish.yml` | `pypi-adapter-m7a` |

Pending publisher 会在首次 OIDC 发布时创建对应 PyPI 项目。项目名、workflow 文件名和
environment 名必须与表格完全一致。

官方说明：

- <https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/>
- <https://docs.pypi.org/trusted-publishers/adding-a-publisher/>

## 首次发布

1. 确认 `main` 上的 CI 全部通过，且四个 `pyproject.toml` 的版本正确。
2. 在 GitHub Actions 手动运行 `Publish`，ref 必须选择 `main`。
3. 选择包并填写与该包 `pyproject.toml` 完全一致的版本号。
4. 先发布 `automas-script-hsr`；发布成功后依次发布两个适配器，最后发布
   `automas-hsr`。
5. 每次都在对应 environment 审批后，才会通过 OIDC 上传。

全仓 CI 会分别安装 SRA/M7A adapter，并用 `--no-index` 从本次构建产物解析和安装
`automas-script-hsr`，验证 adapter 的依赖声明确实会自动拉取 core；还会单独安装
`automas-hsr`，验证它能从本次构建的 wheel 一次解析 core 和两个 adapter，并暴露三个
实际插件 entry point。发布工作流会重新运行测试，只构建一次所选包，并执行
`twine check` 与不解析依赖的单包元数据冒烟测试；依赖包按上述发布顺序已先存在于
PyPI。随后，同一份已验证 artifact 才交给发布 job。手动发布若不在 `main`，或填写
版本与项目版本不一致，会在获取 PyPI OIDC 权限前失败。

## 后续 tag 发布

后续版本使用包级 tag，tag 中版本必须与对应 `pyproject.toml` 一致：

```text
automas-hsr-v0.1.1
automas-script-hsr-v0.1.1
automas-hsr-adapter-sra-v0.1.1
automas-hsr-adapter-m7a-v0.1.1
```

tag 必须指向 `main` 历史中的提交。推送后会触发同一套验证和 environment 审批。
不要复用已发布版本号；PyPI 发行文件不可覆盖。
