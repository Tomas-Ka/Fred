# -*- coding: UTF-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
import re
from random import randint

# ---------------------HOLDER CLASSES---------------------


class DieResults():
    def __init__(self, sides: int, amount: int, result: list = 0) -> None:
        self.sides = sides
        self.amount = amount
        self.result = result


# -----------------------MAIN CLASS-----------------------
class DiceRoller(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(description="Roll a die")
    @app_commands.describe(input='use the ndn+mod (1d20+1) format')
    async def roll(self, interaction: discord.Interaction, input: str) -> None:
        """Rolls an amount of dice with modifier"""

        re_input = re.findall(
            "([+\\-])?\\s*(?:([^+\\-\\s]*)\\s*d\\s*([^+\\-\\s]*)(?=\\s*[+\\-]|\\s*$))|([+\\-])?\\s*(\\d+)",
            input)
        rolls = []

        if len(input) > 256:
            await interaction.response.send_message(content="Input can only be up to 256 characters", ephemeral=True)

        for result in re_input:
            if result[3] == "" and result[4] == "":
                # Dice roll:
                try:
                    amount = int(result[1])
                    sides = int(result[2])

                    if sides == 0:
                        await interaction.response.send_message(content="I can't roll a die with zero sides...", ephemeral=True)
                        return

                    if amount == 0:
                        await interaction.response.send_message(content="I can't roll zero dice", ephemeral=True)
                        return

                    if amount > 100:
                        await interaction.response.send_message(content="You can only roll up to 100 die of each type", ephemeral=True)
                        return

                    elif sides > 1000000:
                        await interaction.response.send_message(content="You can only roll dice with up to a million sides, you seriously don't need more than that", ephemeral=True)
                        return

                except ValueError:
                    await interaction.response.send_message(content="Sorry, I couldn't understand your roll, please try again", ephemeral=True)
                    return

                if result[0] == "-":
                    mod = -1
                else:
                    mod = 1

                die_rolls = []
                for i in range(0, amount):
                    die_rolls.append(randint(1, sides) * mod)

                rolls.append(DieResults(sides, amount, die_rolls))
            else:
                # Modifier:
                try:
                    val = int(result[3] + result[4])
                except ValueError:
                    await interaction.response.send_message(content="Sorry, I couldn't understand your roll, please try again", ephemeral=True)

                rolls.append(val)

        embed_length = len(input) + len(interaction.user.display_name)
        embed = discord.Embed(title=input, color=0xffd700)
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar)
        total = 0
        modifiers = ""
        for obj in rolls:
            if isinstance(obj, DieResults):
                res = obj.result
                val = ""
                for num in res:
                    total += num
                    val += f"({num}), "
                val = val[0:-2]
                embed.add_field(
                    name=f"{obj.amount}d{obj.sides}",
                    value=val,
                    inline=False)
                embed_length = embed_length + \
                    len(f"{obj.amount}d{obj.sides}") + len(val)
            else:
                total += obj
                if obj < 0:
                    modifiers += f"{obj}, "
                    embed_length += len(f"{obj}, ")
                else:
                    modifiers += f"+{obj}, "
                    embed_length += len(f"+{obj}, ")

        if not modifiers == "":
            modifiers = modifiers[0:-2]
            embed.add_field(name="modifiers", value=modifiers, inline=False)
        embed.add_field(name="Total", value=total, inline=False)
        # Length of "total" is 5, and of "modifiers" is 9.
        embed_length = embed_length + 5 + 9 + total + len(modifiers)

        if embed_length > 6000:
            await interaction.response.send_message(content="Sorry, your roll is too large, please try again with a smaller one", ephemeral=True)
            return
        await interaction.response.send_message(embed=embed)


# ----------------------MAIN PROGRAM----------------------
# This setup is required for the cog to setup and run,
# and is run when the cog is loaded with bot.load_extensions().
async def setup(bot: commands.Bot) -> None:
    print("\tcogs.dice_roller begin loading")
    await bot.add_cog(DiceRoller(bot))
