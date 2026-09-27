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
        'fallback_query': 'site:callofduty.com/blog Warzone',
    },
    {
        'game': 'ROCKET LEAGUE',
        'emoji': '🚗',
        'url': 'https://www.rocketleague.com/news',
        'base': 'https://www.rocketleague.com',
        'path_hint': '/news/',
        'include': ('rocket league', 'patch', 'temporada', 'season', 'atualiza', 'update', 'evento', 'event', 'chega', 'novo', 'nova'),
        'exclude': ('rlcs', 'championship', 'major', 'world championship', 'esports'),
        'color': 0x3498DB,
        'fallback_query': 'site:rocketleague.com/news Rocket League',
    },
    {
        'game': 'BATTLEFIELD 6',
        'emoji': '🎖️',
        'url': 'https://www.ea.com/pt-br/games/battlefield/battlefield-6/news',
        'base': 'https://www.ea.com',
        'path_hint': '/games/battlefield/',
        'include': ('battlefield 6', 'battlefield', 'temporada', 'season', 'atualiza', 'update', 'evento', 'event', 'mapa', 'map', 'community'),
        'exclude': ('competitive',),
        'color': 0xE67E22,
        'fallback_query': 'site:ea.com/games/battlefield Battlefield 6',
    },
]

STEAM_MIN_DISCOUNT = 50
EPIC_PROMOTIONS_URL = (
    'https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions'
    '?locale=pt-BR&country=BR&allowCountries=BR'
)
STEAM_SPECIALS_URL = (
    'https://store.steampowered.com/search/'
    '?specials=1&cc=BR&l=brazilian&category1=998'
)

_news_initialized = False
_seen_news_urls = set()
_promos_initialized = False
_seen_promo_ids = set()

STATE_FILE = os.getenv('BOT_STATE_FILE', 'bot_state.json')


def load_persistent_state():
    global _seen_news_urls, _seen_promo_ids
    try:
        if not os.path.exists(STATE_FILE):
            return
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _seen_news_urls.update(data.get('seen_news_urls', []))
        _seen_promo_ids.update(data.get('seen_promo_ids', []))
        print(f"[ESTADO] Carregado: {len(_seen_news_urls)} notícias e {len(_seen_promo_ids)} promoções.")
    except Exception as exc:
        print(f"[ESTADO] Não foi possível carregar o histórico: {exc}")


def save_persistent_state():
    try:
        data = {
            'seen_news_urls': sorted(_seen_news_urls),
            'seen_promo_ids': sorted(_seen_promo_ids),
        }
        temp = STATE_FILE + '.tmp'
        with open(temp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp, STATE_FILE)
    except Exception as exc:
        print(f"[ESTADO] Não foi possível salvar o histórico: {exc}")




def _clean_text(value: str) -> str:
    return ' '.join((value or '').split()).strip()


def _interesting(title: str, source: dict) -> bool:
    low = title.casefold().strip()
    if any(word.casefold() in low for word in source['exclude']):
        return False
    generic = {
        'temporada', 'season', 'notícias', 'news', 'novidades',
        'atualização', 'update', 'evento', 'event', 'comunidade', 'community'
    }
    if low in generic or len(title.strip()) < 12:
        return False
    if source['game'] == 'WARZONE':
        return 'warzone' in low
    if source['game'] == 'BATTLEFIELD 6':
        return ('battlefield' in low or 'bf6' in low)
    return any(word.casefold() in low for word in source['include'])


def _browser_headers():
    return {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/151.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.7',
        'Cache-Control': 'no-cache',
    }


async def _fetch_google_news_fallback(session: aiohttp.ClientSession, source: dict):
    """Fallback: busca no Google News somente resultados do domínio oficial."""
    from urllib.parse import quote_plus
    query = quote_plus(source['fallback_query'])
    url = f'https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419'
    headers = _browser_headers()
    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=25)) as response:
        response.raise_for_status()
        xml = await response.text()

    soup = BeautifulSoup(xml, 'html.parser')
    found = []
    used = set()
    for item in soup.find_all('item'):
        title_tag = item.find('title')
        link_tag = item.find('link')
        if not title_tag or not link_tag:
            continue
        title = _clean_text(title_tag.get_text(' ', strip=True))
        href = _clean_text(link_tag.get_text(' ', strip=True))
        if not title or not href or href in used:
            continue
        # Google News costuma anexar o nome da fonte ao título.
        for suffix in (' - Electronic Arts', ' - EA', ' - Rocket League', ' - Call of Duty'):
            if title.endswith(suffix):
                title = title[:-len(suffix)].strip()
        if len(title) < 12 or title.casefold() in {'temporada', 'season', 'update', 'atualização'}:
            continue
        if source['game'] == 'ROCKET LEAGUE':
            # A busca já é restrita ao domínio oficial; aceita títulos completos do feed.
            pass
        elif not _interesting(title, source):
            continue
        used.add(href)
        found.append({'title': title[:250], 'url': href, 'source': source})
        if len(found) >= 8:
            break
    return found


async def fetch_source_news(session: aiohttp.ClientSession, source: dict):
    """Tenta a página oficial; se houver 403/erro, usa fallback restrito ao domínio oficial."""
    headers = _browser_headers()
    try:
        async with session.get(
            source['url'],
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=25),
            allow_redirects=True,
        ) as response:
            response.raise_for_status()
            html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        found = []
        used = set()
        for a in soup.find_all('a', href=True):
            title = _clean_text(
                a.get('aria-label') or a.get('title') or a.get_text(' ', strip=True)
            )
            href = urljoin(source['base'], a.get('href', ''))
            if not title or source['path_hint'] not in href:
                continue
            if href.rstrip('/') == source['url'].split('?')[0].rstrip('/'):
                continue
            if not _interesting(title, source):
                continue
            href = href.split('?')[0].split('#')[0]
            if href in used:
                continue
            used.add(href)
            found.append({'title': title[:250], 'url': href, 'source': source})
            if len(found) >= 8:
                break
        if found:
            return found
    except Exception as exc:
        print(f"[NOTÍCIAS] Página direta falhou em {source['game']}: {exc}. Tentando fallback.")

    return await _fetch_google_news_fallback(session, source)


async def recent_news_urls(channel: discord.TextChannel):
    urls = set()
    try:
        async for message in channel.history(limit=150):
            if bot.user and message.author.id != bot.user.id:
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
        description=f"**{item['title']}**\n\nAbra a publicação para ver os detalhes.",
        url=item['url'],
        color=source['color'],
    )
    embed.add_field(name='🔗 Publicação', value=f"[Abrir notícia]({item['url']})", inline=False)
    embed.set_footer(text='Cod Warzone Tieki • Notícias • Sem menções')
    await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


async def fetch_epic_free_games(session: aiohttp.ClientSession):
    headers = _browser_headers()
    headers['Accept'] = 'application/json,text/plain,*/*'
    async with session.get(
        EPIC_PROMOTIONS_URL, headers=headers,
        timeout=aiohttp.ClientTimeout(total=25)
    ) as response:
        response.raise_for_status()
        data = await response.json(content_type=None)

    items = []
    elements = (
        data.get('data', {})
            .get('Catalog', {})
            .get('searchStore', {})
            .get('elements', [])
    )

    for game in elements:
        promos = game.get('promotions') or {}
        offers = promos.get('promotionalOffers') or []
        if not offers:
            continue

        active = []
        for group in offers:
            active.extend(group.get('promotionalOffers') or [])
        if not active:
            continue

        title = _clean_text(game.get('title', ''))
        if not title:
            continue

        slug = game.get('productSlug') or game.get('urlSlug') or ''
        if slug:
            slug = slug.strip('/')
            url = f'https://store.epicgames.com/pt-BR/p/{slug}'
        else:
            url = 'https://store.epicgames.com/pt-BR/free-games'

        promo = active[0]
        start = promo.get('startDate', '')
        end = promo.get('endDate', '')
        game_id = f"epic:{game.get('id', title)}:{start}:{end}"
        items.append({
            'id': game_id,
            'title': title,
            'url': url,
            'end': end,
        })
    return items


def _steam_price_text(node, selector):
    el = node.select_one(selector)
    return _clean_text(el.get_text(' ', strip=True)) if el else ''


async def fetch_steam_specials(session: aiohttp.ClientSession):
    headers = _browser_headers()
    async with session.get(
        STEAM_SPECIALS_URL, headers=headers,
        timeout=aiohttp.ClientTimeout(total=30)
    ) as response:
        response.raise_for_status()
        html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')
    items = []
    used = set()

    for row in soup.select('a.search_result_row'):
        href = (row.get('href') or '').split('?')[0]
        title_el = row.select_one('.title')
        discount_el = row.select_one('.discount_pct')
        if not href or not title_el or not discount_el:
            continue

        title = _clean_text(title_el.get_text(' ', strip=True))
        discount_text = _clean_text(discount_el.get_text(' ', strip=True))
        try:
            discount = int(discount_text.replace('-', '').replace('%', '').strip())
        except ValueError:
            continue

        if discount < STEAM_MIN_DISCOUNT:
            continue

        app_id = row.get('data-ds-appid') or href
        promo_id = f'steam:{app_id}:{discount}'
        if promo_id in used:
            continue
        used.add(promo_id)

        original = _steam_price_text(row, '.discount_original_price')
        final = _steam_price_text(row, '.discount_final_price')
        items.append({
            'id': promo_id,
            'title': title,
            'url': href,
            'discount': discount,
            'original': original,
            'final': final,
        })
        if len(items) >= 12:
            break

    return items


async def publish_epic(channel: discord.TextChannel, item: dict):
    description = f"**{item['title']}**\n\n💰 **GRÁTIS por tempo limitado**"
    if item.get('end'):
        try:
            from datetime import datetime, timedelta, timezone
            end_dt = datetime.fromisoformat(item['end'].replace('Z', '+00:00'))
            br_tz = timezone(timedelta(hours=-3))
            end_dt = end_dt.astimezone(br_tz)
            description += f"\n⏰ Grátis até **{end_dt.strftime('%d/%m/%Y às %H:%M')}**"
        except Exception:
            description += f"\n⏰ Término informado pela Epic: `{item['end']}`"
    embed = discord.Embed(
        title='🎁 EPIC GAMES | JOGO GRÁTIS',
        description=description,
        url=item['url'],
        color=0x2F3136,
    )
    embed.add_field(name='🔗 Resgatar', value=f"[Abrir na Epic Games]({item['url']})", inline=False)
    embed.set_footer(text='Cod Warzone Tieki • Promoções • Sem menções')
    await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


async def publish_steam(channel: discord.TextChannel, item: dict):
    prices = ''
    if item.get('original') or item.get('final'):
        prices = f"\n💵 {item.get('original', '')} → **{item.get('final', '')}**"
    embed = discord.Embed(
        title=f"🔥 STEAM | {item['discount']}% OFF",
        description=f"**{item['title']}**{prices}",
        url=item['url'],
        color=0x1B2838,
    )
    embed.add_field(name='🔗 Ver promoção', value=f"[Abrir na Steam]({item['url']})", inline=False)
    embed.set_footer(text=f'Cod Warzone Tieki • Steam ≥ {STEAM_MIN_DISCOUNT}% • Sem menções')
    await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


async def collect_news(session):
    current = []
    for source in NEWS_SOURCES:
        try:
            result = await fetch_source_news(session, source)
            print(f"[NOTÍCIAS] {source['game']}: {len(result)} encontrada(s)")
            current.extend(result)
        except Exception as exc:
            print(f"[NOTÍCIAS] Falha em {source['game']}: {exc}")
    return current


async def collect_promos(session):
    epic, steam = [], []
    try:
        epic = await fetch_epic_free_games(session)
        print(f'[PROMOÇÕES] Epic: {len(epic)} jogo(s) grátis encontrado(s)')
    except Exception as exc:
        print(f'[PROMOÇÕES] Falha na Epic: {exc}')
    try:
        steam = await fetch_steam_specials(session)
        print(f'[PROMOÇÕES] Steam >= {STEAM_MIN_DISCOUNT}%: {len(steam)} promoção(ões)')
    except Exception as exc:
        print(f'[PROMOÇÕES] Falha na Steam: {exc}')
    return epic, steam


@tasks.loop(hours=6)
async def game_news_loop():
    global _news_initialized, _seen_news_urls
    if not bot.guilds:
        return

    async with aiohttp.ClientSession() as session:
        news = await collect_news(session)
        epic, steam = await collect_promos(session)

        for guild in bot.guilds:
            channel = discord.utils.get(guild.text_channels, name='📢・avisos')
            if channel is None:
                continue

            already_posted = await recent_news_urls(channel)

            # NOTÍCIAS: publica cada matéria apenas uma vez.
            if not _news_initialized and not already_posted:
                _seen_news_urls.update(item['url'] for item in news)
                save_persistent_state()
            else:
                pending_news = [
                    item for item in news
                    if item['url'] not in already_posted
                    and item['url'] not in _seen_news_urls
                ]
                for item in reversed(pending_news[:3]):
                    try:
                        await publish_news(channel, item)
                        _seen_news_urls.add(item['url'])
                        save_persistent_state()
                        await asyncio.sleep(2)
                    except (discord.Forbidden, discord.HTTPException) as exc:
                        print(f'[NOTÍCIAS] Não consegui publicar: {exc}')

            # EPIC: lembrete de TODOS os jogos que continuam grátis a cada 6 horas.
            for item in epic:
                try:
                    await publish_epic(channel, item)
                    await asyncio.sleep(2)
                except (discord.Forbidden, discord.HTTPException) as exc:
                    print(f'[EPIC] Não consegui publicar lembrete: {exc}')

    _news_initialized = True


@game_news_loop.before_loop
async def before_game_news_loop():
    await bot.wait_until_ready()
    await asyncio.sleep(10)


@tasks.loop(hours=24)
async def steam_daily_loop():
    if not bot.guilds:
        return

    async with aiohttp.ClientSession() as session:
        try:
            steam = await fetch_steam_specials(session)
            print(f'[STEAM DIÁRIO] {len(steam)} promoção(ões) >= {STEAM_MIN_DISCOUNT}%')
        except Exception as exc:
            print(f'[STEAM DIÁRIO] Falha ao consultar Steam: {exc}')
            return

        for guild in bot.guilds:
            channel = discord.utils.get(guild.text_channels, name='📢・avisos')
            if channel is None:
                continue

            # Resumo diário: republica as promoções que ainda estão válidas.
            # Limite de 12 para evitar excesso de mensagens.
            for item in steam[:12]:
                try:
                    await publish_steam(channel, item)
                    await asyncio.sleep(2)
                except (discord.Forbidden, discord.HTTPException) as exc:
                    print(f'[STEAM DIÁRIO] Não consegui publicar: {exc}')


@steam_daily_loop.before_loop
async def before_steam_daily_loop():
    await bot.wait_until_ready()
    # Desloca o resumo diário da Steam para não sair junto do ciclo da Epic/notícias.
    await asyncio.sleep(60)


@bot.tree.command(name='testar-noticias', description='Testa agora as notícias de Warzone, Rocket League e Battlefield 6.')
@app_commands.checks.has_permissions(administrator=True)
async def testar_noticias(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message('Use este comando dentro do servidor.', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    channel = discord.utils.get(interaction.guild.text_channels, name='📢・avisos')
    if channel is None:
        await interaction.followup.send('Não encontrei o canal 📢・avisos.', ephemeral=True)
        return

    async with aiohttp.ClientSession() as session:
        news = await collect_news(session)

    if not news:
        await interaction.followup.send('⚠️ Nenhuma notícia foi encontrada. Confira os logs do Railway.', ephemeral=True)
        return

    # Uma notícia de cada jogo, quando disponível.
    sent = 0
    for source in NEWS_SOURCES:
        item = next((x for x in news if x['source']['game'] == source['game']), None)
        if item:
            await publish_news(channel, item)
            sent += 1
            await asyncio.sleep(1)

    missing = [src['game'] for src in NEWS_SOURCES if not any(x['source']['game'] == src['game'] for x in news)]
    extra = f" Sem resultado: {', '.join(missing)}." if missing else ''
    await interaction.followup.send(
        f'✅ Teste concluído: {sent} notícia(s) publicada(s) em {channel.mention}.{extra}',
        ephemeral=True
    )


@bot.tree.command(name='testar-promocoes', description='Testa jogos grátis da Epic e promoções da Steam com 50% ou mais.')
@app_commands.checks.has_permissions(administrator=True)
async def testar_promocoes(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message('Use este comando dentro do servidor.', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    channel = discord.utils.get(interaction.guild.text_channels, name='📢・avisos')
    if channel is None:
        await interaction.followup.send('Não encontrei o canal 📢・avisos.', ephemeral=True)
        return

    async with aiohttp.ClientSession() as session:
        epic, steam = await collect_promos(session)

    sent_epic = 0
    sent_steam = 0

    for item in epic[:3]:
        await publish_epic(channel, item)
        sent_epic += 1
        await asyncio.sleep(1)

    for item in steam[:5]:
        await publish_steam(channel, item)
        sent_steam += 1
        await asyncio.sleep(1)

    await interaction.followup.send(
        f'✅ Teste concluído: Epic {sent_epic} | Steam {sent_steam}.',
        ephemeral=True
    )


@bot.event
async def on_ready():
    if not getattr(bot, '_persistent_state_loaded', False):
        load_persistent_state()
        bot._persistent_state_loaded = True
    if not game_news_loop.is_running():
        game_news_loop.start()
    if not steam_daily_loop.is_running():
        steam_daily_loop.start()
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
    print('Comandos: /montar-servidor, /configurar-cargos, /finalizar-servidor, /testar-noticias, /testar-promocoes e /limpar-avisos')

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

class ConfirmClearAvisos(discord.ui.View):
    def __init__(self, requester_id: int):
        super().__init__(timeout=30)
        self.requester_id = requester_id

    @discord.ui.button(label='Confirmar limpeza', style=discord.ButtonStyle.danger, emoji='🗑️')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message('Somente quem executou o comando pode confirmar.', ephemeral=True)
            return

        channel = discord.utils.get(interaction.guild.text_channels, name='📢・avisos') if interaction.guild else None
        if channel is None:
            await interaction.response.edit_message(content='❌ Não encontrei o canal 📢・avisos.', view=None)
            return

        await interaction.response.edit_message(content='🧹 Limpando o canal 📢・avisos...', view=None)
        deleted = 0
        while True:
            messages = [m async for m in channel.history(limit=100)]
            if not messages:
                break
            for message in messages:
                try:
                    await message.delete()
                    deleted += 1
                    await asyncio.sleep(0.35)
                except (discord.NotFound, discord.Forbidden):
                    pass
                except discord.HTTPException:
                    await asyncio.sleep(1)
            if len(messages) < 100:
                break

        # Importante: não apagamos a memória de itens já conhecidos.
        # Assim, notícias/promos antigas não voltam imediatamente após a limpeza.
        await interaction.followup.send(
            f'✅ Canal 📢・avisos limpo. {deleted} mensagem(ns) removida(s). '
            'As notícias e promoções já conhecidas foram preservadas na memória para não serem republicadas.',
            ephemeral=True
        )

    @discord.ui.button(label='Cancelar', style=discord.ButtonStyle.secondary, emoji='✖️')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message('Somente quem executou o comando pode cancelar.', ephemeral=True)
            return
        await interaction.response.edit_message(content='❎ Limpeza cancelada.', view=None)


@bot.tree.command(name='limpar-avisos', description='Apaga as mensagens do canal de avisos após confirmação.')
@app_commands.checks.has_permissions(administrator=True)
async def limpar_avisos(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message('Use este comando dentro do servidor.', ephemeral=True)
        return

    channel = discord.utils.get(interaction.guild.text_channels, name='📢・avisos')
    if channel is None:
        await interaction.response.send_message('Não encontrei o canal 📢・avisos.', ephemeral=True)
        return

    view = ConfirmClearAvisos(interaction.user.id)
    await interaction.response.send_message(
        f'⚠️ Você está prestes a apagar **todas as mensagens** de {channel.mention}.\n'
        'Essa ação não pode ser desfeita. Deseja continuar?',
        view=view,
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
testar_noticias.error(command_error)
testar_promocoes.error(command_error)
limpar_avisos.error(command_error)

if __name__ == '__main__':
    print('=== goKenn Server Bot - Railway ===')
    print('IMPORTANTE: no Developer Portal > Bot, mantenha \"Intenção dos membros do servidor\" ativada.')
    token = os.getenv('DISCORD_TOKEN', '').strip()
    if not token:
        raise SystemExit('Variável DISCORD_TOKEN não configurada no Railway.')
    bot.run(token)
