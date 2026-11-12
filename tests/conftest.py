import pytest
import requests


class FakeResponse:
    """Stands in for a requests.Response: a JSON payload plus a status code."""

    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"{self.status} Server Error")

    def json(self):
        return self.payload


class FakeApi:
    """Replaces requests.get with a table of exact URLs.

    A request for a URL that was never registered raises KeyError, so a test
    fails if the code under test asks for anything it was not expected to.
    """

    def __init__(self):
        self.routes = {}
        self.calls = []

    def add(self, url, payload, status=200):
        self.routes[url] = FakeResponse(payload, status)

    def get(self, url, **kwargs):
        self.calls.append(url)
        return self.routes[url]


@pytest.fixture
def fake_api(monkeypatch):
    api = FakeApi()
    monkeypatch.setattr("hml_rss.requests.get", api.get)
    return api
