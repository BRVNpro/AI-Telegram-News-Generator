from datetime import datetime
from pydantic import BaseModel


class SourceIn(BaseModel):
    """
    Схема для создания/обновления источника новостей.

    Attributes:
        type: Тип источника (например, 'rss', 'api', 'web')
        name: Название источника
        url: URL источника
        enabled: Флаг активности источника (по умолчанию True)
    """
    type: str
    name: str
    url: str
    enabled: bool = True


class SourceOut(SourceIn):
    """
    Схема для возврата данных источника новостей.

    Наследует все поля от SourceIn и добавляет идентификатор.

    Attributes:
        id: Уникальный идентификатор источника
    """
    id: str


class KeywordIn(BaseModel):
    """
    Схема для создания ключевого слова.

    Attributes:
        word: Ключевое слово для поиска/фильтрации новостей
    """
    word: str


class KeywordOut(KeywordIn):
    """
    Схема для возврата данных ключевого слова.

    Наследует все поля от KeywordIn и добавляет идентификатор.

    Attributes:
        id: Уникальный идентификатор ключевого слова
    """
    id: str


class NewsOut(BaseModel):
    """
    Схема для возврата данных новости.

    Attributes:
        id: Уникальный идентификатор новости
        title: Заголовок новости
        url: URL новости (может быть None)
        summary: Краткое содержание новости
        source: Источник новости
        published_at: Дата и время публикации новости
    """
    id: str
    title: str
    url: str | None
    summary: str
    source: str
    published_at: datetime


class PostOut(BaseModel):
    """
    Схема для возврата данных поста.

    Attributes:
        id: Уникальный идентификатор поста
        news_id: Идентификатор связанной новости
        generated_text: Сгенерированный текст поста (может быть None)
        status: Статус поста (например, 'pending', 'published', 'failed')
        published_at: Дата и время публикации поста (может быть None)
        error: Сообщение об ошибке, если возникла (может быть None)
        created_at: Дата и время создания поста
    """
    id: str
    news_id: str
    generated_text: str | None
    status: str
    published_at: datetime | None
    error: str | None
    created_at: datetime


class GenerateRequest(BaseModel):
    """
    Схема для запроса генерации поста.

    Attributes:
        title: Заголовок для генерации
        summary: Краткое содержание для генерации
        source: Источник контента (по умолчанию 'manual')
        url: URL источника (может быть None)
    """
    title: str
    summary: str
    source: str = "manual"
    url: str | None = None