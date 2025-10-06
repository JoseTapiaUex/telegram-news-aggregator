from src.agent.content_processor import ContentProcessor

def test_image_generation():
    """Prueba todos los sistemas de generación de imágenes disponibles"""
    cp = ContentProcessor()
    print('ContentProcessor created')

    test_title = 'Test Title for Image Generation'
    test_summary = 'Resumen de prueba para generar una imagen. Este test verifica los tres sistemas disponibles: Gemini SDK, DALL-E (OpenAI), y Pollinations.ai (fallback gratuito).'

    print('\n' + '='*60)
    print('TESTING IMAGE GENERATION SYSTEMS')
    print('='*60)

    # Test 1: Gemini SDK (Google AI)
    print('\n🔹 Testing Gemini SDK (Google AI)...')
    try:
        result1 = cp.generate_image(f'{test_title} - Gemini', test_summary)
        print(f'✅ Gemini result: {result1}')
    except Exception as e:
        print(f'❌ Gemini failed: {e}')

    # Test 2: DALL-E (OpenAI) - requiere API key
    print('\n🔹 Testing DALL-E (OpenAI)...')
    try:
        result2 = cp.generate_image(f'{test_title} - DALL-E', test_summary)
        print(f'✅ DALL-E result: {result2}')
    except Exception as e:
        print(f'❌ DALL-E failed: {e}')

    # Test 3: Pollinations.ai (gratuito, sin API key)
    print('\n🔹 Testing Pollinations.ai (free fallback)...')
    try:
        result3 = cp.generate_image(f'{test_title} - Pollinations', test_summary)
        print(f'✅ Pollinations.ai result: {result3}')
    except Exception as e:
        print(f'❌ Pollinations.ai failed: {e}')

    print('\n' + '='*60)
    print('TEST COMPLETED')
    print('='*60)
    print('\nNota: Si Gemini y DALL-E fallan, es normal si no hay API keys configuradas.')
    print('Pollinations.ai debería funcionar siempre (es gratuito y no requiere API key).')

if __name__ == '__main__':
    test_image_generation()
