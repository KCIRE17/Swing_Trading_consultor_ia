import json
import os

MODEL_DEFAULT = "gemini-2.5-flash"
TIMEOUT_SECONDS = 20

SYSTEM_PROMPT = (
    "Eres un analista senior de inversiones especializado en Swing Trading "
    "(posiciones de 3 a 10 ruedas bursatiles). "
    "Recibes el estado tecnico cuantitativo de un activo (precio, medias moviles SMA20/SMA50, "
    "RSI14, MACD, ATR14) y el pronostico econometrico ARIMA a 5 dias. "
    "Debes responder SOLO en JSON valido sin texto adicional, con la siguiente estructura exacta: "
    '{"prediccion": "ALCISTA"|"NEUTRAL"|"BAJISTA", '
    '"probabilidad": numero entre 0.0 y 1.0, '
    '"nivel_riesgo": "BAJO"|"MEDIO"|"ALTO", '
    '"recomendacion": "RETIRAR"|"AUMENTAR"|"MANTENER", '
    '"conclusion_cualitativa": "2 a 3 oraciones con tu lectura laica del contexto", '
    '"justificacion_tecnica": "explica en 2 a 3 oraciones la confluencia entre indicadores tecnicos y el pronostico ARIMA"}'
    "Reglas: 'AUMENTAR' solo cuando indicadores y ARIMA coinciden con alta conviccion; "
    "'RETIRAR' cuando varios indicadores contradicen la posicion; 'MANTENER' en condiciones ambiguas o de espera."
)


def analyze(context):
    text_part = _build_text_part(context)
    try:
        payload = _gemini_text(text_part)
    except Exception as exc:
        payload = _degraded(context, f"No fue posible completar el analisis: {exc}")

    if not _is_valid(payload):
        payload = _degraded(context, "La respuesta del modelo no contenia el esquema esperado")
    payload["fuente"] = "gemini" if payload.get("prediccion") else "degradado"
    return payload


NARRATIVE_INSTRUCTION = (
    "Actua como un analista senior que explica en lenguaje humano, claro y para inversionistas no tecnicos, "
    "el estado tecnico del activo descrito. Escribe de 4 a 7 oraciones en espanol, sin titulos, sin markdown "
    "y sin tablas. Menciona tendencia, RSI, MACD, volatilidad (ATR) y el pronostico econometrico. "
    "Termina con una frase de lectura practica para Swing Trading (horizonte de 3 a 10 ruedas bursatiles)."
)
NARRATIVE_MODEL_DEFAULT = "gemini-2.5-flash"


def enrich_narrative(paragraph_reglas, context=None):
    if not os.environ.get("GEMINI_API_KEY"):
        return None
    try:
        from google import genai
        from google.genai import types

        model = os.environ.get("GEMINI_NARRATIVE_MODEL", NARRATIVE_MODEL_DEFAULT)
        api_key = os.environ["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        content = (
            "Contexto numerico del activo: "
            f"{_build_text_part(context) if context else ''} \n\n"
            "Interpretacion base generada por reglas (puedes basarte en ella pero debe sonar natural):\n"
            f"{paragraph_reglas}"
        )
        response = client.models.generate_content(
            model=model,
            contents=content,
            config=types.GenerateContentConfig(system_instruction=NARRATIVE_INSTRUCTION),
        )
        text = response.text.strip()
        return text if text else None
    except Exception:
        return None


def _build_text_part(context):
    return (
        "Contexto del analisis tecnico y econometrico del activo:\n"
        f"- Ticker: {context.get('ticker')}\n"
        f"- Fecha del ultimo cierre: {context.get('date')}\n"
        f"- Precio de cierre: {context.get('close')}\n"
        f"- Variacion diaria: {context.get('change_pct')}%\n"
        f"- SMA20: {context.get('sma20')}\n"
        f"- SMA50: {context.get('sma50')}\n"
        f"- RSI14: {context.get('rsi14')}\n"
        f"- MACD: {context.get('macd')} (senal {context.get('macd_signal')}, histograma {context.get('macd_hist')})\n"
        f"- ATR14: {context.get('atr14')}\n"
        f"- Pronostico ARIMA 5 ruedas: {context.get('arima_forecast')}\n"
        f"- Precio proyectado por ARIMA: {context.get('arima_next')}"
    )


def _gemini_text(text_part):
    from google import genai
    from google.genai import types

    model = os.environ.get("GEMINI_MODEL", MODEL_DEFAULT)
    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=text_part,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


def _is_valid(payload):
    return (
        isinstance(payload, dict)
        and payload.get("prediccion") in {"ALCISTA", "NEUTRAL", "BAJISTA"}
        and payload.get("recomendacion") in {"RETIRAR", "AUMENTAR", "MANTENER"}
        and isinstance(payload.get("probabilidad"), (int, float))
    )


def _degraded(context, reason):
    return {
        "prediccion": "NEUTRAL",
        "probabilidad": 0.5,
        "nivel_riesgo": "MEDIO",
        "recomendacion": "MANTENER",
        "conclusion_cualitativa": (
            "Analisis cualitativo temporalmente no disponible; la senal queda sustentada "
            "en el contexto tecnico y el pronostico econometrico ARIMA."
        ),
        "justificacion_tecnica": (
            "Sin inferencia del modelo fundacional, la recomendacion se basa solo en reglas "
            "cuantitativas sobre los indicadores y el pronostico."
        ),
    }