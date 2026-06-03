locals {
  svc_name     = "fastapi-scaff-app"
  route_prefix = "/"  # 单服务：根路径 /
  #route_prefix = "/${local.svc_name}"  # 多服务：子路径 /xxx
  app_port     = 8000
  app_workers  = 5
}

job "fastapi-scaff" {
  region      = "global"
  datacenters = ["dc1"]
  type        = "service"

  # 滚动更新：依赖 health check 判定就绪，失败自动回滚
  update {
    stagger          = "10s"
    max_parallel     = 1
    health_check     = "checks"
    min_healthy_time = "60s"
    healthy_deadline = "5m"
    auto_revert      = true
    canary           = 1
  }

  # ---------------------------------------------------------------------------
  #  App Group — 应用副本
  #
  #  依赖独立的 Traefik Job (nomad-traefik.hcl) 充当 routing mesh，
  #  通过 Nomad Service tags 自动注册路由，无需硬编码 Traefik 地址。
  # ---------------------------------------------------------------------------
  group "app" {
    count = 3

    network {
      port "http" {
        to = local.app_port
      }
    }

    restart {
      attempts = 3
      interval = "3m"
      delay    = "5s"
      mode     = "fail"
    }

    # 预启动：自动创建 bind mount 所需的宿主机目录
    task "prepare-dirs" {
      driver = "raw_exec"

      lifecycle {
        hook    = "prestart"
        sidecar = false
      }

      config {
        command = "sh"
        args    = ["-c", "mkdir -p /data/fastapi-scaff/logs"]
      }

      resources {
        cpu    = 50
        memory = 32
      }
    }

    task "app" {
      driver = "docker"

      env {
        APP_ENV = "prod"
      }

      config {
        # 生产环境严禁使用 :latest
        image = "fastapi-scaff:v1.0.0"

        ports = ["http"]

        # 镜像未设置 ENTRYPOINT/CMD，必须用 command 指定可执行文件
        command = "uvicorn"
        args = [
          "app.main:app",
          "--host", "0.0.0.0",
          "--port", "${local.app_port}",
          "--workers", "${local.app_workers}",
          "--log-level", "info",
        ]

        mount {
          type     = "bind"
          source   = "/data/fastapi-scaff/logs"
          target   = "/app/logs"
          readonly = false
        }
      }

      resources {
        cpu        = 500
        memory     = 512
        memory_max = 2048
      }

      logs {
        max_files     = 10
        max_file_size = 15
      }

      # Traefik Nomad Provider 充当 routing mesh（等效 Swarm ingress）
      service {
        name     = local.svc_name
        provider = "nomad"
        port     = "http"

        # 生产环境启用 HTTPS 时：
        #   1. entrypoints 改为 websecure
        #   2. 新增 tls=true 与 tls.certresolver=letsencrypt
        tags = concat(
          [
            "traefik.enable=true",
            "traefik.http.routers.${local.svc_name}.rule=PathPrefix(`${local.route_prefix}`)",
            "traefik.http.routers.${local.svc_name}.entrypoints=web",
          ],

          # 如果 route_prefix = / → 不添加 StripPrefix 中间件
          # 如果 route_prefix = /xxx → 添加 StripPrefix 中间件
          local.route_prefix != "/" ? [
            "traefik.http.middlewares.stripprefix-${local.svc_name}.stripprefix.prefixes=${local.route_prefix}",
            "traefik.http.routers.${local.svc_name}.middlewares=stripprefix-${local.svc_name}",
          ] : [],

          [
            "traefik.http.services.${local.svc_name}.loadbalancer.healthcheck.path=/health",
            "traefik.http.services.${local.svc_name}.loadbalancer.healthcheck.interval=30s",
            "traefik.http.services.${local.svc_name}.loadbalancer.healthcheck.timeout=10s",
          ]
        )

        check {
          type     = "http"
          path     = "/health"
          interval = "30s"
          timeout  = "10s"
        }
      }
    }
  }
}

# =============================================================================
#  部署步骤
# =============================================================================
#
# 前置条件：确保 Traefik 已部署
#    nomad job run nomad-traefik.hcl        # 仅首次执行
#    nomad job status traefik               # 确认 running
#
# 1. 准备挂载文件（无则跳过）
#
# 2. 准备镜像（二选一）
#    A. 本地构建：docker build -t fastapi-scaff:v1.0.0 .
#    B. 推送到仓库：修改本文件中 image 为完整仓库路径
#
# 3. 部署
#    nomad job run nomad-app.hcl
#
# 4. 验证
#    nomad job status fastapi-scaff
#    nomad job allocs fastapi-scaff
#    nomad logs -f <alloc-id> app
#
# 5. 访问
#    curl http://<节点IP>:8000/health
#
# 6. 升级（修改 image 后重新执行第 3 步）
#
# 7. 清理
#    nomad job stop -purge fastapi-scaff
#
# 文档：
#   - Nomad: https://developer.hashicorp.com/nomad/docs
#   - Traefik Nomad Provider: https://doc.traefik.io/traefik/providers/nomad/
