import json
import threading
import unittest
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from app import Handler


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def post(self,payload):
        return urlopen(Request(self.base+'/api/recommend',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}))
    def test_page_and_catalog(self):
        with urlopen(self.base+'/') as r:self.assertIn(b'catalog',r.read())
        with urlopen(self.base+'/api/heroes') as r:self.assertEqual(len(json.load(r)),86)
        for path in ('/app.js','/style.css'):
            with urlopen(self.base+path) as r:self.assertEqual(r.status,200)
    def test_pick_and_ban(self):
        for action,method in [('pick','cosine'),('ban','ban_popularity')]:
            with self.post({'action':action,'k':5}) as r:out=json.load(r)
            self.assertEqual(out['method'],method);self.assertEqual(out['returned_count'],5)
    def test_invalid_and_private_paths(self):
        with self.assertRaises(HTTPError) as e:self.post({'action':'pick','k':0})
        self.assertEqual(e.exception.code,400)
        with self.assertRaises(HTTPError) as e:urlopen(self.base+'/liqi_draft/models/pick.json')
        self.assertEqual(e.exception.code,404)

if __name__=='__main__':unittest.main()
