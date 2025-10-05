import os
import sys
sys.path.append('src')

from agent.content_processor import ContentProcessor

# Test image generation
processor = ContentProcessor()

# Test image generation
processor = ContentProcessor()

# Test with title and description
result = processor.generate_image("Test title", "Test description")

print(f"Generated image URL: {result}")

print(f"Generated image URL: {result}")