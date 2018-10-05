"""Alternative domain tests."""
# Pyramid Notebook
from pyramid_notebook.utils import route_to_alt_domain


def test_reroute(pyramid_request):
    """We rewrite URLs to a different domain."""
    request = pyramid_request
    request.registry.settings["pyramid_notebook.alternative_domain"] = "http://ws.example.com"
    alt = route_to_alt_domain(request, "http://example.com/python-notebook/channels")
    assert alt == "http://ws.example.com/python-notebook/channels"


def test_reroute_noop(pyramid_request):
    """When URL rewriting is not active don't do anything."""
    request = pyramid_request
    alt = route_to_alt_domain(request, "http://example.com/python-notebook/channels")
    assert alt == "http://example.com/python-notebook/channels"
