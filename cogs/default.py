import discord
from discord.ext import commands

import asyncio

# Importa a função predicate do mod blacklist, que retorna True ou False, usado como decorator
from cogs._blacklist import is_blacklisted

class Default(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Módulo Default carregado...")

    @commands.command(
        brief="Prefix",
        description="Mudar o prefix do bot no servidor"
        )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def prefix(self, ctx, *, prefix="edu."):
        collection = self.bot.cluster[str(ctx.guild.id)]["config"]
        collection.update_one({"_id":"config_servidor"}, {"$set":{"prefix":prefix}})
        await ctx.send(f"Prefix mudado para `{prefix}` com sucesso")

    @commands.command(
        brief="Blacklist",
        description="Gerencia a blacklist do servidor"
    )
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @is_blacklisted()
    async def blacklist(self, ctx):
        embed_blacklist = discord.Embed(title="Menu: Blacklist", description="```✅ - Adicionar à blacklist\n🅱️ - Remover da blacklist\n📖 - Consultar blacklist```")
        #embed_blacklist.add_field(name="Opções", value="```✅ - Adicionar à blacklist\n🅱️ - Remover da blacklist\n📖 - Consultar blacklist```")
        menu_blacklist = await ctx.send(embed=embed_blacklist)
        await menu_blacklist.add_reaction("✅")
        await menu_blacklist.add_reaction("🅱️")
        await menu_blacklist.add_reaction("📖")

        def emote_blacklist(payload):
            return str(payload.emoji) in ["✅", "🅱️", "📖"] and payload.user_id == ctx.author.id
        
        def ctx_editado(before, after):
            return ctx.message.id == after.id

        def mesmo_user(msg):
            return msg.author.id == ctx.author.id

        try:
            payload = await self.bot.wait_for(
                "raw_reaction_add",
                timeout=120.0,
                check=emote_blacklist
            )
            emoji = str(payload.emoji)
        except asyncio.TimeoutError:
            await ctx.message.delete()
            await ctx.send("Tempo limite excedido", delete_after=10)
        else:
            if emoji == "✅" or emoji == "🅱️":
                if emoji == "✅":
                    operação = "$addToSet"
                    str_operação = "bloqueado"
                    aviso = await ctx.send(content="Edite essa mensagem mencionando um user ou role (ou apenas o id) para adicionar a blacklist", reference=ctx.message)
                else:
                    operação = "$pull"
                    str_operação = "desbloqueado"
                    aviso = await ctx.send(content="Edite essa mensagem mencionando um user ou role (ou apenas o id) para remover da blacklist", reference=ctx.message)
                try:
                    _, editado = await self.bot.wait_for(
                        "message_edit",
                        timeout=120.0,
                        check=ctx_editado
                    )
                except asyncio.TimeoutError:
                    await aviso.delete()
                    await ctx.message.delete()
                    await ctx.send("Tempo limite excedido", delete_after=10)
                else:
                    if len(editado.mentions) > 0 and len(editado.role_mentions) > 0:
                        await ctx.send("Por favor, mencione uma pessoa ou um cargo por vez", delete_after=10)
                        return
                    if len(editado.mentions) == 1 and len(editado.role_mentions) == 0:
                        is_role = False
                        id_db = editado.mentions[0].id
                        nome = str(editado.mentions[0])
                    if len(editado.mentions) == 0 and len(editado.role_mentions) == 1:
                        is_role = True
                        id_db = editado.role_mentions[0].id
                        nome = str(editado.role_mentions[0])
                    if len(editado.mentions) == 0 and len(editado.role_mentions) ==0:
                        try:
                            id_db = int(editado.content)
                        except:
                            await aviso.delete()
                            await ctx.message.delete()
                            await menu_blacklist.delete()
                            await ctx.send("Por favor mencione ou envie apenas o id de um user ou role", delete_after=10)
                            return
                        else:
                            if ctx.guild.get_role(id_db) != None:
                                is_role = True
                                nome = str(ctx.guild.get_role(id_db))
                            elif ctx.guild.get_member(id_db) != None:
                                is_role = False
                                nome = str(ctx.guild.get_member(id_db))
                            else:
                                await aviso.delete()
                                await ctx.message.delete()
                                await menu_blacklist.delete()
                                await ctx.send("ID não encontrado", delete_after=10)
                                return

                    if emoji == "✅":
                        p_comando = await ctx.send("Qual comando a ser bloqueado? (envie apenas o comando na proxima mensagem)")
                    else:
                        p_comando = await ctx.send("Qual comando a ser desbloqueado? (envie apenas o comando na proxima mensagem)")
                    try:
                        msg_comando = await self.bot.wait_for(
                            "message",
                            timeout=120.0,
                            check=mesmo_user
                        )
                        comando = msg_comando.content.lower() 
                    except asyncio.TimeoutError:
                        await p_comando.delete()
                        await aviso.delete()
                        await ctx.message.delete()
                        await ctx.send("Tempo limite excedido", delete_after=10)
                    else:
                        if comando not in ctx.bot.comandos:
                            await msg_comando.delete()
                            await p_comando.delete()
                            await aviso.delete()
                            await ctx.message.delete()
                            await menu_blacklist.delete()
                            await ctx.send("Comando inválido", delete_after=10)
                            return
                        collection = ctx.bot.cluster[str(ctx.guild.id)]["blacklist"]
                        collection.update_one({"_id":id_db, "is_role":is_role}, {"$set":{"nome":nome}, operação:{"comandos":comando}}, upsert=True)
                        await ctx.send(f"Comando `{comando}` {str_operação} para: `{nome}`", delete_after=20)

                        await msg_comando.delete()
                        await p_comando.delete()
                        await aviso.delete()
                        await ctx.message.delete()
            elif emoji == "📖":
                collection = ctx.bot.cluster[str(ctx.guild.id)]["blacklist"]
                embed_lista = discord.Embed(title=f"Blacklist para servidor `{ctx.guild.name}:{ctx.guild.id}`")
                for data in collection.find():
                    comandos = "```\n"
                    for comando in data["comandos"]:
                        comandos += str(comando) + "\n"
                    comandos += "```"
                    id_db = data["_id"]
                    if data["is_role"]:
                        embed_lista.add_field(name=f"Role: {str(ctx.guild.get_role(id_db))}", value=comandos, inline=False)
                    else:
                        embed_lista.add_field(name=f"User: {str(ctx.guild.get_member(id_db))}", value=comandos, inline=False)
                await ctx.send(embed=embed_lista, delete_after=120)
                await ctx.message.delete()
            await menu_blacklist.delete()


    @commands.command(
        brief="Comandos",
        aliases=["help"],
        description="Mostra todos os comandos disponíveis"
    )
    async def comandos(self, ctx):
        comandos = discord.Embed(title="Comandos disponíveis")
        for comando in sorted(ctx.bot.commands, key=lambda x: x.cog_name):
            if comando.description in ["debug", "beta", None]:
                continue
            aliases = "Aliases: "
            if comando.aliases:
                for i, alias in enumerate(comando.aliases):
                    if i == len(comando.aliases)-1:
                        aliases += alias
                    else:
                        aliases += alias + ", "
                aliases += "\n\n"
            else:
                aliases = ""
            comandos.add_field(name=str(comando.name), value= "```" + aliases + str(comando.description) + "```", inline=False)
        await ctx.send(embed=comandos)

    @commands.command(
        brief="Testes",
        aliases=["debug"],
        description="debug"
    )
    async def testes(self, ctx):
        def ctx_editado(before, after):
            return ctx.message.id == after.id
        
        msg = await ctx.send(f"Edite sua mensagem do comando mencionando um user ou um role")
        try:
            _, editado = await self.bot.wait_for(
                "message_edit",
                timeout=60.0,
                check=ctx_editado
                )
        except asyncio.TimeoutError:
            await ctx.message.delete()
            await msg.delete()
            await ctx.send("Tempo limite excedido", delete_after=10)
        else:
            if len(editado.mentions) != 1:
                await ctx.send("Por favor, mencione um por vez", delete_after=10)
                await editado.delete()
                await msg.delete()
                return
            mention = editado.mentions[0]
            await editado.delete()
            await msg.delete()
            await ctx.send(f"Mention: {mention}")

def setup(bot):
    bot.add_cog(Default(bot))