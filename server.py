#!/usr/bin/env python3
"""
简单的 HTTP 服务器，用于托管 Ollama Web 面板
"""
import http.server
import socketserver
import os

PORT = 8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加 CORS 头，允许跨域请求
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Ollama Web 面板已启动！")
        print(f"📱 访问地址: http://localhost:{PORT}")
        print(f"⚠️  请确保 Ollama 服务正在运行")
        print(f"💡 按 Ctrl+C 停止服务\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 服务已停止")
