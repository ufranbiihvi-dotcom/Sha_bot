import discord
from discord import app_commands

intents = discord.Intents.default()
intents.members = True

class MiBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        # Diccionario para guardar varios textos con su nombre clave (ej: {"adoptme": "texto...", "bloxfruits": "texto..."})
        self.scripts_guardados = {}

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Comandos de barra sincronizados con éxito!")

bot = MiBot()

@bot.event
async def on_ready():
    print(f'¡Conectado como {bot.user} desde el móvil!')

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

    # Guardamos el texto usando el nombre en minúsculas para evitar confusiones
    clave = nombre.lower().strip()
    bot.scripts_guardados[clave] = texto
    await interaction.response.send_message(f'✅ ¡Script guardado con éxito bajo el nombre **"{clave}"**!')

# --- COMANDO DE BARRA /script ---
@bot.tree.command(name='script', description='Busca y muestra un script guardado por su nombre')
@app_commands.describe(nombre='El nombre del script que quieres buscar (ej: adoptme)')
async def script(interaction: discord.Interaction, nombre: str):
    clave = nombre.lower().strip()
    
    # Verificamos si existe el script guardado con ese nombre
    if clave in bot.scripts_guardados:
        contenido = bot.scripts_guardados[clave]
        await interaction.response.send_message(f'📤 **Script para `{clave}`**:\n{contenido}')
    else:
        await interaction.response.send_message(f'❌ No se encontró ningún script guardado con el nombre **"{clave}"**.', ephemeral=True)

# PEGA TU TOKEN AQUÍ ENTRE LAS COMILLAS
bot.run('MTU2NjU0NjI5Nzc2OTQzNTMxNg.GO0fox.MNtFqMAXqiMNxa_iqzA5Tb2eTU6n-GIWMRNfO0')
