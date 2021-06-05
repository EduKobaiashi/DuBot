import discord
from discord.ext import commands

class NOME_CLASSE(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Módulo NOME_MODULO carregado...")

    @commands.command()
    async def foo(self, ctx):
        pass

def setup(bot):
    bot.add_cog(NOME_CLASSE(bot))