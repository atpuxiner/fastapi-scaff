# 测试目录说明

## 脚本说明

| 文件 | 说明 |
| --- | --- |
| `conftest.py` | 公共夹具：会话级隔离应用、TestClient、CLI 子进程运行器、测试项目目录、数据库连接 |
| `db_config.py` | 写死的 PG / MySQL / Redis 测试连接配置及建库、环境变量辅助函数 |
| `test_app.py` | 脚手架自身接口测试：路由注册、健康检查、用户 CRUD/认证、统一响应、500 / CORS 异常处理 |
| `test_app_core.py` | 核心工具单元测试：状态码、`Responses`、JWT、密码哈希、API Key |
| `test_app_units.py` | 应用单元测试：中间件、配置、数据库工具、模型校验、服务层成功/失败分支、认证依赖 |
| `test_cli.py` | CLI 子进程集成测试：`new` / `add` / `tpl` 各子命令及 `runmigration.py` 冒烟 |
| `test_cli_units.py` | CLI 单元测试：`CMD` 参数校验与模板处理函数 |
| `test_cli_combinations.py` | 代表性生成组合测试：8 组主要参数组合的生成结果校验 |
| `test_e2e_generated_project.py` | 端到端测试：SQLite / MySQL / PostgreSQL + Redis 0/1/2 下生成项目、add API、真实启动服务并 HTTP 调用户/图书接口 |
| `test_db_settings.py` | 数据库配置测试：校验 PG / MySQL 的 `tests` 库与 Redis 0/1/2 可用 |
| `test_api_registration.py` | 路由自动注册测试：跳过非激活模块、递归深度、导入失败、空路由边界 |
| `test_celery.py` | Celery 测试：任务注册表、选项合并不泄漏、未知任务、任务体、任务自动发现 |

## 执行命令

在项目根目录执行：

```powershell
# 全部测试
python -m pytest tests -q

# 代码风格检查
python -m ruff check app celery_app fastapi_scaff tests

# 仅单元测试
python -m pytest tests/test_app_core.py tests/test_app_units.py tests/test_cli_units.py -q

# 仅 CLI 相关
python -m pytest tests/test_cli.py tests/test_cli_combinations.py -q

# 仅端到端测试（会启动本地服务，约 30 秒）
python -m pytest tests/test_e2e_generated_project.py -q

# 仅数据库配置测试（需要本地 PG / MySQL / Redis 服务）
python -m pytest tests/test_db_settings.py -q

# 一键执行 lint + 全部测试（默认逐条打印用例）
.\tests\run_tests.ps1

# 同时显示测试内的 print / 日志输出
.\tests\run_tests.ps1 -ShowOutput

# 快速执行，跳过端到端测试
.\tests\run_tests.ps1 -SkipE2E

# 指定测试项目生成目录（默认为 data/tests/）
python -m pytest tests -q --test-projects-dir=tmp/my-projects
.\tests\run_tests.ps1 -TestProjectsDir 'tmp/my-projects'
```

也可通过环境变量 `TEST_PROJECTS_DIR` 指定目录；命令行参数优先。
相对路径基于项目根目录解析，每次运行生成一个 `时间串-uuid/` 子目录，各用例项目位于其中。

如执行策略限制，使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\run_tests.ps1
```

## 注意事项

- CLI 测试以子进程运行，生成物位于 `data/tests/`（已 gitignore）；每次运行一个 `时间串-uuid/` 目录，用例再分自己的子目录，可手动清理。
- 数据库用例依赖本地服务：PG `127.0.0.1:5432`、MySQL `127.0.0.1:3306`、Redis `127.0.0.1:6379`；连接信息见 `db_config.py`，会自动创建 PG / MySQL 的 `tests` 库。
- E2E 覆盖 SQLite、MySQL、PostgreSQL + Redis 0/1/2；启动前清理 SQL 表与 Redis key，结束后终止服务。
- 当前全量结果：118 passed，`ruff` 检查通过。
