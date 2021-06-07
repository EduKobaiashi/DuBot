import discord
from discord.ext import commands

from requests import get

# Importa a função predicate do mod blacklist, que retorna True ou False, usado como decorator
from cogs._blacklist import is_blacklisted

# Comandos utilizados para jogar Minecraft com meus amigos, onde compartilho meu IP e rodo um servidor localmente
# As vezes o IP acaba mudando, com esse comando não é necessário que eu fique enviando o novo IP para eles
class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Módulo Minecraft carregado...")

    @commands.command(
        description="Mostra o atual IP do servidor de Minecraft",
        enabled=False
    )
    async def ip(self, ctx):
        ip = get('https://api.ipify.org').text
        await ctx.send(f"O IP do servidor é: {ip}")
        await ctx.send("Caso não esteja conectando me envie mensagem para eu arrumar a porta", delete_after=60)

    @commands.command(
        hidden=True
    )
    @commands.is_owner()
    async def desativaip(self, ctx):
        comando = self.bot.get_command("ip")
        if not comando.enabled:
            await ctx.message.delete()
            return await ctx.send("Comando ja desabilitado", delete_after=30)
        comando.enabled = False
        await ctx.send("Comando desabilitado")
    
    @commands.command(
        hidden=True
    )
    @commands.is_owner()
    async def ativaip(self, ctx):
        comando = self.bot.get_command("ip")
        if comando.enabled:
            await ctx.message.delete()
            return await ctx.send("Comando ja habilitado", delete_after=30)
        comando.enabled = True
        await ctx.send("Comando habilitado")


def setup(bot):
    bot.add_cog(Minecraft(bot))