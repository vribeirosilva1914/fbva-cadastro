FROM rssbridge/rss-bridge:latest

# Copia a lista de pontes permitidas
COPY whitelist.txt /app/whitelist.txt

# Render injeta $PORT — usa PHP built-in server (Apache não usa $PORT por padrão)
CMD ["sh", "-c", "php -S 0.0.0.0:${PORT:-80} -t /app"]
