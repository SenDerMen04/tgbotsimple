# Заглушка для анализа описаний группы / музыкантов

def analyze_band_description(description):
    """
    Простая функция-заглушка, которая "определяет жанр" по тексту.
    Можно использовать реальные AI сервисы.
    """
    description = description.lower()
    if "рок" in description:
        genre = "Рок"
    elif "джаз" in description:
        genre = "Джаз"
    elif "поп" in description:
        genre = "Поп"
    elif "метал" in description:
        genre = "Метал"
    else:
        genre = "Разное"

    return {"genre": genre}

def analyze_image_issue(file_bytes, caption=""):
    """
    Заглушка для анализа изображений.
    Возвращает фиктивные данные.
    """
    return {
        "problem": "Н/Д",
        "danger": "Н/Д",
        "specialization": "general"
    }
