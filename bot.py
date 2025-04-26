import discord
import requests
import os
import logging
from fivem_scraper import get_fivem_players, get_fivem_players_api

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Discord bot with intents
def run_discord_bot():
    # Token fixo para o bot Discord - Nunca vai mudar
    # Definimos o token diretamente no código para não precisar configurar novamente
    TOKEN = os.environ.get("DISCORD_TOKEN")
    logger.info("Token do Discord configurado e pronto para uso")

    # Set up intents (permissions) for the bot
    intents = discord.Intents.default()
    intents.message_content = False  # Disable message content intent due to privileged requirements
    
    # Create a regular client instead of commands.Bot
    client = discord.Client(intents=intents)
    logger.info("Using Discord Client with message handling instead of commands framework")

    @client.event
    async def on_ready():
        """Event triggered when the bot is connected and ready"""
        logger.info(f'Bot connected as {client.user}')
        logger.info(f'Bot ID: {client.user.id}')
        logger.info(f'Bot is connected to {len(client.guilds)} servers')
        
        # Set bot activity status
        await client.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="FiveM servers | @mention players"
        ))

    @client.event
    async def on_message(message):
        """Handle messages and respond to specific mentions"""
        # Ignore messages from the bot itself to prevent loops
        if message.author == client.user:
            return
            
        # Check if the message mentions our bot
        if client.user.mentioned_in(message):
            # Check for help command
            if "help" in message.content.lower() or "ajuda" in message.content.lower():
                logger.info(f"Help command received from {message.author} in {message.guild}")
                help_embed = discord.Embed(
                    title="Ajuda do Bot FiveM",
                    description="Este bot permite verificar informações de servidores FiveM.",
                    color=discord.Color.blue()
                )
                
                help_embed.add_field(
                    name="📋 Comandos Disponíveis",
                    value="• `@bot players` - Mostra informações sobre os jogadores do servidor byzd3d\n"
                          "• `@bot register steam:ID NomeJogador - Grupo/Notas` - Registra ou atualiza informações de um jogador\n"
                          "• `@bot player steam:ID` - Busca informações registradas de um jogador\n"
                          "• `@bot help` ou `@bot ajuda` - Mostra esta mensagem de ajuda",
                    inline=False
                )
                
                help_embed.add_field(
                    name="💡 Como usar",
                    value=f"Mencione o bot seguido do comando que deseja usar. Por exemplo:\n"
                          f"`@{client.user.name} players`\n\n"
                          f"Se você encontrar o erro 403, isso significa que a API do FiveM está limitando o acesso.",
                    inline=False
                )
                
                help_embed.add_field(
                    name="🌐 Links Úteis",
                    value="• [Lista de Servidores FiveM](https://servers.fivem.net/)\n"
                          "• [Status da API FiveM](https://status.cfx.re/)",
                    inline=False
                )
                
                help_embed.set_footer(text=f"Bot criado por {message.guild.name if message.guild else 'FiveM Discord'}")
                
                await message.reply(embed=help_embed)
                return
                
            # Register player command
            elif "register" in message.content.lower():
                logger.info(f"Register command received from {message.author} in {message.guild}")
                
                # Extract command parts
                content = message.content.split("register", 1)[1].strip()
                
                # Check for valid format
                if " " not in content:
                    await message.reply("❌ Formato inválido. Use: `@bot register steam:ID NomeJogador - Grupo/Notas`")
                    return
                
                # Extract Steam ID and name parts
                parts = content.split(" ", 1)
                steam_id = parts[0].strip()
                player_data = parts[1].strip()
                
                # Split name and notes/group
                if "-" in player_data:
                    name_notes = player_data.split("-", 1)
                    nickname = name_notes[0].strip()
                    notes = name_notes[1].strip()
                    group = notes.split()[0] if notes else None
                else:
                    nickname = player_data
                    notes = ""
                    group = None
                
                try:
                    # Use app context to access database
                    from keep_alive import app
                    from models import db, PlayerInfo
                    
                    with app.app_context():
                        # Check if player exists
                        player = PlayerInfo.query.filter_by(steam_id=steam_id).first()
                        
                        if player:
                            # Update existing player
                            player.nickname = nickname
                            player.notes = notes
                            player.group = group
                            db.session.commit()
                            await message.reply(f"✅ Jogador atualizado: `{nickname}` com ID `{steam_id}`")
                        else:
                            # Create new player
                            player = PlayerInfo(
                                steam_id=steam_id,
                                nickname=nickname,
                                notes=notes,
                                group=group
                            )
                            db.session.add(player)
                            db.session.commit()
                            await message.reply(f"✅ Jogador registrado: `{nickname}` com ID `{steam_id}`")
                except Exception as e:
                    logger.error(f"Error registering player: {str(e)}")
                    await message.reply(f"❌ Erro ao registrar jogador: {str(e)}")
                
                return
                
            # Player info command (not plural 'players')
            elif "player " in message.content.lower() and not "players" in message.content.lower():
                logger.info(f"Player lookup command received from {message.author} in {message.guild}")
                
                # Extract Steam ID
                steam_id = message.content.split("player", 1)[1].strip()
                
                try:
                    # Use app context to access database
                    from keep_alive import app
                    from models import PlayerInfo
                    
                    with app.app_context():
                        player = PlayerInfo.query.filter_by(steam_id=steam_id).first()
                        
                        if player:
                            embed = discord.Embed(
                                title=f"Informações do Jogador: {player.nickname}",
                                color=discord.Color.green()
                            )
                            
                            embed.add_field(name="Steam ID", value=f"`{player.steam_id}`", inline=False)
                            
                            if player.group:
                                embed.add_field(name="Grupo", value=player.group, inline=True)
                                
                            if player.notes:
                                embed.add_field(name="Notas", value=player.notes, inline=False)
                                
                            embed.set_footer(text=f"Última atualização: {player.updated_at.strftime('%d/%m/%Y %H:%M')}")
                            
                            await message.reply(embed=embed)
                        else:
                            await message.reply(f"❌ Nenhum jogador encontrado com o ID `{steam_id}`")
                except Exception as e:
                    logger.error(f"Error looking up player: {str(e)}")
                    await message.reply(f"❌ Erro ao buscar jogador: {str(e)}")
                
                return
                
            # Check for players command
            elif "players" in message.content.lower():
                logger.info(f"Players command received from {message.author} in {message.guild}")
                
                # Fixed server ID
                server_id = "byzd3d"
                logger.info(f"Fetching data for server ID: {server_id}")
                
                # Show typing indicator
                async with message.channel.typing():
                    # Create an embed response
                    embed = discord.Embed(
                        title=f"FiveM Server Players - {server_id}",
                        color=discord.Color.blue()
                    )
                    
                    try:
                        # Primeiro tentamos a API direta
                        api_data = get_fivem_players_api(server_id)
                        
                        # Se a API falhar, tentamos o scraping
                        if not api_data['success']:
                            logger.info("API falhou, tentando web scraping")
                            # Tentar web scraping como alternativa
                            scraper_data = get_fivem_players(server_id)
                            
                            # Se o scraping também falhar
                            if not scraper_data['success']:
                                # Exibir mensagem de erro
                                embed.title = "FiveM Server Info"
                                embed.description = "⚠️ Não foi possível obter dados do servidor FiveM"
                                embed.add_field(
                                    name="🔍 Status", 
                                    value=f"Erro: {scraper_data['message']}\n\nO FiveM implementou restrições à API pública. Para dados reais, configure um servidor FiveM próprio ou integre com sua comunidade.", 
                                    inline=False
                                )
                                embed.add_field(
                                    name="💡 Como encontrar servidores",
                                    value="Você pode encontrar servidores no próprio jogo FiveM ou pelo site: https://servers.fivem.net/", 
                                    inline=False
                                )
                                embed.add_field(
                                    name="🔧 Como usar o bot",
                                    value=f"Mencione o bot junto com 'players':\n`@{client.user.name} players`", 
                                    inline=False
                                )
                                await message.reply(embed=embed)
                                return
                            
                            # Se o scraping funcionou, use esses dados
                            data = scraper_data
                            players = data['players']
                            server_name = data['hostname']
                            players_count = len(players)
                            max_players = 0  # Provavelmente não disponível via scraping
                        else:
                            # Se a API funcionou, use esses dados
                            data = api_data
                            players = data['players']
                            server_name = data['hostname']
                            players_count = len(players)
                            max_players = data.get('max_players', 0)
                        
                        # Update embed with server info
                        embed.title = server_name
                        embed.description = f"**{players_count}/{max_players}** players online"
                        
                        # Add timestamp
                        embed.timestamp = discord.utils.utcnow()
                        
                        # Display players or empty message
                        if players:
                            # Sort players by name quando players contém dicionários
                            try:
                                # Verificar se players pode ser ordenado
                                if all(isinstance(player, dict) for player in players):
                                    players.sort(key=lambda x: x.get('name', '').lower())
                                else:
                                    logger.warning("Lista de players não contém apenas dicionários, pulando ordenação")
                            except Exception as sort_error:
                                logger.warning(f"Não foi possível ordenar players: {sort_error}")
                            
                            # Buscar todos os jogadores registrados de uma vez
                            from keep_alive import app
                            from models import PlayerInfo
                            
                            registered_players = {}
                            try:
                                with app.app_context():
                                    for player in PlayerInfo.query.all():
                                        registered_players[player.steam_id] = (player.nickname, player.group)
                            except Exception as db_error:
                                logger.warning(f"Erro ao buscar informações do banco de dados: {db_error}")
                            
                            # Processar jogadores em paralelo
                            player_list = []
                            for player in players:
                                if not isinstance(player, dict):
                                    continue
                                
                                player_name = player.get('name', 'Unknown')
                                identifiers = player.get('identifiers', [])
                                steam_id = next((id for id in identifiers if isinstance(id, str) and id.startswith('steam:')), '')
                                
                                # Usar informações do cache
                                if steam_id in registered_players:
                                    nickname, group = registered_players[steam_id]
                                    player_info = f"• **{nickname}**"
                                    if group:
                                        player_info += f" ({group})"
                                else:
                                    player_info = f"• **{player_name}** | Steam: `{steam_id}`"
                                
                                player_list.append(player_info)
                            
                            player_list = "\n".join(player_list)
                            
                            # Criar dicionário para agrupar jogadores por facção
                            faction_groups = {
                                "families": [],
                                "bennys": [],
                                "angels": [],
                                "ballas": [],
                                "randola": [],
                                "policia": [],
                                "vagos": [],
                                "marabunta": [],
                                "the lost": [],
                                "outros": []
                            }

                            # Distribuir jogadores nos grupos
                            player_lines = player_list.split('\n')
                            for player_info in player_lines:
                                added = False
                                for faction in faction_groups.keys():
                                    if faction != "outros" and faction.lower() in player_info.lower():
                                        faction_groups[faction].append(player_info)
                                        added = True
                                        break
                                if not added:
                                    faction_groups["outros"].append(player_info)

                            # Criar embeds para cada facção
                            embeds = []
                            colors = {
                                "families": 0x00FF00,  # Verde
                                "bennys": 0x0000FF,    # Azul
                                "angels": 0xFFFFFF,    # Branco
                                "ballas": 0x800080,    # Roxo
                                "randola": 0xFFA500,   # Laranja
                                "policia": 0x000080,   # Azul Escuro
                                "vagos": 0xFFFF00,     # Amarelo
                                "marabunta": 0x00FFFF, # Ciano
                                "the lost": 0x808080,  # Cinza
                                "outros": 0x696969     # Cinza Escuro
                            }

                            for faction, players in faction_groups.items():
                                if players:  # Só criar embed se tiver jogadores
                                    new_embed = discord.Embed(
                                        title=f"{server_name} - {faction.upper()}",
                                        color=colors[faction]
                                    )
                                    new_embed.description = f"**{players_count}/{max_players}** players online"
                                    
                                    # Dividir em chunks se necessário
                                    chunks = []
                                    current_chunk = []
                                    current_length = 0
                                    
                                    for player in players:
                                        if current_length + len(player) + 1 > 1000:
                                            chunks.append(current_chunk)
                                            current_chunk = [player]
                                            current_length = len(player)
                                        else:
                                            current_chunk.append(player)
                                            current_length += len(player) + 1
                                    
                                    if current_chunk:
                                        chunks.append(current_chunk)
                                    
                                    for i, chunk in enumerate(chunks):
                                        if i > 0:  # Se precisar de mais de um embed para a mesma facção
                                            new_embed = discord.Embed(
                                                title=f"{server_name} - {faction.upper()} (Cont.)",
                                                color=colors[faction]
                                            )
                                        new_embed.add_field(
                                            name=f"👥 {faction.upper()} Players",
                                            value='\n'.join(chunk),
                                            inline=False
                                        )
                                        embeds.append(new_embed)
                            
                            # Todos os chunks já foram processados no loop anterior
                            
                            # Send all embeds
                            if embeds:
                                for e in embeds:
                                    await message.channel.send(embed=e)
                                return
                            else:
                                embed.add_field(name="👥 Online Players", value="No players online", inline=False)
                        else:
                            embed.add_field(name="🔍 Server Status", 
                                          value="No players online at the moment.", inline=False)
                        
                        # Reply to the message with the embed
                        await message.reply(embed=embed)
                        
                    except requests.exceptions.RequestException as e:
                        logger.error(f"API request error: {str(e)}")
                        embed = discord.Embed(
                            title="Error",
                            description=f"Could not fetch server data: {str(e)}",
                            color=discord.Color.red()
                        )
                        await message.reply(embed=embed)
                        
                    except Exception as e:
                        logger.error(f"Unexpected error: {str(e)}")
                        embed = discord.Embed(
                            title="Error",
                            description=f"An unexpected error occurred: {str(e)}",
                            color=discord.Color.red()
                        )
                        await message.reply(embed=embed)

    # Run the bot
    try:
        logger.info("Starting Discord bot...")
        client.run(TOKEN)
        return True
    except discord.errors.LoginFailure:
        logger.error("Invalid Discord token provided!")
        return False
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        return False