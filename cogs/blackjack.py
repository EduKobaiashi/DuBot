import discord
from discord.ext import commands

import random
from datetime import date
import asyncio
import time
import pymongo

# Importa a função predicate do mod blacklist, que retorna True ou False, usado como decorator
from cogs._blacklist import is_blacklisted

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Módulo Blackjack carregado...")

    @commands.command(
        description="Comando para ganhar pontos para o blackjack diariamente"
    )
    @commands.guild_only()
    @is_blacklisted()
    async def dailyjack(self, ctx):
        collection = ctx.bot.cluster[str(ctx.guild.id)]["blackjack"]
        user = collection.find_one({"_id":ctx.author.id, "name":ctx.author.name})
        if user == None or user["ultimo-daily"] != str(date.today()):
            collection.update_one({"_id":ctx.author.id}, {"$set":{"name":ctx.author.name, "ultimo-daily":str(date.today())}, "$inc":{"pontos":10}}, upsert=True)
            await ctx.send("10 pontos diários adicionados")
        elif user["ultimo-daily"] == str(date.today()):
            await ctx.message.delete()
            await ctx.send("Você ja resgatou seus pontos hoje", delete_after=60)

    @commands.command(
        aliases=["jack", "jacks"],
        brief="- help ajuda tutorial - scoreboard placar pontuacao rank leaderboard - balance pontos carteira -",
        description="Mini-game Blackjack"
    )
    @commands.guild_only()
    @commands.max_concurrency(1, per=commands.BucketType.user, wait=False)
    @is_blacklisted()
    async def blackjack(self, ctx, modo=""):
        cartas = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        naipes = ["♣️", "♠️", "♦️", "♥️"]
        baralho = []
        for carta in cartas:
            for naipe in naipes:
                baralho += [[carta, naipe]]
        random.shuffle(baralho)

        try:
            aposta = int(modo)
        except ValueError:
            collection = self.bot.cluster[str(ctx.guild.id)]["blackjack"]
            if modo in ["balance", "pontos", "carteira"]:
                user = collection.find_one({"_id":ctx.author.id, "name":ctx.author.name}) 
                if user == None:
                    await ctx.message.delete()
                    await ctx.send(f"Você ainda não tem pontos, use o comando dailyjack para ganhar pontos", delete_after=60)
                else:
                    pontos = user["pontos"]
                    await ctx.send(f"Você tem {pontos} ponto(s) na sua balance")
            elif modo in ["scoreboard", "placar", "pontuacao", "rank", "rankings", "leaderboard"]:
                scoreboard = "```\n"
                for posicao, data in enumerate(collection.find().sort([("pontos", pymongo.DESCENDING), ("nome", pymongo.ASCENDING)])):
                    nome = data["name"]
                    pontos = data["pontos"]
                    if posicao == 0:
                        scoreboard += f"🥇 {nome}: {pontos}\n"
                    elif posicao == 1:
                        scoreboard += f"🥈 {nome}: {pontos}\n"
                    elif posicao == 2:
                        scoreboard += f"🥉 {nome}: {pontos}\n"
                    else:
                        scoreboard += f" {nome}: {pontos}\n"
                scoreboard += "```"
                scoreboard_embed = discord.Embed(title=f"Scoreboard Blackjack - Servidor: `{ctx.guild.name}`", description = scoreboard)
                await ctx.send(embed=scoreboard_embed)
            elif modo in ["help", "ajuda", "tutorial"]:
                prefix = ctx.bot.cluster[str(ctx.guild.id)]["config"].find_one({"_id":"config_servidor"})["prefix"]
                help_embed = discord.Embed(title="Como jogar Blackjack")
                help_embed.set_thumbnail(url="https://cdn1.iconfinder.com/data/icons/gambling-26/128/gambling-10-512.png")
                help_embed.add_field(name="Objetivo do jogo", value="```O objetivo de qualquer mão de Blackjack é derrotar o dealer. Para fazer isso, você deve ter uma mão em que a pontuação seja mais elevada do que a mão do dealer, mas não exceda 21 no valor total. Como alternativa, você pode ganhar tendo uma pontuação menor que 22 quando o valor da mão do dealer ultrapassar 21. Quando o valor total da sua mão for 22 ou mais, você vai automaticamente perder qualquer valor apostado.```", inline=False)
                help_embed.add_field(name="Cartas", value="```No Blackjack, os dez, valetes, damas e reis têm o valor de dez cada um. Os Áses podem ter dois valores diferentes, tanto um como onze (Você pode escolher qual. Por exemplo, quando você combina um ás e um quatro, a sua mão pode ter o valor tanto de cinco como de quinze). Todas as outras cartas tem o valor indicado na mesma```")
                help_embed.add_field(name="🎯 - Bater", value="```Você pode pedir cartas adicionais para melhorar sua mão. As cartas serão distribuídas uma por vez até que o valor total da mão seja 21 ou superior.```", inline=False)
                help_embed.add_field(name="🛑 - Manter", value="```Quando o valor total da sua mão é de 21 ou inferior, você pode escolher manter e não arriscar a oportunidade da mão ultrapassar o valor total de 21.```", inline=False)
                help_embed.add_field(name="2️⃣ - Dobrar", value="```Você pode colocar uma aposta adicional, igual à aposta inicial, em troca de apenas mais uma carta para a sua mão, após a qual você irá automaticamente manter.```", inline=False)
                help_embed.add_field(name="Mão da casa", value="```A casa deve bater até que alcance uma contagem de 17 ou mais.```", inline=False)
                help_embed.add_field(name="Blackjack", value="```A mão mais elevada no blackjack é um Ás e uma carta de 10 pontos e é chamada justamente de blackjack. Um blackjack paga 1.5x sua aposta.```", inline=False)
                help_embed.add_field(name="Comando", value=f"```{prefix}dailyjack - Para conseguir 10 pontos (diariamente)\n\n{prefix}blackjack balance - Para ver quantos pontos você tem\n\n{prefix}blackjack <valor inteiro> - Para fazer uma aposta e jogar blackjack (Aposta mínima: 1)\n\n{prefix}blackjack scoreboard - Para ver as pontuações do servidor```")
                await ctx.send(embed=help_embed)
            elif modo == "":
                await ctx.message.delete()
                await ctx.send("Utilize o sub-comando 'help' para instruções de como utilizar esse comando", delete_after=60)
            else:
                await ctx.message.delete()
                await ctx.send("Sub-comando inválido", delete_after=30)

        else:
            collection = self.bot.cluster[str(ctx.guild.id)]["blackjack"]
            user = collection.find_one({"_id":ctx.author.id})
            if user == None:
                await ctx.message.delete()
                await ctx.send(f"Você ainda não tem pontos, use o comando dailyjack para ganhar pontos", delete_after=60)
            if aposta > user["pontos"]:
                await ctx.message.delete()
                await ctx.send("Você não tem pontos suficientes para fazer essa aposta", delete_after=60)
            elif aposta < 1:
                await ctx.message.delete()
                await ctx.send("Aposta minima de 1 ponto", delete_after=60)
            else:
                balance = user["pontos"]
                embed_blackjack = discord.Embed()
                embed_blackjack.colour = 12632256
                embed_blackjack.set_author(name=f"Blackjack - {ctx.author.name}", icon_url=ctx.author.avatar_url)
                embed_blackjack.set_footer(text=f"Aposta: {aposta} | Balance: {balance}")
                embed_blackjack.set_thumbnail(url="https://cdn1.iconfinder.com/data/icons/gambling-26/128/gambling-10-512.png")
                embed_blackjack.add_field(name="Cartas da casa:", value="🃏 | 🃏", inline=False)
                embed_blackjack.add_field(name="Suas cartas:", value="🃏 | 🃏", inline=False)
                embed_blackjack.add_field(name="Aceitar aposta", value="```✅ para aceitar a aposta\n🚪 para cancelar o jogo```", inline=False)
                menu_blackjack = await ctx.send(embed=embed_blackjack)
                await menu_blackjack.add_reaction("✅")
                await menu_blackjack.add_reaction("🚪")

                def aceitar_aposta(payload):
                    return str(payload.emoji) in ["✅", "🚪"] and payload.user_id == ctx.author.id and payload.message_id == menu_blackjack.id

                def valor_mao(mao):
                    As = 0
                    for carta in mao:
                        if carta[0] == "A":
                            As += 1
                    valorMao1 = 0
                    valorMao2 = 0
                    if As == 0:
                        for carta in mao:
                            if carta[0] in ["J", "Q", "K"]:
                                valorMao1 += 10
                            else:
                                valorMao1 += int(carta[0])
                        return [valorMao1]
                    elif As == 1:
                        for carta in mao:
                            if carta[0] == "A":
                                valorMao1 += 11
                                valorMao2 += 1
                            elif carta[0] in ["J", "Q", "K"]:
                                valorMao1 += 10
                                valorMao2 += 10
                            else:
                                valorMao1 += int(carta[0])
                                valorMao2 += int(carta[0])
                        if valorMao1 <= 21:
                            return [valorMao1, valorMao2]
                        else:
                            return [valorMao2]
                    elif As >= 2:
                        for carta in mao:
                            if carta[0] == "A":
                                if As == 1:
                                    valorMao1 += 11
                                    valorMao2 += 1
                                else:
                                    valorMao1 += 1
                                    valorMao2 += 1
                                    As -= 1
                            elif carta[0] in ["J", "Q", "K"]:
                                valorMao1 += 10
                                valorMao2 += 10
                            else:
                                valorMao1 += int(carta[0])
                                valorMao2 += int(carta[0])
                        if valorMao1 <= 21:
                            return [valorMao1, valorMao2]
                        else:
                            return [valorMao2]

                def mao_para_string(mao):
                    string_mao = f"{mao[0][0]}.{mao[0][1]}"
                    for carta in mao[1:]:
                        string_mao += f" | {carta[0]}.{carta[1]}"
                    return string_mao

                try:
                    payload = await self.bot.wait_for(
                        "raw_reaction_add", 
                        timeout=120,
                        check=aceitar_aposta
                    )
                    emoji = str(payload.emoji)
                except asyncio.TimeoutError:
                    await ctx.message.delete()
                    await menu_blackjack.delete()
                    await ctx.send("Aposta cancelada, tempo limite para aceitar excedido", delete_after=60)
                else:
                    if emoji == "🚪":
                        await ctx.message.delete()
                        await menu_blackjack.delete()
                        await ctx.send("Aposta cancelada", delete_after=60)
                    else:
                        mao_user = [baralho.pop(), baralho.pop()]
                        string_mao_user = mao_para_string(mao_user)
                        valor_mao_user = valor_mao(mao_user)
                        mao_bot = [baralho.pop(), baralho.pop()]

                        if mao_bot[0][0] == "A":
                            valor_mao_bot = [11, 1]
                        elif mao_bot[0][0] in ["J", "Q", "K"]:
                            valor_mao_bot = [10]
                        else:
                            valor_mao_bot = [int(mao_bot[0][0])]

                        embed_blackjack.remove_field(2)
                        embed_blackjack.colour = 8388736
                        if len(valor_mao_bot) == 1:
                            embed_blackjack.set_field_at(0, name=f"Cartas da casa ({valor_mao_bot[0]}):", value=f"{mao_bot[0][0]}.{mao_bot[0][1]} | 🃏", inline=False)
                        else:
                            embed_blackjack.set_field_at(0, name=f"Cartas da casa ({valor_mao_bot[0]} | {valor_mao_bot[1]}):", value=f"{mao_bot[0][0]}.{mao_bot[0][1]} | 🃏", inline=False)
                        if len(valor_mao_user) == 1:
                            embed_blackjack.set_field_at(1, name=f"Suas cartas ({valor_mao_user[0]}):", value=string_mao_user, inline=False)
                        else:
                            embed_blackjack.set_field_at(1, name=f"Suas cartas ({valor_mao_user[0]} | {valor_mao_user[1]}):", value=string_mao_user, inline=False)
                        await menu_blackjack.clear_reactions()
                        await menu_blackjack.edit(embed=embed_blackjack)
                        await menu_blackjack.add_reaction("🎯")
                        await menu_blackjack.add_reaction("🛑")
                        double = False
                        if balance//2 >= aposta:
                            await menu_blackjack.add_reaction("2️⃣")
                            double = True
                            
                        def emoji_blackjack(payload):
                            if str(payload.emoji) == "2️⃣":
                                return double and payload.user_id == ctx.author.id and payload.message_id == menu_blackjack.id
                            return str(payload.emoji) in ["🎯", "🛑"] and payload.user_id == ctx.author.id and payload.message_id == menu_blackjack.id

                        try:
                            payload = await self.bot.wait_for(
                                "raw_reaction_add", 
                                timeout=120,
                                check=emoji_blackjack
                            )
                            emoji = str(payload.emoji)
                        except asyncio.TimeoutError:
                            await ctx.send("Tempo limite para escolher excedido", delete_after=15)
                            emoji = "🛑"
                        finally:
                            await menu_blackjack.clear_reaction("2️⃣")
                            while emoji == "🎯" and valor_mao_user[0] < 21:
                                mao_user += [baralho.pop()]
                                valor_mao_user = valor_mao(mao_user)
                                string_mao_user = mao_para_string(mao_user)

                                if len(valor_mao_user) == 1:
                                    embed_blackjack.set_field_at(1, name=f"Suas cartas ({valor_mao_user[0]}):", value=string_mao_user, inline=False)
                                else:
                                    embed_blackjack.set_field_at(1, name=f"Suas cartas ({valor_mao_user[0]} | {valor_mao_user[1]}):", value=string_mao_user, inline=False)
                                await menu_blackjack.edit(embed=embed_blackjack)

                                if valor_mao_user[0] < 21:
                                    tasks = []
                                    try:
                                        tasks = [
                                            asyncio.ensure_future(self.bot.wait_for("raw_reaction_add", check=emoji_blackjack)),
                                            asyncio.ensure_future(self.bot.wait_for("raw_reaction_remove", check=emoji_blackjack)),
                                        ]
                                        done, pending = await asyncio.wait(tasks, timeout=1800, return_when=asyncio.FIRST_COMPLETED)
                                        for task in pending:
                                            task.cancel()

                                        if len(done) == 0:
                                            raise asyncio.TimeoutError()

                                        payload = done.pop().result()
                                        emoji = str(payload.emoji)
                                    except asyncio.TimeoutError:
                                        await ctx.send("Tempo limite para escolher excedido", delete_after=15)
                                        emoji = "🛑"
                            await menu_blackjack.clear_reactions()

                            if emoji == "2️⃣":
                                aposta *= 2
                                embed_blackjack.set_footer(text=f"Aposta: {aposta} | Balance: {balance}")
                                mao_user += [baralho.pop()]
                                valor_mao_user = valor_mao(mao_user)
                                string_mao_user = mao_para_string(mao_user)
                                if len(valor_mao_user) == 1:
                                    embed_blackjack.set_field_at(1, name=f"Suas cartas ({valor_mao_user[0]}):", value=string_mao_user, inline=False)
                                else:
                                    embed_blackjack.set_field_at(1, name=f"Suas cartas ({valor_mao_user[0]} | {valor_mao_user[1]}):", value=string_mao_user, inline=False)
                                await menu_blackjack.edit(embed=embed_blackjack)

                            valor_mao_bot = valor_mao(mao_bot)
                            string_mao_bot = mao_para_string(mao_bot)
                            if len(valor_mao_bot) == 1:
                                embed_blackjack.set_field_at(0, name=f"Cartas da casa ({valor_mao_bot[0]}):", value=string_mao_bot, inline=False)
                            else:
                                embed_blackjack.set_field_at(0, name=f"Cartas da casa ({valor_mao_bot[0]} | {valor_mao_bot[1]}):", value=string_mao_bot, inline=False)
                            await menu_blackjack.edit(embed=embed_blackjack)
                            while valor_mao_bot[0] < 17 and valor_mao_user[0] <= 21:
                                mao_bot += [baralho.pop()]
                                valor_mao_bot = valor_mao(mao_bot)
                                string_mao_bot = mao_para_string(mao_bot)
                                if len(valor_mao_bot) == 1:
                                    embed_blackjack.set_field_at(0, name=f"Cartas da casa ({valor_mao_bot[0]}):", value=string_mao_bot, inline=False)
                                else:
                                    embed_blackjack.set_field_at(0, name=f"Cartas da casa ({valor_mao_bot[0]} | {valor_mao_bot[1]}):", value=string_mao_bot, inline=False)
                                time.sleep(.5)
                                await menu_blackjack.edit(embed=embed_blackjack)

                            if valor_mao_user[0] > 21:
                                embed_blackjack.title = f"Bust!"
                                embed_blackjack.colour = 16711680
                                embed_blackjack.description = f"Você perdeu {aposta} pontos\nBalance: `{balance-aposta} pontos`"
                                collection.update_one({"_id":ctx.author.id}, {"$set":{"name":ctx.author.name}, "$inc":{"pontos":-aposta}})
                            elif valor_mao_user[0] == 21 and valor_mao_bot[0] != 21:
                                if len(mao_user) == 2:
                                    aposta = int(aposta*1.5)
                                    embed_blackjack.title = f"Blackjack!"
                                    embed_blackjack.description = f"Você ganhou {aposta} pontos\nBalance: `{balance+aposta} pontos`"
                                else:
                                    embed_blackjack.title = f"21!"
                                embed_blackjack.colour = 65280
                                embed_blackjack.description = f"Você ganhou {aposta} pontos\nBalance: `{balance+aposta} pontos`"
                                collection.update_one({"_id":ctx.author.id}, {"$set":{"name":ctx.author.name}, "$inc":{"pontos":aposta}})
                            elif valor_mao_user[0] > valor_mao_bot[0] or valor_mao_bot[0] > 21:
                                embed_blackjack.title = f"Winner!"
                                embed_blackjack.colour = 65280
                                embed_blackjack.description = f"Você ganhou {aposta} pontos\nBalance: `{balance+aposta} pontos`"
                                collection.update_one({"_id":ctx.author.id}, {"$set":{"name":ctx.author.name}, "$inc":{"pontos":aposta}})
                            elif valor_mao_user[0] < valor_mao_bot[0]:
                                embed_blackjack.title = "Loser!"
                                embed_blackjack.colour = 16711680
                                embed_blackjack.description = f"Você perdeu {aposta} pontos\nBalance: `{balance-aposta} pontos`"
                                collection.update_one({"_id":ctx.author.id}, {"$set":{"name":ctx.author.name}, "$inc":{"pontos":-aposta}})
                            elif valor_mao_user[0] == valor_mao_bot[0]:
                                embed_blackjack.title = f"Push!"
                                embed_blackjack.colour = 16776960
                                embed_blackjack.description = f"Você não perdeu nem ganhou pontos\nBalance: `{balance} pontos`"
                            time.sleep(.75)
                            await menu_blackjack.edit(embed=embed_blackjack)

def setup(bot):
    bot.add_cog(Blackjack(bot))