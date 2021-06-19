#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import discord
from discord.ext import commands

from tomodachi.core import CogMixin


class Events(CogMixin):
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        query = "INSERT INTO guilds (guild_id, prefix) VALUES ($1, $2) ON CONFLICT DO NOTHING;"
        await self.bot.db.pool.execute(query, guild.id, self.bot.config.DEFAULT_PREFIX)


def setup(bot):
    bot.add_cog(Events(bot))
