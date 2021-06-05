import discord
from discord.ext import commands

class Blacklisted(commands.CheckFailure):
    pass

def predicate(ctx):
    if ctx.guild != None:
        # Override para administrador do servidor nunca ser bloqueado pela blacklist
        if ctx.message.channel.permissions_for(ctx.message.author).administrator:
            return True
        
        comandos = [ctx.command.name.lower()] + ctx.command.aliases
        collection = ctx.bot.cluster[str(ctx.guild.id)]["blacklist"]
        
        role_ban = False
        for role in ctx.author.roles:
            if collection.find_one({"_id":role.id, "is_role":True, "comandos":{"$in":comandos}}) != None:
                role_ban = True
                break
            pass

        if collection.find_one({"_id":ctx.author.id, "is_role":False, "comandos":{"$in":comandos}}) != None or role_ban:
            raise Blacklisted()
    return True

def is_blacklisted():
    return commands.check(predicate)