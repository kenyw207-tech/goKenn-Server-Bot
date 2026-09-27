import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import asyncio
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

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
]

# Estes cargos servem apenas para identificar os jogos de cada membro.
# Nenhum canal novo é criado para estes jogos.
GAMES = [
    ('🚗', 'Rocket League', '🚗 Rocket League'),
    ('🎖️', 'Battlefield 6', '🎖️ Battlefield 6'),
    ('⚽', 'eFootball', '⚽ eFootball'),
    ('🎯', 'Call of Duty', '🎯 Call of Duty'),
    ('🏗️', 'Fortnite', '🏗️ Fortnite'),
    ('🔫', 'Modern Warfare III', '🔫 Modern Warfare III'),
    ('🟢', 'Delta Force', '🟢 Delta Force'),
    ('💥', 'Counter-Strike 2', '💥 Counter-Strike 2'),
    ('☠️', 'Modern Warfare II', '☠️ Modern Warfare II'),
    ('🪖', 'Warzone', '🪖 Warzone'),
    ('🔺', 'VALORANT', '🔺 VALORANT'),
    ('⚔️', 'League of Legends', '⚔️ League of Legends'),
    ('🏎️', 'Forza Horizon 6', '🏎️ Forza Horizon 6'),
]

GAME_COLOURS = [
    discord.Colour.blue(), discord.Colour.orange(), discord.Colour.gold(),
    discord.Colour.dark_grey(), discord.Colour.purple(), discord.Colour.red(),
    discord.Colour.green(), discord.Colour.orange(), discord.Colour.dark_red(),
    discord.Colour.green(), discord.Colour.magenta(), discord.Colour.blue(),
    discord.Colour.teal(),
]

async def toggle_game_role(interaction: discord.Interaction, role_name: str):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message('Use este botão dentro do servidor.', ephemeral=True)
        return
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    if role is None:
        await interaction.response.send_message('Esse cargo ainda não existe. Um administrador precisa executar /configurar-cargos.', ephemeral=True)
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

class GameButton(discord.ui.Button):
    def __init__(self, emoji: str, label: str, role_name: str, index: int):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f'game_role:v6:{index}',
            row=index // 5,
        )
        self.role_name = role_name

    async def callback(self, interaction: discord.Interaction):
        await toggle_game_role(interaction, self.role_name)

class GameRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for index, (emoji, label, role_name) in enumerate(GAMES):
            self.add_item(GameButton(emoji, label, role_name, index))

@bot.event
async def on_member_join(member: discord.Member):
    # Cargo automático de membro.
    role = discord.utils.get(member.guild.roles, name='🎮 Membro')
    if role:
        try:
            await member.add_roles(role, reason='Cargo automático de membro')
        except discord.Forbidden:
            pass

    # Boas-vindas em embed no chat-geral.
    channel = discord.utils.get(member.guild.text_channels, name='💬・chat-geral')
    escolha = discord.utils.get(member.guild.text_channels, name='🎭・escolha-seus-jogos')
    if channel:
        try:
            destino = escolha.mention if escolha else '#escolha-seus-jogos'
            embed = discord.Embed(
                title='👋 Bem-vindo(a) ao Cod Warzone Tieki!',
                description=(
                    f'Fala, {member.mention}! 🎮\n\n'
                    'Seja muito bem-vindo(a) à nossa comunidade!\n\n'
                    f'🎭 Vá até {destino} e selecione os jogos que você joga.\n\n'
                    'Escolha quantos jogos quiser e mostre para a galera o que você joga.\n\n'
                    '🎮 O cargo **Membro** já foi adicionado automaticamente.\n\n'
                    '**Entre em uma call, conheça a galera e bora jogar! 🔥**'
                ),
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f'Agora somos {member.guild.member_count} membros • Cod Warzone Tieki')
            await channel.send(content=member.mention, embed=embed)
        except discord.Forbidden:
            pass



NEWS_SOURCES = [
    {
        'game': 'WARZONE',
        'emoji': '🪖',
        'url': 'https://www.callofduty.com/br/pt/blog/warzone',
        'base': 'https://www.callofduty.com',
        'path_hint': '/blog/',
        'include': ('warzone', 'temporada', 'season', 'patch', 'atualiza', 'evento', 'event', 'mapa', 'mode', 'modo'),
        'exclude': ('mobile', 'esports', 'endowment'),
        'color': 0x43B581,
    },
    {
        'game': 'ROCKET LEAGUE',
        'emoji': '🚗',
        'url': 'https://www.rocketleague.com/news?lang=pt-br',
        'base': 'https://www.rocketleague.com',
        'path_hint': '/news/',
        'include': ('patch', 'temporada', 'season', 'atualiza', 'update', 'evento', 'event', 'chega', 'novo', 'nova'),
        'exclude': ('rlcs', 'championship', 'major', 'world championship', 'esports'),
        'color': 0x3498DB,
    },
    {
        'game': 'BATTLEFIELD 6',
        'emoji': '🎖️',
        'url': 'https://www.ea.com/pt-br/games/battlefield/battlefield-6/news',
        'base': 'https://www.ea.com',
        'path_hint': '/games/battlefield/battlefield-6/news/',
        'include': ('battlefield 6', 'temporada', 'season', 'atualiza', 'update', 'evento', 'event', 'mapa', 'map', 'community'),
        'exclude': ('antitrapaça', 'anticheat', 'competitive', 'redsec competitivo'),
        'color': 0xE67E22,
    },
]

_news_initialized = False
_seen_news_urls = set()


def _clean_text(value: str) -> str:
    return ' '.join((value or '').split()).strip()


def _interesting(title: str, source: dict) -> bool:
    low = title.casefold()
    if any(word.casefold() in low for word in source['exclude']):
        return False
    return any(word.casefold() in low for word in source['include'])


async def fetch_source_news(session: aiohttp.ClientSession, source: dict):
    headers = {'User-Agent': 'Mozilla/5.0 goKenn-Discord-NewsBot/1.0'}
    async with session.get(source['url'], headers=headers, timeout=aiohttp.ClientTimeout(total=25)) as response:
        response.raise_for_status()
        html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')
    found = []
    used = set()
    for a in soup.find_all('a', href=True):
        title = _clean_text(a.get_text(' ', strip=True))
        href = urljoin(source['base'], a.get('href', ''))
        if not title or source['path_hint'] not in href:
            continue
        if href.rstrip('/') == source['url'].split('?')[0].rstrip('/'):
            continue
        if not _interesting(title, source):
            continue
        # Evita cards/links duplicados da mesma matéria.
        href = href.split('?')[0].split('#')[0]
        if href in used:
            continue
        used.add(href)
        found.append({'title': title[:250], 'url': href, 'source': source})
        if len(found) >= 8:
            break
    return found


async def recent_news_urls(channel: discord.TextChannel):
    urls = set()
    try:
        async for message in channel.history(limit=100):
            if message.author.id != bot.user.id:
                continue
            for embed in message.embeds:
                if embed.url:
                    urls.add(embed.url)
    except (discord.Forbidden, discord.HTTPException):
        pass
    return urls


async def publish_news(channel: discord.TextChannel, item: dict):
    source = item['source']
    embed = discord.Embed(
        title=f"{source['emoji']} {source['game']} | NOVIDADE",
        description=f"**{item['title']}**\n\nClique no título abaixo para abrir a publicação oficial.",
        url=item['url'],
        color=source['color'],
    )
    embed.add_field(name='🔗 Fonte oficial', value=f"[Abrir publicação]({item['url']})", inline=False)
    embed.set_footer(text='Cod Warzone Tieki • Notícias oficiais • Sem menções')
    await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


@tasks.loop(hours=6)
async def game_news_loop():
    global _news_initialized, _seen_news_urls
    if not bot.guilds:
        return

    async with aiohttp.ClientSession() as session:
        for guild in bot.guilds:
            channel = discord.utils.get(guild.text_channels, name='📢・avisos')
            if channel is None:
                continue

            already_posted = await recent_news_urls(channel)
            current = []
            for source in NEWS_SOURCES:
                try:
                    current.extend(await fetch_source_news(session, source))
                except Exception as exc:
                    print(f"[NOTÍCIAS] Falha em {source['game']}: {exc}")

            # Na primeira execução de uma instalação sem notícias do bot,
            # apenas registra o conteúdo atual para não despejar notícias antigas.
            if not _news_initialized and not already_posted:
                _seen_news_urls.update(item['url'] for item in current)
                continue

            # Publica no máximo 3 novidades por ciclo, da ordem mais antiga para a mais nova.
            pending = [item for item in current if item['url'] not in already_posted and item['url'] not in _seen_news_urls]
            for item in reversed(pending[:3]):
                try:
                    await publish_news(channel, item)
                    _seen_news_urls.add(item['url'])
                    await asyncio.sleep(2)
                except (discord.Forbidden, discord.HTTPException) as exc:
                    print(f"[NOTÍCIAS] Não consegui publicar: {exc}")

    _news_initialized = True


@game_news_loop.before_loop
async def before_game_news_loop():
    await bot.wait_until_ready()
    await asyncio.sleep(10)


@bot.event
async def on_ready():
    if not game_news_loop.is_running():
        game_news_loop.start()
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

    # Cria/atualiza os cargos de identificação dos jogos, sem criar canais.
    for index, (_, _, role_name) in enumerate(GAMES):
        role = discord.utils.get(guild.roles, name=role_name)
        colour = GAME_COLOURS[index]
        if role is None:
            await guild.create_role(name=role_name, permissions=discord.Permissions.none(), colour=colour, reason='Cargo de identificação de jogo')
            created.append(role_name)
        else:
            try:
                await role.edit(permissions=discord.Permissions.none(), colour=colour, reason='Atualização de cargo de jogo')
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

    jogos_texto = '\n'.join(f'{emoji} **{label}**' for emoji, label, _ in GAMES)
    embed = discord.Embed(
        title='🎮 Escolha seus jogos',
        description=(
            'Clique nos botões para adicionar ou remover seus cargos. '
            'Você pode escolher quantos jogos quiser.\n\n' + jogos_texto
        ),
        color=discord.Color.red()
    )
    embed.set_footer(text='Esses cargos servem apenas para mostrar quais jogos você joga.')
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

    # Garante que todos os cargos de jogos existam, sem criar canais adicionais.
    for index, (_, _, role_name) in enumerate(GAMES):
        role = discord.utils.get(guild.roles, name=role_name)
        colour = GAME_COLOURS[index]
        if role is None:
            await guild.create_role(name=role_name, permissions=discord.Permissions.none(), colour=colour, reason='Finalização dos cargos de jogos')
        else:
            try:
                await role.edit(permissions=discord.Permissions.none(), colour=colour, reason='Finalização dos cargos de jogos')
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
