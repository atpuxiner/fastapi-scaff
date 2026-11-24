# 测试目录说明

## 脚本说明

| 文件 | 说明 |
| --- | --- |
| `conftest.py` | 公共夹具：会话级隔离应用、TestClient、CLI 子进程运行器、测试项目目录、数据库连接 |
| `db_config.py` | 写死的 PG / MySQL / Redis 测试连接配置及建库、环境变量辅助函数 |
| `test_app.py` | 脚手架自身接口测试：路由注册、健康检查、用户 CRUD/认证、统一响应与异常处理 |
| `test_app_core.py` | 核心工具单元测试：状态码、`Responses`、JWT、密码哈希、API Key |
| `test_app_units.py` | 应用单元测试：中间件、配置、数据库工具、模型校验、服务层、认证依赖 |
| `test_cli.py` | CLI 子进程集成测试：`new` / `add` / `tpl` 各子命令 |
| `test_cli_units.py` | CLI 单元测试：`CMD` 参数校验与模板处理函数 |
| `test_cli_combinations.py` | 代表性生成组合测试：8 组主要参数组合的生成结果校验 |
| `test_e2e_generated_project.py` | 端到端测试：生成项目 -> add API -> 真实启动服务 -> HTTP 调用户/图书接口 |
| `test_db_settings.py` | 数据库配置测试：校验 PG / MySQL 的 `tests` 库与 Redis 0/1/2 可用 |

## 执行命令

在项目根目录执行：

```powershell
# 全部测试
python -m pytest tests -q

# 代码风格检查
python -m ruff check tests

# 仅单元测试
python -m pytest tests/test_app_core.py tests/test_app_units.py tests/test_cli_units.py -q

# 仅 CLI 相关
python -m pytest tests/test_cli.py tests/test_cli_combinations.py -q

# 仅端到端测试（会启动本地服务，约 10 秒）
python -m pytest tests/test_e2e_generated_project.py -q

# 仅数据库配置测试（需要本地 PG / MySQL / Redis 服务）
python -m pytest tests/test_db_settings.py -q

# 一键执行 lint + 全部测试
.\tests\run_tests.ps1

# 快速执行，跳过端到端测试
.\tests\run_tests.ps1 -SkipE2E

# 指定测试项目生成目录（默认为 data/tests/）
python -m pytest tests -q --test-projects-dir=tmp/my-projects
.\tests\run_tests.ps1 -TestProjectsDir 'tmp/my-projects'
```

也可通过环境变量 `FASTAPI_SCAFF_TEST_PROJECTS_DIR` 指定目录；命令行参数优先。
相对路径基于项目根目录解析，生成的每个用例项目位于该目录下的 `模块名_用例名/` 子目录中。

如执行策略限制，使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\run_tests.ps1
```

## 注意事项

- CLI 测试通过子进程执行 `python -m fastapi_scaff`，工作目录默认在项目根目录的 `data/tests/` 下（`data/` 已被 `.gitignore` 忽略），便于失败后检查生成产物。
- 每个用例运行前会清空自己名下的旧目录；其他用例和手动指定的目录不会被清理。
- 数据库测试连接信息统一写在 `db_config.py`：`sql_test_databases` 夹具会幂等创建 PG / MySQL 的 `tests` 库，`redis_test_clients` 提供 Redis 0/1/2 客户端。
- PG 端口按实测使用 `5432`（输入里写的 `6379` 与 Redis 冲突）；其余连接信息按提供的值写入。
- 数据库用例依赖本地服务：PG `127.0.0.1:5432`、MySQL `127.0.0.1:3306`、Redis `127.0.0.1:6379`。
- 端到端测试会选取空闲端口启动生成的项目，并在结束时终止进程；失败信息会附带服务端日志。
- 当前全量结果：96 passed，`ruff` 检查通过。
