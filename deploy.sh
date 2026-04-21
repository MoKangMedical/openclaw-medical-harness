#!/bin/bash
# OpenClaw-Medical-Harness 一键部署脚本
PORT=${1:-8094}
echo "🔧 OpenClaw-Medical-Harness 部署中..."
echo "   端口: $PORT"

cd "$(dirname "$0")"
pip3 install -e ".[server]" 2>/dev/null || pip3 install fastapi uvicorn

echo "   启动 Demo Server..."
python3 -m uvicorn demo_server:app --host 0.0.0.0 --port $PORT &
sleep 2

echo "✅ Harness 已启动: http://localhost:$PORT"
echo "   API文档: http://localhost:$PORT/docs"
echo "   诊断端点: POST http://localhost:$PORT/diagnose"
echo "   药物发现: POST http://localhost:$PORT/drug-discovery"
