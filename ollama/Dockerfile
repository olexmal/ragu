FROM ollama/ollama:latest

# Pre-pull required models
# Note: This will be done at container startup via entrypoint script
# as Ollama needs to be running to pull models

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ollama", "serve"]

