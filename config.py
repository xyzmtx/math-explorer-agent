"""
Math Explorer Agent Configuration File

IMPORTANT: Set these environment variables before running:
  - API_KEY: Your LLM API key
  - BASE_URL: API endpoint (optional, defaults to OpenAI)
  - MODEL: Model name (optional, defaults to gpt-4)
"""
import os

# Load .env file if it exists (requires: pip install python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()  # Loads .env file from current directory
except ImportError:
    pass  # dotenv not installed, use system environment variables only

# API Configuration - MUST be set via environment variables or .env file
API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('BASE_URL', 'https://api.openai.com/v1')
MODEL = os.getenv('MODEL', 'gpt-4')

if not API_KEY:
    import sys
    print("ERROR: API_KEY environment variable is not set!")
    print("Please set it before running:")
    print("  Windows: set API_KEY=your-api-key")
    print("  Linux/Mac: export API_KEY=your-api-key")
    # Don't exit in case we're just importing for documentation

# LLM Call Configuration
LLM_TIMEOUT = 600.0          # Timeout in seconds, deep thinking models may need longer time
LLM_MAX_RETRIES = 3          # Maximum retry count
LLM_DEFAULT_MAX_TOKENS = 32768  # Default maximum tokens (32K), DeepSeek-V3.2-Thinking limit
LLM_DEFAULT_TEMPERATURE = 0.7   # Default temperature

# Memory Save Path
MEMORY_SAVE_PATH = './memory_snapshots/'
LOG_PATH = './logs/'

# Verifier Configuration
MAX_VERIFY_ROUNDS = 3  # Maximum modification rounds
PROOF_CHUNK_SIZE = 6   # Number of lines per verification segment

# Parallel Configuration
MAX_PARALLEL_ACTIONS = 10
