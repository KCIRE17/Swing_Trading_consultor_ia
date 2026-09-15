# Prompt de Construcción: MVP de Swing Trading con Business Analytics e IA Multimodal

> **Instrucción para el agente (Claude Code / Codex):** Este documento es la especificación completa y autónoma de un producto mínimo viable (MVP). Léelo de principio a fin y construye el sistema completo respetando la arquitectura, la lógica, los contratos JSON y los criterios de aceptación descritos. No omitas ninguna sección. Trabaja en español (código de interfaz, mensajes y comentarios en español). No expongas secretos en código ni en logs.

---

## 1. Objetivo y contexto del producto

Construir un **Sistema de Soporte a la Toma de Decisiones (DSS)** para inversores que operan bajo la modalidad de **Swing Trading** (posiciones mantenidas entre **3 y 10 ruedas bursátiles**). El sistema combina:

- **Indicadores de análisis técnico** en vivo (SMA, RSI, MACD, ATR).
- Una **línea base econométrica ARIMA** como benchmark estadístico.
- **Inferencia multimodal** con el modelo fundacional **Google Gemini Flash** (consume contexto técnico + imagen de noticia financiera por URL o archivo subido).
- Un **motor de señales** operativas con Stop-Loss y Take-Profit basados en ATR.
- **Backtesting** histórico con partición cronológica estricta.
- Un **screener** de mercado y un **dashboard web** interactivo de 5 pestañas.

Es un **prototipo académico de investigación** bajo la metodología **TDSP (Team Data Science Process)** de Microsoft, fase de prototipado. **Costo total: S/ 0.00** (todo con herramientas open source y capas gratuitas).

**Límites éticos:** el sistema **no** ejecuta órdenes con dinero real, no se conecta a brokers y **no constituye asesoría de inversión personalizada**. Las señales son simulaciones de apoyo al análisis humano.

---

## 2. Requisitos funcionales

### RF-1. Indicadores técnicos
Para cualquier ticker y periodo (`1mo`, `3mo`, `6mo`, `1y`) se debe descargar OHLCV ajustado en vivo desde Yahoo Finance (vía `yfinance`) y calcular:

- **SMA20** y **SMA50** — medias móviles simples para tendencia.
- **RSI14** — índice de fuerza relativa (media suavizada de Wilder, alpha = 1/14).
- **MACD (12, 26, 9)** — línea MACD, línea de señal e histograma.
- **ATR14** — rango verdadero medio (media EWMA alpha = 1/14).

### RF-2. Benchmark econométrico ARIMA
- Aplicar prueba **ADF** (Augmented Dickey-Fuller) sobre el cierre.
- Determinar el grado de diferenciación `d` (hasta 2): si `p-value > 0.05`, diferenciar; repetir hasta que `p-value ≤ 0.05`.
- Probar grid `p,q ∈ {0,1,2}` (excluyendo `(0,0)`), calibrar con `statsmodels.tsa.arima.model.ARIMA` y elegir el orden de **menor AIC**.
- Pronosticar **5 ruedas bursátiles**.
- **Fallback:** si ARIMA falla, ajustar una recta por mínimos cuadrados sobre los últimos 20 cierres (`np.polyfit`) y proyectar 5 puntos (reportar `method: "trend"`).

### RF-3. Inferencia multimodal (Google Gemini)
- Enviar el contexto técnico+econométrico del activo y, opcionalmente, una **imagen de noticia financiera** (desde URL o archivo multipart).
- Normalizar la imagen antes del envío: reescalar a un máximo de **1024 px** en su lado mayor, convertir a RGB y comprimir a **JPEG con calidad 85%** (Pillow).
- El modelo debe responder **solo JSON** con este esquema exacto:

```json
{
  "prediccion": "ALCISTA" | "NEUTRAL" | "BAJISTA",
  "probabilidad": 0.0–1.0,
  "nivel_riesgo": "BAJO" | "MEDIO" | "ALTO",
  "resumen_noticia": "1 a 2 oraciones sobre el evento fundamental de la imagen",
  "justificacion_tecnica": "explica la confluencia indicadores + contexto visual"
}
```

- **Degradación elegante:** si no hay `GEMINI_API_KEY`, no hay red, la imagen no se puede descargar/procesar o la respuesta no cumple el esquema, el sistema debe responder con un payload degradado: `prediccion="NEUTRAL"`, `probabilidad=0.5`, `nivel_riesgo="MEDIO"`, con mensajes explicando la causa y una justificación que aclare que la señal se basa solo en contexto técnico + ARIMA. Indicar `fuente: "gemini" | "degradado"` y `con_imagen: bool`.

### RF-4. Motor de señales
A partir del análisis de Gemini + contexto técnico devolver `BUY / HOLD / SELL`:

- **BUY** si: `prediccion == "ALCISTA"`, `probabilidad >= 0.65`, `close > SMA50` y `RSI14 <= 65`.
- **SELL** si: `prediccion == "BAJISTA"`, `probabilidad >= 0.65`.
- **HOLD** en cualquier otro caso.
- Cálculo de riesgo:
  - `stop_loss = round(close − 1.5 × ATR14, 4)`
  - `take_profit = round(close + 3.0 × ATR14, 4)`
  - `ratio_riesgo_beneficio = 2.0`
- Incluir en la respuesta: predicción/probabilidad/nivel de riesgo IA, resumen de noticia, justificación técnica y lista de **razones** en lenguaje natural que expliquen la decisión.

### RF-5. Backtesting
Simulación histórica sobre el mismo activo:

- Partición cronológica estricta: **70% entrenamiento/calibración, 15% validación, 15% prueba fuera de muestra** (sin data leakage).
- **Fricción transaccional: 0.1%** por operación.
- Entrada: precio sobre `SMA50` y (recuperación de sobreventa `RSI <= 35 → > 35` o breakout de momentum `RSI > 35 y ≤ 70 y MACD_HIST > 0`).
- Salida: tocar `SL` (1.5×ATR), tocar `TP` (3×ATR) o **máximo 10 velas** de permanencia.
- Si la serie tiene menos de 60 velas válidas, devolver `disponible: false` con mensaje.
- Métricas a reportar: win rate, % retorno total, % retorno Buy & Hold, maximum drawdown %, Sharpe anualizado (×√252), exceso de retorno vs Buy & Hold, detalle de operaciones (últimas 20) y curva de capital de estrategia vs Buy & Hold.

### RF-6. Screener de mercado
Analizar 8 activos (`SPY, AAPL, NVDA, MSFT, AMZN, TSLA, GOOGL, META`) con señal por reglas locales:

- `score` inicial 0.
- `+1` si `close > SMA50`, `−1` si `close < SMA50`.
- `+1` si `40 ≤ RSI14 ≤ 65`, `−1` si `RSI14 ≥ 75`.
- `+1` si `MACD_HIST > 0`, `−1` si `MACD_HIST < 0`.
- `score ≥ 2` → **BUY**; `score ≤ −2` → **SELL**; si no → **HOLD**.
- Cada fila incluye nombre de la empresa, cierre, variación %, RSI, MACD hist, ATR, SMA20/50, fecha y consejo de precio.

### RF-7. Asesoría/narración en lenguaje natural
- **Asesoria por indicador** (precio/SMA, RSI, MACD, ARIMA, backtest): cada bloque devuelve `{descripcion, recomendacion, advertencia}` donde `recomendacion` es `"Apto" | "Precaución" | "No invertir"`, con texto en español explicando el estado y, cuando detecta condiciones de riesgo, una advertencia concreta.
- **Narración integral** (`/api/interpret` y dentro de `/api/signal`): un párrafo en español con bullets que cubre tendencia, RSI, MACD, volatilidad (ATR) y proyección ARIMA, y termina con una conclusión práctica con la señal y los niveles SL/TP.
- **Mejora con IA (opcional):** si hay clave Gemini, regenerar el párrafo con el modelo para que "suene natural" (instrucción de sistema: 4–7 oraciones, sin títulos/markdown/tablas, en español, para inversionistas no técnicos, cerrando con lectura práctica para 3–10 ruedas).

### RF-8. Dashboard web
Frontend estático (HTML + Vanilla JS + Chart.js) con **5 pestañas**:

1. **Resumen de Mercado** — KPIs generales y resumen/screener de los 8 activos, con filtro por señal (Compra/Mantener/Venta) y búsqueda por nombre.
2. **Análisis Técnico** — gráficos de precio (con SMA20/SMA50), RSI, MACD e interpretación por reglas.
3. **Inferencia Multimodal** — selector de ticker, campo para URL de imagen y subida de archivo; muestra predicción, probabilidad, nivel de riesgo, resumen de noticia, justificación técnica y dirección de la señal con SL/TP.
4. **Backtesting** — métricas de la simulación, curva de capital vs Buy & Hold y consejo.
5. **Metodología** — paso a paso TDSP con sus 5 fases.

---

## 3. Arquitectura técnica y stack

| Capa | Tecnología |
|------|-----------|
| Backend | **Python ≥ 3.12** + **FastAPI** + Uvicorn |
| Datos | **yfinance** (OHLCV en vivo) + pandas + numpy |
| Econometría | **statsmodels** (ADF, ARIMA) |
| IA multimodal | **google-genai** (Google Gemini Flash) + requests + Pillow |
| Frontend | HTML + Vanilla JS + **Chart.js** (CDN) |
| Despliegue | **Vercel** (plan free), cron diario, uploads multipart con python-multipart |
| Tiempo de vida | Caché LRU en memoria **TTL 1 hora** (máx 128 entradas) anti rate-limit de Yahoo |

### Pipelines
- **Datos:** `yfinance` → limpieza (dropna en Close, corrección de zonas horarias, reorden de columnas) → cálculo de indicadores → payload de series para gráficos.
- **Caché:** key `ohlcv:{TICKER}:{period}` con TTL de 3600 s; `force=True` para el refresh diario.

---

## 4. Estructura de archivos esperada

```
main.py               # FastAPI (entrypoint para Vercel)
vercel.json           # Cron diario /api/refresh 22:00 UTC
pyproject.toml        # Empacado e instalación editable
README.md             # Documentación de ejecución y despliegue
.env.example          # Plantilla de variables de entorno
.vercelignore         # Exclusiones para el build de Vercel
.gitignore            # Exclusiones de control de versiones
app/
  __init__.py
  cache.py            # Caché TTL en memoria (thread-safe)
  data.py             # Descarga OHLCV (yfinance) + payload de series
  indicators.py       # SMA, RSI, MACD, ATR
  advisor.py          # Consejos por indicador + screener
  arima_benchmark.py  # ADF + ARIMA (con fallback tendencial)
  gemini_client.py    # Análisis multimodal + narrativa enriquecida
  signal_engine.py    # Reglas BUY/HOLD/SELL + SL/TP
  backtest.py         # Simulación 70/15/15 con fricción
  companies.py        # Catálogo de empresas y resolución de nombres
  narrator.py         # Narración en lenguaje humano por reglas
public/
  index.html          # Dashboard 5 pestañas
  app.js              # Lógica del frontend (fetch a la API + Chart.js)
  style.css           # Estilos
scripts/
  smoke.py            # Smoke test del pipeline completo
```

### `pyproject.toml` (dependencias exactas)
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "swing-trading-consultor-ia"
version = "0.1.0"
description = "Sistema de Soporte a la Toma de Decisiones para Swing Trading (MVP)"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "yfinance",
    "pandas",
    "numpy",
    "statsmodels",
    "google-genai",
    "pillow",
    "requests",
    "python-multipart",
]

[tool.setuptools]
py-modules = ["main"]

[tool.setuptools.packages.find]
include = ["app*"]
```

### Variables de entorno (`.env.example`)
```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `GEMINI_API_KEY` | No | Key de Google AI Studio. Sin ella el sistema degrada a análisis técnico. |
| `GEMINI_MODEL` | No | Modelo (default: `gemini-2.5-flash`) |

Notas:
- Mientras el `GEMINI_NARRATIVE_MODEL`: variable opcional para la narración (default `gemini-2.5-flash`).
- El archivo `.env` **nunca** debe commitearse.

---

## 5. Especificación detallada de lógica

### 5.1 Cálculo de indicadores (`app/indicators.py`)

```python
SMA(series, w)     = series.rolling(w).mean()
RSI(series, 14):   delta = diff; gain = clip(lower=0); loss = -clip(upper=0)
                   avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
                   avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
                   rs = avg_gain / avg_loss (replace 0 → NaN)
                   RSI = 100 - 100/(1+rs); fillna(50)
MACD:  ema_fast = ewm(span=12), ema_slow = ewm(span=26)
       macd_line = ema_fast - ema_slow
       signal = macd_line.ewm(span=9)
       hist = macd_line - signal
ATR(14): TR = max(high-low, |high-prev_close|, |low-prev_close|)
         ATR = TR.ewm(alpha=1/14, adjust=False).mean()
augment(df): añade columnas SMA20, SMA50, RSI14, MACD, MACD_SIGNAL, MACD_HIST, ATR14
```

`latest_values(df)`: devuelve el último cierre con `close, change_pct, volume, high, low, open, sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14` (valores limpios: NaN/inf → `None`; números redondeados a 6 dígitos).

### 5.2 Carga de datos (`app/data.py`)
```python
PERIOD_LOOKBACK = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 360}
fetch_ohlcv(ticker, period="6mo", force=False)
```
- Consulta caché a menos que `force=True`.
- Descarga con `yf.Ticker(ticker).history(period=period, auto_adjust=True)`, 2 intentos con espera de 1 s.
- Elimina filas sin cierre, normaliza índices de fecha (sin zona horaria), conserva solo `Open, High, Low, Close, Volume` y recorta a `PERIOD_LOOKBACK`.
- Aplica `augment` y guarda en caché.

`series_payload(frame, limit=180)`: serie de `dates` y listas `close, open, high, low, volume, sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14` (números a 6 decimales, volúmenes enteros, `None` para NaN).

### 5.3 Catálogo de empresas (`app/companies.py`)
```python
COMPANIES = {
    "SPY": "S&P 500 ETF Trust (SPDR)",
    "AAPL": "Apple Inc.",
    "NVDA": "NVIDIA Corporation",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com, Inc.",
    "TSLA": "Tesla, Inc.",
    "GOOGL": "Google",
    "META": "Meta Platforms, Inc.",
}
SCREENER_TICKERS = ["SPY", "AAPL", "NVDA", "MSFT", "AMZN", "TSLA", "GOOGL", "META"]
resolve(ticker)  # UPPER + strip, con fallback al propio ticker como nombre
```

### 5.4 ARIMA (`app/arima_benchmark.py`)
```python
HORIZON = 5; P_GRID = [0,1,2]; Q_GRID = [0,1,2]
estimate(frame) → {
  adf_pvalue, d, order {p,d,q}, aic,
  forecast [5 valores], forecast_dates [],
  last_close, next_close, method ("arima"|"trend"), points
}
```
- Requiere ≥ 30 cierres válidos, si no `ValueError`.
- `d` por ADF iterado (hasta 2 diferenciaciones).
- Selección de `(p,d,q)` por menor AIC entre el grid.
- Fallback tendencial: `np.polyfit` sobre últimos 20 cierres, proyectar horizontes 1..5, reportar `order (1,1,0)`.

### 5.5 Gemini (`app/gemini_client.py`)
- `analyze(context, image_url=None, image_bytes=None)`:
  - Construye texto de contexto (ticker, fecha, close, change_pct, SMA20/50, RSI14, MACD triplete, ATR14, pronóstico ARIMA 5 ruedas, precio proyectado).
  - Imagen: si vienen bytes, prepararlos; si no, descargar por URL con `requests` (User-Agent de navegador, validar `Content-Type` de imagen).
  - Si hay imagen → llamada multimodal; si no → llamada solo texto.
  - Cualquier fallo → payload degradado.
  - Valida el esquema; si no cumple → degradado.
  - Devuelve `{prediccion, probabilidad, nivel_riesgo, resumen_noticia, justificacion_tecnica, fuente, con_imagen}`.
- **System prompt esencial:** "Eres un analista de inversiones especializado en Swing Trading (posiciones de 3 a 10 ruedas bursátiles)… responde SOLO en JSON válido sin texto adicional" con la estructura exacta descrita en RF-3.
- `enrich_narrative(paragraph_reglas, context)`: si hay API key, pide al modelo una narración humana de 4–7 oraciones en español (sin títulos/markdown/tablas) basada en el contexto numérico y el párrafo base; ante cualquier error devuelve `None`.

### 5.6 Motor de señales (`app/signal_engine.py`)
```python
SL_MULTIPLER = 1.5; TP_MULTIPLER = 3.0
MIN_ALCISTA_PROBABILITY = 0.65; MAX_RSI_BUY = 65.0
```
Reglas de dirección y razones en lenguaje natural (ver RF-4). La respuesta incluye `señal`, `direccion`, `stop_loss`, `take_profit`, `ratio_riesgo_beneficio` (2.0), `prediccion_ia`, `probabilidad_ia`, `nivel_riesgo`, `resumen_noticia`, `justificacion_tecnica`, `razones[]`, `regla_sl`, `regla_tp`.

**Reglas de narración de razones:**
- BUY: "Predicción alcista con alta probabilidad, precio por encima de su promedio de 50 días y fuerza del movimiento en zona saludable".
- ALCISTA pero `RSI > 65`: "Precio por encima de su promedio de 50 días, pero la fuerza del movimiento está muy alta; se espera un mejor punto de entrada".
- ALCISTA pero `close ≤ SMA50`: "Predicción alcista, pero el precio está bajo su promedio de 50 días (la tendencia de mediano plazo no confirma)".
- SELL: "Predicción bajista con alta probabilidad".
- HOLD: "Sin dirección clara o probabilidad baja: se mantiene la posición esperando confirmación".

### 5.7 Backtest (`app/backtest.py`)
```python
TRAIN_RATIO = 0.70; FRICTION = 0.001; MAX_HOLD_BARS = 10
SL_MULTIPLIER = 1.5; TP_MULTIPLIER = 3.0; RSI_ENTRY_FLOOR = 35.0
```
- Requiere ≥ 60 velas con Close/SMA50/ATR14/RSI14 válidas.
- Entradas (solo fuera del tramo de entrenamiento):
  - `oversold_recovery`: `RSI[i-1] ≤ 35` y `RSI[i] > 35`
  - `momentum_breakout`: `35 < RSI[i] ≤ 70` y `MACD_HIST[i] > 0`
  - condición de entrada: `close[i] > sma50[i]` **y** alguna de las dos anteriores.
- Salidas: SL intrabar (`low ≤ stop_loss` → precio SL), TP intrabar (`high ≥ take_profit` → precio TP), o `held ≥ 10` → cierre. Operación abierta al final → cierra a último cierre ("fin_simulacion").
- Retorno neto = `exit/entry − 1 − FRICTION`.
- Métricas: `n_trades`, `n_ganadoras`, `win_rate`, `total_return_pct`, `buy_hold_return_pct`, `max_drawdown_pct`, `sharpe_ratio` (×√252), `exceso_retorno_pct`, `arima_coincide` ("Concuerda"/"Difirio"/"Sin referencia"), `trades` (últimas 20), `curva {dates, estrategia, buy_hold}`, `config` (repite los parámetros usados y `n_train`, `n_test`).
- Si `arima_forecast` se pasa y existe, comparar dirección del pronóstico (último vs primero) contra el movimiento real de los últimos 5 cierres.

### 5.8 Reglas de consejo (`app/advisor.py`)
Valores de recomendación: `GREEN = "Apto"`, `AMBER = "Precaución"`, `RED = "No invertir"`.

- **Precio:** si `close > SMA50` → tendencia alcista; refuerza con SMA20; `change_pct > +1%` → más compradores, `< −1%` → más vendedores. `close > SMA50` (y sobre SMA20) → Apto; solo una condición → Precaución; bajo ambos promedios → No invertir (con advertencia de estructura bajista).
- **RSI:** `≥ 70` → No invertir (zona de compra intensa, riesgo de corrección); `≤ 30` → Precaución (posible rebote pero no comprar solo por barato); `≥ 55` → Precaución (zona media-alta); resto → Apto (zona media-baja).
- **MACD:** `hist > 0` y `macd > signal` → Apto; `hist < 0` y `macd < signal` → No invertir; caso contrario → Precaución.
- **ARIMA:** proyección a 5 días; `diff_pct > +0.5%` → Apto; `< −0.5%` → No invertir; si no → Precaución (proyección plana).
- **Backtest:** sin operaciones → Precaución; win rate < 50% → Precaución; ≥ 60% → Apto; si `exceso_retorno_pct < 0` → No invertir con advertencia ("operar activamente rindió peor que no hacer nada").

### 5.9 Narrador (`app/narrator.py`)
Genera un párrafo con bullets: tendencia (vs SMA50/SMA20 + change_pct), RSI (≥70 corrección, ≤30 rebote, ≥55 media-alta, resto media-baja), MACD (hist positivo/negativo/cero + posición de la línea), volatilidad (ATR % del precio: >3% alta, >1.5% moderada, resto baja), sección ARIMA (proyección + diff_pct con umbral ±0.5%) y conclusión con dirección (compra/venta/mantenerse) + SL/TP + `razones[0]`.

---

## 6. Contratos de la API (endpoints)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado y presencia de la key de Gemini. |
| GET | `/api/indicators?ticker=&period=` | OHLCV + indicadores + series para gráficos. |
| GET | `/api/forecast?ticker=&period=` | Pronóstico ARIMA 5 ruedas (ADF, orden, AIC). |
| POST | `/api/analyze` | Body `{ticker, period?, image_url?}` → análisis IA. |
| GET | `/api/signal?ticker=&period=&image_url=` | Señal final + SL/TP + explicación. |
| POST | `/api/signal` | Multipart `{ticker, period, file}` → señal con imagen subida. |
| GET | `/api/interpret?ticker=&period=` | Narración en lenguaje humano. |
| GET | `/api/backtest?ticker=&period=1y` | Métricas de la simulación + consejo. |
| GET | `/api/refresh?tickers=SPY,AAPL,NVDA,MSFT` | Pre-cálculo/refresco (manual o cron). |
| GET | `/api/screener?tickers=&period=` | Empresas analizadas con señal BUY/HOLD/SELL. |
| GET | `/favicon.ico` · `/favicon.png` | Favicon SVG (emoji de gráfico). |

Detalles por endpoint:

- **`/api/health`** → `{"status": "ok", "gemini_key_present": bool}`.
- **`/api/indicators`** → `{ticker, nombre, period, ultimo, series, meta, asesoria}` donde `meta` incluye `proveedor ("Yahoo Finance (yfinance)"), tipo, period_solicitado, n_velas, ultima_fecha` y `asesoria` trae `{precio, rsi, macd}`. Errores → **HTTP 502** con `{error: true, mensaje}`.
- **`/api/forecast`** → `{ticker, period, forecast}` donde `forecast = estimate(frame)` + `forecast_dates` (5 próximos días hábiles desde hoy) + `asesoria` (ARIMA).
- **`/api/analyze`** (POST, JSON `{ticker, period, image_url}`) → `{ticker, analisis}` (payload completo de Gemini).
- **`/api/signal`** GET → `{ticker, nombre, contexto_tecnico, analisis_ia, senal, narracion}`. Igual para POST multipart (si no hay archivo, `image_bytes=None`).
- **`/api/interpret`** → `{ticker, nombre, narracion}`.
- **`/api/backtest`** → `{ticker, period, backtest}` donde `backtest` incorpora `asesoria`.
- **`/api/refresh`** → `{evento: "vercel-cron" | "manual", resultados: [{ticker, status, datos: {close, rsi14, forecast_next}}]}`. Por ticker, descarga forzada (`force=True`), calcula último close/RSI/forecast; fallo por ticker → `status: "error"` con mensaje.
- **`/api/screener`** → `{period, companies: [{ticker, nombre, close, change_pct, rsi14, macd_hist, atr14, sma20, sma50, ultima_fecha, senal, asesoria, error?}]}`.
- **CORS:** `*` en orígenes, métodos y cabeceras.
- **Servir estático:** si `VERCEL` no está definida, montar `public/` en `/` con `StaticFiles(html=True)`.
- **Manejo de errores común:** capturar excepciones, acortar mensaje a 400 chars y responder 502 con `{error: true, mensaje}`.

**Estructura de la señal (`senal`):**
```json
{
  "señal": "BUY|HOLD|SELL",
  "direccion": "BUY|HOLD|SELL",
  "stop_loss": 123.45,
  "take_profit": 130.12,
  "ratio_riesgo_beneficio": 2.0,
  "prediccion_ia": "ALCISTA",
  "probabilidad_ia": 0.78,
  "nivel_riesgo": "MEDIO",
  "resumen_noticia": "...",
  "justificacion_tecnica": "...",
  "razones": ["..."],
  "regla_sl": "Cierre - 1.5 * ATR",
  "regla_tp": "Cierre + 3.0 * ATR"
}
```

**Estructura de la narración (`narracion`):**
```json
{
  "parrafo": "texto completo...",
  "bullets": ["...", "..."],
  "fuente": "reglas" | "gemini"
}
```

**`contexto_tecnico`:** el resultado de `latest_values` + `ticker` + `arima_forecast`, `arima_next`, `arima_order`, `arima_adf_pvalue` (con fallback `None` si ARIMA falla).

---

## 7. Configuración de despliegue

### `vercel.json`
```json
{
  "crons": [
    { "path": "/api/refresh", "schedule": "0 22 * * *" }
  ]
}
```
Cron diario a las 22:00 UTC (cierre de NY). En el plan Hobby, un cron al día sin reintentos; la actualización principal de datos es bajo demanda.

### `vercelignore`
Excluir del build: `.venv`, `__pycache__`, `*.py[co]`, `*.egg-info`, `build/`, `dist/`, `wheels/`, `.env`, `*.log`, `*log*.json` como los exports `*-log-export-*.json`, `.git`.

### Ejecución local
```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e .        # Windows
# .venv/bin/python -m pip install -e .          # Linux/macOS
.venv\Scripts\python -m uvicorn main:app --port 8000
# Abrir http://localhost:8000  ·  API docs en http://localhost:8000/docs
```

### Despliegue en Vercel (free)
1. `npm i -g vercel && vercel`
2. Variables de entorno: `vercel env add GEMINI_API_KEY` (y opcional `GEMINI_MODEL`), o desde *Project → Settings → Environment Variables*, luego *Redeploy*.
3. Desplegar `vercel --prod`.
4. Verificar: dashboard en `/`, docs en `/docs`, smoke test contra producción.

---

## 8. Criterios de aceptación

### 8.1 Smoke test (`scripts/smoke.py`)
Implementar un script que valide en este orden y reporte `[PASS]/[FAIL]` con tiempos:

1. **Reglas locales:** `advisor.advise_rsi(78) → "No invertir"`; nombres reales de MSFT; presencia de AMZN/TSLA/GOOGL/META en el catálogo.
2. **Pipeline por ticker** (`SPY`, `AAPL`, `NVDA`, period `6mo`):
   - `fetch_ohlcv` devuelve ≥ 50 velas.
   - `latest_values` tiene `rsi14, macd, atr14, sma20` no `None`.
   - `series_payload` con `len(dates) == len(close) > 0`.
   - `arima_benchmark.estimate` devuelve `forecast` no vacío y `next_close` definido.
3. **Degradación sin API key:** `gemini_client.analyze` (sin key) → `prediccion == "NEUTRAL"` y `probabilidad == 0.5`; `signal_engine.decide` → `HOLD`; `narrator.explain` → párrafo y bullets no vacíos.
4. **Backtest SPY** (`1y`): `disponible` es `true` o hay `mensaje`.
5. **Endpoints HTTP** con `TestClient(fastapi)`:
   - `/api/health` → 200.
   - `/api/indicators?ticker=SPY&period=3mo` → 200, `series.dates` no vacío, serializable sin NaN.
   - `/api/forecast?ticker=SPY&period=3mo` → 200.
   - `/api/signal?ticker=SPY&period=3mo` → 200 con `senal.direccion ∈ {BUY, HOLD, SELL}`, `narracion.parrafo` y `nombre`.
   - `/api/backtest?ticker=SPY` → 200.
   - `/api/screener?tickers=SPY,AAPL&period=3mo` → 200, 2 companies, cada una con `nombre` y `senal ∈ {BUY, HOLD, SELL}`.
   - `/api/indicators` incluye `asesoria.precio/rsi/macd`.
   - `/api/forecast` incluye `asesoria.recomendacion`.
   - `/api/interpret?ticker=AAPL&period=3mo` → 200 con `narracion.parrafo`.
   - `/favicon.ico` → 200.

### 8.2 Checklist de producto
- [ ] Los 9+ endpoints responden según sus contratos y los errores devuelven 502 con `{error, mensaje}`.
- [ ] Sin `GEMINI_API_KEY`, todo el sistema funciona degradando con elegancia (señal HOLD coherente, narrativa por reglas).
- [ ] Con imagen de noticia (URL o archivo), la respuesta incluye `resumen_noticia` y `justificacion_tecnica` del modelo.
- [ ] El dashboard carga las 5 pestañas y consume únicamente la API descrita.
- [ ] El cron de `vercel.json` apunta a `/api/refresh` a las 22:00 UTC.
- [ ] `README.md` documenta funcionalidades, estructura, ejecución local, variables de entorno, despliegue y endpoints.

---

## 9. Instrucciones para el agente (orden de implementación)

Implementar en este orden:

1. **Esqueleto y config:** `pyproject.toml`, `.env.example`, `.gitignore`, `.vercelignore`, `vercel.json`, `README.md`, carpeta `app/` con `__init__.py`.
2. **Datos e indicadores:** `cache.py` → `indicators.py` → `data.py` → `companies.py`.
3. **Modelos:** `arima_benchmark.py` → `advisor.py`.
4. **IA multimodal:** `gemini_client.py` → `signal_engine.py` → `narrator.py`.
5. **Backtesting:** `backtest.py`.
6. **API:** `main.py` con todos los endpoints, CORS, favicon y montaje de estáticos condicional a `VERCEL`.
7. **Frontend:** `public/index.html`, `style.css`, `app.js` con las 5 pestañas y Chart.js por CDN.
8. **Validación:** `scripts/smoke.py` y ejecutar el smoke test local hasta que todo pase en verde.

**Reglas de escritura:**
- Sin comentarios en el código salvo que se pidan; nombres de funciones/variables autocontenidos en inglés o español consistente.
- No commitear `.env` ni expulsar la API key en logs o respuestas.
- Todo texto visible al usuario (dashboard, narrativas, consejos) en español.
- Mantener el costo en S/0: sin servicios de pago ni dependencias privativas.