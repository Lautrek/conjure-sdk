"""Client module."""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import httpx

from .exceptions import (
    AuthenticationError,
    ConjureAPIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


@dataclass
class OperationResult:
    """Op result."""

    success: bool
    object_id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ConjureClient:
    """API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("CONJURE_API_KEY")
        if not self.api_key:
            raise AuthenticationError("API key required")

        # URL must be provided or set via env
        self.base_url = (base_url or os.environ.get("CONJURE_API_URL", "")).rstrip("/")
        if not self.base_url:
            raise ValueError("base_url required. Set CONJURE_API_URL env var or pass base_url.")

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )
        self._ops = None  # Lazy-loaded op mapping

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._client.close()

    def _load_ops(self):
        """Load op mapping from server."""
        if self._ops is None:
            resp = self._client.get("/ops")
            if resp.status_code == 200:
                data = resp.json()
                self._ops = {op["id"]: op for op in data.get("operations", [])}
            else:
                self._ops = {}

    def _op(self, cmd: str, p: Dict) -> Dict[str, Any]:
        """Execute op via obfuscated endpoint."""
        try:
            resp = self._client.post("/op", json={"op": cmd, "p": p})
        except httpx.RequestError as e:
            raise ConjureAPIError(f"Request failed: {e}")
        return self._handle_response(resp)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        try:
            response = self._client.request(method, endpoint, params=params, json=json)
        except httpx.RequestError as e:
            raise ConjureAPIError(f"Request failed: {e}")
        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError(
                "Invalid API key",
                status_code=401,
                response=response.json() if response.content else None,
            )
        if response.status_code == 403:
            raise AuthenticationError(
                "Access denied",
                status_code=403,
                response=response.json() if response.content else None,
            )
        if response.status_code == 404:
            raise NotFoundError(
                "Resource not found",
                status_code=404,
                response=response.json() if response.content else None,
            )
        if response.status_code == 422:
            data = response.json() if response.content else {}
            raise ValidationError(
                data.get("detail", "Validation error"),
                status_code=422,
                response=data,
            )
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                status_code=429,
                retry_after=int(retry_after) if retry_after else None,
            )
        if response.status_code >= 400:
            data = response.json() if response.content else {}
            raise ConjureAPIError(
                data.get("detail", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response=data,
            )

        return response.json() if response.content else {}

    # Operations

    def create_box(
        self,
        width: float,
        height: float,
        depth: float,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
    ) -> OperationResult:
        d = self._op(
            "create_box", {"width": width, "height": height, "depth": depth, "name": name, "position": position}
        )
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def create_cylinder(
        self, radius: float, height: float, name: Optional[str] = None, position: Optional[List[float]] = None
    ) -> OperationResult:
        d = self._op("create_cylinder", {"radius": radius, "height": height, "name": name, "position": position})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def create_sphere(
        self, radius: float, name: Optional[str] = None, position: Optional[List[float]] = None
    ) -> OperationResult:
        d = self._op("create_sphere", {"radius": radius, "name": name, "position": position})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def union(self, objects: List[str], name: Optional[str] = None) -> OperationResult:
        d = self._op("boolean_fuse", {"objects": objects, "name": name})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def cut(self, target: str, tool: str, name: Optional[str] = None) -> OperationResult:
        d = self._op("boolean_cut", {"target": target, "tool": tool, "name": name})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def intersect(self, objects: List[str], name: Optional[str] = None) -> OperationResult:
        d = self._op("boolean_intersect", {"objects": objects, "name": name})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def translate(self, object_id: str, x: float = 0, y: float = 0, z: float = 0) -> OperationResult:
        d = self._op("move_object", {"name": object_id, "x": x, "y": y, "z": z})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def rotate(self, object_id: str, axis: str = "z", angle: float = 0) -> OperationResult:
        d = self._op("rotate_object", {"name": object_id, "axis": axis, "angle": angle})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def scale(self, object_id: str, factor: Union[float, List[float]] = 1.0) -> OperationResult:
        d = self._op("scale_object", {"name": object_id, "factor": factor})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def fillet(self, object_id: str, radius: float, edges: Optional[List[str]] = None) -> OperationResult:
        d = self._op("create_fillet", {"object_name": object_id, "radius": radius, "edges": edges or []})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def chamfer(self, object_id: str, size: float, edges: Optional[List[str]] = None) -> OperationResult:
        d = self._op("create_chamfer", {"object_name": object_id, "size": size, "edges": edges or []})
        return OperationResult(success=d.get("s", False), data=d.get("r"))

    def list_objects(self) -> List[Dict[str, Any]]:
        d = self._op("find_objects", {"pattern": "*"})
        return d.get("r", {}).get("o", []) if d.get("s") else []

    def measure(self, from_obj: str, to_obj: str) -> Dict[str, Any]:
        d = self._op("measure_distance", {"from": from_obj, "to": to_obj})
        return d.get("r", {})

    def bounding_box(self, object_id: str) -> Dict[str, Any]:
        d = self._op("get_bounding_box", {"name": object_id})
        return d.get("r", {})

    def export(self, format: str = "stl", filename: Optional[str] = None, objects: Optional[List[str]] = None) -> bytes:
        op = "export_stl" if format == "stl" else "export_step"
        d = self._op(op, {"filepath": filename, "objects": objects or []})
        return d.get("r", {})


class AsyncConjureClient:
    """Async API client."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key or os.environ.get("CONJURE_API_KEY")
        if not self.api_key:
            raise AuthenticationError("API key required")
        self.base_url = (base_url or os.environ.get("CONJURE_API_URL", "")).rstrip("/")
        if not self.base_url:
            raise ValueError("base_url required")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        await self._client.aclose()

    async def _op(self, cmd: str, p: Dict) -> Dict[str, Any]:
        try:
            resp = await self._client.post("/op", json={"op": cmd, "p": p})
        except httpx.RequestError as e:
            raise ConjureAPIError(f"Request failed: {e}")
        if resp.status_code >= 400:
            raise ConjureAPIError(f"Error: {resp.status_code}")
        return resp.json() if resp.content else {}

    async def create_box(
        self,
        width: float,
        height: float,
        depth: float,
        name: Optional[str] = None,
        position: Optional[List[float]] = None,
    ) -> OperationResult:
        d = await self._op(
            "create_box", {"width": width, "height": height, "depth": depth, "name": name, "position": position}
        )
        return OperationResult(success=d.get("s", False), data=d.get("r"))
