# Courtesy of https://bitbucket.org/dahlia/wsgi-proxy/raw/02ab0dfa8e0078add268e91426e1cc1a52664cf5/wsgi_proxy/__init__.py

import http.client
import logging
from urllib.parse import urlparse, urlunsplit, urlunparse, unquote_plus


#: (:class:`frozenset`) The set of hop-by-hop headers.  All header names
#: all normalized to lowercase.
HOPPISH_HEADERS = frozenset([
    'keep-alive', 'proxy-authenticate',
    'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
    'proxy-connection'
    # "upgrade", "connection"
])


def is_hop_by_hop(header):
    """Returns :const:`True` if the given ``header`` is hop by hop.

    :param header: the header name
    :type header: :class:`basestring`
    :returns: whether the given ``header`` is hop by hop or not
    :rtype: :class:`bool`

    """
    return header.lower() in HOPPISH_HEADERS


def reconstruct_url(environ, port):
    """Reconstruct the remote url from the given WSGI ``environ`` dictionary.

    :param environ: the WSGI environment
    :type environ: :class:`collections.MutableMapping`
    :returns: the remote url to proxy
    :rtype: :class:`basestring`

    """
    # From WSGI spec, PEP 333
    url = environ.get('PATH_INFO', '')
    if not url.startswith(('http://', 'https://')):
        url = '%s://%s%s' % (
            environ['wsgi.url_scheme'],
            environ['HTTP_HOST'],
            url
        )
    # Fix ;arg=value in url
    if '%3B' in url:
        url, arg = url.split('%3B', 1)
        url = ';'.join([url, arg.replace('%3D', '=')])
    # Stick query string back in
    try:
        query_string = environ['QUERY_STRING']
    except KeyError:
        pass
    else:
        url += '?' + query_string


    parsed = urlparse(url)
    replaced = parsed._replace(netloc="localhost:{}".format(port))
    url = urlunparse(replaced)
    environ['reconstructed_url'] = url
    return url


class WSGIProxyApplication:
    """WSGI application to handle requests that need to be proxied.
    You have to instantiate the class before using it as WSGI app::

        from wsgiref.simple_server import make_server

        app = WSGIProxyApplication()
        make_server('', 8080, app).serve_forever()

    """

    #: (:class:`types.ClassType`) The connection class of :mod:`httplib` module.
    #: It should be a subtype of :class:`httplib.HTTPConnection`.
    #: Default is :class:`httplib.HTTPConnection`.
    connection_class = http.client.HTTPConnection

    def __init__(self, port):
        # Target port where we proxy IPython Notebook
        self.port = port

    def handler(self, environ, start_response):
        """Proxy for requests to the actual http server"""
        logger = logging.getLogger(__name__ + '.WSGIProxyApplication.handler')
        url = urlparse(reconstruct_url(environ, self.port))

        # Create connection object
        try:
            connection = self.connection_class(url.netloc)
            # Build path
            path = url.geturl().replace('%s://%s' % (url.scheme, url.netloc),
                                        '')
        except Exception:
            start_response('501 Gateway Error', [('Content-Type', 'text/html')])
            logger.exception('Could not Connect')
            yield '<H1>Could not connect</H1>'
            return

        # Read in request body if it exists
        body = length = None
        try:
            length = int(environ['CONTENT_LENGTH'])
        except (KeyError, ValueError):

            # This is a situation where client HTTP POST is missing content-length.
            # This is also situation where (WebOb?) may screw up encoding and isert extranous = in the body.
            # https://github.com/ipython/ipython/issues/8416
            if environ["REQUEST_METHOD"] == "POST":
                if environ.get("CONTENT_TYPE") == 'application/x-www-form-urlencoded; charset=UTF-8':
                    body = environ['wsgi.input'].read()
                    try:
                        body = unquote_plus(body.decode("utf-8"))

                        # Fix extra = at end of JSON payload
                        if body.startswith("{") and body.endswith("}="):
                            body = body[0:len(body)-1]

                    except Exception as e:
                        logger.exception(e)
                        logger.error("Could not decode body: %s", body)

                    length = len(body)
        else:
            body = environ['wsgi.input'].read(length)

        # Build headers
        logger.debug('environ = %r', environ)
        headers = dict(
            (key, value)
            for key, value in (
                # This is a hacky way of getting the header names right
                (key[5:].lower().replace('_', '-'), value)
                for key, value in environ.items()
                # Keys that start with HTTP_ are all headers
                if key.startswith('HTTP_')
            )
            if not is_hop_by_hop(key)
        )

        # Handler headers that aren't HTTP_ in environ
        try:
            headers['content-type'] = environ['CONTENT_TYPE']
        except KeyError:
            pass

        # Add our host if one isn't defined
        if 'host' not in headers:
            headers['host'] = environ['SERVER_NAME']

        # Make the remote request
        try:

            logger.debug('%s %s %r',
                         environ['REQUEST_METHOD'], path, headers)
            connection.request(environ['REQUEST_METHOD'], path,
                               body=body, headers=headers)
        except Exception as e:
            # We need extra exception handling in the case the server fails
            # in mid connection, it's an edge case but I've seen it
            logger.exception(e)
            start_response('501 Gateway Error', [('Content-Type', 'text/html')])
            yield '<H1>Could not proxy IPython Notebook running localhost:{}</H1>'.format(self.port).encode("utf-8")
            return

        response = connection.getresponse()

        hopped_headers = response.getheaders()
        headers = [(key, value)
                   for key, value in hopped_headers
                   if not is_hop_by_hop(key)]

        start_response('{0.status} {0.reason}'.format(response), headers)
        while True:
            chunk = response.read(4096)
            if chunk:
                yield chunk
            else:
                break

    def __call__(self, environ, start_response):
        return self.handler(environ, start_response)

