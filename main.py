import os
import json
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import discord
from discord import app_commands

ARCHIVO_SCRIPTS = "scripts.json"

def cargar_scripts():
    if os.path.exists(ARCHIVO_SCRIPTS):
        try:
            with open(ARCHIVO_SCRIPTS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_en_disco(data):
    with open(ARCHIVO_SCRIPTS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sha_bot is alive!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

intents = discord.Intents.default()
intents.members = True

class MiBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.scripts_guardados = cargar_scripts()

    async def setup_hook(self):
        await self.tree.sync()
        print("¡Comandos de barra sincronizados con éxito!")

bot = MiBot()

@bot.event
async def on_ready():
    print(f'¡Conectado como {bot.user}!')

def es_superior_al_bot(interaction: discord.Interaction):
    if interaction.user == interaction.guild.owner:
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    me = interaction.guild.me
    if not me or not me.roles:
        return False
    rol_mas_alto_del_bot = max(me.roles, key=lambda r: r.position)
    for role in interaction.user.roles:
        if role.position > rol_mas_alto_del_bot.position:
            return True
    return False

# --- COMANDO /meter ---
@bot.tree.command(name='meter', description='Añade un script (Solo rangos por encima del bot)')
@app_commands.describe(nombre='Nombre del juego o categoría (ej: adoptme)', texto='El contenido o script que quieres añadir')
async def meter(interaction: discord.Interaction, nombre: str, texto: str):
    if not es_superior_al_bot(interaction):
        await interaction.response.send_message("❌ Solo los usuarios con un rango superior al del bot pueden usar este comando.", ephemeral=True)
        return

    clave = nombre.lower().strip()
    if clave not in bot.scripts_guardados:
        bot.scripts_guardados[clave] = []
    
    bot.scripts_guardados[clave].append(texto)
    guardar_en_disco(bot.scripts_guardados)
    
    total_guardados = len(bot.scripts_guardados[clave])
    await interaction.response.send_message(f'✅ ¡Script añadido a **"{clave}"**! (Total en esta categoría: {total_guardados})')

# --- MENÚ DESPLEGABLE PARA VER (/script) ---
class SelectorDeScripts(discord.ui.View):
    def __init__(self, lista_scripts: list, nombre_categoria: str):
        super().__init__(timeout=60)
        opciones = []
        for index, texto in enumerate(lista_scripts):
            descripcion_corta = texto[:50] + "..." if len(texto) > 50 else texto
            opciones.append(discord.SelectOption(label=f"Opción {index + 1}", description=descripcion_corta, value=str(index)))
        self.add_item(MenuDesplegable(opciones, nombre_categoria, lista_scripts))

class MenuDesplegable(discord.ui.Select):
    def __init__(self, opciones, nombre_categoria, lista_scripts):
        self.lista_scripts = lista_scripts
        self.nombre_categoria = nombre_categoria
        super().__init__(placeholder="Elige qué versión o script quieres ver...", min_values=1, max_values=1, options=opciones)

    async def callback(self, interaction: discord.Interaction):
        indice_elegido = int(self.values[0])
        texto_seleccionado = self.lista_scripts[indice_elegido]
        await interaction.response.send_message(f'📤 **Script `{self.nombre_categoria}` (Opción {indice_elegido + 1})**:\n{texto_seleccionado}')

# --- COMANDO /script ---
@bot.tree.command(name='script', description='Busca una categoría y elige entre los scripts guardados')
@app_commands.describe(nombre='El nombre de la categoría que quieres buscar (ej: adoptme)')
async def script(interaction: discord.Interaction, nombre: str):
    clave = nombre.lower().strip()
    if clave in bot.scripts_guardados and len(bot.scripts_guardados[clave]) > 0:
        lista_scripts = bot.scripts_guardados[clave]
        if len(lista_scripts) == 1:
            await interaction.response.send_message(f'📤 **Script para `{clave}`**:\n{lista_scripts[0]}')
        else:
            view = SelectorDeScripts(lista_scripts, clave)
            await interaction.response.send_message(f'🔍 Hay **{len(lista_scripts)} scripts** guardados bajo **"{clave}"**. Selecciona uno en el menú de abajo:', view=view, ephemeral=True)
    else:
        await interaction.response.send_message(f'❌ No se encontró ningún script guardado con el nombre **"{clave}"**.', ephemeral=True)

# --- MENÚ DESPLEGABLE PARA BORRAR (/borar) ---
class SelectorParaBorrar(discord.ui.View):
    def __init__(self, lista_scripts: list, nombre_categoria: str, bot_instance):
        super().__init__(timeout=60)
        opciones = []
        for index, texto in enumerate(lista_scripts):
            descripcion_corta = texto[:50] + "..." if len(texto) > 50 else texto
            opciones.append(discord.SelectOption(label=f"Opción {index + 1}", description=descripcion_corta, value=str(index)))
        self.add_item(MenuBorrarSelect(opciones, nombre_categoria, lista_scripts, bot_instance))

class MenuBorrarSelect(discord.ui.Select):
    def __init__(self, opciones, nombre_categoria, lista_scripts, bot_instance):
        self.lista_scripts = lista_scripts
        self.nombre_categoria = nombre_categoria
        self.bot_instance = bot_instance
        super().__init__(placeholder="Elige qué script quieres eliminar...", min_values=1, max_values=1, options=opciones)

    async def callback(self, interaction: discord.Interaction):
        indice_elegido = int(self.values[0])
        script_eliminado = self.lista_scripts.pop(indice_elegido)
        
        if len(self.lista_scripts) == 0:
            del self.bot_instance.scripts_guardados[self.nombre_categoria]
        else:
            self.bot_instance.scripts_guardados[self.nombre_categoria] = self.lista_scripts
        
        guardar_en_disco(self.bot_instance.scripts_guardados)
        await interaction.response.send_message(f'🗑️ **Script eliminado con éxito** de la categoría `{self.nombre_categoria}` (Opción {indice_elegido + 1}).', ephemeral=True)

@bot.tree.command(name='borar', description='Elimina un script específico (Solo rangos por encima del bot)')
@app_commands.describe(nombre='El nombre de la categoría del script a borrar (ej: adoptme)')
async def borar(interaction: discord.Interaction, nombre: str):
    if not es_superior_al_bot(interaction):
        await interaction.response.send_message("❌ Solo los usuarios con un rango superior al del bot pueden usar este comando.", ephemeral=True)
        return

    clave = nombre.lower().strip()
    if clave in bot.scripts_guardados and len(bot.scripts_guardados[clave]) > 0:
        lista_scripts = bot.scripts_guardados[clave]
        view = SelectorParaBorrar(lista_scripts, clave, bot)
        await interaction.response.send_message(f'🗑️ Selecciona el script que deseas **borrar** de la categoría **"{clave}"**:', view=view, ephemeral=True)
    else:
        await interaction.response.send_message(f'❌ No se encontró ningún script guardado bajo el nombre **"{clave}"** para borrar.', ephemeral=True)

# --- COMANDO /buscar (ScriptBlox con código directo) ---
class SelectorResultadosScriptBlox(discord.ui.View):
    def __init__(self, scripts_encontrados):
        super().__init__(timeout=60)
        opciones = []
        for index, item in enumerate(scripts_encontrados[:25]):
            titulo = item.get("title", "Sin título")[:95]
            opciones.append(discord.SelectOption(label=titulo[:100], value=str(index)))
        self.scripts_encontrados = scripts_encontrados
        self.add_item(MenuSeleccionScriptBlox(opciones, scripts_encontrados))

class MenuSeleccionScriptBlox(discord.ui.Select):
    def __init__(self, opciones, scripts_encontrados):
        self.scripts_encontrados = scripts_encontrados
        super().__init__(placeholder="Elige un script para ver su código...", min_values=1, max_values=1, options=opciones)

    async def callback(self, interaction: discord.Interaction):
        indice = int(self.values[0])
        script_seleccionado = self.scripts_encontrados[indice]
        
        titulo = script_seleccionado.get("title", "Script")
        codigo_script = script_seleccionado.get("script", "No se encontró el código o el script está cifrado.")
        
        if len(codigo_script) > 1950:
            codigo_script = codigo_script[:1950] + "\n-- [Código recortado por ser demasiado largo]"

        await interaction.response.send_message(
            f'📜 **{titulo}**:\n```lua\n{codigo_script}\n```', 
            ephemeral=True
        )

@bot.tree.command(name='buscar', description='Busca scripts en ScriptBlox y muestra el código directamente')
@app_commands.describe(query='Nombre del juego o script que quieres buscar (ej: bloxfruit)')
async def buscar(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)
    
    url = f"https://scriptblox.com/api/script/search?q={query}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    scripts = data.get("result", {}).get("scripts", [])
                    
                    if not scripts:
                        await interaction.followup.send(f'❌ No se han encontrado resultados en ScriptBlox para **"{query}"**.')
                        return
                    
                    view = SelectorResultadosScriptBlox(scripts)
                    await interaction.followup.send(f'🔍 Resultados encontrados en ScriptBlox para **"{query}"**. Selecciona uno:', view=view)
                else:
                    await interaction.followup.send('❌ Hubo un error al conectar con la página de ScriptBlox.')
        except Exception as e:
            await interaction.followup.send(f'❌ Ocurrió un error inesperado al realizar la búsqueda.')

bot.run(os.getenv('DISCORD_TOKEN'))
