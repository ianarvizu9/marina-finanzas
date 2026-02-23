from .banjercito_parser import BanjercitoParser

def detect_parser(text: str):
    """
    Detecta qué banco generó el estado de cuenta
    y devuelve la clase parser correspondiente.
    """

    text_lower = text.lower()

    if "banjercito" in text_lower:
        return BanjercitoParser()

    # Aquí después agregamos más bancos:
    # if "banorte" in text_lower:
    #     return BanorteParser()

    raise ValueError("No se pudo identificar el banco del estado de cuenta")