import discord
from discord.ext import commands

import typing
import asyncio

# Importa a função predicate do mod blacklist, que retorna True ou False, usado como decorator
from cogs._blacklist import is_blacklisted

class Jokenpo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Módulo Jokenpo carregado...")

    @commands.command(
        aliases=["jokenpo"],
        brief="- help ajuda tutorial -",
        description="Desafia um jogador para pedra papel de tesoura"
    )
    @commands.guild_only()
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @is_blacklisted()
    async def jokempo(self, ctx, modo: typing.Union[discord.Member, str] = ""):
        if len(ctx.message.mentions) == 0:
            if modo in ["help", "ajuda", "tutorial"]:
                prefix = ctx.bot.cluster[str(ctx.guild.id)]["config"].find_one({"_id":"config_servidor"})["prefix"]
                help_embed = discord.Embed(title="Como jogar Jokempo")
                help_embed.set_thumbnail(url="https://lh3.googleusercontent.com/cDo7huS5WTjjioOU2ds9t_KBwZ8wz9ttrlKfaafvBuzTkLAIM0jZNbVGXvL4QraXgefS=s150-rw")
                help_embed.add_field(name="Comando", value=f"```Para jogar, utilize o comando {prefix}jokempo @User, mencionando o usuário que deseja jogar contra.\n\nO usuário desafiado deve aceitar o desafio selecionando ✅.\n\nO bot então irá mandar uma mensagem privada para cada jogador escolher sua jogada.\n\nApós ambos jogadores escolherem sua jogada, o resultado será atualizado na mensagem original do bot.```")
                await ctx.send(embed=help_embed)
            elif modo == "":
                await ctx.message.delete()
                await ctx.send("Utilize o sub-comando 'help' para instruções de como utilizar esse comando", delete_after=60)
            else:
                await ctx.message.delete()
                await ctx.send("Sub-comando inválido", delete_after=30)
        elif len(ctx.message.mentions) != 1:
            await ctx.message.delete()
            await ctx.send("Mencione apenas um usuário", delete_after=60)
        elif modo == ctx.author:
            await ctx.message.delete()
            await ctx.send("Não é possível desafiar a si mesmo", delete_after=60)
        elif modo.bot:
            await ctx.message.delete()
            await ctx.send("Não é possível desafiar bots", delete_after=60)
        else:
            embed_servidor = discord.Embed()
            embed_servidor.colour = 11869215
            embed_servidor.set_author(name="Jokempo", icon_url="https://lh3.googleusercontent.com/cDo7huS5WTjjioOU2ds9t_KBwZ8wz9ttrlKfaafvBuzTkLAIM0jZNbVGXvL4QraXgefS=s150-rw")
            embed_servidor.set_footer(text=f"{ctx.author.name} vs {modo.name}")
            embed_servidor.add_field(name="Aceitar desafio", value="```✅ para aceitar o desafio\n🚪 para recusar o desafio```", inline=False)
            menu_servidor = await ctx.send(embed=embed_servidor)
            await menu_servidor.add_reaction("✅")
            await menu_servidor.add_reaction("🚪")

            def aceitar_desafio(payload):
                return str(payload.emoji) in ["✅", "🚪"] and payload.user_id == modo.id and payload.message_id == menu_servidor.id

            try:
                payload = await self.bot.wait_for(
                    "raw_reaction_add", 
                    timeout=120, 
                    check=aceitar_desafio
                )
                emoji = str(payload.emoji)
            except asyncio.TimeoutError:
                await ctx.message.delete()
                await menu_servidor.delete()
                await ctx.send(f"{modo.name} falhou em aceitar o desafio a tempo", delete_after=60)
            else:
                if emoji == "✅":
                    embed_jogo = discord.Embed()
                    embed_jogo.set_footer(text=f"{ctx.author.name} vs {modo.name}")
                    embed_jogo.add_field(name="Sua jogada", value="✊ - Pedra\n✋ - Papel\n✌️ - Tesoura", inline=False)
                    try:
                        embed_jogo.set_author(name="Jokenpo", icon_url=ctx.author.avatar_url)
                        menu_p1 = await ctx.author.send(embed=embed_jogo)
                    except discord.Forbidden:
                        await menu_servidor.delete()
                        await ctx.message.delete()
                        await ctx.send(f"Não foi possível enviar o jogo para {ctx.author.name}", delete_after=60)
                        return
                    try:
                        embed_jogo.set_author(name=f"Jokenpo", icon_url=modo.avatar_url)
                        menu_p2 = await modo.send(embed=embed_jogo)
                    except discord.Forbidden:
                        await menu_p1.delete()
                        await menu_servidor.delete()
                        await ctx.message.delete()
                        await ctx.send(f"Não foi possível enviar o jogo para {ctx.author.name}", delete_after=60)
                        return

                    embed_servidor.set_field_at(0, name="Desafio aceito", value="```Aguardando jogadas```", inline=False)
                    await menu_servidor.edit(embed=embed_servidor)
                    await menu_servidor.clear_reactions()

                    await menu_p1.add_reaction("✊")
                    await menu_p2.add_reaction("✊")
                    await menu_p1.add_reaction("✋")
                    await menu_p2.add_reaction("✋")
                    await menu_p1.add_reaction("✌️")
                    await menu_p2.add_reaction("✌️")

                    def jogada_p1(payload):
                        return str(payload.emoji) in ["✊", "✋", "✌️"] and payload.user_id == ctx.author.id and payload.message_id == menu_p1.id

                    def jogada_p2(payload):
                        return str(payload.emoji) in ["✊", "✋", "✌️"] and payload.user_id == modo.id and payload.message_id == menu_p2.id


                    tasks = []
                    try:
                        tasks = [
                            asyncio.ensure_future(self.bot.wait_for("raw_reaction_add", check=jogada_p1)),
                            asyncio.ensure_future(self.bot.wait_for("raw_reaction_add", check=jogada_p2)),
                        ]
                        done, pending = await asyncio.wait(tasks, timeout=60, return_when=asyncio.ALL_COMPLETED)
                        
                        for task in pending:
                            task.cancel()

                        emoji_p1, emoji_p2 = None, None

                        if len(pending) == 2:
                            raise asyncio.TimeoutError()

                        emoji_p1, emoji_p2 = None, None
                        for task in done:
                            if task.result().user_id == ctx.author.id:
                                emoji_p1 = str(task.result().emoji)
                            else:
                                emoji_p2 = str(task.result().emoji)
                    except asyncio.TimeoutError:
                        await menu_p1.delete()
                        await menu_p2.delete()
                        await menu_servidor.delete()
                        await ctx.message.delete()
                        await ctx.send("Nenhum jogador escolheu uma jogada, partida cancelada", delete_after=30)
                    else:
                        await menu_p1.delete()
                        await menu_p2.delete()
                        embed_servidor.remove_field(0)
                        if emoji_p1 == None:
                            embed_servidor.title = f"{modo.name} venceu a partida!"
                            embed_servidor.add_field(name=f"{modo.name} jogou:", value=f"{emoji_p2}", inline=False)
                            embed_servidor.add_field(name=f"{ctx.author.name} não jogou:", value=f"WO", inline=False)
                        elif emoji_p2 == None:
                            embed_servidor.title = f"{ctx.author.name} venceu a partida!"
                            embed_servidor.add_field(name=f"{ctx.author.name} jogou:", value=f"{emoji_p1}", inline=False)
                            embed_servidor.add_field(name=f"{modo.name} não jogou:", value=f"WO", inline=False)
                        elif emoji_p1 == emoji_p2:
                            embed_servidor.title = "Empate!"
                            embed_servidor.add_field(name=f"Ambos jogaram:", value=f"{emoji_p1}", inline=False)
                        elif (emoji_p1 == "✊" and emoji_p2 == "✌️") or (emoji_p1 == "✋" and emoji_p2 == "✊") or (emoji_p1 == "✌️" and emoji_p2 == "✋"):
                            embed_servidor.title = f"{ctx.author.name} venceu!"
                            embed_servidor.add_field(name=f"{ctx.author.name} jogou:", value=f"{emoji_p1}", inline=False)
                            embed_servidor.add_field(name=f"{modo.name} jogou:", value=f"{emoji_p2}", inline=False)
                        else:
                            embed_servidor.title = f"{modo.name} venceu!"
                            embed_servidor.add_field(name=f"{ctx.author.name} jogou:", value=f"{emoji_p1}", inline=False)
                            embed_servidor.add_field(name=f"{modo.name} jogou:", value=f"{emoji_p2}", inline=False)

                        await menu_servidor.edit(embed=embed_servidor)
                
def setup(bot):
    bot.add_cog(Jokenpo(bot))