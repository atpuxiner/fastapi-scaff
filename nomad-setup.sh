#!/bin/bash
set -e

show_help() {
  cat <<'EOF'
用法: ./nomad-setup.sh [-y] [-h] [--version <ver>] [--ip <ip>] [--servers <ips>] [--clients <ips>] [--datacenter <name>]

  -y                    静默模式，缺失参数走默认值，不交互
  -h, --help            显示帮助信息
  --version             Nomad 版本，默认 1.11.3
  --ip                  本机 advertise IP，默认自动检测
  --servers             Server 节点 IP（逗号分隔），默认仅本机
  --clients             Client 节点 IP（逗号分隔），默认同 servers
  --datacenter          数据中心名称，默认 dc1

集群部署 — 每台节点分别执行，--servers 保持一致，--ip 为当前节点 IP：
  server: ./nomad-setup.sh -y --ip 10.0.0.1 --servers 10.0.0.1,10.0.0.2,10.0.0.3
  client: ./nomad-setup.sh -y --ip 10.0.0.4 --servers 10.0.0.1,10.0.0.2,10.0.0.3 --clients 10.0.0.4
EOF
}

SILENT=false
NOMAD_VERSION="1.11.3"
ARG_IP=""
ARG_SERVERS=""
ARG_CLIENTS=""
ARG_DATACENTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y)
      SILENT=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    --version)
      NOMAD_VERSION="$2"
      shift 2
      ;;
    --ip)
      ARG_IP="$2"
      shift 2
      ;;
    --servers)
      ARG_SERVERS="$2"
      shift 2
      ;;
    --clients)
      ARG_CLIENTS="$2"
      shift 2
      ;;
    --datacenter)
      ARG_DATACENTER="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      show_help
      exit 1
      ;;
  esac
done

# ========================================
# 1. 解析本机 IP（advertise ip）
# ========================================
if [ -n "$ARG_IP" ]; then
  LOCAL_IP="$ARG_IP"
  echo "Advertise IP (from argument): $LOCAL_IP"
else
  IPS=$(ip -4 addr show scope global \
    | awk '/inet /{print $2}' \
    | cut -d/ -f1)
  FIRST_IP=$(echo "$IPS" | head -1)

  if [ "$SILENT" = true ]; then
    LOCAL_IP="$FIRST_IP"
    echo "Advertise IP (auto-detected): $LOCAL_IP"
  else
    echo "Available IPs:"
    echo "$IPS"
    read -p "Select advertise ip ($FIRST_IP): " ADVERTISE_IP
    LOCAL_IP="${ADVERTISE_IP:-$FIRST_IP}"
  fi
fi

# ========================================
# 2. 解析其它配置（已传则用，未传按 -y/交互 处理）
# ========================================

# Datacenter
if [ -n "$ARG_DATACENTER" ]; then
  DATACENTER="$ARG_DATACENTER"
elif [ "$SILENT" = true ]; then
  DATACENTER="dc1"
else
  read -p "数据中心名称 (默认: dc1): " input
  DATACENTER="${input:-dc1}"
fi

# Server IPs
if [ -n "$ARG_SERVERS" ]; then
  IFS=', ' read -r -a SERVER_IPS <<< "$ARG_SERVERS"
elif [ "$SILENT" = true ]; then
  SERVER_IPS=("$LOCAL_IP")
else
  read -p "Server 节点 IP 列表（逗号或空格分隔，默认: $LOCAL_IP）: " input
  if [ -z "$input" ]; then
    SERVER_IPS=("$LOCAL_IP")
  else
    IFS=', ' read -r -a SERVER_IPS <<< "$input"
  fi
fi

# Client IPs
if [ -n "$ARG_CLIENTS" ]; then
  IFS=', ' read -r -a CLIENT_IPS <<< "$ARG_CLIENTS"
elif [ "$SILENT" = true ]; then
  # -y 模式默认与 servers 相同
  CLIENT_IPS=("${SERVER_IPS[@]}")
else
  DEFAULT_CLIENTS="${SERVER_IPS[*]}"
  read -p "Client 节点 IP 列表（逗号或空格分隔，默认: $DEFAULT_CLIENTS）: " input
  if [ -z "$input" ]; then
    CLIENT_IPS=("${SERVER_IPS[@]}")
  else
    IFS=', ' read -r -a CLIENT_IPS <<< "$input"
  fi
fi

SERVER_COUNT=${#SERVER_IPS[@]}
CLIENT_COUNT=${#CLIENT_IPS[@]}

# ========================================
# 3. 配置汇总 + 确认
# ========================================
echo ""
echo "----------------------------------------"
echo "  配置汇总："
echo "    Nomad 版本:  $NOMAD_VERSION"
echo "    本机 IP:     $LOCAL_IP"
echo "    数据中心:    $DATACENTER"
echo "    Server 数量: $SERVER_COUNT"
echo "    Client 数量: $CLIENT_COUNT"
echo "    Server IP:   ${SERVER_IPS[*]}"
echo "    Client IP:   ${CLIENT_IPS[*]}"
echo "----------------------------------------"

if [ "$SILENT" = false ]; then
  read -p "确认安装？(y/N): " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "取消安装"
    exit 0
  fi
fi

# ========================================
# 通用安装函数（按版本号下载官方二进制）
# ========================================
install_nomad() {
  if command -v nomad &>/dev/null; then
    local current
    current=$(nomad version | head -1 | awk '{print $2}' | sed 's/^v//')
    if [ "$current" = "$NOMAD_VERSION" ]; then
      echo ">>> Nomad v$NOMAD_VERSION 已安装，跳过"
      return 0
    fi

    echo ">>> 当前 Nomad 版本 v$current，目标版本 v$NOMAD_VERSION"
    if [ "$SILENT" = false ]; then
      read -p "    是否清理旧版本并升级？(y/N): " upgrade_confirm
      if [[ ! "$upgrade_confirm" =~ ^[Yy]$ ]]; then
        echo "    已取消升级，保留当前版本 v$current"
        return 0
      fi
    fi
    echo ">>> 开始清理旧版本..."
    sudo systemctl stop nomad 2>/dev/null || true
    sudo systemctl disable nomad 2>/dev/null || true

    # 清理 apt 安装的旧包（防止 /usr/bin/nomad 与 /usr/local/bin/nomad 共存）
    if dpkg -l 2>/dev/null | grep -q '^ii  nomad '; then
      echo "    检测到 apt 包，执行 apt purge..."
      sudo apt-get remove --purge -y nomad || true
    fi

    # 删除可能残留的旧二进制
    for bin in /usr/bin/nomad /usr/local/bin/nomad; do
      if [ -f "$bin" ]; then
        echo "    删除旧二进制: $bin"
        sudo rm -f "$bin"
      fi
    done

    # 删除旧版本附带的 systemd unit 与默认配置，避免与新 unit 冲突
    sudo rm -f /etc/default/nomad
    sudo rm -f /lib/systemd/system/nomad.service
    sudo rm -f /etc/systemd/system/nomad.service
    sudo systemctl daemon-reload
  fi

  echo ""
  echo ">>> 下载并安装 Nomad v$NOMAD_VERSION ..."
  local arch
  arch=$(uname -m)
  case "$arch" in
    x86_64)  arch="amd64" ;;
    aarch64) arch="arm64" ;;
    armv7l)  arch="arm" ;;
    *) echo "不支持的架构: $arch"; exit 1 ;;
  esac

  local tmpdir
  tmpdir=$(mktemp -d)
  local url="https://releases.hashicorp.com/nomad/${NOMAD_VERSION}/nomad_${NOMAD_VERSION}_linux_${arch}.zip"
  echo "    URL: $url"
  curl -fsSL "$url" -o "$tmpdir/nomad.zip"

  # 确保 unzip 可用
  if ! command -v unzip &>/dev/null; then
    sudo apt update && sudo apt install -y unzip
  fi

  sudo unzip -o "$tmpdir/nomad.zip" -d /usr/local/bin
  sudo chmod +x /usr/local/bin/nomad
  rm -rf "$tmpdir"

  # 创建 nomad 用户与目录
  if ! id nomad &>/dev/null; then
    sudo useradd --system --home /etc/nomad.d --shell /bin/false nomad
  fi
  sudo mkdir -p /etc/nomad.d /opt/nomad
  sudo chown -R nomad:nomad /opt/nomad

  # 写入 systemd unit（若不存在）
  if [ ! -f /etc/systemd/system/nomad.service ]; then
    sudo tee /etc/systemd/system/nomad.service > /dev/null <<'EOF'
[Unit]
Description=Nomad
Documentation=https://developer.hashicorp.com/nomad/docs
Wants=network-online.target
After=network-online.target

[Service]
ExecReload=/bin/kill -HUP $MAINPID
ExecStart=/usr/local/bin/nomad agent -config=/etc/nomad.d
KillMode=process
KillSignal=SIGINT
LimitNOFILE=65536
LimitNPROC=infinity
Restart=on-failure
RestartSec=2
TasksMax=infinity
OOMScoreAdjust=-1000

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
  fi

  echo ">>> Nomad v$NOMAD_VERSION 安装完成：$(/usr/local/bin/nomad version | head -1)"
}

# 判断 IP 是否在数组中
in_array() {
  local needle=$1
  shift
  for item in "$@"; do
    [[ "$item" == "$needle" ]] && return 0
  done
  return 1
}

setup_node() {
  local ip=$1
  local is_server=false
  local is_client=false
  in_array "$ip" "${SERVER_IPS[@]}" && is_server=true
  in_array "$ip" "${CLIENT_IPS[@]}" && is_client=true

  echo ""
  echo ">>> 配置节点 $ip (server=$is_server, client=$is_client)"

  # 节点必须是 server 或 client 其中一种
  if [ "$is_server" = false ] && [ "$is_client" = false ]; then
    echo "❌ 错误：当前节点既不是 Server 也不是 Client，退出配置"
    exit 1
  fi

  sudo mkdir -p /etc/nomad.d /opt/nomad

  # 构建配置：公共部分
  local conf="datacenter = \"$DATACENTER\"
data_dir   = \"/opt/nomad\"

bind_addr = \"0.0.0.0\"
advertise {
  http = \"$LOCAL_IP:4646\"
  rpc  = \"$LOCAL_IP:4647\"
  serf = \"$LOCAL_IP:4648\"
}
"

  # Server 块
  if [ "$is_server" = true ]; then
    conf+="
server {
  enabled          = true
  bootstrap_expect = $SERVER_COUNT
}
"
  fi

  # Client 块
  if [ "$is_client" = true ]; then
    local SERVERS=""
    for sip in "${SERVER_IPS[@]}"; do
      SERVERS+="\"$sip:4647\","
    done
    SERVERS=${SERVERS%,}

    conf+="
client {
  enabled     = true
  servers     = [$SERVERS]

  options {
    driver.raw_exec.enable = true
  }

  reserved {
    cpu    = 500
    memory = 1024
    #cores = 2
  }
}
"
  fi

  # Docker plugin：允许容器挂载宿主机目录（bind mount）
  conf+="
plugin \"docker\" {
  config {
    volumes {
      enabled = true
    }
  }
}
"

  # 备份旧配置（如果存在）
  local BACKUP=""
  if [ -f /etc/nomad.d/nomad.hcl ]; then
    BACKUP="/etc/nomad.d/nomad.hcl.bak.$(date +%Y%m%d%H%M%S)"
    sudo cp /etc/nomad.d/nomad.hcl "$BACKUP"
    echo "📦 旧配置已备份: $BACKUP"
  fi

  echo "$conf" | sudo tee /etc/nomad.d/nomad.hcl > /dev/null
  echo "📝 配置文件已写入: /etc/nomad.d/nomad.hcl"

  # 静态校验配置（修复版：无需 Nomad 运行即可校验）
  echo ">>> 正在静态校验配置文件..."
  if nomad config validate /etc/nomad.d/nomad.hcl; then
    echo "✅ 配置语法验证通过"
  else
    echo "❌ 配置验证失败，请检查配置文件后重试"
    exit 1
  fi

  sudo systemctl enable nomad
  sudo systemctl restart nomad

  # 等待服务启动，检查是否真正运行
  sleep 2
  if ! systemctl is-active --quiet nomad; then
    echo "❌ Nomad 服务启动失败！"
    echo "--- systemctl status ---"
    sudo systemctl status nomad --no-pager || true
    echo ""
    echo "--- 最近日志 ---"
    sudo journalctl -u nomad -n 30 --no-pager || true

    # 如果有旧配置备份，自动回滚
    if [ -n "$BACKUP" ]; then
      echo ""
      echo "🔄 正在回滚到旧配置..."
      sudo cp "$BACKUP" /etc/nomad.d/nomad.hcl
      sudo systemctl restart nomad
      sleep 2
      if systemctl is-active --quiet nomad; then
        echo "✅ 已回滚到旧配置，服务已恢复"
      else
        echo "❌ 回滚后服务仍未恢复，请手动检查"
      fi
    fi

    echo ""
    echo "💡 请检查上方日志中的错误信息，常见原因："
    echo "   - HCL 配置语法错误"
    echo "   - 端口 4646/4647/4648 被占用"
    echo "   - 数据目录权限不足 (/opt/nomad)"
    echo "   - Server 节点 IP 无法连通"
    return 1
  fi

  echo "✅ 节点 $ip 已启动"
}

# ========================================
# 主流程
# ========================================

# 合并去重所有节点 IP
ALL_IPS=()
for ip in "${SERVER_IPS[@]}" "${CLIENT_IPS[@]}"; do
  if ! in_array "$ip" "${ALL_IPS[@]}"; then
    ALL_IPS+=("$ip")
  fi
done

echo ""
echo "========================================"
echo "  开始安装 Nomad 集群"
echo "  Datacenter: $DATACENTER"
echo "  Servers: ${#SERVER_IPS[@]} | Clients: ${#CLIENT_IPS[@]}"
echo "  节点列表: ${ALL_IPS[*]}"
echo "========================================"

# 1. 安装 Nomad
install_nomad

# 2. 配置本机节点（脚本在每台机器上分别执行，只配置当前节点）
echo ""
echo "========================================"
echo "  配置节点"
echo "========================================"
setup_node "$LOCAL_IP"

# 4. 验证
echo ""
echo "========================================"
echo "  验证集群状态"
echo "========================================"

# 等待 Nomad API 就绪（最多 30 秒）
API_READY=false
for i in $(seq 1 10); do
  if nomad node status &>/dev/null; then
    API_READY=true
    break
  fi
  echo "  等待 Nomad 启动... ($i/10)"
  sleep 3
done

if [ "$API_READY" = true ]; then
  nomad node status
  echo ""
  echo "========================================"
  echo "  ✅ 安装完成！"
  echo "  Web UI: http://$LOCAL_IP:4646"
  echo "========================================"
else
  echo "❌ Nomad API 未就绪，请检查日志："
  echo "   sudo journalctl -u nomad -n 50 --no-pager"
  exit 1
fi
