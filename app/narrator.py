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
            parts.append(f"El precio ({close:.2f}) opera por encima de la SMA50 ({sma50:.2f}), lo que indica una tendencia alcista de medio plazo.")
        elif close < sma50:
            parts.append(f"El precio ({close:.2f}) se encuentra por debajo de la SMA50 ({sma50:.2f}), sugiriendo una tendencia bajista de medio plazo.")
        else:
            parts.append(f"El precio ({close:.2f}) se encuentra en la zona de la SMA50 ({sma50:.2f}), sin tendencia clara de medio plazo.")
    if _safe(close) and _safe(sma20):
        if close > sma20:
            parts.append("El precio también supera la SMA20, lo que refuerza el sesgo alcista a corto plazo.")
        elif close < sma20:
            parts.append("El precio está por debajo de la SMA20, señalando debilidad a corto plazo.")
    if _safe(change_pct):
        if change_pct > 1:
            parts.append(f"La variación diaria fue de +{change_pct:.2f}%, mostrando impulso positivo.")
        elif change_pct < -1:
            parts.append(f"La variación diaria fue de {change_pct:.2f}%, mostrando presión vendedora.")
        else:
            parts.append(f"La variación diaria fue de {change_pct:.2f}%, dentro del rango normal.")
    return " ".join(parts) if parts else "No hay datos suficientes para evaluar la tendencia."


def _rsi_section(rsi14):
    if not _safe(rsi14):
        return "El RSI no está disponible para evaluar."
    if rsi14 >= 70:
        return f"El RSI14 ({rsi14:.1f}) indica zona de sobrecompra, lo que puede anticipar una corrección a la baja."
    if rsi14 <= 30:
        return f"El RSI14 ({rsi14:.1f}) indica zona de sobreventa, lo que puede anticipar un rebote."
    if rsi14 >= 55:
        return f"El RSI14 ({rsi14:.1f}) está en zona neutral-alta, sin señales extremas."
    return f"El RSI14 ({rsi14:.1f}) está en zona neutral-baja, sin señales extremas."


def _macd_section(macd, macd_signal, macd_hist):
    parts = []
    if _safe(macd_hist):
        if macd_hist > 0:
            parts.append(f"El histograma MACD ({macd_hist:.4f}) es positivo, señalando momentum alcista.")
        elif macd_hist < 0:
            parts.append(f"El histograma MACD ({macd_hist:.4f}) es negativo, señalando momentum bajista.")
        else:
            parts.append("El histograma MACD está en cero, indicando un punto de inflexión.")
    if _safe(macd) and _safe(macd_signal):
        if macd > macd_signal:
            parts.append("La línea MACD está por encima de la línea de señal, lo que refuerza el sesgo alcista.")
        else:
            parts.append("La línea MACD está por debajo de la línea de señal, indicando sesgo bajista.")
    return " ".join(parts) if parts else "El MACD no está disponible."


def _volatility(atr14, close):
    if not _safe(atr14) or not _safe(close) or close == 0:
        return "La volatilidad (ATR) no está disponible."
    atr_pct = (atr14 / close) * 100
    if atr_pct > 3:
        return f"La volatilidad es alta (ATR {atr14:.2f} = {atr_pct:.2f}% del precio), lo que implica mayor riesgo y oportunidad."
    if atr_pct > 1.5:
        return f"La volatilidad es moderada (ATR {atr14:.2f} = {atr_pct:.2f}% del precio)."
    return f"La volatilidad es baja (ATR {atr14:.2f} = {atr_pct:.2f}% del precio), mercados tranquilos."


def _arima_section(arima_next, arima_forecast, close):
    if not _safe(arima_next) or not _safe(close):
        return "El pronóstico ARIMA no está disponible para evaluar la dirección esperada."
    diff_pct = ((arima_next / close) - 1) * 100
    if diff_pct > 0.5:
        return f"El ARIMA proyecta un precio de {arima_next:.2f} a 5 días ({diff_pct:+.2f}%), sugiriendo tendencia alcista."
    if diff_pct < -0.5:
        return f"El ARIMA proyecta un precio de {arima_next:.2f} a 5 días ({diff_pct:+.2f}%), sugiriendo tendencia bajista."
    return f"El ARIMA proyecta un precio de {arima_next:.2f} a 5 días ({diff_pct:+.2f}%), sin dirección clara."


def _conclusion(direction, signal):
    direction_labels = {
        "BUY": "compra (BUY)",
        "SELL": "venta (SELL)",
        "HOLD": "mantenimiento (HOLD)",
    }
    label = direction_labels.get(direction, "mantenimiento (HOLD)")
    sl = signal.get("stop_loss")
    tp = signal.get("take_profit")
    parts = [f"La señal integral del sistema indica {label}."]
    if _safe(sl) and _safe(tp):
        parts.append(f"El stop loss sugerido es {sl:.2f} y el take profit es {tp:.2f}, con un ratio riesgo-beneficio de 1:2.")
    reasons = signal.get("razones", [])
    if reasons:
        parts.append(f"Razón principal: {reasons[0]}.")
    return " ".join(parts)
