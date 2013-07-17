import socket
import cStringIO
from http_parser.parser import HttpParser
from urlparse import urlparse
from werkzeug import Request, Response

BUFSIZE = 2 ** 14

class HttpQuery(object):
    def __init__(self, location):
        # dns resolution done by getaddrinfo
        resolutions = socket.getaddrinfo(location, 80, 0, 0, socket.SOL_TCP)
        (family, socktype, _, _, sockaddr) = resolutions[0]
        self.queryurl = location + "/search?q="
        self.addr = sockaddr
        self.s = socket.socket(family, socktype)
        self.s.connect(self.addr)

    def query(self, qstring):
        url = self.queryurl + qstring
        req = self.request(url)
        self.s.send('%s %s HTTP/1.1\r\n%s' % (req.method, url, str(req.headers)))
        resp = self.receive()
        if resp.status_code != 200:
            return None
        return resp.data

    def request(self, url):
        headers = {}
        url_info = urlparse(url)
        fake_wsgi = {
                'REQUEST_METHOD' : "GET",
                'SCRIPT_NAME' : '',
                'PATH_INFO' : url_info[2],
                'QUERY_STRING' : url_info[4],
                'wsgi.version' : (1,0),
                'wsgi.url_scheme' : 'http',
                'wsgi.input' : cStringIO.StringIO(''),
                'wsgi.multithread' : False,
                'wsgi.multiprocess' : False,
                'wsgi.run_once' : False,
                }
        return Request(fake_wsgi)

    def receive(self):
        h = HttpParser()
        body = []
        data = None
        while True:
            if data:
                used = h.execute(data, len(data))
                if h.is_headers_complete():
                    body.append(h.recv_body())
                if h.is_message_complete():
                    data = data[used:]
                    break
            data = self.s.recv(BUFSIZE)

        return Response(response=''.join(body),
                        status=h.get_status_code(),
                        headers=h.get_headers(),
                        )

    def __exit__(self):
        self.s.close()
