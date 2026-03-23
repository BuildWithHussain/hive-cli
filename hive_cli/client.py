"""HTTP client for Frappe REST API v2."""

import json
import sys

import requests


class HiveClient:
    """Thin wrapper around Frappe REST API v2."""

    def __init__(self, url: str, api_key: str, api_secret: str):
        self.base_url = url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {api_key}:{api_secret}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/v2/document/{path}"

    def _method_url(self, dotted_path: str) -> str:
        return f"{self.base_url}/api/method/{dotted_path}"

    def _handle(self, resp: requests.Response) -> dict:
        if resp.status_code >= 400:
            try:
                body = resp.json()
                # v2 uses "errors", v1 uses "exc_type"/"_server_messages"
                msg = body.get("errors") or body.get("exc_type") or body.get("_server_messages") or resp.text
                if isinstance(msg, list):
                    msg = msg[0]
                if isinstance(msg, str):
                    try:
                        parsed = json.loads(msg)
                        if isinstance(parsed, list) and parsed:
                            parsed = json.loads(parsed[0])
                        if isinstance(parsed, dict):
                            msg = parsed.get("message", msg)
                    except (json.JSONDecodeError, TypeError):
                        pass
            except Exception:
                msg = resp.text
            print(f"Error ({resp.status_code}): {msg}", file=sys.stderr)
            raise SystemExit(1)
        data = resp.json()
        # v2 returns {"data": ...}, v1 returns {"message": ...} or {"data": ...}
        return data.get("data", data.get("message", data))

    # --- Document CRUD ---

    def get_doc(self, doctype: str, name: str, fields: list[str] | None = None) -> dict:
        params = {}
        if fields:
            params["fields"] = json.dumps(fields)
        resp = self.session.get(self._url(f"{doctype}/{name}"), params=params)
        return self._handle(resp)

    def get_list(
        self,
        doctype: str,
        fields: list[str] | None = None,
        filters: dict | list | None = None,
        order_by: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        params: dict = {"limit_page_length": limit}
        if fields:
            params["fields"] = json.dumps(fields)
        if filters:
            params["filters"] = json.dumps(filters)
        if order_by:
            params["order_by"] = order_by
        resp = self.session.get(self._url(doctype), params=params)
        return self._handle(resp)

    def create_doc(self, doctype: str, data: dict) -> dict:
        resp = self.session.post(self._url(doctype), json=data)
        return self._handle(resp)

    def update_doc(self, doctype: str, name: str, data: dict) -> dict:
        resp = self.session.put(self._url(f"{doctype}/{name}"), json=data)
        return self._handle(resp)

    # --- Whitelisted methods ---

    def call_method(self, method: str, data: dict | None = None) -> dict:
        resp = self.session.post(self._method_url(method), json=data or {})
        return self._handle(resp)
