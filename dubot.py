# Bibliotecas padrão
import os
import json
import sys

# Bibliotecas discord
import discord
from discord.ext import commands

# Cwd
from pathlib import Path

# Bibliotecas para o banco de dados
import pymongo
from pymongo import MongoClient

from cogs._blacklist import Blacklisted

def get_prefix(bot, message):
    if isinstance(message.channel, discord.DMChannel):
        return commands.when_mentioned_or("edu.")(bot, message)
    config = bot.cluster[str(message.guild.id)]["config"].find_one({"_id":"config_servidor"})
    prefix = config["prefix"]
    return commands.when_mentioned_or(prefix)(bot, message)

# Função que inicializa um novo servidor no banco de dados
def init_bd(id_servidor, nome_servidor):
    collection = bot.cluster["global"]["servidores"]
    if collection.update_one({"_id":id_servidor}, {"$set":{"_id":id_servidor, "nome_servidor":nome_servidor}}, upsert=True).upserted_id != None:
        # Novo servidor
        collection = bot.cluster[str(id_servidor)]["config"]
        collection.insert_one({"_id":"config_servidor", "prefix":"edu."})
        return
    # Servidor ja existente
    return

print(f"Versão discord.py: {discord.__version__}")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, help_command=None, intents=intents)

# Current working directory
bot.cwd = str(Path(__file__).parents[0])
segredos = json.load(open(bot.cwd + "/segredos.json"))

if __name__ == "__main__":
    try:
        if str(sys.argv[1] == "beta"):
            print("Versão Beta - Developer")
            bot.token = segredos["token-beta"]
            bot.cluster = MongoClient(segredos["url-mongodb-beta"])
    except:
        bot.token = segredos["token"]
        bot.cluster = MongoClient(segredos["url-mongodb"])
print("Cluster conectado!")

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    print("Bot[Status] = Online")

    # Adiciona possiveis novos servidores ao banco de dados (servidor adicionados enquanto o bot estava offline)
    for guild in bot.guilds:
        init_bd(guild.id, guild.name)
    print("Servidores conectados atualizado")

# Filtro de mensagem
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Executa a mensagem
    await bot.process_commands(message)

# Adiciona o novo servidor conectado ao banco de dados
@bot.event
async def on_guild_join(guild):
    init_bd(guild.id, guild.name)
    print(f"Novo servidor conectado: {guild.name}")

# Lê e carrega todos os cogs (que não iniciam com underscore)
# Se esta rodando o arquivo, e não sendo importado nem algo do tipo
if __name__ == "__main__":
    # Passa por todos os arquivos dentro da pasta cogs
    for file in os.listdir(bot.cwd + "/cogs"):
        # Caso seja um arquivo python, carrega como cog (usa underscore pra desativar arquivos e não carrega-los)
        if file.endswith(".py") and not file.startswith("_"):
            # Carrega a extensão, com o nome do arquivo menos ".py"
            bot.load_extension(f"cogs.{file[:-3]}")

bot.comandos = []
for cog in bot.cogs:
    for comando in bot.cogs[cog].get_commands():
        bot.comandos += [comando.name.lower()] + comando.aliases

print(f"Comandos do bot: {bot.comandos}")

# Filtro de erros
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.send("Esse comando não está ativado para mensagem privada")
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("Você não tem permissão para usar esse comando")
    elif isinstance(error, Blacklisted):
        await ctx.send("Você não pode usar esse comando")
    elif isinstance(error, commands.errors.MaxConcurrencyReached):
        if error.per == commands.BucketType.user:
            await ctx.send("Esse comando só é permitido um por vez por usuário")

bot.run(bot.token)