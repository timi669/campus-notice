# -*- coding: utf-8 -*-
"""
Redis 缓存工具模块
- 优先使用 Redis 缓存
- Redis 不可用时自动降级为内存缓存（带 TTL），保证开发环境不装 Redis 也能运行
"""
import time
import json
import threading
from typing import Optional, Any

from config import settings

_redis_client = None
_redis_available = False

# 内存缓存降级方案
_memory_cache: dict = {}
_memory_lock = threading.Lock()


def _get_redis_client():
    global _redis_client, _redis_available
    if not settings.REDIS_ENABLED:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _redis_client.ping()
        _redis_available = True
        print(f"[Cache] Redis 已连接: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as e:
        print(f"[Cache] Redis 不可用，降级为内存缓存: {e}")
        _redis_available = False
        _redis_client = None
    return _redis_client


def is_redis_available() -> bool:
    return _redis_available


def _serialize(value: Any) -> str:
    if isinstance(value, (dict, list, int, float, str, bool)) or value is None:
        return json.dumps(value, ensure_ascii=False, default=str)
    return json.dumps(str(value), ensure_ascii=False)


def _deserialize(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value


def get(key: str) -> Optional[Any]:
    """获取缓存"""
    client = _get_redis_client()
    if client:
        try:
            val = client.get(key)
            return _deserialize(val) if val else None
        except Exception:
            pass
    # 内存缓存
    with _memory_lock:
        item = _memory_cache.get(key)
        if item is None:
            return None
        if item["expire"] > 0 and time.time() > item["expire"]:
            del _memory_cache[key]
            return None
        return item["value"]


def set(key: str, value: Any, expire: int = 0) -> bool:
    """设置缓存，expire 为秒数，0 表示不过期"""
    client = _get_redis_client()
    if client:
        try:
            if expire > 0:
                client.setex(key, expire, _serialize(value))
            else:
                client.set(key, _serialize(value))
            return True
        except Exception:
            pass
    # 内存缓存
    with _memory_lock:
        _memory_cache[key] = {
            "value": value,
            "expire": time.time() + expire if expire > 0 else 0,
        }
    return True


def delete(key: str) -> bool:
    """删除缓存"""
    client = _get_redis_client()
    if client:
        try:
            client.delete(key)
            return True
        except Exception:
            pass
    with _memory_lock:
        _memory_cache.pop(key, None)
    return True


def delete_pattern(pattern: str) -> bool:
    """按模式删除缓存（如 notice:list:*）"""
    client = _get_redis_client()
    if client:
        try:
            for key in client.scan_iter(match=pattern):
                client.delete(key)
            return True
        except Exception:
            pass
    with _memory_lock:
        keys_to_del = [k for k in _memory_cache if k.startswith(pattern.replace("*", ""))]
        for k in keys_to_del:
            del _memory_cache[k]
    return True


def incr(key: str, amount: int = 1) -> int:
    """原子递增（用于浏览量计数）"""
    client = _get_redis_client()
    if client:
        try:
            return int(client.incrby(key, amount))
        except Exception:
            pass
    with _memory_lock:
        item = _memory_cache.get(key)
        # 检查是否已过期，过期则视为不存在（与 get 方法逻辑一致）
        now = time.time()
        if item and item["expire"] > 0 and now > item["expire"]:
            del _memory_cache[key]
            item = None
        cur = int(item["value"]) if item else 0
        new_val = cur + amount
        # 保留已有的过期时间，避免限流等场景下 TTL 被清零导致永久不过期
        expire = item["expire"] if item else 0
        _memory_cache[key] = {"value": new_val, "expire": expire}
        return new_val


def get_int(key: str) -> int:
    """获取整数缓存值"""
    val = get(key)
    try:
        return int(val) if val is not None else 0
    except (TypeError, ValueError):
        return 0
