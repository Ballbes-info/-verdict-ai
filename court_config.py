COURT_MODELS = [
    # === Groq ===
    {"id": "groq/llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "service": "Groq", "strength": 5,
     "speed": "Мгновенно", "speed_cls": "instant", "russian": "good", "tokens": "Средняя"},
    {"id": "groq/openai-gpt-oss-120b", "name": "GPT-OSS 120B", "service": "Groq", "strength": 5, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "good", "tokens": "Затратная"},
    {"id": "groq/qwen-qwen3-32b", "name": "Qwen 3 32B", "service": "Groq", "strength": 4, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "good", "tokens": "Средняя"},
    {"id": "groq/meta-llama-llama-4-scout-17b-16e-instruct", "name": "Llama 4 Scout 17B", "service": "Groq",
     "strength": 4, "speed": "Мгновенно", "speed_cls": "instant", "russian": "mid", "tokens": "Средняя"},
    {"id": "groq/qwen-qwen3.6-27b", "name": "Qwen 3.6 27B", "service": "Groq", "strength": 4, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "good", "tokens": "Средняя"},
    {"id": "groq/llama-3.1-8b-instant", "name": "Llama 3.1 8B", "service": "Groq", "strength": 3, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "mid", "tokens": "Экономная"},
    {"id": "groq/openai-gpt-oss-20b", "name": "GPT-OSS 20B", "service": "Groq", "strength": 3, "speed": "Мгновенно",
     "speed_cls": "instant", "russian": "good", "tokens": "Средняя"},

    # === Mistral ===
    {"id": "mistral/mistral-large-latest", "name": "Mistral Large", "service": "Mistral", "strength": 5,
     "speed": "Быстро", "speed_cls": "fast", "russian": "good", "tokens": "Затратная"},
    {"id": "mistral/mistral-medium-latest", "name": "Mistral Medium", "service": "Mistral", "strength": 4,
     "speed": "Быстро", "speed_cls": "fast", "russian": "good", "tokens": "Средняя"},
    {"id": "mistral/mistral-small-latest", "name": "Mistral Small", "service": "Mistral", "strength": 3,
     "speed": "Быстро", "speed_cls": "fast", "russian": "good", "tokens": "Экономная"},
    {"id": "mistral/open-mistral-nemo", "name": "Mistral Nemo", "service": "Mistral", "strength": 3, "speed": "Быстро",
     "speed_cls": "fast", "russian": "good", "tokens": "Средняя"},
    {"id": "mistral/ministral-8b-latest", "name": "Ministral 8B", "service": "Mistral", "strength": 3,
     "speed": "Быстро", "speed_cls": "fast", "russian": "mid", "tokens": "Экономная"},
    {"id": "mistral/ministral-3b-latest", "name": "Ministral 3B", "service": "Mistral", "strength": 2,
     "speed": "Быстро", "speed_cls": "fast", "russian": "mid", "tokens": "Экономная"},

    # === OpenRouter ===
    {"id": "openrouter/nvidia-nemotron-3-ultra-550b-a55b", "name": "Nemotron 3 Ultra", "service": "OpenRouter",
     "strength": 5, "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Затратная"},
    {"id": "openrouter/nvidia-nemotron-3-super-120b-a12b", "name": "Nemotron 3 Super", "service": "OpenRouter",
     "strength": 5, "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Затратная"},
    {"id": "openrouter/openai-gpt-oss-120b", "name": "GPT-OSS 120B", "service": "OpenRouter", "strength": 5,
     "speed": "Средне", "speed_cls": "mid", "russian": "good", "tokens": "Затратная"},
    {"id": "openrouter/google-gemma-4-26b-a4b-it", "name": "Gemma 4 26B", "service": "OpenRouter", "strength": 4,
     "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Средняя"},
    {"id": "openrouter/nvidia-nemotron-3-nano-30b-a3b", "name": "Nemotron Nano 30B", "service": "OpenRouter",
     "strength": 3, "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Экономная"},
    {"id": "openrouter/nvidia-nemotron-nano-9b-v2", "name": "Nemotron Nano 9B", "service": "OpenRouter", "strength": 3,
     "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Средняя"},
    {"id": "openrouter/cohere-north-mini-code", "name": "North Mini Code", "service": "OpenRouter", "strength": 3,
     "speed": "Средне", "speed_cls": "mid", "russian": "mid", "tokens": "Экономная"},

    # === GitHub ===
    {"id": "github/gpt-4o", "name": "GPT-4o", "service": "GitHub", "strength": 5, "speed": "Средне", "speed_cls": "mid",
     "russian": "good", "tokens": "Средняя"},
    {"id": "github/gpt-4o-mini", "name": "GPT-4o mini", "service": "GitHub", "strength": 5, "speed": "Средне",
     "speed_cls": "mid", "russian": "good", "tokens": "Экономная"},

    # === Cerebras ===
    {"id": "cerebras/gpt-oss-120b", "name": "GPT-OSS 120B", "service": "Cerebras", "strength": 5, "speed": "Быстро",
     "speed_cls": "fast", "russian": "good", "tokens": "Затратная"},
    {"id": "cerebras/gemma-4-31b", "name": "Gemma 4 31B", "service": "Cerebras", "strength": 4, "speed": "Быстро",
     "speed_cls": "fast", "russian": "mid", "tokens": "Средняя"},

    # === Cloudflare ===
    {"id": "cloudflare/deepseek-r1-distill-qwen-32b", "name": "DeepSeek R1 32B", "service": "Cloudflare", "strength": 4,
     "speed": "Быстро", "speed_cls": "fast", "russian": "good", "tokens": "Средняя"},
    {"id": "cloudflare/llama-3.1-8b-instruct", "name": "Llama 3.1 8B", "service": "Cloudflare", "strength": 3,
     "speed": "Быстро", "speed_cls": "fast", "russian": "mid", "tokens": "Экономная"},

    # === GigaChat ===
    {"id": "gigachat/gigachat", "name": "GigaChat (Сбер)", "service": "GigaChat", "strength": 3, "speed": "Средне",
     "speed_cls": "mid", "russian": "native", "tokens": "Средняя"},

    # === Gemini ===
    {"id": "gemini/gemini-2.5-flash", "name": "Gemini 2.5 Flash", "service": "Gemini", "strength": 3, "speed": "Средне",
     "speed_cls": "mid", "russian": "good", "tokens": "Экономная"},
]

CLASSIC_COURT_ROLES = [
    {"key": "prosecutor", "name": "Прокурор", "accent": "red"},
    {"key": "advocate", "name": "Адвокат", "accent": "blue"},
    {"key": "judge", "name": "Судья", "accent": "gold"},
]

PROMPT_VERSIONS = [
    {
        "key": "FULL",
        "name": "FULL — Максимальное качество",
        "tokens": "1500-4000",
        "icon": "⭐",
        "desc": "Детальные аргументы, глубокий анализ",
        "tags": ["Глубокий", "Качественный", "Premium"]
    },
    {
        "key": "MEDIUM",
        "name": "MEDIUM — Оптимальный баланс",
        "tokens": "400-1000",
        "icon": "⚖️",
        "desc": "Хорошее качество, экономия токенов",
        "tags": ["Баланс", "Основной", "Экономный"]
    },
    {
        "key": "COMPACT",
        "name": "COMPACT — Быстро и дёшево",
        "tokens": "100-400",
        "icon": "⚡",
        "desc": "Быстрые игры, минимальные затраты",
        "tags": ["Быстрый", "Экономичный", "Массовый"]
    },
]