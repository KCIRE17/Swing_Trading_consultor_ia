import math


def explain(context, signal):
    close = context.get("close")
    sma20 = context.get("sma20")
    sma50 = context.get("sma50")
    rsi14 = context.get("rsi14")
    macd = context.get("macd")
    macd_signal = context.get("macd_signal")
    macd_hist = context.get("macd_hist")
    atr14 = context.get("atr14")
    change_pct = context.get("change_pct")
    arima_next = context.get("arima_next")
    arima_forecast = context.get("arima_forecast")
    direction = signal.get("direccion", "HOLD")

    paragraphs = []
    bullets = []

    trend_text = _trend(close, sma20, sma50, change_pct)
    paragraphs.append(trend_text)
    bullets.append(trend_text)

    rsi_text = _rsi_section(rsi14)
    paragraphs.append(rsi_text)
    bullets.append(rsi_text)

    macd_text = _macd_section(macd, macd_signal, macd_hist)
    paragraphs.append(macd_text)
    bullets.append(macd_text)

    vol_text = _volatility(atr14, close)
    paragraphs.append(vol_text)
    bullets.append(vol_text)

    arima_text = _arima_section(arima_next, arima_forecast, close)
    paragraphs.append(arima_text)
    bullets.append(arima_text)

    conclusion = _conclusion(direction, signal)
    paragraphs.append(conclusion)
    bullets.append(conclusion)

    return {
        "parrafo": " ".join(paragraphs),
        "bullets": bullets,
        "fuente": "reglas",
    }


def _safe(v):
    return v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))


def _trend(close, sma20, sma50, change_pct):
    parts = []
    if _safe(close) and _safe(sma50):
        if close > sma50:
            parts.append(f"El precio ({close:.2f}) opera por encima de su promedio de 50 días (SMA50) ({sma50:.2f}), lo que indica una tendencia alcista de mediano plazo.")
        elif close < sma50:
            parts.append(f"El precio ({close:.2f}) se encuentra por debajo de su promedio de 50 días (SMA50) ({sma50:.2f}), sugiriendo una tendencia bajista de mediano plazo.")
        else:
            parts.append(f"El precio ({close:.2f}) se encuentra justo en su promedio de 50 días (SMA50) ({sma50:.2f}), sin una tendencia clara de mediano plazo.")
    if _safe(close) and _safe(sma20):
        if close > sma20:
            parts.append("El precio también supera el promedio de los últimos 20 días (SMA20), lo que refuerza la subida a corto plazo.")
        elif close < sma20:
            parts.append("El precio está por debajo del promedio de los últimos 20 días (SMA20), señalando debilidad a corto plazo.")
    if _safe(change_pct):
        if change_pct > 1:
            parts.append(f"La variación diaria fue de +{change_pct:.2f}%, mostrando más compradores que vendedores.")
        elif change_pct < -1:
            parts.append(f"La variación diaria fue de {change_pct:.2f}%, mostrando más vendedores que compradores.")
        else:
            parts.append(f"La variación diaria fue de {change_pct:.2f}%, dentro del rango normal.")
    return " ".join(parts) if parts else "No hay datos suficientes para evaluar la tendencia."


def _rsi_section(rsi14):
    if not _safe(rsi14):
        return "La fuerza del movimiento (RSI) no está disponible para evaluar."
    if rsi14 >= 70:
        return f"La fuerza del movimiento (RSI) marca {rsi14:.1f} de 0 a 100, en zona de compra muy intensa, lo que puede anticipar una corrección a la baja."
    if rsi14 <= 30:
        return f"La fuerza del movimiento (RSI) marca {rsi14:.1f} de 0 a 100, en zona de venta muy intensa, lo que puede anticipar un rebote."
    if rsi14 >= 55:
        return f"La fuerza del movimiento (RSI) marca {rsi14:.1f}: zona media-alta, sin señales extremas."
    return f"La fuerza del movimiento (RSI) marca {rsi14:.1f}: zona media-baja, sin señales extremas."


def _macd_section(macd, macd_signal, macd_hist):
    parts = []
    if _safe(macd_hist):
        if macd_hist > 0:
            parts.append(f"Las barras del impulso (MACD) ({macd_hist:.4f}) son positivas, señalando un impulso alcista.")
        elif macd_hist < 0:
            parts.append(f"Las barras del impulso (MACD) ({macd_hist:.4f}) son negativas, señalando un impulso bajista.")
        else:
            parts.append("Las barras del impulso (MACD) están en cero, indicando un punto de cambio de dirección.")
    if _safe(macd) and _safe(macd_signal):
        if macd > macd_signal:
            parts.append("La línea del impulso está por encima de su línea de referencia, lo que refuerza el sesgo alcista.")
        else:
            parts.append("La línea del impulso está por debajo de su línea de referencia, indicando un sesgo bajista.")
    return " ".join(parts) if parts else "El indicador de impulso (MACD) no está disponible."


def _volatility(atr14, close):
    if not _safe(atr14) or not _safe(close) or close == 0:
        return "La volatilidad (ATR) no está disponible."
    atr_pct = (atr14 / close) * 100
    if atr_pct > 3:
        return f"La volatilidad es alta (movimiento típico de {atr14:.2f}, {atr_pct:.2f}% del precio), lo que implica mayor riesgo y oportunidad."
    if atr_pct > 1.5:
        return f"La volatilidad es moderada (movimiento típico de {atr14:.2f}, {atr_pct:.2f}% del precio)."
    return f"La volatilidad es baja (movimiento típico de {atr14:.2f}, {atr_pct:.2f}% del precio), mercados tranquilos."


def _arima_section(arima_next, arima_forecast, close):
    if not _safe(arima_next) or not _safe(close):
        return "La proyección estadística del precio no está disponible para evaluar la dirección esperada."
    diff_pct = ((arima_next / close) - 1) * 100
    if diff_pct > 0.5:
        return f"El modelo estadístico proyecta un precio de {arima_next:.2f} a 5 días ({diff_pct:+.2f}%), sugiriendo una tendencia alcista."
    if diff_pct < -0.5:
        return f"El modelo estadístico proyecta un precio de {arima_next:.2f} a 5 días ({diff_pct:+.2f}%), sugiriendo una tendencia bajista."
    return f"El modelo estadístico proyecta un precio de {arima_next:.2f} a 5 días ({diff_pct:+.2f}%), sin una dirección clara."


def _conclusion(direction, signal):
    direction_labels = {
        "BUY": "compra",
        "SELL": "venta",
        "HOLD": "mantenerse sin operar por ahora",
    }
    label = direction_labels.get(direction, "mantenerse sin operar por ahora")
    sl = signal.get("stop_loss")
    tp = signal.get("take_profit")
    parts = [f"La señal integral del sistema indica {label}."]
    if _safe(sl) and _safe(tp):
        parts.append(f"El tope de pérdida sugerido es {sl:.2f} y el objetivo de ganancia es {tp:.2f}, con una relación riesgo-beneficio de 1:2.")
    reasons = signal.get("razones", [])
    if reasons:
        parts.append(f"Razón principal: {reasons[0]}.")
    return " ".join(parts)
