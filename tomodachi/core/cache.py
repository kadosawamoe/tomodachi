#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from contextlib import asynccontextmanager

import orjson
import aioredis

from tomodachi.core.models import Settings
from tomodachi.core.exceptions import CacheFail, CacheMiss

if TYPE_CHECKING:
    from tomodachi.core.bot import Tomodachi


class CacheProto(Protocol):
    bot: Tomodachi
    redis: aioredis.Redis


class CachedSettings:
    def __init__(self, parent: CacheProto) -> None:
        self._parent = parent

    @asynccontextmanager
    async def fresh(self, guild_id: int):
        try:
            yield None
        finally:
            await self.refresh(guild_id)

    async def refresh(self, guild_id: int):
        async with self._parent.bot.db.pool.acquire() as conn:
            query = """select
                g.guild_id,
                g.prefix,
                g.lang,
                ms.mute_role,
                ms.mod_roles,
                ms.audit_infractions,
                ms.dm_targets
            from guilds g
                left join mod_settings ms on g.guild_id = ms.guild_id
            where g.guild_id = $1;"""
            record = await conn.fetchrow(query, guild_id)

        if not record:
            raise CacheFail(f"{guild_id} doesn't exist in the mod_settings table.")

        await self._parent.redis.set(f"MS-{guild_id}", orjson.dumps(dict(record)))

    async def get(self, guild_id: int, *, refresh: bool = True):
        data = await self._parent.redis.get(f"MS-{guild_id}")
        if not data:
            if not refresh:
                raise CacheMiss(f"There's no cached mod_settings for {guild_id}")

            await self.refresh(guild_id)
            data = await self._parent.redis.get(f"MS-{guild_id}")

        return Settings(**orjson.loads(data))


class Cache(CacheProto):
    def __init__(self, bot: Tomodachi) -> None:
        self.bot = bot
        self.redis = aioredis.from_url(bot.config.REDIS_URI, decode_responses=True)
        self.settings = CachedSettings(self)

    async def refresh_by_guild(self, guild_id: int):
        await self.settings.refresh(guild_id)

    async def close(self):
        self.settings = None
        await self.cache.redis.flushdb(True)
        await self.redis.close()
