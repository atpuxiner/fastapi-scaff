# fastapi-scaff

## What is this?

- by: axiner
- fastapi-scaff
- This is a fastapi scaff.
    - new project
    - add api
    - about project:
        - auto init project (conf, db, log...)
        - auto register router
        - auto register middleware
        - ...
        - integrated api-key/jwt
        - integrated sqlalchemy
        - integrated migration
        - integrated celery
        - integrated docker deployment
        - ...
    - more documents: [请点击链接](https://blog.csdn.net/atpuxiner/article/details/144291336?fromshare=blogdetail&sharetype=blogdetail&sharerId=144291336&sharerefer=PC&sharesource=atpuxiner&sharefrom=from_link)

## Project template

- Architecture: ASM
    - A api
    - S services(&schemas)
    - M models(&repositories)
- Flow: main.py(initializer) - (middleware) - api - services(&schemas) - (models&repositories)
- Layout: (The naming has been finalized after multiple revisions, making it concise and easy to understand)
  ```
  └── fastapi-scaff
      ├── app                         (应用)
      │   ├── api                     ├── (接口)
      │   │   └── v1                  │   └── (版本1)
      │   ├── initializer             ├── (初始化)
      │   │   ├── conf                │   ├── (配置)
      │   │   ├── db                  │   ├── (数据库)
      │   │   ├── log                 │   ├── (日志)
      │   │   └── ...                 │   └── (...)
      │   ├── middleware              ├── (中间件)
      │   ├── migrations              ├── (数据库迁移)
      │   ├── models                  ├── (数据模型)
      │   ├── repositories            ├── (数据仓库)
      │   ├── schemas                 ├── (数据结构)
      │   ├── services                ├── (业务逻辑)
      │   ├── utils                   ├── (工具集)
      │   └── main.py                 └── (主入口)
      ├── app_celery                  (应用-异步任务)
      ├── config                      (配置目录)
      ├── docs                        (文档目录)
      ├── logs                        (日志目录)
      ├── tests                       (测试目录)
      ├── .dockerignore
      ├── .gitignore
      ├── .python-version
      ├── build.sh
      ├── docker-compose.yaml
      ├── Dockerfile
      ├── LICENSE
      ├── README.md
      ├── requirements.txt
      └── runserver.py
  ```

- 【Other】
    - light：Please create and view (with `-t light`)
    - tiny：Please create and view (with `-t tiny`)
    - single：Please create and view (with `-t single`)

- 【Tips】Database, Redis, Snowflake and Celery can all be controlled through parameters to integrate or not, allowing you to flexibly customize the functional modules needed for your project.

## Installation

This package can be installed using pip (Python>=3.11):
> pip install fastapi-scaff

## Scaff usage

- 1）help document
    - `fastapi-scaff -h`
- 2）new project
    - `fastapi-scaff new <myproj>`
    - *light*: `fastapi-scaff new <myproj> -t light`
    - *tiny*: `fastapi-scaff new <myproj> -t tiny`
    - *single*: `fastapi-scaff new <myproj> -t single`
- 3）add api
    - `cd to project root dir`
    - `fastapi-scaff add <myapi>`
- 4）integrated celery
    - M1。`new` with `--celery`: `fastapi-scaff new <myproj> --celery`
    - M2。`add` with `--celery`: `fastapi-scaff add <mycelery> --celery`

## Project run

- 1）cd to project root dir
- 2）modify the configuration, such as for the database
- 3）`pip install -r requirements.txt`
- 4）`python runserver.py`
    - more parameters see:
        - about uvicorn: [click here](https://www.uvicorn.org/)
        - about gunicorn: [click here](https://docs.gunicorn.org/en/stable/)
- x）migration
    - eg (Can be executed before runserver):
        - generate: `python runmigration.py generate init`
        - upgrade: `python runmigration.py upgrade`
    - about alembic: [click here](https://alembic.sqlalchemy.org/en/latest/)
- x）docker, please see:
    - project files:
        - build.sh
        - docker-compose.yaml | docker-compose.swarm.yaml[config/nginx.conf]
        - Dockerfile | Dockerfile.slim
    - about docker: [click here](https://docs.docker.com/)

## License

This project is released under the MIT License (MIT). See [LICENSE](LICENSE)

-----

## ☕ 请我喝咖啡

享受开源，也感谢支持。

如果本项目对您有用，可以考虑 Buy Me a Coffee :)

![](BuyMeaCoffee.jpg)
