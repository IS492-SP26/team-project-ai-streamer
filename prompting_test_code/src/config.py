import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # API Endpoints
    CLAUDE_MESSAGES_URL = 'https://api.anthropic.com/v1/messages'
    OPENAI_CHAT_URL = 'https://api.openai.com/v1/chat/completions'
    GEMINI_GENERATE_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
    
    # Models
    CLAUDE_MODEL = 'claude-haiku-4-5-20251001'
    OPENAI_MODEL = 'gpt-4o-mini'
    GEMINI_MODEL = 'gemini-2.5-flash' 
    
    # Request settings
    REQUEST_DELAY = 1.5
    MAX_RETRIES = 3
    TIMEOUT = 30
