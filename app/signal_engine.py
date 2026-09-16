SL_MULTIPLER = 1.5
TP_MULTIPLER = 3.0
MIN_ALCISTA_PROBABILITY = 0.65
MAX_RSI_BUY = 65.0

RECOMENDACION_TO_SEÑAL = {
    "AUMENTAR": "BUY",
    "RETIRAR": "SELL",
    "MANTENER": "HOLD",
}


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
    recomendacion = gemini.get("recomendacion", "MANTENER")

    direction = RECOMENDACION_TO_SEÑAL.get(recomendacion, "HOLD")
    reasons, warnings = _technical_reasons(context, prediccion, probabilidad)

    if recomendacion == "AUMENTAR" and not (
        close is not None
        and context.get("sma50")
        and close > context["sma50"]
        and context.get("rsi14") is not None
        and context["rsi14"] <= MAX_RSI_BUY
        and probabilidad is not None
        and probabilidad >= MIN_ALCISTA_PROBABILITY
    ):
        warnings.append(
            "La recomendación es aumentar, pero la confluencia técnica (media, fuerza y probabilidad) "
            "no confirma plenamente: vigila el punto de entrada."
        )

    news_tone, news_reason = _news_factor(context)
    if news_reason:
        reasons.append(news_reason)

    return {
        "señal": direction,
        "direccion": direction,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "ratio_riesgo_beneficio": round(TP_MULTIPLER / SL_MULTIPLER, 4),
        "prediccion_ia": prediccion,
        "probabilidad_ia": probabilidad,
        "nivel_riesgo": nivel_riesgo,
        "recomendacion_ia": recomendacion,
        "conclusion_cualitativa": gemini.get("conclusion_cualitativa"),
        "justificacion_tecnica": gemini.get("justificacion_tecnica"),
        "sentimiento_noticias": news_tone,
        "razones": reasons,
        "advertencias": warnings,
        "regla_sl": "Cierre - 1.5 * ATR",
        "regla_tp": "Cierre + 3.0 * ATR",
    }


def _technical_reasons(context, prediccion, probabilidad):
    reasons = []
    warnings = []
    close = context.get("close")

    if prediccion == "ALCISTA" and probabilidad is not None:
        if probabilidad >= MIN_ALCISTA_PROBABILITY:
            reasons.append(
                f"Predicción alcista con alta probabilidad ({probabilidad * 100:.0f}%) respaldada por el modelo fundacional."
            )
        else:
            warnings.append(
                f"La predicción es alcista pero la probabilidad ({probabilidad * 100:.0f}%) es moderada: menor convicción."
            )
    elif prediccion == "BAJISTA" and probabilidad is not None and probabilidad >= MIN_ALCISTA_PROBABILITY:
        reasons.append(f"Predicción bajista con alta probabilidad ({probabilidad * 100:.0f}%).")

    if close is not None and context.get("sma50"):
        if close > context["sma50"]:
            reasons.append("El precio opera por encima de su promedio de 50 días (tendencia alcista de mediano plazo).")
        else:
            reasons.append("El precio opera por debajo de su promedio de 50 días (estructura bajista de mediano plazo).")

    if context.get("rsi14") is not None:
        if context["rsi14"] >= 70:
            warnings.append("El RSI está en zona de compra muy intensa (>=70): riesgo de corrección.")
        elif context["rsi14"] <= 30:
            warnings.append("El RSI está en zona de venta muy intensa (<=30): posible rebote pero con riesgo.")
        else:
            reasons.append(f"La fuerza del movimiento (RSI {context['rsi14']:.1f}) está en zona saludable.")

    if context.get("arima_next") is not None and close:
        diff_pct = (context["arima_next"] / close - 1.0) * 100.0
        if abs(diff_pct) >= 0.5:
            reasons.append(f"El modelo ARIMA proyecta {diff_pct:+.2f}% en 5 ruedas.")

    return reasons, warnings


def _news_factor(context):
    news = context.get("noticias") or {}
    counts = news.get("counts") or {}
    total = sum(counts.values())
    if total == 0:
        return "NEUTRAL", None
    score = counts.get("POS", 0) - counts.get("NEG", 0)
    share = score / total
    if share >= 0.4:
        return "POSITIVO", "El sentimiento de las noticias recientes refuerza una dirección positiva."
    if share <= -0.4:
        return "NEGATIVO", "El sentimiento de las noticias recientes presiona de forma negativa."
    if score > 0:
        return "LIGERAMENTE_POSITIVO", "El sentimiento de las noticias recientes es levemente positivo."
    if score < 0:
        return "LIGERAMENTE_NEGATIVO", "El sentimiento de las noticias recientes es levemente negativo."
    return "NEUTRAL", None