job "traefik" {
  region      = "global"
  datacenters = ["dc1"]
  type        = "service"

  # ---------------------------------------------------------------------------
  #  Traefik — 共享路由与负载均衡
  #
  #  所有项目共用此 Traefik 实例，各项目只需在自己的 HCL 中声明
  #  traefik tags 即可自动注册路由。
  #
  #  内置两个 entrypoint：
  #    web    :8000  应用入口（供上游调用）
  #    traefik :8080  Dashboard（仅供本地调试）
  # ---------------------------------------------------------------------------
  group "traefik" {
    count = 1

    network {
      port "api" {
        static = 8080
      }
      port "http" {
        static = 8000
      }
    }

    restart {
      attempts = 15
      interval = "3m"
      delay    = "5s"
      mode     = "fail"
    }

    task "traefik" {
      driver = "docker"

      config {
        image = "traefik:v3.6.17"

        # host 网络模式：直接共享宿主机网络栈，可访问 127.0.0.1:4646 (Nomad API)
        network_mode = "host"

        # 生产环境必改项：
        #   1. 删除 --api.insecure=true
        #   2. 新增 --entrypoints.websecure.address=:443 + TLS 配置（Let's Encrypt）
        #   3. 把 web 改为 80->443 重定向，app 入口改到 websecure
        #   4. Dashboard 改用 basic auth / OAuth 中间件保护
        args = [
          "--api=true",
          "--api.dashboard=true",
          "--api.insecure=true",
          "--ping=true",
          "--providers.nomad=true",
          "--providers.nomad.refreshInterval=30s",
          "--entrypoints.web.address=:8000",
          "--entrypoints.traefik.address=:8080",
          "--serversTransport.forwardingTimeouts.dialTimeout=5s",
          "--serversTransport.forwardingTimeouts.responseHeaderTimeout=60s",
          "--accesslog=true",
          "--log.level=INFO",
        ]
      }

      resources {
        cpu        = 500
        memory     = 256
        memory_max = 1024
      }

      service {
        name     = "traefik"
        provider = "nomad"
        port     = "api"

        # 生产环境建议：
        #   - rule 改为具体 Host() 限定
        #   - 新增 middlewares=traefik-auth 启用 basic auth
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.traefik-dashboard.rule=Host(`traefik.localhost`)",
          "traefik.http.routers.traefik-dashboard.entrypoints=traefik",
          "traefik.http.routers.traefik-dashboard.service=api@internal",
        ]

        check {
          type     = "http"
          path     = "/ping"
          interval = "10s"
          timeout  = "5s"
        }
      }
    }
  }
}

# =============================================================================
#  部署步骤
# =============================================================================
#
# 1. 首次部署（仅执行一次）
#    nomad job run nomad-traefik.hcl
#
# 2. 验证
#    nomad job status traefik
#    nomad logs -f <alloc-id> traefik
#
# 3. 访问
#    Dashboard: http://<节点IP>:8080/  （需通过 traefik.localhost Host 访问）
#
# 4. 升级（修改 image 后重新执行第 1 步）
#
# 5. 清理
#    nomad job stop -purge traefik
#
# 文档：https://doc.traefik.io/traefik/providers/nomad/
