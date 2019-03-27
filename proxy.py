"""A proxy server that forwards requests from one port to another server.

To run this using Python 2.7:

% python proxy.py

It listens on a port (`LISTENING_PORT`, below) and forwards commands to the
server. The server is at `SERVER_ADDRESS`:`SERVER_PORT` below.
"""

# This code uses Python 2.7. These imports make the 2.7 code feel a lot closer
# to Python 3. (They're also good changes to the language!)
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import library

# Where to find the server. This assumes it's running on the smae machine
# as the proxy, but on a different port.
SERVER_ADDRESS = 'localhost'
SERVER_PORT = 8000

# The port that the proxy server is going to occupy. This could be the same
# as SERVER_PORT, but then you couldn't run the proxy and the server on the
# same machine.
LISTENING_PORT = 8004

# Cache values retrieved from the server for this long.
MAX_CACHE_AGE_SEC = 60.0  # 1 minute

MAX_BUFFER_SIZE = 512;


def ForwardCommandToServer(command, server_addr, server_port):
  """Opens a TCP socket to the server, sends a command, and returns response.

  Args:
    command: A single line string command with no newlines in it.
    server_addr: A string with the name of the server to forward requests to.
    server_port: An int from 0 to 2^16 with the port the server is listening on.
  Returns:
    A single line string response with no newlines.
  """

  client_sock = library.CreateClientSocket(server_addr, server_port)
  client_sock.send('%s\n' % command)
  response = client_sock.recv(MAX_BUFFER_SIZE)
  client_sock.close()
  return response
  

def ProxyClientCommand(sock, server_addr, server_port, cache):
  """Receives a command from a client and forwards it to a server:port.

  A single command is read from `sock`. That command is passed to the specified
  `server`:`port`. The response from the server is then passed back through
  `sock`.

  Args:
    sock: A TCP socket that connects to the client.
    server_addr: A string with the name of the server to forward requests to.
    server_port: An int from 0 to 2^16 with the port the server is listening on.
    cache: A KeyValueStore object that maintains a temorary cache.
    max_age_in_sec: float. Cached values older than this are re-retrieved from
      the server.
  """

  # Read the command line and parse it. 
  command_line = library.ReadCommand(sock)
  command, name, value = library.ParseCommand(command_line)

  # Determine the type of command.
  if command == 'PUT':
    response = ForwardCommandToServer(command_line, SERVER_ADDRESS, SERVER_PORT)
    cache.StoreValue(name, response)
  elif (command == 'GET'):
    response = cache.GetValue(name, MAX_CACHE_AGE_SEC)
    if response == None: 
      response = ForwardCommandToServer(command_line, SERVER_ADDRESS, SERVER_PORT)
      cache.StoreValue(name, response)
  else:
    response = ForwardCommandToServer(command_line, SERVER_ADDRESS, SERVER_PORT)

  sock.send(response)
  


def main():
  # Listen on a specified port...
  server_sock = library.CreateServerSocket(LISTENING_PORT)
  cache = library.KeyValueStore()
  # Accept incoming commands indefinitely.
  while True:
    # Wait until a client connects and then get a socket that connects to the
    # client.
    client_sock, (address, port) = library.ConnectClientToServer(server_sock)
    print('Received connection from %s:%d' % (address, port))
    ProxyClientCommand(client_sock, SERVER_ADDRESS, SERVER_PORT,
                       cache)

    # Close the cliend socket after use. 
    client_sock.close()
  
  # Close the server socket at the end.
  server_sock.close()


main()
