import os
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')


intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

queue = []
inactive_users = set()
queue_message = None
notify_message = None

def sort_queue():
    global queue
    queue.sort(key=lambda member: member.display_name)

@tree.command(name='iniciar', description='Inicia a fila do Bot Bastão')
async def iniciar(interaction: discord.Interaction):
    global queue_message
    print(f"Comando iniciar chamado por {interaction.user}")
    queue.clear()
    for member in interaction.channel.members:
        print(f"Verificando membro: {member.display_name} - Status: {member.status} - É bot: {member.bot}")
        if (member.status in [discord.Status.online, discord.Status.idle]) and not member.bot:
            queue.append(member)

    sort_queue()
    await update_queue_message(interaction.channel)
    print(f"**#Fila atualizada#**: {[member.display_name for member in queue]}")
    await notify_first_user(interaction.channel)
    await interaction.response.send_message("Fila iniciada.", ephemeral=True)
    return queue_message

@tree.command(name='show_queue', description='Mostra a fila atual')
async def show_queue(interaction: discord.Interaction):
    await update_queue_message(interaction.channel)
    print(f"Fila atual: {[member.display_name for member in queue]}")
    await interaction.response.send_message("Fila exibida.", ephemeral=True)

@tree.command(name='remove', description='Remove um membro da fila')
async def remove(interaction: discord.Interaction, member: discord.Member):
    print(f"Comando remove chamado por {interaction.user} para remover {member.display_name.upper()}")
    if member in queue:
        queue.remove(member)
        await interaction.response.send_message(f"{member.display_name} foi removido da fila.", ephemeral=True)
    else:
        await interaction.response.send_message(f"{member.display_name} não está na fila.", ephemeral=True)
    print(f"Fila atualizada: {[member.display_name for member in queue]}")
    await update_queue_message(interaction.channel)
    await notify_first_user(interaction.channel)
    return queue_message

async def pass_baton(interaction: discord.Interaction):
    user = interaction.user
    print(f"Interação pass_baton chamada por {user}")
    if queue and queue[0] == user:
        queue.append(queue.pop(0))
        await interaction.response.send_message(f"{user.display_name} passou o bastão.", ephemeral=True)
    else:
        await interaction.response.send_message("Você não está no início da fila.", ephemeral=True)
    print(f"Fila atualizada: {[member.display_name for member in queue]}")
    await update_queue_message(interaction.channel)
    await notify_first_user(interaction.channel)
    return queue_message

async def leave_queue(interaction: discord.Interaction):
    user = interaction.user
    print(f"Interação leave_queue chamada por {user}")
    if user in queue:
        queue.remove(user)
        await interaction.response.send_message(f"{user.display_name} saiu da fila.", ephemeral=True)
    else:
        await interaction.response.send_message("Você não está na fila.", ephemeral=True)
    print(f"Fila atualizada: {[member.display_name for member in queue]}")
    await update_queue_message(interaction.channel)
    await notify_first_user(interaction.channel)
    return queue_message

async def indisponivel(interaction: discord.Interaction):
    user = interaction.user
    print(f"Interação indisponivel chamada por {user}")
    if user in inactive_users:
        inactive_users.remove(user)
        await interaction.response.send_message(f"{user.display_name} saiu do indisponível.", ephemeral=True)
    else:
        inactive_users.add(user)
        await interaction.response.send_message(f"{user.display_name} está em indisponível.", ephemeral=True)
    
    print(f"Usuários inativos: {[member.display_name for member in inactive_users]}")
    await update_queue_message(interaction.channel)
    await notify_first_user(interaction.channel)
    return queue_message

async def update_queue_message(channel, new_member=None):
    global queue_message
    if queue_message:
        await queue_message.delete()
    if not queue:
        await channel.send("A fila está vazia.")
    else:
        if queue[0] in inactive_users:
            await channel.send(f"{queue[0]} estava em indisponível e foi movido para o final da fila.")
            queue.append(queue.pop(0))
        if new_member:
            sorted_queue = sorted(queue + [new_member], key=lambda member: member.display_name)
            for i, member in enumerate(sorted_queue):
                if member == new_member:
                    if i == 0:
                        insert_position = queue.index(sorted_queue[-1]) + 1 if sorted_queue[-1] in queue else len(queue)
                        queue.insert(insert_position, new_member)
                    else:
                        insert_position = queue.index(sorted_queue[i - 1]) + 1 if sorted_queue[i - 1] in queue else len(queue)
                        queue.insert(insert_position, new_member)
                    break
            print(f"queue pos insert: {[member.display_name for member in queue]}")
        msg = "\n".join([f"{i+1}. {member.display_name} - indisponível" if member in inactive_users else f"{i+1}. {member.display_name}" for i, member in enumerate(queue)])
        queue_message = await channel.send(f"**# Fila Atual #**:\n{msg}")
        view = QueueView()
        queue_message = await channel.send("Gerencie a fila usando os botões abaixo:", view=view)

async def notify_first_user(channel):
    global notify_message
    if queue:
        first_user = queue[0]
        if notify_message:
            await notify_message.delete()
        notify_message = await channel.send(f"**# {first_user.mention}, você é o próximo na fila! #**" )

async def iniciar_or_leave_queue(interaction: discord.Interaction):
    user = interaction.user
    print(f"Interação iniciar_or_leave_queue chamada por {user}")
    if user in queue:
        queue.remove(user)
        await interaction.response.send_message(f"{user.display_name} saiu da fila.", ephemeral=True)
        await update_queue_message(interaction.channel)
    else:
        await interaction.response.send_message(f"{user.display_name} entrou na fila.", ephemeral=True)
        await update_queue_message(interaction.channel, user)
    await notify_first_user(interaction.channel)

class QueueView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction):
        return True

    @discord.ui.button(label="Passar Bastão", style=discord.ButtonStyle.success, custom_id="pass_baton_2")
    async def pass_baton_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await pass_baton(interaction)

    @discord.ui.button(label="Entrar / Sair da fila", style=discord.ButtonStyle.red, custom_id="iniciar_or_leave_queue")
    async def iniciar_or_leave_queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await iniciar_or_leave_queue(interaction)

    @discord.ui.button(label="Entrar / Sair do indisponível", style=discord.ButtonStyle.blurple, custom_id="indisponivel")
    async def indisponivel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await indisponivel(interaction)

@bot.event
async def on_ready():
    await register_slash_commands()
    print(f'Bot {bot.user} está online e comandos sincronizados no servidor.')

async def register_slash_commands():
    url = f"https://discord.com/api/v9/applications/{bot.user.id}/guilds/{GUILD_ID}/commands"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    commands = [
        {
            "name": "iniciar",
            "description": "Inicia a fila do Bot Bastão"
        },
        {
            "name": "show_queue",
            "description": "Mostra a fila atual"
        },
        {
            "name": "remove",
            "description": "Remove um membro da fila",
            "options": [
                {
                    "name": "member",
                    "description": "O membro a ser removido da fila",
                    "type": 6,
                    "required": True
                }
            ]
        }
    ]

    for command in commands:
        response = requests.post(url, headers=headers, json=command)
        print(response.json())

bot.run(TOKEN)
