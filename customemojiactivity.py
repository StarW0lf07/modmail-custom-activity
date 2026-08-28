import re

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


EMOJI_REGEX = re.compile(r"^<(a?):([A-Za-z0-9_]+):(\d+)>\s*(.*)$")


class CustomActivityEmoji(commands.Cog):
    """Adds custom emoji support to Modmail's custom activity."""

    def __init__(self, bot):
        self.bot = bot
        self.utility = bot.get_cog("Utility")
        self.original_activity = bot.get_command("activity")

        # Replace Modmail's built-in activity command.
        if self.original_activity:
            bot.remove_command("activity")

    @commands.command(
        name="activity",
        aliases=["presence"],
    )
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def activity(self, ctx, activity_type: str.lower, *, message: str = ""):
        """Set an activity with optional custom emoji support."""

        if activity_type == "clear":
            self.bot.config.remove("activity_type")
            self.bot.config.remove("activity_message")
            self.bot.config.remove("activity_emoji")
            await self.bot.config.update()

            await self.utility.set_presence()

            return await ctx.send(
                embed=discord.Embed(
                    title="Activity Removed",
                    color=self.bot.main_color,
                )
            )

        if not message:
            raise commands.MissingRequiredArgument(
                commands.Parameter(
                    name="message",
                    kind=commands.Parameter.KEYWORD_ONLY,
                )
            )

        try:
            activity_enum = discord.ActivityType[activity_type]
        except KeyError:
            raise commands.BadArgument(
                "Invalid activity type. Use `playing`, `streaming`, "
                "`listening`, `watching`, `competing`, or `custom`."
            )

        emoji = None
        activity_message = message

        # Parse Discord custom emoji:
        # <:name:id>
        # <a:name:id>
        if activity_enum == discord.ActivityType.custom:
            match = EMOJI_REGEX.match(message)

            if match:
                animated = bool(match.group(1))
                emoji_name = match.group(2)
                emoji_id = int(match.group(3))
                activity_message = match.group(4).strip()

                emoji = discord.PartialEmoji(
                    name=emoji_name,
                    id=emoji_id,
                    animated=animated,
                )

                self.bot.config["activity_emoji"] = {
                    "name": emoji_name,
                    "id": emoji_id,
                    "animated": animated,
                }
            else:
                self.bot.config.remove("activity_emoji")

        # Normal activities use Modmail's normal presence system.
        if activity_enum != discord.ActivityType.custom:
            activity, _ = await self.utility.set_presence(
                activity_type=activity_enum,
                activity_message=activity_message,
            )

        else:
            activity = discord.CustomActivity(
                name=activity_message,
                emoji=emoji,
            )

            await self.bot.change_presence(activity=activity)

        self.bot.config["activity_type"] = activity_enum.value
        self.bot.config["activity_message"] = activity_message

        await self.bot.config.update()

        return await ctx.send(
            embed=discord.Embed(
                title="Activity Changed",
                description=f"Activity set to: Custom {activity_message}.",
                color=self.bot.main_color,
            )
        )


async def setup(bot):
    await bot.add_cog(CustomActivityEmoji(bot))
