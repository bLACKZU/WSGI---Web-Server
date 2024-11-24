import socket
import sys
import io
from datetime import date

class WSGIServer():
    
    address_family = socket.AF_INET     #ipv4
    socket_type = socket.SOCK_STREAM    #TCP

    def __init__(self, server_address):

        #Create listening socket object to initiate connection 
        self.lsock = lsock = socket.socket(self.address_family, self.socket_type)

        #Bind socket with host & port
        lsock.bind(server_address)
        
        #Sets up a queue for accepting connections, default value is set
        lsock.listen()

        #Get the actual host and port bound on the server
        host, port = lsock.getsockname()[:2]

        self.server_name = socket.getfqdn(host)
        self.server_port = port

        self.headers_set = []

    def set_app(self, application):
        self.application = application

    def serve_requests(self):
        
        lsock = self.lsock
        while True:
            self.client_connection, self.client_address = lsock.accept()
            self.handle_one_request()

    def handle_one_request(self):

        request_data = self.client_connection.recv(1024)
        self.request_data =  request_data = request_data.decode('utf-8')

        print(''.join(f'< {line}\n' for line in request_data.splitlines()))

        self.parse_request(request_data)

        #Construct env data using request data from client
        env = self.get_environ() 

        #Call the framework/application callable & get back result or response that becomes HTTP response body
        result = self.application(env, self.start_response)

        self.finish_response(result)

    def parse_request(self, text):

        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')

        (self.request_method,   #GET
         self.path,             #/hello
         self.request_version   #HTTP version
        ) = request_line.split()

    def get_environ(self):
        
        env = {}
        # Required WSGI variables
        env['wsgi.version']      = (1, 0)
        env['wsgi.url_scheme']   = 'http'
        env['wsgi.input']        = io.StringIO(self.request_data)
        env['wsgi.errors']       = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once']     = False
        # Required CGI variables
        env['REQUEST_METHOD']    = self.request_method    # GET
        env['PATH_INFO']         = self.path              # /hello
        env['SERVER_NAME']       = self.server_name       # localhost
        env['SERVER_PORT']       = str(self.server_port)  # 8888
        return env

    def start_response(self, status, response_headers, exc_info=None):

        server_headers = [('Date', 'Sun, 24 Nov 2024 4:42 IST'), ('Server', 'WSGIServer 0.2')]

        self.headers_set = [status, server_headers + response_headers]

    def finish_response(self, result):

        try:
            status, response_headers = self.headers_set
            response = f'HTTP/2.1 {status}\r\n'
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')
            print(''.join(
                f'> {line}\n' for line in response.splitlines()
            ))
            response_bytes = response.encode()
            self.client_connection.sendall(response_bytes)
        
        finally:
            self.client_connection.close()

SERVER_ADDRESS = (HOST, PORT) = '', 8888


def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print(f'WSGIServer: Serving HTTP on port {PORT} ...\n')
    httpd.serve_requests()







