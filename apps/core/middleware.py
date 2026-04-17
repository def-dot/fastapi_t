"""中间件"""

import json
import time

from fastapi import Request, Response

from apps.core.logging import get_logger

logger = get_logger(__name__)

# 敏感参数名，记录日志时脱敏
_SENSITIVE_KEYS = {"password", "token", "secret", "authorization"}


def _mask_sensitive(params: dict) -> dict:
    """对敏感参数脱敏"""
    return {k: "***" if k.lower() in _SENSITIVE_KEYS else v for k, v in params.items()}


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP（支持反向代理）"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


async def _build_params(request: Request) -> dict:
    """合并所有请求参数：query + path + body，并对敏感信息脱敏"""
    params: dict = {}

    if request.query_params:
        params.update(dict(request.query_params))

    if hasattr(request, "path_params") and request.path_params:
        params.update(dict(request.path_params))

    content_type = request.headers.get("content-type", "")
    if request.method in ("POST", "PUT", "PATCH"):
        raw = await request.body()
        # 缓存 body 供路由再次读取
        if raw:

            async def _receive():
                return {"type": "http.request", "body": raw}

            request._receive = _receive

            try:
                if "application/json" in content_type:
                    body = json.loads(raw)
                    if isinstance(body, dict):
                        params.update(body)
                elif "application/x-www-form-urlencoded" in content_type:
                    from urllib.parse import parse_qs

                    form = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(raw.decode()).items()}
                    params.update(form)
            except Exception:
                pass

    return _mask_sensitive(params)


async def access_log_middleware(request: Request, call_next) -> Response:
    """访问日志中间件：记录来源 IP、URL path、请求参数、状态、耗时、错误信息"""
    start = time.time()
    client_ip = _get_client_ip(request)
    path = request.url.path
    params = await _build_params(request)
    params_str = json.dumps(params, ensure_ascii=False) if params else "-"

    response = await call_next(request)

    elapsed = time.time() - start
    response.headers["X-Process-Time"] = f"{elapsed:.3f}"

    # 从异常处理器获取错误信息
    error_msg = getattr(request.state, "error_msg", None)
    log_payload = {
        "ip": client_ip,
        "method": request.method,
        "path": path,
        "params": params_str,
        "status": response.status_code,
        "latency": f"{elapsed:.3f}s",
    }
    if error_msg:
        log_payload["error"] = error_msg
        log_func = logger.error
    else:
        log_func = logger.info
    log_func(f"{client_ip} {request.method} {path} -> {response.status_code} ({elapsed:.3f}s), payload: {log_payload}")
    return response
