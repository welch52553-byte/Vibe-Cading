#!/usr/bin/env python3
"""
SCAD 几何标注工具 — 本地服务器
提供静态文件服务 + model/ 目录的读写 API
首次启动时自动从 GitHub 下载 openscad-wasm 文件（约 20MB，之后完全本地运行）
"""
import os, json, sys, mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT     = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model')
WASM_DIR  = os.path.join(BASE_DIR, 'wasm')

WASM_BASE  = 'https://github.com/openscad/openscad-wasm/releases/download/2022.03.20/'
WASM_FILES = ['openscad.js', 'openscad.wasm.js', 'openscad.wasm']

mimetypes.add_type('application/wasm',       '.wasm')
mimetypes.add_type('application/javascript', '.js')

def ensure_wasm():
    os.makedirs(WASM_DIR, exist_ok=True)
    missing = [f for f in WASM_FILES if not os.path.exists(os.path.join(WASM_DIR, f))]
    if not missing:
        return
    print('首次启动：正在下载 openscad-wasm（约 20MB，仅需一次）…')
    import urllib.request
    for fname in missing:
        dest = os.path.join(WASM_DIR, fname)
        url  = WASM_BASE + fname
        print(f'  下载 {fname} …', end='', flush=True)
        try:
            urllib.request.urlretrieve(url, dest)
            kb = os.path.getsize(dest) // 1024
            print(f' {kb} KB ✓')
        except Exception as e:
            print(f' 失败: {e}')
            if os.path.exists(dest):
                os.remove(dest)
    print('下载完成，后续完全本地运行。')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, fmt, *args):
        pass  # 静默日志

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs     = parse_qs(parsed.query)

        # GET /api/list-scad  →  返回 model/ 目录下所有 .scad 文件名
        if parsed.path == '/api/list-scad':
            files = sorted(f for f in os.listdir(MODEL_DIR) if f.lower().endswith('.scad'))
            self.send_json(files)

        # GET /api/list-stl  →  返回 model/ 目录下所有 .stl 文件名（向后兼容）
        elif parsed.path == '/api/list-stl':
            files = sorted(f for f in os.listdir(MODEL_DIR) if f.lower().endswith('.stl'))
            self.send_json(files)

        # GET /api/stl?file=example.stl  →  返回 STL 二进制（向后兼容）
        elif parsed.path == '/api/stl':
            name = os.path.basename(qs.get('file', [''])[0])
            path = os.path.join(MODEL_DIR, name)
            if not name or not os.path.isfile(path):
                self.send_json({'error': 'not found'}, 404); return
            with open(path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)

        # GET /api/stl-mtime?file=example.stl
        elif parsed.path == '/api/stl-mtime':
            name = os.path.basename(qs.get('file', [''])[0])
            path = os.path.join(MODEL_DIR, name)
            if not name or not os.path.isfile(path):
                self.send_json({'error': 'not found'}, 404); return
            self.send_json({'mtime': os.path.getmtime(path)})

        # GET /api/scad?file=example.scad  →  返回 SCAD 源码文本
        elif parsed.path == '/api/scad':
            name = os.path.basename(qs.get('file', [''])[0])
            path = os.path.join(MODEL_DIR, name)
            if not name or not os.path.isfile(path):
                self.send_json({'error': 'not found'}, 404); return
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_json({'content': content, 'mtime': os.path.getmtime(path)})

        # GET /api/scad-mtime?file=example.scad  →  仅返回修改时间
        elif parsed.path == '/api/scad-mtime':
            name = os.path.basename(qs.get('file', [''])[0])
            path = os.path.join(MODEL_DIR, name)
            if not name or not os.path.isfile(path):
                self.send_json({'error': 'not found'}, 404); return
            self.send_json({'mtime': os.path.getmtime(path)})

        # GET /api/json?file=example.json  →  返回已保存的标注 JSON
        elif parsed.path == '/api/json':
            name = os.path.basename(qs.get('file', [''])[0])
            path = os.path.join(MODEL_DIR, name)
            if not name or not os.path.isfile(path):
                self.send_json({'error': 'not found'}, 404); return
            with open(path, 'r', encoding='utf-8') as f:
                self.send_json(json.load(f))

        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        # POST /api/save-json  body: { filename, content }  →  写入 model/ 目录
        if parsed.path == '/api/save-json':
            length  = int(self.headers.get('Content-Length', 0))
            body    = json.loads(self.rfile.read(length))
            name    = os.path.basename(body.get('filename', ''))
            content = body.get('content', '')
            if not name or not name.endswith('.json'):
                self.send_json({'error': 'invalid filename'}, 400); return
            path = os.path.join(MODEL_DIR, name)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.send_json({'ok': True, 'saved': name})
        else:
            self.send_json({'error': 'not found'}, 404)

if __name__ == '__main__':
    os.chdir(BASE_DIR)
    ensure_wasm()
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'服务器运行中：http://localhost:{PORT}/viewer/index.html')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务器已停止')
