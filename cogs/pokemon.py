import discord
from discord.ext import commands

import json
import requests
from random import randrange

# Importa a função predicate do mod blacklist, que retorna True ou False, usado como decorator
from cogs._blacklist import is_blacklisted

class Pokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Módulo Pokemon carregado...")

    def get_pokemon(self):
        url_api = "https://pokeapi.co/api/v2/pokemon/" + str(randrange(1,494))
        response = requests.get(url_api)
        json_data = json.loads(response.text)
        poke = json_data["name"].capitalize()
        url_imagem = json_data["sprites"]["versions"]["generation-v"]["black-white"]["animated"]["front_default"]
        url_icon = json_data["sprites"]["other"]["official-artwork"]["front_default"]
        poke_type = json_data["types"][0]["type"]["name"]
        #poke_id = json_data["id"]
        return poke, poke_type, url_imagem, url_icon

    @commands.command(
        brief="Poke, Pokemon",
        aliases=["pokemon"],
        description="Gif aleatório de um pokemon entre 1 à 493 na pokedex"
    )
    @is_blacklisted()
    async def poke(self, ctx):
        pokemon, tipo_pokemon, url_imagem_pokemon, url_icon_pokemon = self.get_pokemon()
        cores = """{
            "normal":7171406,
            "fire":10244895,
            "fighting":8199962,
            "water":4480668,
            "flying":7167644,
            "grass":5145140,
            "poison":6826600,
            "electric":10585887,
            "ground":9600324,
            "psychic":10565977,
            "rock":7890980,
            "ice":6524301,
            "bug":7174165,
            "dragon":4793505,
            "ghost":4798819,
            "dark":4798767,
            "steel":7895175,
            "fairy":10183792
        }"""
        json_cores = json.loads(cores)
        embedPoke = discord.Embed(colour=int(json_cores[tipo_pokemon])).set_image(url=url_imagem_pokemon).set_author(name=pokemon,icon_url=url_icon_pokemon)
        await ctx.send(embed=embedPoke)

def setup(bot):
    bot.add_cog(Pokemon(bot))