import os
from dotenv import load_dotenv

load_dotenv()

#Memory
MEMORY_BACKEND = os.getenv(
    "MEMORY_BACKEND",
    "memory"
)

# Redis
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

# LLM
LLM_MODEL = "deepseek-flash"

# Agent
MAX_AGENT_STEPS = 5

# Memory
MAX_HISTORY_TURNS = 5

# Tool / RAG policy
MAX_RAG_SEARCHES_PER_REQUEST = 1
DEFAULT_RAG_TOP_K = 3

# RAG
RETRIEVAL_TOP_N = 5
RETRIEVAL_MIN_SCORE = 0.4

RERANK_TOP_K = 3
RERANK_MIN_SCORE = 0.5

# log
LOG_LEVEL = "INFO"