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
        - integrated sqlalchemy
        - integrated jwt\api-key
        - integrated celery
        - ...
    - about structure:
        - standard
        - light
        - micro
    - more documents: [请点击链接](https://blog.csdn.net/atpuxiner/article/details/144291336?fromshare=blogdetail&sharetype=blogdetail&sharerId=144291336&sharerefer=PC&sharesource=atpuxiner&sharefrom=from_link)

## Project structure

- ASM: ASM mode
    - A api
    - S services(&schemas)
    - M models
- Calling process: main.py(initializer) -> (middleware) - api - services(&schemas) - (models)
- Structure: (The naming has been finalized after multiple revisions, making it concise and easy to understand)
  ```
  └── fastapi-scaff
      ├── app                         (应用)
      │   ├── api                     ├── (api)
      │   │   └── v1                  │   └── (v1)
      │   ├── initializer             ├── (初始化)
      │   │   ├── conf                │   ├── (配置)
      │   │   ├── db                  │   ├── (数据库)
      │   │   ├── log                 │   ├── (日志)
      │   │   └── ...                 │   └── (...)
      │   ├── middleware              ├── (中间件)
      │   ├── models                  ├── (数据模型)
      │   ├── schemas                 ├── (数据结构)
      │   ├── services                ├── (业务逻辑)
      │   ├── utils                   ├── (utils)
      │   └── main.py                 └── (main.py)
      ├── app_celery                  (应用-celery)
      ├── config                      (配置目录)
      ├── deploy                      (部署目录)
      ├── docs                        (文档目录)
      ├── logs                        (日志目录)
      ├── tests                       (测试目录)
      ├── .gitignore
      ├── LICENSE
      ├── README.md
      ├── requirements.txt
      └── runcbeat.py
      └── runcworker.py
      └── runserver.py
  ```

- 【Other structure】
    - light：Please create and view (with `-e light`)
    - micro：Please create and view (with `-e micro`)

## Installation

This package can be installed using pip (Python>=3.11):
> pip install fastapi-scaff

## Scaff usage

- 1）help document
    - `fastapi-scaff -h`
- 2）new project
    - `fastapi-scaff new <myproj>`
    - *light structure*: `fastapi-scaff new <myproj> -e light`
    - *micro structure*: `fastapi-scaff new <myproj> -e micro`
- 3）add api
    - `cd to project root dir`
    - `fastapi-scaff add <myapi>`
- 4）integrated celery (default not integrated)
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

## License

This project is released under the MIT License (MIT). See [LICENSE](LICENSE)
