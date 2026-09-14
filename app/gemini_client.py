import base64
import io
import json
import os

import requests
from PIL import Image

MODEL_DEFAULT = "gemini-2.5-flash"
TIMEOUT_SECONDS = 20
MAX_IMAGE_SIZE = 1024
IMAGE_QUALITY = 85
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

SYSTEM_PROMPT = (
    "Eres un analista de inversiones especializado en Swing Trading (posiciones de 3 a 10 ruedas bursatiles). "
    "Recibes el estado tecnico cuantitativo de un activo (precio, medias moviles SMA20/SMA50, RSI14, MACD, ATR14) "
    "y el pronostico econometrico ARIMA a 5 dias, junto con una imagen de noticia financiera. "
    "Debes responder SOLO en JSON valido sin texto adicional, con la siguiente estructura exacta: "
    '{"prediccion": "ALCISTA"|"NEUTRAL"|"BAJISTA", '
    '"probabilidad": numero entre 0.0 y 1.0, '
    '"nivel_riesgo": "BAJO"|"MEDIO"|"ALTO", '
    '"resumen_noticia": "1 a 2 oraciones resumiendo el evento fundamental de la imagen", '
    '"justificacion_tecnica": "explica la confluencia entre los indicadores tecnicos y el contexto visual de la noticia"}'
)


def analyze(context, image_url=None, image_bytes=None):
    text_part = _build_text_part(context)
    image_part = None
    if image_bytes is not None:
        try:
            image_part = {
                "mime_type": "image/jpeg",
                "data": _prepare_bytes(image_bytes),
            }
        except Exception as exc:
            image_part = None
            text_part += f"\n[Nota: la imagen no pudo procesarse: {exc}]"
    elif image_url:
        try:
            image_part = {
                "mime_type": "image/jpeg",
                "data": _download_and_prepare(image_url),
            }
        except Exception as exc:
            image_part = None
            text_part += f"\n[Nota: la imagen no pudo descargarse: {exc}]"

    payload = {}
    if image_part is not None:
        try:
            payload = _gemini_multimodal(text_part, image_part)
        except Exception as exc:
            payload = _degraded(context, f"No fue posible completar el analisis multimodal: {exc}")
    else:
        try:
            payload = _gemini_text(text_part)
        except Exception as exc:
            payload = _degraded(context, f"No fue posible completar el analisis: {exc}")

    if not _is_valid(payload):
        payload = _degraded(context, "La respuesta del modelo no contenia el esquema esperado")
    payload["fuente"] = "gemini" if payload.get("prediccion") else "degradado"
    payload["con_imagen"] = image_part is not None
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
        f"- Precio proyectado por ARIMA: {context.get('arima_next')}\n"
        "Adicionalmente te adjunto la imagen de la noticia financiera del dia."
    )


def _download_and_prepare(image_url):
    response = requests.get(
        image_url,
        timeout=TIMEOUT_SECONDS,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "image/jpeg")
    if not content_type.startswith("image"):
        raise ValueError(f"La URL no devolvio una imagen (Content-Type: {content_type})")
    return _prepare_bytes(response.content)


def _prepare_bytes(image_bytes):
    original = Image.open(io.BytesIO(image_bytes))
    original.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.LANCZOS)
    if original.mode not in ("RGB", "L"):
        original = original.convert("RGB")
    buffer = io.BytesIO()
    original.save(buffer, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
    return buffer.getvalue()


def _gemini_multimodal(text_part, image_part):
    from google import genai
    from google.genai import types

    model = os.environ.get("GEMINI_MODEL", MODEL_DEFAULT)
    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_part["data"], mime_type=image_part["mime_type"]),
                types.Part.from_text(text_part),
            ],
        ),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


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
        and isinstance(payload.get("probabilidad"), (int, float))
    )


def _degraded(context, reason):
    return {
        "prediccion": "NEUTRAL",
        "probabilidad": 0.5,
        "nivel_riesgo": "MEDIO",
        "resumen_noticia": f"Analisis multimodal temporalmente no disponible. {reason}",
        "justificacion_tecnica": (
            "Sin inferencia del modelo fundacional, la senal se basa solo en el contexto tecnico "
            "y el pronostico econometrico ARIMA."
        ),
    }