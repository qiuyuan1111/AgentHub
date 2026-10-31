import pytest

from app.memory import (
    MemoryStore,
    InMemoryMemoryStore,
    create_memory_store,
)

from app.redis_memory import (
    RedisMemoryStore
)

def test_create_in_memory_store():

    store = create_memory_store(
        "memory"
    )

    assert isinstance(
        store,
        MemoryStore
    )

    assert isinstance(
        store,
        InMemoryMemoryStore
    )


def test_create_redis_memory_store():

    store = create_memory_store(
        "redis"
    )

    assert isinstance(
        store,
        MemoryStore
    )

    assert isinstance(
        store,
        RedisMemoryStore
    )


def test_create_memory_store_rejects_unknown_backend():

    with pytest.raises(
        ValueError,
        match="不支持的 MEMORY_BACKEND"
    ):
        create_memory_store(
            "mongodb"
        )