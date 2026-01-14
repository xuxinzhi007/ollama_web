#!/usr/bin/env python3
"""
Ollama Web 服务器 - Flask 版本
"""
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

PORT = 8080
app = Flask(__name__, static_folder='.')
CORS(app)


# ==================== 静态文件路由 ====================

@app.route('/')
def index():
    """主页"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """静态文件服务"""
    return send_from_directory('.', path)


# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'server': 'Ollama Web (Flask)'
    })


# ==================== 主函数 ====================

if __name__ == '__main__':
    print("🚀 Ollama Web 服务器已启动（Flask 版本）！")
    print(f"📱 Web 界面: http://localhost:{PORT}")
    print(f"⚠️  请确保 Ollama 服务正在运行 (ollama serve)")
    print(f"🛑 按 Ctrl+C 停止服务\n")

    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
