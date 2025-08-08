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
    - more documents: [请点击链接](https://blog.csdn.net/atpuxiner/article/details/144291336?fromshare=blogdetail&sharetype=blogdetail&sharerId=144291336&sharerefer=PC&sharesource=atpuxiner&sharefrom=from_link)

## Project structure

- ABD: ABD模式
    - A api
    - B business
    - D datatype
- 调用过程: main.py(initializer) -> (middleware) - router - api - business - (datatype)
- 结构如下: (命名经过多次修改敲定，简洁易懂，ABD目录贴合避免杂乱无章)
  ```
  └── fastapi-scaff
      ├── app                         (应用)
      │   ├── api                     ├── (api)
      │   │   └── v1                  │   └── (v1)
      │   ├── business                ├── (业务)
      │   ├── datatype                ├── (数据类型)
      │   ├── initializer             ├── (初始化)
      │   │   ├── conf                │   ├── (配置)
      │   │   ├── db                  │   ├── (数据库)
      │   │   ├── log                 │   ├── (日志)
      │   │   └── ...                 │   └── (...)
      │   ├── middleware              ├── (中间件)
      │   ├── router                  ├── (路由)
      │   ├── utils                   ├── (utils)
      │   └── main.py                 └── (main.py)
      ├── config                      (配置目录)
      ├── deploy                      (部署目录)
      ├── docs                        (文档目录)
      ├── log                         (日志目录)
      ├── .gitignore
      ├── LICENSE
      ├── README.md
      ├── requirements.txt
      └── runserver.py
  ```

## Installation

This package can be installed using pip (Python>=3.11):
> pip install fastapi-scaff

## Scaff usage

- 1）help document
    - `fastapi-scaff -h`
- 2）new project
    - `fastapi-scaff new <myproj>`
- 3）add api
    - `cd to project root dir`
    - `fastapi-scaff add <myapi>`

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
