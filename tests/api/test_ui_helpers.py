"""Regression tests for ui/app.py JSON-parsing helpers.

Tests import the helpers directly without a running Streamlit server.
"""

import sys
import types
import unittest.mock as mock

import pytest


def _import_helpers():
    # Stub streamlit so the module-level st.* calls don't execute during import.
    st_stub = types.ModuleType("streamlit")
    for attr in ("set_page_config", "title", "caption", "sidebar", "radio",
                 "write", "text_area", "button", "file_uploader", "header",
                 "subheader", "success", "info", "error", "warning", "expander",
                 "json"):
        setattr(st_stub, attr, mock.MagicMock())
    st_stub.sidebar = mock.MagicMock()
    # __enter__/__exit__ for the "with st.sidebar:" context manager
    st_stub.sidebar.__enter__ = mock.MagicMock(return_value=st_stub.sidebar)
    st_stub.sidebar.__exit__ = mock.MagicMock(return_value=False)

    with mock.patch.dict(sys.modules, {"streamlit": st_stub}):
        # Force a fresh import so the stub is used
        if "ui.app" in sys.modules:
            del sys.modules["ui.app"]
        import ui.app as app_mod
        return app_mod._safe_json, app_mod._error_detail


@pytest.fixture(scope="module")
def helpers():
    return _import_helpers()


def _make_resp(body: bytes, status: int = 200):
    """Build a minimal httpx.Response-like object."""
    import httpx
    return httpx.Response(status_code=status, content=body)


def test_safe_json_valid(helpers):
    safe_json, _ = helpers
    resp = _make_resp(b'{"status": "ok"}')
    assert safe_json(resp) == {"status": "ok"}


def test_safe_json_empty_body(helpers):
    safe_json, _ = helpers
    resp = _make_resp(b"")
    assert safe_json(resp) is None


def test_safe_json_html_not_json(helpers):
    safe_json, _ = helpers
    resp = _make_resp(b"<html>Internal Server Error</html>", status=500)
    assert safe_json(resp) is None


def test_safe_json_truncated_json(helpers):
    safe_json, _ = helpers
    resp = _make_resp(b'{"answer": "hello"')  # missing closing brace
    assert safe_json(resp) is None


def test_error_detail_from_json(helpers):
    _, error_detail = helpers
    resp = _make_resp(b'{"detail": "unsupported framework"}', status=400)
    assert error_detail(resp) == "unsupported framework"


def test_error_detail_falls_back_to_text_when_not_json(helpers):
    _, error_detail = helpers
    resp = _make_resp(b"<html>Bad Gateway</html>", status=502)
    assert error_detail(resp) == "<html>Bad Gateway</html>"


def test_error_detail_empty_body(helpers):
    _, error_detail = helpers
    resp = _make_resp(b"", status=500)
    assert error_detail(resp) == "HTTP 500"
