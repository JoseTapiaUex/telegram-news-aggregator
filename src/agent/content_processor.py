"""
Procesador de contenido para extraer información de URLs
Ruta: src/agent/content_processor.py
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import SCRAPING_CONFIG, IMAGE_API_CONFIG, CONTENT_TYPES


class ContentProcessor:
    """Procesa URLs para extraer título, resumen, imágenes y metadatos"""
    
    def __init__(self):
        self.timeout = SCRAPING_CONFIG['timeout']
        self.user_agent = SCRAPING_CONFIG['user_agent']
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
        }
    
    def fetch_url_content(self, url):
        """Obtiene el contenido HTML de una URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[ERROR] Error obteniendo contenido de {url}: {str(e)}")
            return None
    
    def extract_open_graph_data(self, soup):
        """Extrae metadatos Open Graph de la página"""
        og_data = {}
        
        og_tags = {
            'og:title': 'title',
            'og:description': 'description',
            'og:image': 'image',
            'og:type': 'type',
            'og:site_name': 'site_name'
        }
        
        for og_tag, key in og_tags.items():
            tag = soup.find('meta', property=og_tag)
            if tag and tag.get('content'):
                og_data[key] = tag.get('content')
        
        return og_data
    
    def extract_twitter_card_data(self, soup):
        """Extrae metadatos de Twitter Card"""
        twitter_data = {}
        
        twitter_tags = {
            'twitter:title': 'title',
            'twitter:description': 'description',
            'twitter:image': 'image'
        }
        
        for twitter_tag, key in twitter_tags.items():
            tag = soup.find('meta', attrs={'name': twitter_tag})
            if tag and tag.get('content'):
                twitter_data[key] = tag.get('content')
        
        return twitter_data
    
    def extract_title(self, soup, og_data, twitter_data):
        """Extrae el título de la página"""
        # Prioridad: Open Graph > Twitter Card > Title tag > H1
        if og_data.get('title'):
            return og_data['title']
        if twitter_data.get('title'):
            return twitter_data['title']
        
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Sin título"
    
    def extract_description(self, soup, og_data, twitter_data):
        """Extrae la descripción/resumen de la página"""
        # Prioridad: Open Graph > Twitter Card > Meta description > Primer párrafo
        if og_data.get('description'):
            return og_data['description']
        if twitter_data.get('description'):
            return twitter_data['description']
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()
        
        # Intentar obtener el primer párrafo con contenido sustancial
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 100:  # Al menos 100 caracteres
                return text[:300] + "..."  # Limitar a 300 caracteres
        
        return "Sin descripción disponible"
    
    def extract_image_url(self, soup, og_data, twitter_data):
        """Extrae la URL de la imagen principal"""
        # Prioridad: Open Graph > Twitter Card > Primera imagen relevante
        if og_data.get('image'):
            return og_data['image']
        if twitter_data.get('image'):
            return twitter_data['image']
        
        # Buscar imágenes en el contenido
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            # Filtrar imágenes pequeñas o de tracking
            if src and not any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'pixel', '1x1']):
                if img.get('width', 0) or img.get('height', 0):
                    try:
                        width = int(img.get('width', 0))
                        height = int(img.get('height', 0))
                        if width >= 300 or height >= 300:
                            return src
                    except:
                        pass
        
        return None
    
    def determine_provider(self, url):
        """Determina el proveedor/fuente basándose en la URL"""
        domain = urlparse(url).netloc
        
        # Quitar 'www.' si existe
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Mapeo de dominios conocidos
        providers = {
            'openai.com': 'OpenAI Blog',
            'anthropic.com': 'Anthropic Blog',
            'techcrunch.com': 'TechCrunch',
            'theverge.com': 'The Verge',
            'arstechnica.com': 'Ars Technica',
            'wired.com': 'Wired',
            'medium.com': 'Medium',
            'github.com': 'GitHub',
            'youtube.com': 'YouTube',
            'youtu.be': 'YouTube',
            'twitter.com': 'Twitter/X',
            'x.com': 'Twitter/X',
            'arxiv.org': 'arXiv',
            'news.ycombinator.com': 'Hacker News'
        }
        
        return providers.get(domain, domain.capitalize())
    
    def determine_content_type(self, soup, og_data, url):
        """Determina el tipo de contenido"""
        # Verificar tipo Open Graph
        og_type = og_data.get('type', '').lower()
        
        if 'video' in og_type or 'youtube.com' in url or 'youtu.be' in url:
            return 'Video'
        if 'article' in og_type:
            return 'Artículo de Blog'
        if 'arxiv.org' in url or 'research' in url.lower():
            return 'Investigación'
        if 'news' in url.lower() or 'techcrunch' in url.lower():
            return 'Noticia'
        if 'tutorial' in url.lower() or 'guide' in url.lower():
            return 'Tutorial'
        if 'docs' in url.lower() or 'documentation' in url.lower():
            return 'Documentación'
        
        return 'Artículo de Blog'  # Por defecto
    
    def generate_image(self, title, summary):
        """Genera una imagen usando una API de generación de imágenes"""
        if not IMAGE_API_CONFIG['api_key'] or not IMAGE_API_CONFIG['api_url']:
            print("[WARNING] API de generación de imágenes no configurada")
            return None
        
        try:
            # Este es un ejemplo genérico. Adapta según la API que uses
            prompt = f"Create a professional blog post header image for: {title}"
            
            # Aquí deberías implementar la llamada específica a tu API
            # Por ejemplo, para OpenAI DALL-E:
            # response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
            # image_url = response['data'][0]['url']
            
            print("[INFO] Generación de imágenes no implementada completamente")
            return None
            
        except Exception as e:
            print(f"[ERROR] Error generando imagen: {str(e)}")
            return None
    
    def process_url(self, url, message_date):
        """Procesa una URL y extrae toda la información necesaria"""
        print(f"[INFO] Procesando URL: {url}")
        
        # Obtener contenido HTML
        html_content = self.fetch_url_content(url)
        if not html_content:
            return None
        
        # Parsear HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extraer metadatos
        og_data = self.extract_open_graph_data(soup)
        twitter_data = self.extract_twitter_card_data(soup)
        
        # Extraer información
        title = self.extract_title(soup, og_data, twitter_data)
        summary = self.extract_description(soup, og_data, twitter_data)
        image_url = self.extract_image_url(soup, og_data, twitter_data)
        
        # Si no hay imagen, intentar generar una
        if not image_url:
            image_url = self.generate_image(title, summary)
        
        # Determinar proveedor y tipo de contenido
        provider = self.determine_provider(url)
        content_type = self.determine_content_type(soup, og_data, url)
        
        # Construir objeto de datos del post
        post_data = {
            'title': title,
            'summary': summary[:500],  # Limitar resumen a 500 caracteres
            'source_url': url,
            'image_url': image_url or '',
            'release_date': message_date,
            'provider': provider,
            'type': content_type
        }
        
        return post_data