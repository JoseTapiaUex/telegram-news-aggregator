import sqlite3
conn = sqlite3.connect('data/posts.db')
c = conn.cursor()
c.execute("UPDATE posts SET image_url = REPLACE(image_url, '.png', '.jpg') WHERE image_url LIKE '%/generated/%'")
conn.commit()
conn.close()
print('Updated image URLs in DB')