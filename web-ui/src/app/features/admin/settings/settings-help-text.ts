/**
 * Help text content for all settings page fields
 */
export const SETTINGS_HELP_TEXT: { [section: string]: { [field: string]: string } } = {
  system: {
    systemName: 'The name displayed throughout the application in the header, footer, and login page. This helps personalize your RAG system.'
  },
  confluence: {
    url: 'Your Confluence instance URL. For Cloud: https://your-domain.atlassian.net. For Server: https://confluence.example.com',
    instanceType: 'Select whether you\'re using Confluence Cloud or Confluence Server/Data Center. This determines the authentication method.',
    apiToken: 'For Confluence Cloud, generate an API token from your Atlassian account settings. For Server, use a Personal Access Token.',
    username: 'Your Confluence username. Required for Server/Data Center instances or as an alternative to API token.',
    password: 'For Cloud: use your API token here. For Server: use your account password or Personal Access Token.',
    pageIds: 'Comma-separated list of Confluence page IDs to sync. Find page IDs in the page URL: /pages/viewpage.action?pageId=123456',
    autoSync: 'Enable automatic synchronization to periodically fetch and update Confluence pages. Pages are checked at the specified interval.',
    syncInterval: 'How often (in seconds) to check for updates. Minimum: 60 seconds. Lower values increase server load.'
  },
  llmProviders: {
    model: 'The language model to use for text generation. Examples: mistral, llama2, gpt-4, claude-3-opus. Must match your provider\'s available models.',
    temperature: 'Controls randomness in responses (0-2). Lower values (0-0.5) = more focused/deterministic. Higher values (1-2) = more creative/varied.',
    apiKey: 'Your API key for the LLM provider. Required for cloud providers (OpenAI, Anthropic, etc.). Leave empty for local providers (Ollama).',
    baseUrl: 'API endpoint URL. For Ollama: http://localhost:11434. For cloud providers, usually auto-detected. Override if using a proxy or custom endpoint.'
  },
  embeddingProviders: {
    model: 'The embedding model to use for converting text to vectors. Examples: nomic-embed-text, text-embedding-ada-002. Must match your provider\'s available models.',
    apiKey: 'Your API key for the embedding provider. Required for cloud providers. Leave empty for local providers (Ollama).',
    baseUrl: 'API endpoint URL. For Ollama: http://localhost:11434. For cloud providers, usually auto-detected. Override if using a proxy or custom endpoint.'
  }
};

