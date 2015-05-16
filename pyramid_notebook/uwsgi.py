"""UWSGI websocket proxy."""
from urllib.parse import urlparse, urlunparse
import logging
import time

import uwsgi
from pyramid import httpexceptions
from ws4py import WS_VERSION
from ws4py.client import WebSocketBaseClient


#: HTTP headers we need to proxy to upstream websocket server when the Connect: upgrade is performed
CAPTURE_CONNECT_HEADERS = ["sec-websocket-extensions", "sec-websocket-key", "origin"]


logger = logging.getLogger(__name__)


class ProxyClient(WebSocketBaseClient):
    """Proxy between upstream WebSocket server and downstream UWSGI."""

    @property
    def handshake_headers(self):
        """
        List of headers appropriate for the upgrade
        handshake.
        """
        headers = [
            ('Host', self.host),
            ('Connection', 'Upgrade'),
            ('Upgrade', 'WebSocket'),
            ('Sec-WebSocket-Key', self.key.decode('utf-8')),
            # Origin is proxyed from the downstream server, don't set it twice
            # ('Origin', self.url),
            ('Sec-WebSocket-Version', str(max(WS_VERSION)))
            ]

        if self.protocols:
            headers.append(('Sec-WebSocket-Protocol', ','.join(self.protocols)))

        if self.extra_headers:
            headers.extend(self.extra_headers)

        logger.info("Handshake headers: %s", headers)
        return headers

    def received_message(self, m):
        """Push upstream messages to downstream."""

        # TODO: No support for binary messages
        m = str(m)
        logger.debug("Incoming upstream WS: %s", m)
        uwsgi.websocket_send(m)
        logger.debug("Send ok")

    def handshake_ok(self):
        """
        Called when the upgrade handshake has completed
        successfully.

        Starts the client's thread.
        """
        self.run()

    def terminate(self):
        super(ProxyClient, self).terminate()

    def run(self):
        """Combine async uwsgi message loop with ws4py message loop.

        TODO: This could do some serious optimizations and behave asynchronously correct instead of just sleep().
        """

        self.sock.setblocking(False)
        try:
            while not self.terminated:
                logger.debug("Doing nothing")
                time.sleep(0.050)

                logger.debug("Asking for downstream msg")
                msg = uwsgi.websocket_recv_nb()
                if msg:
                    logger.debug("Incoming downstream WS: %s", msg)
                    self.send(msg)

                s = self.stream

                self.opened()

                logger.debug("Asking for upstream msg")
                try:
                    bytes = self.sock.recv(self.reading_buffer_size)
                    if bytes:
                        self.process(bytes)
                except BlockingIOError:
                    pass

        except Exception as e:
            logger.exception(e)
        finally:
            logger.info("Terminating WS proxy loop")
            self.terminate()


def serve_websocket(request, port):
    """Start UWSGI websocket loop and proxy."""
    env = request.environ

    # Send HTTP response 101 Switch Protocol downstream
    uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))

    # Map the websocket URL to the upstream localhost:4000x Notebook instance
    parts = urlparse(request.url)
    parts = parts._replace(scheme="ws", netloc="localhost:{}".format(port))
    url = urlunparse(parts)

    # Proxy initial connection headers
    headers = [(header, value) for header, value in request.headers.items() if header.lower() in CAPTURE_CONNECT_HEADERS]

    logger.info("Connecting to upstream websockets: %s, headers: %s", url, headers)

    ws = ProxyClient(url, headers=headers)
    ws.connect()

    # TODO: Will complain loudly about already send headers - how to abort?
    return httpexceptions.HTTPOk()