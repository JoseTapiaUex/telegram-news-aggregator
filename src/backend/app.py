"""
Servidor Flask con API REST
Ruta: src/backend/app.py
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import FLASK_CONFIG
from src.backend.database import Database


def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    
    # Habilitar CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Instanciar base de datos
    db = Database()
    
    # Ruta para servir el frontend
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def static_files(path):
        return send_from_directory(app.static_folder, path)
    
    # ==================== ENDPOINTS DEL API ====================
    
    @app.route('/api/posts', methods=['GET'])
    def get_posts():
        """Obtiene todos los posts con paginación opcional"""
        try:
            # Parámetros de paginación
            limit = request.args.get('limit', type=int)
            offset = request.args.get('offset', default=0, type=int)
            
            # Filtros opcionales
            provider = request.args.get('provider')
            content_type = request.args.get('type')
            search = request.args.get('search')
            
            # Aplicar filtros
            if search:
                posts = db.search_posts(search)
            elif provider:
                posts = db.get_posts_by_provider(provider)
            elif content_type:
                posts = db.get_posts_by_type(content_type)
            else:
                posts = db.get_all_posts(limit=limit, offset=offset)
            
            return jsonify({
                'success': True,
                'posts': posts,
                'count': len(posts)
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/posts/<int:post_id>', methods=['GET'])
    def get_post(post_id):
        """Obtiene un post específico por ID"""
        try:
            post = db.get_post_by_id(post_id)
            
            if post:
                return jsonify({
                    'success': True,
                    'post': post
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Post no encontrado'
                }), 404
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/posts', methods=['POST'])
    def create_post():
        """Crea un nuevo post"""
        try:
            data = request.get_json()
            
            # Validar campos requeridos
            required_fields = ['title', 'summary', 'source_url', 'release_date']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({
                    'success': False,
                    'error': f'Campos faltantes: {", ".join(missing_fields)}'
                }), 400
            
            # Insertar post
            post = db.insert_post(data)
            
            if post:
                return jsonify({
                    'success': True,
                    'post': post,
                    'message': 'Post creado exitosamente'
                }), 201
            else:
                return jsonify({
                    'success': False,
                    'error': 'Post duplicado o error al insertar'
                }), 409
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/posts/<int:post_id>', methods=['DELETE'])
    def delete_post(post_id):
        """Elimina un post por ID"""
        try:
            deleted = db.delete_post(post_id)
            
            if deleted:
                return jsonify({
                    'success': True,
                    'message': 'Post eliminado exitosamente'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Post no encontrado'
                }), 404
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Obtiene estadísticas generales"""
        try:
            stats = db.get_stats()
            
            return jsonify({
                'success': True,
                'stats': stats
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Endpoint de salud del API"""
        return jsonify({
            'success': True,
            'status': 'healthy',
            'message': 'API funcionando correctamente'
        }), 200
    
    # Manejador de errores 404
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint no encontrado'
        }), 404
    
    # Manejador de errores 500
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500
    
    return app


def main():
    """Función principal para ejecutar el servidor"""
    app = create_app()
    
    print(f"\n{'='*60}")
    print(f"🚀 Servidor Flask iniciado")
    print(f"{'='*60}")
    print(f"📡 API disponible en: http://{FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}/api")
    print(f"🌐 Frontend disponible en: http://localhost:{FLASK_CONFIG['port']}")
    print(f"{'='*60}\n")
    
    app.run(
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port'],
        debug=FLASK_CONFIG['debug']
    )


if __name__ == '__main__':
    main()