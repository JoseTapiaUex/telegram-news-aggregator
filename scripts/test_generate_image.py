from src.agent.content_processor import ContentProcessor

if __name__ == '__main__':
    cp = ContentProcessor()
    print('ContentProcessor created')
    res = cp.generate_image('Test Title for Gemini', 'Resumen de prueba para generar una imagen con Gemini. If Gemini SDK is not installed, fallback should happen and function should return None or print warnings.')
    print('generate_image returned:', res)
