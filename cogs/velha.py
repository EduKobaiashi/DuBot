import discord
from discord.ext import commands

import typing
import asyncio

# Importa a função predicate do mod blacklist, que retorna True ou False, usado como decorator
from cogs._blacklist import is_blacklisted

class velha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Módulo Jogo da Velha carregado...")

    @commands.command(
        description="Mencione um usuário e o desafie para um jogo da velha"
    )
    @commands.guild_only()
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @is_blacklisted()
    async def velha(self, ctx, p2: typing.Union[discord.Member, str] = ""):
        if len(ctx.message.mentions) != 1:
            await ctx.message.delete()
            await ctx.send("Mencione um usuário para jogar", delete_after=60)
        elif p2 == ctx.author:
            await ctx.message.delete()
            await ctx.send("Não é possível desafiar a si mesmo", delete_after=60)
        elif p2.bot:
            await ctx.message.delete()
            await ctx.send("Não é possível desafiar bots", delete_after=60)
        else:
            #emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
            emojis = ["↖️", "⬆️", "↗️", "⬅️", "⏹️", "➡️", "↙️", "⬇️", "↘️"]
            tabuleiro = {f"{emojis[0]}": "⬛", f"{emojis[1]}": "⬛", f"{emojis[2]}": "⬛", f"{emojis[3]}": "⬛", f"{emojis[4]}": "⬛", f"{emojis[5]}": "⬛", f"{emojis[6]}": "⬛", f"{emojis[7]}": "⬛", f"{emojis[8]}": "⬛"}
            tabuleiro_embed = discord.Embed(title="Jogo da Velha")
            tabuleiro_embed.colour = 8388736
            tabuleiro_string = f"`{emojis[0]}` `{emojis[1]}` `{emojis[2]}`\n`{emojis[3]}` `{emojis[4]}` `{emojis[5]}`\n`{emojis[6]}` `{emojis[7]}` `{emojis[8]}`"
            tabuleiro_embed.add_field(name=f"{ctx.author.name} é sua vez", value=tabuleiro_string, inline=False)
            menu_velha = await ctx.send(embed=tabuleiro_embed)

            jogador = 1
            for emoji in emojis:
                await menu_velha.add_reaction(emoji)

            def jogada(payload):
                if jogador == 1:
                    return str(payload.emoji) in emojis and payload.user_id == ctx.author.id and payload.message_id == menu_velha.id
                else:
                    return str(payload.emoji) in emojis and payload.user_id == p2.id and payload.message_id == menu_velha.id

            def tabuleiroToString(tabuleiro):
                tabuleiro_string = ""
                for i, jogada in enumerate(tabuleiro.items()):
                    if i == len(tabuleiro)-1:
                        tabuleiro_string += f"`{jogada[1]}`"
                    elif (i+1)%3 == 0:
                        tabuleiro_string += f"`{jogada[1]}`\n"
                    else:
                        tabuleiro_string += f"`{jogada[1]}` "
                return tabuleiro_string

            def ganhou(tabuleiro):
                jogadas = list(tabuleiro.values())
                for i in range(3):
                    soma = 0
                    for j in range(3):
                        if jogadas[(i*3)+j] == "❌":
                            soma += 1
                        elif jogadas[(i*3)+j] == "⭕":
                            soma -= 1
                    if soma == 3:
                        return True, "❌"
                    elif soma == -3:
                        return True, "⭕"

                for i in range(3):
                    soma = 0
                    for j in range(3):
                        if jogadas[(j*3)+i] == "❌":
                            soma += 1
                        elif jogadas[(j*3)+i] == "⭕":
                            soma -= 1
                    if soma == 3:
                        return True, "❌"
                    elif soma == -3:
                        return True, "⭕"

                if (jogadas[0] == "❌" and jogadas[4] == "❌" and jogadas[8] == "❌") or (jogadas[2] == "❌" and jogadas[4] == "❌" and jogadas[6] == "❌"):
                    return True, "❌"
                elif (jogadas[0] == "⭕" and jogadas[4] == "⭕" and jogadas[8] == "⭕") or (jogadas[2] == "⭕" and jogadas[4] == "⭕" and jogadas[6] == "⭕"):
                    return True, "⭕"

                return False, "⬛"

            while not ganhou(tabuleiro)[0]:
                try:
                    tasks = [
                        asyncio.ensure_future(self.bot.wait_for("raw_reaction_add", check=jogada)),
                        asyncio.ensure_future(self.bot.wait_for("raw_reaction_remove", check=jogada)),
                    ]
                    done, pending = await asyncio.wait(tasks, timeout=1800, return_when=asyncio.FIRST_COMPLETED)
                    for task in pending:
                        task.cancel()

                    if len(done) == 0:
                        raise asyncio.TimeoutError()

                    payload = done.pop().result()
                    emoji = str(payload.emoji)
                except asyncio.TimeoutError:
                    await ctx.message.delete()
                    await menu_velha.delete()
                    await ctx.send("Tempo limite para escolher jogada excedido, partida finalizada", delete_after=60)
                    return
                else:
                    await menu_velha.clear_reaction(emoji)
                    emojis.remove(emoji)

                    if jogador == 1:
                        tabuleiro[emoji] = "❌"
                        jogador = 2
                        vez = f"{p2.name} é sua vez"
                    else:
                        tabuleiro[emoji] = "⭕"
                        jogador = 1
                        vez = f"{ctx.author.name} é sua vez"

                    tabuleiro_string = tabuleiroToString(tabuleiro)
                    tabuleiro_embed.set_field_at(0, name=vez, value=tabuleiro_string, inline=False)

                    await menu_velha.edit(embed=tabuleiro_embed)
            
            await menu_velha.clear_reactions()
            ganhador = ganhou(tabuleiro)[1]
            if ganhador == "❌":
                tabuleiro_embed.title = f"{ctx.author.name} Venceu!"
            elif ganhador == "⭕":
                tabuleiro_embed.title = f"{p2.name} Venceu!"
            else:
                tabuleiro_embed.title = "Deu velha!"

            await menu_velha.edit(embed=tabuleiro_embed)


                



def setup(bot):
    bot.add_cog(velha(bot))