SL_MULTIPLER = 1.5
TP_MULTIPLER = 3.0
MIN_ALCISTA_PROBABILITY = 0.65
MAX_RSI_BUY = 65.0


def decide(context, gemini):
    close = context.get("close")
    atr_value = context.get("atr14")
    stop_loss = None
    take_profit = None
    if close is not None and atr_value:
        stop_loss = round(close - SL_MULTIPLER * atr_value, 4)
        take_profit = round(close + TP_MULTIPLER * atr_value, 4)

    prediccion = gemini.get("prediccion")
    probabilidad = gemini.get("probabilidad")
    nivel_riesgo = gemini.get("nivel_riesgo")

    reasons = []
    direction = "HOLD"

    if prediccion == "ALCISTA" and probabilidad is not None and probabilidad >= MIN_ALCISTA_PROBABILITY:
        if close is not None and context.get("sma50") and close > context["sma50"]:
            if context.get("rsi14") is not None and context["rsi14"] <= MAX_RSI_BUY:
                direction = "BUY"
                reasons.append("Prediccion ALCISTA con alta probabilidad, precio sobre SMA50 y RSI en zona operativa")
            else:
                reasons.append("Precio sobre SMA50 pero RSI agotado (>65), se espera mejor punto de entrada")
        else:
            reasons.append("Prediccion ALCISTA pero precio bajo la SMA50 (tendencia macro no confirma)")
    elif prediccion == "BAJISTA" and probabilidad is not None and probabilidad >= MIN_ALCISTA_PROBABILITY:
        direction = "SELL"
        reasons.append("Prediccion BAJISTA con alta probabilidad")
    else:
        reasons.append("Prediccion NEUTRAL o probabilidad baja: se mantiene posicion esperando confirmacion")

    return {
        "señal": direction,
        "direccion": direction,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "ratio_riesgo_beneficio": 2.0,
        "prediccion_ia": prediccion,
        "probabilidad_ia": probabilidad,
        "nivel_riesgo": nivel_riesgo,
        "resumen_noticia": gemini.get("resumen_noticia"),
        "justificacion_tecnica": gemini.get("justificacion_tecnica"),
        "razones": reasons,
        "regla_sl": "Cierre - 1.5 * ATR",
        "regla_tp": "Cierre + 3.0 * ATR",
    }