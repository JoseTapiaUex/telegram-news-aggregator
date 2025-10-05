"""
Gestión de la base de datos SQLite
Ruta: src/backend/database.py
"""
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import DATABASE_CONFIG


class Database:
    """Clase para gestionar operaciones de la base de datos"""
    
    def __init__(self):
        self.db_path = DATABASE_CONFIG['path']
        self.init_database()
    
    def get_connection(self):
        """Crea una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas si no existen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                source_url TEXT NOT NULL UNIQUE,
                image_url TEXT,
                release_date TEXT NOT NULL,
                provider TEXT,
                type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear índices para mejorar el rendimiento
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_release_date ON posts(release_date DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_provider ON posts(provider)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_type ON posts(type)
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"[INFO] Base de datos inicializada: {self.db_path}")
    
    def insert_post(self, post_data):
        """Inserta un nuevo post en la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO posts (title, summary, source_url, image_url, release_date, provider, type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                post_data['title'],
                post_data['summary'],
                post_data['source_url'],
                post_data.get('image_url', ''),
                post_data['release_date'],
                post_data.get('provider', ''),
                post_data.get('type', '')
            ))
            
            conn.commit()
            post_id = cursor.lastrowid
            
            # Obtener el post recién creado
            cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
            post = dict(cursor.fetchone())
            
            conn.close()
            return post
            
        except sqlite3.IntegrityError:
            conn.close()
            print(f"[WARNING] Post duplicado: {post_data['source_url']}")
            return None
        except Exception as e:
            conn.close()
            print(f"[ERROR] Error insertando post: {str(e)}")
            return None
    
    def get_all_posts(self, limit=None, offset=0):
        """Obtiene todos los posts ordenados por fecha de creación"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM posts ORDER BY created_at DESC'
        
        if limit:
            query += f' LIMIT {limit} OFFSET {offset}'
        
        cursor.execute(query)
        posts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return posts
    
    def get_post_by_id(self, post_id):
        """Obtiene un post específico por su ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_posts_by_provider(self, provider):
        """Obtiene posts filtrados por proveedor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM posts WHERE provider = ? ORDER BY created_at DESC',
            (provider,)
        )
        posts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return posts
    
    def get_posts_by_type(self, content_type):
        """Obtiene posts filtrados por tipo de contenido"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM posts WHERE type = ? ORDER BY created_at DESC',
            (content_type,)
        )
        posts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return posts
    
    def search_posts(self, query):
        """Busca posts por título o resumen"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_query = f'%{query}%'
        cursor.execute('''
            SELECT * FROM posts 
            WHERE title LIKE ? OR summary LIKE ?
            ORDER BY created_at DESC
        ''', (search_query, search_query))
        
        posts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return posts
    
    def delete_post(self, post_id):
        """Elimina un post por su ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
        
        deleted = cursor.rowcount > 0
        conn.close()
        
        return deleted
    
    def get_stats(self):
        """Obtiene estadísticas generales de la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total de posts
        cursor.execute('SELECT COUNT(*) as total FROM posts')
        stats['total_posts'] = cursor.fetchone()['total']
        
        # Posts por proveedor
        cursor.execute('''
            SELECT provider, COUNT(*) as count 
            FROM posts 
            GROUP BY provider 
            ORDER BY count DESC
        ''')
        stats['by_provider'] = [dict(row) for row in cursor.fetchall()]
        
        # Posts por tipo
        cursor.execute('''
            SELECT type, COUNT(*) as count 
            FROM posts 
            GROUP BY type 
            ORDER BY count DESC
        ''')
        stats['by_type'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return stats