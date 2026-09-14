import math

GREEN = "Apto"
AMBER = "Precaución"
RED = "No invertir"


def _safe(v):
    return v is not None and not (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))


def _base(descripcion, recomendacion, advertencia=None):
    out = {
        "descripcion": descripcion,
        "recomendacion": recomendacion,
        "advertencia": advertencia or None,
    }
    return out


def advise_precio(close, sma20, sma50, change_pct=None):
    if not _safe(close) or not _safe(sma50):
        return _base(
            "No hay datos suficientes para interpretar la tendencia del precio y sus promedios.",
            AMBER,
            "Verifica que el periodo solicitado tenga al menos 50 días de historia para calcular el promedio de 50 días (SMA50).",
        )

    partes = []
    advertencias = []

    if close > sma50:
        partes.append(
            f"El precio ({close:.2f}) está por encima de su promedio de 50 días (SMA50) ({sma50:.2f}), "
            "lo que marca una tendencia alcista de mediano plazo."
        )
    elif close < sma50:
        partes.append(
            f"El precio ({close:.2f}) está por debajo de su promedio de 50 días (SMA50) ({sma50:.2f}), "
            "tendencia bajista de mediano plazo."
        )
        advertencias.append("Cuando el precio cae bajo su promedio de 50 días, suele anticipar una caída mayor.")

    if _safe(sma20):
        if close > sma20:
            partes.append("Además supera el promedio de los últimos 20 días (SMA20), reforzando la subida a corto plazo.")
        elif close < sma20:
            partes.append("Está bajo el promedio de los últimos 20 días (SMA20), señal de debilidad a corto plazo.")
            advertencias.append("Mientras no recupere ese promedio, las subidas pueden durar poco.")

    if _safe(change_pct):
        if change_pct > 1:
            partes.append(f"La variación diaria fue +{change_pct:.2f}%, con más compradores que vendedores.")
        elif change_pct < -1:
            partes.append(f"La variación diaria fue {change_pct:.2f}%, con más vendedores que compradores.")

    if close > sma50 and (not _safe(sma20) or close > sma20):
        recomendacion = GREEN
    elif close > sma50 or (not _safe(sma20) or close > sma20):
        recomendacion = AMBER
    else:
        recomendacion = RED
        advertencias.append("Estructura bajista en el precio y sus promedios: evita abrir posiciones de compra.")

    return _base(
        " ".join(partes),
        recomendacion,
        (" ".join(advertencias) if advertencias else None),
    )


def advise_rsi(rsi14):
    if not _safe(rsi14):
        return _base("La fuerza del movimiento (RSI) no está disponible.", AMBER)

    if rsi14 >= 70:
        return _base(
            f"La fuerza del movimiento (RSI) marca {rsi14:.1f} de 0 a 100, en zona de compra muy "
            "intensa (>=70): el precio subió con fuerza y es probable una pausa o corrección.",
            RED,
            "Comprar ahora arriesga entrar en el peor momento de la subida. Espera que el indicador "
            "vuelva a la zona normal antes de entrar.",
        )
    if rsi14 <= 30:
        return _base(
            f"La fuerza del movimiento (RSI) marca {rsi14:.1f} de 0 a 100, en zona de venta muy "
            "intensa (<=30): el precio cayó con fuerza y podría rebotar, pero también podría seguir cayendo.",
            AMBER,
            "No compres solo por estar barato: espera una señal de rebote (que la fuerza suba de 30 "
            "o que aparezca una vela alcista).",
        )
    if rsi14 >= 55:
        return _base(
            f"La fuerza del movimiento (RSI) marca {rsi14:.1f}: zona media-alta, hay solidez pero sin excesos.",
            AMBER,
            "Zona aceptable para operar, pero vigila que no llegue a 70 (compra muy intensa).",
        )
    return _base(
        f"La fuerza del movimiento (RSI) marca {rsi14:.1f}: zona media-baja, sin tensiones.",
        GREEN,
        "Buena condición para analizar entradas junto con los demás indicadores.",
    )


def advise_macd(macd, macd_signal, macd_hist):
    if not _safe(macd_hist) and not _safe(macd):
        return _base("El impulso del precio (MACD) no está disponible.", AMBER)

    partes = []
    advertencias = []
    if _safe(macd_hist):
        if macd_hist > 0:
            partes.append(f"Las barras del impulso (MACD) son positivas ({macd_hist:.4f}): la fuerza acompaña la subida.")
        elif macd_hist < 0:
            partes.append(f"Las barras del impulso (MACD) son negativas ({macd_hist:.4f}): la fuerza acompaña la caída.")
            advertencias.append("El impulso está en contra: las caídas tienen más fuerza que las subidas.")
        else:
            partes.append("Las barras del impulso (MACD) están en cero: punto de cambio de dirección.")

    if _safe(macd) and _safe(macd_signal):
        if macd > macd_signal:
            partes.append("La línea del impulso está por encima de su línea de referencia, con dirección alcista.")
        else:
            partes.append("La línea del impulso está por debajo de su línea de referencia, con dirección bajista.")

    if _safe(macd_hist) and _safe(macd):
        if macd_hist > 0 and macd > macd_signal:
            recomendacion = GREEN
        elif macd_hist < 0 and macd < macd_signal:
            recomendacion = RED
        else:
            recomendacion = AMBER
    else:
        recomendacion = AMBER

    return _base(
        " ".join(partes),
        recomendacion,
        (" ".join(advertencias) if advertencias else None),
    )


def advise_arima(arima_next, close, order=None, adf_pvalue=None):
    if not _safe(arima_next) or not _safe(close) or close == 0:
        return _base(
            "La proyección estadística del precio no está disponible.",
            AMBER,
            "Revisa que la serie tenga datos suficientes; si el modelo falla, se usa una tendencia lineal simple.",
        )

    diff_pct = ((arima_next / close) - 1.0) * 100.0
    if diff_pct > 0.5:
        recomendacion = GREEN
        texto = (
            f"La proyección estadística estima el precio en {arima_next:.2f} dentro de 5 días "
            f"({diff_pct:+.2f}%), con una dirección alcista esperada."
        )
        advertencia = None
    elif diff_pct < -0.5:
        recomendacion = RED
        texto = (
            f"La proyección estadística estima el precio en {arima_next:.2f} dentro de 5 días "
            f"({diff_pct:+.2f}%), con una dirección bajista esperada."
        )
        advertencia = "La proyección anticipa una caída: no fuerces una compra en contra de esa estimación."
    else:
        recomendacion = AMBER
        texto = (
            f"La proyección estadística estima el precio en {arima_next:.2f} dentro de 5 días "
            f"({diff_pct:+.2f}%), sin una dirección clara."
        )
        advertencia = "Proyección plana: espera que el mercado defina la dirección antes de comprometer capital."

    return _base(texto, recomendacion, advertencia)


def advise_backtest(metrics):
    if not metrics or metrics.get("disponible") is not True:
        return _base(
            "La simulación histórica no pudo ejecutarse para este activo.",
            AMBER,
            "Se necesita un historial de más de 60 días para poder simular.",
        )

    win_rate = metrics.get("win_rate")
    exceso = metrics.get("exceso_retorno_pct")
    n_trades = metrics.get("n_trades", 0)
    max_dd = metrics.get("max_drawdown_pct")

    if n_trades == 0:
        return _base(
            "La simulación no generó operaciones en el periodo de prueba.",
            AMBER,
            "Las reglas de entrada (promedio de 50 días más el resto de indicadores) no se activaron en ese tramo.",
        )

    partes = [
        f"Tras {n_trades} operaciones simuladas, la estrategia acertó el {win_rate * 100:.1f}% de las veces, "
        f"con una caída máxima del {max_dd:.1f}%."
    ]
    advertencias = []

    if win_rate is not None and win_rate < 0.5:
        recom = AMBER
        advertencias.append("El acierto es menor al 50%: la estrategia pierde más operaciones de las que gana.")
    elif win_rate is not None and win_rate >= 0.6:
        recom = GREEN
    else:
        recom = AMBER

    if exceso is not None:
        if exceso > 0:
            partes.append(f"Superó a mantenerse sin operar (Buy & Hold) en {exceso:+.2f} puntos.")
        elif exceso < 0:
            recom = RED
            partes.append(f"Quedó {exceso:+.2f} puntos por debajo de simplemente mantener (Buy & Hold).")
            advertencias.append("Operar activamente rindió peor que no hacer nada en este historial: no es buen momento.")

    return _base(
        " ".join(partes),
        recom,
        (" ".join(advertencias) if advertencias else None),
    )


def advise_screener(close, sma20, sma50, rsi14, macd_hist):
    score = 0
    if _safe(close) and _safe(sma50):
        score += 1 if close > sma50 else -1
    if _safe(rsi14):
        if 40 <= rsi14 <= 65:
            score += 1
        elif rsi14 >= 75:
            score -= 1
    if _safe(macd_hist):
        score += 1 if macd_hist > 0 else -1
    if score >= 2:
        return "BUY"
    if score <= -2:
        return "SELL"
    return "HOLD"