#  Copyright (c) 2020 — present, howaitoreivun.
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import itertools
from typing import List, Union

import discord
from discord.ext import commands

from tomodachi.core import CogMixin, TomodachiContext

# Type alias for a commands mapping, quite helpful
Commands = List[Union[commands.Command, commands.Group]]


class TomodachiHelpCommand(commands.MinimalHelpCommand):
    context: TomodachiContext

    def __init__(self, **options):
        super().__init__(**options, command_attrs=dict(hidden=True))
        self._e_colour = 0x2F3136

    async def send_pages(self):
        e = discord.Embed(colour=self._e_colour)
        e.description = "".join(self.paginator.pages)

        await self.get_destination().send(embed=e)

    def format_command(self, command: Union[commands.Command, commands.Group]):
        fmt = "`{0}{1}` — {2}\n" if command.short_doc else "`{0}{1}`\n"
        return fmt.format(self.context.prefix, command.qualified_name, command.short_doc)

    async def send_bot_help(self, _):
        embed = discord.Embed(
            colour=self._e_colour,
            description=self.get_opening_note(),
        )

        embed.set_thumbnail(url=self.context.bot.user.avatar.url)

        def get_category(command):
            _cog: CogMixin = command.cog
            return _cog.formatted_name if _cog is not None else "Uncategorized"

        filtered: Commands = await self.filter_commands(self.context.bot.commands, sort=True, key=get_category)

        igrouped = itertools.groupby(filtered, key=get_category)
        # cast iterators to tuples because we need to reuse values of it
        grouped = tuple((cat, tuple(cmds)) for cat, cmds in igrouped)

        def get_total_length(group):
            return len("".join(cmd.name for cmd in group[1]))

        # order group categories by the total length of command names
        ordered = sorted(grouped, key=get_total_length, reverse=True)

        for category, _commands in ordered:
            _commands = sorted(_commands, key=lambda c: c.name)
            embed.add_field(name=category, value=" ".join(f"`{c.qualified_name}`" for c in _commands), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog: CogMixin):
        description = ""

        embed = discord.Embed(title=cog.qualified_name, colour=self._e_colour)
        embed.set_thumbnail(url=self.context.bot.user.avatar.url)

        if cog.description:
            description += f"{cog.description}\n\n"

        filtered: Commands = await self.filter_commands(cog.get_commands(), sort=True)

        if filtered:
            for command in filtered:
                description += self.format_command(command)

        embed.description = description

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        description = ""

        embed = discord.Embed(colour=self._e_colour, title=f"{group} commands")
        embed.set_thumbnail(url=self.context.bot.user.avatar.url)

        filtered: Commands = await self.filter_commands(group.commands, sort=True)
        if filtered:
            for command in filtered:
                description += self.format_command(command)

        embed.description = description

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            colour=self._e_colour,
            title=self.get_command_signature(command),
        )

        description = ""
        if command.help:
            description += f"{self.context.bot.icon('rich_presence')} {command.help}"

        if command.description:
            description += f"\n\n{command.description}"

        if description:
            embed.description = description

        if cooldown := command._buckets._cooldown:  # noqa
            embed.add_field(name="Cooldown", value=f"{self.context.bot.icon('slowmode')} {int(cooldown.per)} seconds")

        if command.aliases:
            aliases = (f"`{alias}`" for alias in command.aliases)
            embed.add_field(name="Aliases", value=" ".join(aliases))

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = discord.Embed(colour=self._e_colour)
        embed.title = f"{self.context.bot.icon('question')} {error}"

        await self.get_destination().send(embed=embed)


class TomodachiHelp(CogMixin):
    def __init__(self, /, tomodachi):
        super().__init__(tomodachi)
        self._original_help_command = tomodachi.help_command
        tomodachi.help_command = TomodachiHelpCommand()
        tomodachi.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(TomodachiHelp(bot))
