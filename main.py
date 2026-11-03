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
        # Diccionario que guardará una LISTA de textos por cada nombre: {"adoptme": ["texto a", "hola"]}
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
@bot.tree.command(name='meter', description='Añade un script a una categoría (Guarda varios bajo el mismo nombre)')
@app_commands.describe(nombre='Nombre del juego o categoría (ej: adoptme)', texto='El contenido o script que quieres añadir')
async def meter(interaction: discord.Interaction, nombre: str, texto: str):
    if not es_superior_a_helper(interaction):
        await interaction.response.send_message("❌ Solo los rangos superiores a **Helper** pueden usar este comando.", ephemeral=True)
        return

    clave = nombre.lower().strip()
    
    # Si la categoría no existe, la creamos como una lista vacía
    if clave not in bot.scripts_guardados:
        bot.scripts_guardados[clave] = []
    
    # Añadimos el nuevo texto a la lista de esa categoría
    bot.scripts_guardados[clave].append(texto)
    
    total_guardados = len(bot.scripts_guardados[clave])
    await interaction.response.send_message(f'✅ ¡Script añadido a **"{clave}"**! (Total en esta categoría: {total_guardados})')

# --- CLASE PARA EL MENÚ DESPLEGABLE (SELECT VIEW) ---
class SelectorDeScripts(discord.ui.View):
    def __init__(self, lista_scripts: list, nombre_categoria: str):
        super().__init__(timeout=60)
        
        # Creamos opciones en el menú desplegable para cada texto guardado
        opciones = []
        for index, texto in enumerate(lista_scripts):
            # Recortamos el texto si es muy largo para que entre bonito en la opción del menú
            descripcion_corta = texto[:50] + "..." if len(texto) > 50 else texto
            opciones.append(
                discord.SelectOption(
                    label=f"Opción {index + 1}", 
                    description=descripcion_corta, 
                    value=str(index)
                )
            )

        # Añadimos el selector al mensaje
        self.add_item(MenuDesplegable(opciones, nombre_categoria, lista_scripts))

class MenuDesplegable(discord.ui.Select):
    def __init__(self, opciones, nombre_categoria, lista_scripts):
        self.lista_scripts = lista_scripts
        self.nombre_categoria = nombre_categoria
        super().__init__(placeholder="Elige qué versión o script quieres ver...", min_values=1, max_values=1, options=opciones)

    async def callback(self, interaction: discord.Interaction):
        # Obtenemos el índice que eligió el usuario en el menú
        indice_elegido = int(self.values[0])
        texto_seleccionado = self.lista_scripts[indice_elegido]
        
        await interaction.response.send_message(f'📤 **Script `{self.nombre_categoria}` (Opción {indice_elegido + 1})**:\n{texto_seleccionado}')

# --- COMANDO DE BARRA /script ---
@bot.tree.command(name='script', description='Busca una categoría y elige entre los scripts guardados')
@app_commands.describe(nombre='El nombre de la categoría que quieres buscar (ej: adoptme)')
async def script(interaction: discord.Interaction, nombre: str):
    clave = nombre.lower().strip()

    # Verificamos si existe la categoría
    if clave in bot.scripts_guardados and len(bot.scripts_guardados[clave]) > 0:
        lista_scripts = bot.scripts_guardados[clave]
        
        # Si solo hay uno, lo mandamos directamente
        if len(lista_scripts) == 1:
            await interaction.response.send_message(f'📤 **Script para `{clave}`**:\n{lista_scripts[0]}')
        else:
            # Si hay varios, mandamos un menú desplegable interactivo para que elija
            view = SelectorDeScripts(lista_scripts, clave)
            await interaction.response.send_message(f'🔍 Hay **{len(lista_scripts)} scripts** guardados bajo **"{clave}"**. Selecciona uno en el menú de abajo:', view=view, ephemeral=True)
    else:
        await interaction.response.send_message(f'❌ No se encontró ningún script guardado con el nombre **"{clave}"**.', ephemeral=True)

# Token seguro obtenido de las variables de entorno de Render
bot.run(os.getenv('DISCORD_TOKEN'))
