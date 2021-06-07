import discord
from discord.ext import commands

import requests
import json
import asyncio
import typing

# Importa a função predicate do mod blacklist, que retorna True ou False, usado como decorator
from cogs._blacklist import is_blacklisted

class Wikipedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Módulo Wikipedia carregado...")

    @commands.command(
        aliases=["wikipedia", "wiki"],
        brief="- help ajuda tutorial -",
        description="Mini-game Wikirace"
    )
    @commands.guild_only()
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @is_blacklisted()
    async def wikirace(self, ctx, modo: typing.Union[discord.Member, str] = ""):
        if len(ctx.message.mentions) == 0:
            if modo in ["help", "ajuda", "tutorial"]:
                help_embed = discord.Embed(title="Como jogar Wikirace")
                help_embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Wikipedia_Logo_1.0.png/768px-Wikipedia_Logo_1.0.png")
                help_embed.add_field(name="Objetivo do jogo", value="```No Wikirace você tera uma página de inicio e fim, seu objetivo é chegar no fim através das referencias dentro de cada página```", inline=False)
                help_embed.add_field(name="Regras", value="```🞄 Você não pode voltar entre páginas, depois de entrar em uma você só pode sair dela através de outra referencia\n\n🞄 Você só pode utilizar uma aba do navegador, não pode abrir os links em novas abas\n\n🞄 Você só pode utilizar links no corpo da página```", inline=False)
                help_embed.add_field(name="🎲 - Novo inicio", value="```Para sortear outro inicio aleatório, selecione o 🎲```", inline=False)
                help_embed.add_field(name="🏁 - Novo fim", value="```Para sortear outro fim aleatório, selecione o 🏁```", inline=False)
                help_embed.add_field(name="⏱️ - Iniciar partida", value="```Para iniciar a partida, ambos os jogadores devem selecionar ⏱️```", inline=False)
                help_embed.add_field(name="🚪 - Cancelar partida", value="```Para cancelar a partida```", inline=False)
                help_embed.add_field(name="🏆 - Chegou no fim", value="```Selecione 🏆 quando você chegar no fim, o bot irá então avisar ao outro jogador que você venceu```", inline=False)
                await ctx.send(embed=help_embed)
            elif modo == "":
                await ctx.message.delete()
                await ctx.send("Utilize o sub-comando 'help' para instruções de como utilizar esse comando", delete_after=60)
            else:
                await ctx.message.delete()
                await ctx.send("Sub-comando inválido", delete_after=30)
        elif len(ctx.message.mentions) != 1:
            await ctx.send("Mencione apenas um usuário para desafiar", delete_after=30)
        elif modo == ctx.author:
            await ctx.send("Não é possível desafiar a si mesmo", delete_after=30)
        elif modo.bot:
            await ctx.message.delete()
            await ctx.send("Não é possível desafiar bots", delete_after=60)
        else:
            embed_wiki = discord.Embed(color=16316922)
            session = requests.Session()
            response = session.get("https://pt.wikipedia.org/w/api.php?action=query&generator=random&grnnamespace=0&prop=info&inprop=url&grnlimit=2&format=json")
            random_wiki_json = json.loads(response.text)
            ini_wiki_title = random_wiki_json["query"]["pages"][str(list(random_wiki_json["query"]["pages"].keys())[0])]["title"]
            ini_wiki_url = random_wiki_json["query"]["pages"][str(list(random_wiki_json["query"]["pages"].keys())[0])]["fullurl"]
            fim_wiki_title = random_wiki_json["query"]["pages"][str(list(random_wiki_json["query"]["pages"].keys())[1])]["title"]
            fim_wiki_url = random_wiki_json["query"]["pages"][str(list(random_wiki_json["query"]["pages"].keys())[1])]["fullurl"]
            embed_wiki.set_author(name=f"{ctx.message.author.name} vs {ctx.message.mentions[0].name}")
            embed_wiki.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Wikipedia_Logo_1.0.png/768px-Wikipedia_Logo_1.0.png")
            embed_wiki.set_footer(text="🎲:Outro início, 🏁:Outra chegada, ⏱️:Iniciar partida - 0/2")
            embed_wiki.add_field(name="• Inicio corrida:", value=f"[{ini_wiki_title}]({ini_wiki_url})", inline=False)
            embed_wiki.add_field(name="• Chegada corrida:", value=f"[{fim_wiki_title}]({fim_wiki_url})", inline=False)
            menu_wiki = await ctx.send(embed=embed_wiki)
            await menu_wiki.add_reaction("🎲")
            await menu_wiki.add_reaction("🏁")
            await menu_wiki.add_reaction("⏱️")
            await menu_wiki.add_reaction("🚪")

            def emoji_wiki(payload):
                return str(payload.emoji) in ["🎲", "🏁", "⏱️", "🚪"] and (payload.user_id == ctx.author.id or payload.user_id == ctx.message.mentions[0].id) and payload.message_id == menu_wiki.id

            def emoji_ganhador(payload):
                return str(payload.emoji) == "🏆" and (payload.user_id == ctx.author.id or payload.user_id == ctx.message.mentions[0].id) and payload.message_id == trofeu.id

            statusP1, statusP2 = False, False
            while not statusP1 or not statusP2:
                tasks = []
                try:
                    tasks = [
                        asyncio.ensure_future(self.bot.wait_for("raw_reaction_add", check=emoji_wiki)),
                        asyncio.ensure_future(self.bot.wait_for("raw_reaction_remove", check=emoji_wiki)),
                    ]
                    done, pending = await asyncio.wait(tasks, timeout=1800, return_when=asyncio.FIRST_COMPLETED)
                    for task in pending:
                        task.cancel()

                    if len(done) == 0:
                        raise asyncio.TimeoutError()

                    payload = done.pop().result()
                    emoji = str(payload.emoji)
                except asyncio.TimeoutError:
                    await ctx.send("Tempo limite para iniciar excedido", delete_after=30)
                else:
                    if emoji in ["🎲", "🏁"]:
                        response = session.get("https://pt.wikipedia.org/w/api.php?action=query&generator=random&grnnamespace=0&prop=info&inprop=url&grnlimit=1&format=json")
                        random_wiki_json = json.loads(response.text)
                        new_wiki_title = random_wiki_json["query"]["pages"][str(list(random_wiki_json["query"]["pages"].keys())[0])]["title"]
                        new_wiki_url = random_wiki_json["query"]["pages"][str(list(random_wiki_json["query"]["pages"].keys())[0])]["fullurl"]
                    if emoji == "🎲":
                        embed_wiki.set_field_at(0, name="• Inicio corrida:", value=f"[{new_wiki_title}]({new_wiki_url})", inline=False)
                    elif emoji == "🏁":
                        embed_wiki.set_field_at(1, name="• Chegada corrida:", value=f"[{new_wiki_title}]({new_wiki_url})", inline=False)
                    elif emoji == "⏱️":
                        if payload.user_id == ctx.author.id and payload.event_type == "REACTION_ADD":
                            statusP1 = True
                        elif payload.user_id == ctx.message.mentions[0].id and payload.event_type == "REACTION_ADD":
                            statusP2 = True
                        elif payload.user_id == ctx.author.id and payload.event_type == "REACTION_REMOVE":
                            statusP1 = False
                        elif payload.user_id == ctx.message.mentions[0].id and payload.event_type == "REACTION_REMOVE":
                            statusP2 = False
                        if statusP1 and statusP2:
                            embed_wiki.set_footer(text="🎲:Outro início, 🏁:Outra chegada, ⏱️:Iniciar partida - 2/2")
                        elif not statusP1 and not statusP2:
                            embed_wiki.set_footer(text="🎲:Outro início, 🏁:Outra chegada, ⏱️:Iniciar partida - 0/2")
                        else:
                            embed_wiki.set_footer(text="🎲:Outro início, 🏁:Outra chegada, ⏱️:Iniciar partida - 1/2")
                    elif emoji == "🚪":
                        await menu_wiki.delete()
                        await ctx.message.delete()
                        await ctx.send("Partida cancelada", delete_after=30)
                        return
                    await menu_wiki.edit(embed=embed_wiki)
            await menu_wiki.clear_reactions()
            trofeu = await ctx.send("Partida iniciada! Ao chegar na página final aperte no 🏆")
            await trofeu.add_reaction("🏆")
            try:
                payload = await self.bot.wait_for(
                    "raw_reaction_add",
                    timeout=3600,
                    check=emoji_ganhador
                )
            except asyncio.TimeoutError:
                await trofeu.delete()
                await menu_wiki.delete()
                await ctx.message.delete()
                await ctx.send("Tempo limite de jogo (1hr) excedido", delete_after=60)
            else:
                await trofeu.delete()
                await ctx.send(f"{payload.member.name} foi o vencedor da WikiRace! 🏆")

def setup(bot):
    bot.add_cog(Wikipedia(bot))