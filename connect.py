import socket
import cStringIO
from Queue import Queue
from http_parser.parser import HttpParser
from urlparse import urlparse
from werkzeug import Request, Response

BUFSIZE = 2 ** 14

#
# Let's first try to connect to the socket
# multiple times, using a pool of connections
#

class HttpQueryPool(object):
    def __init__(self, pool_max=5):
        self.pool_size = 0
        self.pool_max = pool_max
        self.pool = dict()
        self.queue = Queue()

    def new(self, location):
        obj = HttpQuery()
        obj.connect(location)
        self.pool[location] = obj
        self.queue.put(obj)
        return obj

    def get(self, location):
        try:
            connection = self.pool[location]
            return connection
        except:
            if self.pool_size < self.pool_max:
                obj = self.new(location)
                self.pool_size += 1
                return obj
            else:
                old = self.queue.get()
                del self.pool[old.location]
                old.destroy()
                obj = self.new(location)
                self.pool_size += 1
                return obj

class HttpQuery(object):
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self, location):
        # dns resolution done by getaddrinfo
        resolutions = socket.getaddrinfo(location, 80, 0, 0, socket.SOL_TCP)
        (_, _, _, _, sockaddr) = resolutions[0]
        self.location = location
        self.s.connect(sockaddr)

    def query(self, url):
        req = self.request(url)
        self.s.send('%s %s HTTP/1.1\r\n%s' % (req.method, url, str(req.headers)))
        resp = self.receive()
        print "status code ", resp.status_code
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

    def destroy(self):
        self.__exit__()

    def __exit__(self):
        self.s.close()
