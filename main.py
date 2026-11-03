import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import discord
from discord import app_commands

# Servidor web falso para mantener contento a Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sha_bot is alive!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Arranca el servidor web en segundo plano
threading.Thread(target=run_server, daemon=True).start()

intents = discord.Intents.default()
intents.members = True

class MiBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        # Diccionario para guardar varios textos con su nombre clave
        self.scripts_guardados = {}

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Comandos de barra sincronizados con éxito!")

bot = MiBot()

@bot.event
async def on_ready():
    print(f'¡Conectado como {bot.user}!')

# Función para comprobar si el usuario tiene un rango superior a "Helper"
def es_superior_a_helper(interaction: discord.Interaction):
    if interaction.user == interaction.guild.owner:
        return True

    helper_role = discord.utils.get(interaction.guild.roles, name="Helper")

    if not helper_role:
        return interaction.user.guild_permissions.administrator

    for role in interaction.user.roles:
        if role.position > helper_role.position:
            return True

    return False

# --- COMANDO DE BARRA /meter ---
@bot.tree.command(name='meter', description='Guarda un script con un nombre (Solo rangos superiores a Helper)')
@app_commands.describe(nombre='Nombre del juego o categoría (ej: adoptme)', texto='El contenido o script que quieres guardar')
async def meter(interaction: discord.Interaction, nombre: str, texto: str):
    if not es_superior_a_helper(interaction):
        await interaction.response.send_message("❌ Solo los rangos superiores a **Helper** pueden usar este comando.", ephemeral=True)
        return

    clave = nombre.lower().strip()
    bot.scripts_guardados[clave] = texto
    await interaction.response.send_message(f'✅ ¡Script guardado con éxito bajo el nombre **"{clave}"**!')

# --- COMANDO DE BARRA /script ---
@bot.tree.command(name='script', description='Busca y muestra un script guardado por su nombre')
@app_commands.describe(nombre='El nombre del script que quieres buscar (ej: adoptme)')
async def script(interaction: discord.Interaction, nombre: str):
    clave = nombre.lower().strip()

    if clave in bot.scripts_guardados:
        contenido = bot.scripts_guardados[clave]
        await interaction.response.send_message(f'📤 **Script para `{clave}`**:\n{contenido}')
    else:
        await interaction.response.send_message(f'❌ No se encontró ningún script guardado con el nombre **"{clave}"**.', ephemeral=True)

# Token seguro obtenido de las variables de entorno de Render
bot.run(os.getenv('DISCORD_TOKEN'))
