"""Local-only Liqi demo. Start: python app.py"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from liqi_draft import DraftRecommender

ROOT=Path(__file__).resolve().parent
SERVICE=DraftRecommender()

class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,kind='application/json; charset=utf-8'):
        if isinstance(body,(dict,list)): body=json.dumps(body,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers();self.wfile.write(body)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/heroes':return self.send(200,SERVICE.heroes())
        files={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
        if path not in files:return self.send(404,{'error':'Không tìm thấy trang.'})
        name,kind=files[path];self.send(200,(ROOT/'static'/name).read_bytes(),kind)

    def do_POST(self):
        if urlsplit(self.path).path!='/api/recommend':return self.send(404,{'error':'Không tìm thấy API.'})
        origin=self.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
            return self.send(403,{'error':'Nguồn yêu cầu không hợp lệ.'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=16384:return self.send(413,{'error':'Yêu cầu quá lớn hoặc rỗng.'})
            request=json.loads(self.rfile.read(length))
            self.send(200,SERVICE.recommend(request))
        except (ValueError,TypeError) as exc:
            self.send(400,{'error':str(exc)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);args=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Liqi dang chay: http://127.0.0.1:{args.port} | Ctrl+C de dung',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
