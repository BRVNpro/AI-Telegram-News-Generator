import httpx


class OllamaClient:
    """
    Клиент для взаимодействия с Ollama API.

    Предоставляет асинхронный интерфейс для генерации текста
    с использованием языковых моделей Ollama.
    """

    def __init__(self, base_url: str, model: str, timeout: float = 60.0):
        """
        Инициализация клиента Ollama.

        Args:
            base_url: Базовый URL сервера Ollama (например, "http://localhost:11434")
            model: Название модели для использования (например, "llama2", "mistral")
            timeout: Таймаут запроса в секундах (по умолчанию 60.0)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(self, prompt: str) -> str:
        """
        Генерирует текст на основе переданного промпта.

        Args:
            prompt: Текстовый промпт для генерации ответа

        Returns:
            str: Сгенерированный текст (обрезанный от пробелов)

        Raises:
            httpx.HTTPStatusError: При ошибке HTTP-запроса
            httpx.RequestError: При ошибке соединения с сервером
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            return (data.get("response") or "").strip()