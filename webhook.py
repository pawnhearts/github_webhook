#!/usr/bin/env python3
import os
import hmac
import hashlib
import json
import logging
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

SECRET = 'foo'
HOST_NAME = '127.0.0.1'
PORT_NUMBER = 8585
PATH = '/hook/'


class EventHandlers:
    """
        Handle github events. Shouldn't block or you would get a timeout
        :argument data - decoded json with payload
    """
    def push(self, data):
        os.system('(cd ~/map && git pull && supervisorctl restart map) & disown')
        return 'Started deploy'
    def ping(self, data):
        print('pong')
        return 'Pong'


class Server(BaseHTTPRequestHandler):
    def get_digest(self, data):
        return hmac.new(bytes(SECRET, 'UTF-8'), data, hashlib.sha1).hexdigest()

    def do_GET(self):
        return self.respond(404, 'Not found')

    def do_POST(self):
        if self.path != PATH:
            return self.respond(404, 'Not found')
        length = int(self.headers.get('content-length', 0))
        data = self.rfile.read(length)
        if SECRET and self.headers.get('X-Hub-Signature', '=').split('=', 1)[-1] != self.get_digest(data):
            self.log_message('Bad signature')
            return self.respond(403, 'Nice try')
        try:
            params = json.loads(data.decode('utf-8'))
        except Exception as e:
            return self.respond(400, 'Bad json')
        guid = self.headers.get('X-GitHub-Delivery', '')
        event = self.headers.get('X-GitHub-Event', 'unknown')
        self.log_message('Got %s event from github %s' % (event, guid))
        handlers = EventHandlers()
        cmd = getattr(handlers, event)
        if cmd:
            message = cmd(params)
            return self.respond(200, message)
        else:
            return self.respond(400, 'Unknown event %s' % event)

    def respond(self, code, message):
        self.send_response(code, bytes(message, 'UTF-8'))
        self.send_header('Content-type', 'text/plain')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(bytes(message, 'UTF-8'))
        self.wfile.flush()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('Started webhook server at %s:%s' % (HOST_NAME, PORT_NUMBER))
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), Server)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    logging.info('Stopping webhook server at %s:%s' % (HOST_NAME, PORT_NUMBER))
    httpd.server_close()
