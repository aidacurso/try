import requests
import trafilatura
import re
import json
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def get_fivem_players(server_id):
    """
    Tentar obter dados do servidor FiveM via web scraping
    """
    url = f"https://servers.fivem.net/servers/detail/{server_id}"
    
    try:
        # Configurar headers para parecer um navegador real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://servers.fivem.net/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        # Se obtermos uma resposta HTML
        if response.status_code == 200:
            # Usar trafilatura para extrair o conteúdo principal
            html_content = response.text
            logger.info(f"Página carregada com sucesso: {len(html_content)} bytes")
            
            # Usando BeautifulSoup para analisar o HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Procurar dados de jogadores que estão geralmente em um script JSON
            scripts = soup.find_all('script')
            player_data = []
            
            # Procurar por scripts que contenham dados do servidor
            for script in scripts:
                if script.string and 'window.nuxt=' in script.string:
                    logger.info("Encontrado script com dados do Nuxt")
                    # Extrair os dados JSON
                    match = re.search(r'window\.nuxt=(.+?);', script.string, re.DOTALL)
                    if match:
                        try:
                            nuxt_data = json.loads(match.group(1))
                            # Navegar nos dados para encontrar informações do servidor
                            if 'state' in nuxt_data and 'serverData' in nuxt_data['state']:
                                server_data = nuxt_data['state']['serverData']
                                if 'players' in server_data:
                                    player_data = server_data['players']
                                    break
                        except json.JSONDecodeError:
                            logger.error("Erro ao decodificar JSON")
                            continue
            
            return {
                "success": True,
                "message": "Dados obtidos via web scraping",
                "hostname": soup.title.string if soup.title else "FiveM Server",
                "players": player_data
            }
        
        # Se for redirecionado para Cloudflare ou outro bloqueador
        else:
            logger.warning(f"Resposta não bem-sucedida: {response.status_code}")
            return {
                "success": False,
                "message": f"Não foi possível acessar a página do servidor (Status: {response.status_code})",
                "hostname": f"FiveM Server {server_id}",
                "players": []
            }
    
    except Exception as e:
        logger.error(f"Erro ao obter dados do servidor: {str(e)}")
        return {
            "success": False,
            "message": f"Erro ao obter dados: {str(e)}",
            "hostname": f"FiveM Server {server_id}",
            "players": []
        }

# Função alternativa usando API direta (mas que está com erro 403/404)
def get_fivem_players_api(server_id):
    """
    Tentar acessar a API direta do FiveM (provavelmente bloqueada)
    """
    # Tentar vários endpoints conhecidos
    endpoints = [
        f"https://servers-frontend.fivem.net/api/servers/single/{server_id}",
        f"https://servers-live.fivem.net/api/servers/single/{server_id}",
        f"https://servers-data.fivem.net/{server_id}"
    ]
    
    for endpoint in endpoints:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Origin': 'https://servers.fivem.net',
                'Referer': 'https://servers.fivem.net/'
            }
            
            logger.info(f"Tentando endpoint: {endpoint}")
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Sucesso com endpoint: {endpoint}")
                
                if 'Data' in data and 'players' in data['Data']:
                    return {
                        "success": True,
                        "message": "Dados obtidos via API",
                        "hostname": data['Data'].get('hostname', f"FiveM Server {server_id}"),
                        "players": data['Data']['players'],
                        "max_players": data['Data'].get('svMaxclients', 0)
                    }
            else:
                logger.warning(f"Falha no endpoint {endpoint}: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Erro no endpoint {endpoint}: {str(e)}")
    
    # Se chegarmos aqui, todos os endpoints falharam
    return {
        "success": False,
        "message": "Todos os endpoints da API falharam (acesso bloqueado ou indisponível)",
        "hostname": f"FiveM Server {server_id}",
        "players": []
    }

if __name__ == "__main__":
    # Teste
    logging.basicConfig(level=logging.INFO)
    result = get_fivem_players("byzd3d")
    print(json.dumps(result, indent=2))