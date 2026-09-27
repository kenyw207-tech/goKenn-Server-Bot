import discord
from discord import app_commands
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

STRUCTURE = [
    ('👋・INÍCIO', [('text','📢・avisos'), ('text','🎭・escolha-seus-jogos')]),
    ('💬・GERAL', [('text','💬・chat-geral'), ('text','📸・clips-e-prints'), ('text','😂・memes'), ('text','🤖・comandos')]),
    ('🚗・ROCKET LEAGUE', [('voice','Rocket League 1'), ('voice','Rocket League 2'), ('voice','🏆・Ranked 1'), ('voice','🏆・Ranked 2')]),
    ('🪖・WARZONE', [('voice','Warzone 1'), ('voice','Warzone 2'), ('voice','🏆・Ranked 1'), ('voice','🏆・Ranked 2')]),
    ('🎖️・BATTLEFIELD', [('voice','Battlefield 1'), ('voice','Battlefield 2'), ('voice','Battlefield 3'), ('voice','Battlefield 4')]),
    ('🎵・MÚSICA', [('text','🎶・pedir-musica'), ('voice','Música')]),
]

ROLE_SPECS = [
    ('👑 Founder', discord.Permissions(administrator=True), discord.Colour.gold()),
    ('🛡️ Administrador', discord.Permissions(administrator=True), discord.Colour.red()),
    ('🎮 Membro', discord.Permissions.none(), discord.Colour.light_grey()),
    ('🚗 Rocket League', discord.Permissions.none(), discord.Colour.blue()),
    ('🪖 Warzone', discord.Permissions.none(), discord.Colour.green()),
    ('🎖️ Battlefield', discord.Permissions.none(), discord.Colour.orange()),
]

async def toggle_game_role(interaction: discord.Interaction, role_name: str):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message('Use este botão dentro do servidor.', ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if role is None:
        await interaction.response.send_message('Esse cargo ainda não existe.', ephemeral=True)
        return
    try:
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role, reason='Painel de escolha de jogos')
            await interaction.response.send_message(f'➖ Cargo {role.name} removido.', ephemeral=True)
        else:
            await interaction.user.add_roles(role, reason='Painel de escolha de jogos')
            await interaction.response.send_message(f'✅ Cargo {role.name} adicionado.', ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message('Não consegui alterar o cargo. Coloque o cargo do goKenn Server Bot acima dos cargos de jogos.', ephemeral=True)

class GameRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Rocket League', emoji='🚗', style=discord.ButtonStyle.primary, custom_id='game_role:rocket')
    async def rocket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await toggle_game_role(interaction, '🚗 Rocket League')

    @discord.ui.button(label='Warzone', emoji='🪖', style=discord.ButtonStyle.primary, custom_id='game_role:warzone')
    async def warzone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await toggle_game_role(interaction, '🪖 Warzone')

    @discord.ui.button(label='Battlefield', emoji='🎖️', style=discord.ButtonStyle.primary, custom_id='game_role:battlefield')
    async def battlefield(self, interaction: discord.Interaction, button: discord.ui.Button):
        await toggle_game_role(interaction, '🎖️ Battlefield')

@bot.event
async def on_member_join(member: discord.Member):
    role = discord.utils.get(member.guild.roles, name='🎮 Membro')
    if role:
        try:
            await member.add_roles(role, reason='Cargo automático de membro')
        except discord.Forbidden:
            pass
    channel = discord.utils.get(member.guild.text_channels, name='💬・chat-geral')
    if channel:
        try:
            await channel.send(f'👋 Bem-vindo(a), {member.mention}! Escolha seus jogos em <#{discord.utils.get(member.guild.text_channels, name="🎭・escolha-seus-jogos").id}>' if discord.utils.get(member.guild.text_channels, name='🎭・escolha-seus-jogos') else f'👋 Bem-vindo(a), {member.mention}!')
        except discord.Forbidden:
            pass

@bot.event
async def on_ready():
    bot.add_view(GameRoleView())
    total = 0
    # Registra os comandos diretamente em cada servidor para aparecerem imediatamente.
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            total += len(synced)
            print(f'Comandos sincronizados no servidor {guild.name}: {len(synced)}')
        except Exception as e:
            print(f'Erro ao sincronizar no servidor {guild.name}: {e}')
    # Remove as cópias globais antigas para acabar com comandos duplicados.
    try:
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print('Comandos globais antigos removidos.')
    except Exception as e:
        print(f'Aviso ao limpar comandos globais: {e}')
    print(f'Total de comandos sincronizados localmente: {total}')
    print(f'Bot online como {bot.user}')
    print('Comandos: /montar-servidor, /configurar-cargos e /finalizar-servidor')

@bot.tree.command(name='montar-servidor', description='Cria a estrutura gamer aprovada no servidor.')
@app_commands.checks.has_permissions(administrator=True)
async def montar_servidor(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message('Use este comando dentro do servidor.', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild
    created, skipped = [], []
    for category_name, channels in STRUCTURE:
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            category = await guild.create_category(category_name, reason='Montagem automática do servidor')
            created.append(category_name)
        else:
            skipped.append(category_name)
        for kind, channel_name in channels:
            pool = category.text_channels if kind == 'text' else category.voice_channels
            if discord.utils.get(pool, name=channel_name) is None:
                if kind == 'text':
                    await guild.create_text_channel(channel_name, category=category, reason='Montagem automática do servidor')
                else:
                    await guild.create_voice_channel(channel_name, category=category, reason='Montagem automática do servidor')
                created.append(channel_name)
            else:
                skipped.append(channel_name)
    await interaction.followup.send(f'✅ Estrutura concluída. Criados: {len(created)}. Já existentes: {len(skipped)}.', ephemeral=True)

@bot.tree.command(name='configurar-cargos', description='Cria os cargos e publica o painel de escolha de jogos.')
@app_commands.checks.has_permissions(administrator=True)
async def configurar_cargos(interaction: discord.Interaction):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message('Use este comando dentro do servidor.', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild
    created = []
    for role_name, permissions, colour in ROLE_SPECS:
        role = discord.utils.get(guild.roles, name=role_name)
        if role is None:
            role = await guild.create_role(name=role_name, permissions=permissions, colour=colour, reason='Configuração automática de cargos')
            created.append(role_name)
        else:
            try:
                await role.edit(permissions=permissions, colour=colour, reason='Atualização automática de cargos')
            except discord.Forbidden:
                pass

    founder = discord.utils.get(guild.roles, name='👑 Founder')
    if founder and founder not in interaction.user.roles:
        try:
            await interaction.user.add_roles(founder, reason='Usuário que executou /configurar-cargos')
        except discord.Forbidden:
            pass

    channel = discord.utils.get(guild.text_channels, name='🎭・escolha-seus-jogos')
    if channel is None:
        await interaction.followup.send('Cargos criados, mas não encontrei o canal 🎭・escolha-seus-jogos.', ephemeral=True)
        return

    embed = discord.Embed(title='🎮 Escolha seus jogos', description='Clique nos botões para adicionar ou remover seus cargos. Você pode escolher mais de um jogo.')
    embed.add_field(name='🚗 Rocket League', value='Receba o cargo de Rocket League.', inline=False)
    embed.add_field(name='🪖 Warzone', value='Receba o cargo de Warzone.', inline=False)
    embed.add_field(name='🎖️ Battlefield', value='Receba o cargo de Battlefield.', inline=False)
    await channel.send(embed=embed, view=GameRoleView())
    await interaction.followup.send(f'✅ Cargos configurados. Novos cargos: {len(created)}. Painel publicado em {channel.mention}.', ephemeral=True)

@bot.tree.command(name='finalizar-servidor', description='Aplica permissões, cores, cargo automático e acabamento final.')
@app_commands.checks.has_permissions(administrator=True)
async def finalizar_servidor(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message('Use este comando dentro do servidor.', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild

    # Cria/atualiza cargos e cores.
    for role_name, permissions, colour in ROLE_SPECS:
        role = discord.utils.get(guild.roles, name=role_name)
        if role is None:
            await guild.create_role(name=role_name, permissions=permissions, colour=colour, reason='Finalização do servidor')
        else:
            try:
                await role.edit(permissions=permissions, colour=colour, reason='Finalização do servidor')
            except discord.Forbidden:
                pass

    founder = discord.utils.get(guild.roles, name='👑 Founder')
    admin = discord.utils.get(guild.roles, name='🛡️ Administrador')
    bot_member = guild.me

    # Avisos: membros leem, Founder/Admin escrevem.
    avisos = discord.utils.get(guild.text_channels, name='📢・avisos')
    if avisos:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True),
        }
        if founder: overwrites[founder] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        if admin: overwrites[admin] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        if bot_member: overwrites[bot_member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        await avisos.edit(overwrites=overwrites, reason='Finalização do servidor')

    # Escolha de jogos: membros veem e usam botões, mas não escrevem.
    escolha = discord.utils.get(guild.text_channels, name='🎭・escolha-seus-jogos')
    if escolha:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True),
        }
        if founder: overwrites[founder] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        if admin: overwrites[admin] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        if bot_member: overwrites[bot_member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
        await escolha.edit(overwrites=overwrites, reason='Finalização do servidor')

    await interaction.followup.send(
        '✅ Servidor finalizado!\n'
        '• Cores dos cargos aplicadas\n'
        '• 📢 avisos bloqueado para membros\n'
        '• 🎭 escolha-seus-jogos bloqueado para mensagens\n'
        '• 🎮 Membro será automático para novos integrantes\n'
        '• Boas-vindas serão enviadas no 💬 chat-geral\n'
        '• Comandos globais duplicados serão removidos',
        ephemeral=True
    )

async def command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        msg = 'Você precisa ter permissão de Administrador para usar este comando.'
    else:
        msg = f'Erro: {error}'
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)

montar_servidor.error(command_error)
configurar_cargos.error(command_error)
finalizar_servidor.error(command_error)

if __name__ == '__main__':
    print('=== goKenn Server Bot - Railway ===')
    print('IMPORTANTE: no Developer Portal > Bot, mantenha \"Intenção dos membros do servidor\" ativada.')
    token = os.getenv('DISCORD_TOKEN', '').strip()
    if not token:
        raise SystemExit('Variável DISCORD_TOKEN não configurada no Railway.')
    bot.run(token)
