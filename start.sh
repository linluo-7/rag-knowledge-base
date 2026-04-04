#!/bin/bash
# RAG 知识库系统启动脚本

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$BASE_DIR/backend"
LOG_FILE="$BASE_DIR/rag-backend.log"
PID_FILE="$BASE_DIR/rag-backend.pid"
NGINX_PID_FILE="$BASE_DIR/rag-nginx.pid"

# Docker 容器名称
CONTAINERS="milvus-etcd milvus-minio milvus-standalone neo4j-standalone"

start_docker() {
    echo "启动 Docker 容器..."
    docker start $CONTAINERS 2>/dev/null
    sleep 5
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "milvus|neo4j" || true
}

start_backend() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo "后端已在运行 (PID: $OLD_PID)"
            return
        fi
        rm -f "$PID_FILE"
    fi

    echo "启动后端服务 (5003)..."
    cd "$BACKEND_DIR"
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 5003 >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 3
    
    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✅ 后端启动成功 (PID: $(cat "$PID_FILE"))"
    else
        echo "❌ 后端启动失败，查看日志: $LOG_FILE"
    fi
}

start_nginx() {
    if /usr/sbin/nginx -t 2>&1 | grep -q "syntax is ok"; then
        echo "启动 Nginx (5004)..."
        /usr/sbin/nginx
        echo "✅ Nginx 启动成功"
    else
        echo "❌ Nginx 配置错误"
    fi
}

status() {
    echo "=== Docker 容器 ==="
    docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -E "milvus|neo4j" || echo "无"
    
    echo ""
    echo "=== 后端服务 (5003) ==="
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "运行中 (PID: $(cat "$PID_FILE"))"
        curl -s http://127.0.0.1:5003/health | python3 -m json.tool 2>/dev/null || true
    else
        echo "未运行"
    fi
    
    echo ""
    echo "=== Nginx (5004) ==="
    if pgrep -x nginx > /dev/null; then
        echo "运行中"
        curl -s http://127.0.0.1:5004/ | head -1
    else
        echo "未运行"
    fi
}

stop() {
    echo "停止所有服务..."
    
    # Nginx
    pkill nginx 2>/dev/null && echo "✅ Nginx 已停止"
    
    # 后端
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE") 2>/dev/null && echo "✅ 后端已停止"
        rm -f "$PID_FILE"
    fi
    
    # Docker
    docker stop $CONTAINERS 2>/dev/null && echo "✅ Docker 容器已停止"
}

case "$1" in
    start)
        start_docker
        start_backend
        start_nginx
        ;;
    stop) stop ;;
    restart)
        stop
        sleep 2
        start_docker
        start_backend
        start_nginx
        ;;
    status) status ;;
    *) echo "用法: $0 {start|stop|restart|status}" ;;
esac
