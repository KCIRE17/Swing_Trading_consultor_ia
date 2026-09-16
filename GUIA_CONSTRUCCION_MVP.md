# Prompt de Construcción: Swing Trading Consulter IA — MVP con Business Analytics, IA Cualitativa y ML Clásico

> **Instrucción para el agente (Claude Code / Codex):** Este documento es la especificación completa y autónoma de un producto mínimo viable (MVP) ya construido. Léelo de principio a fin para entender la arquitectura, la lógica, los contratos JSON y los criterios de aceptación del sistema actual; úsalo como base para mantenerlo, evolucionario o reproducirlo. No omitas ninguna sección. Trabaja en español (código de interfaz, mensajes y comentarios en español). No expongas secretos en código ni en logs.

---

## 1. Objetivo y contexto del producto

Sistema de Soporte a la Toma de Decisiones (DSS) para inversores que operan bajo la modalidad de **Swing Trading** (posiciones mantenidas entre **3 y 10 ruedas bursátiles**). El sistema combina:

- **Indicadores de análisis técnico** en vivo (SMA20/SMA50, RSI14, MACD, ATR14).
- Una **línea base econométrica ARIMA** como benchmark estadístico (pronóstico a 5 ruedas).
- **IA cualitativa** con el modelo fundacional **Google Gemini Flash** (consumo de contexto técnico en texto; responde solo JSON).
- **Machine Learning clásico** para **sentimiento de noticias** (TF-IDF + LogisticRegression, entrenado diariamente).
- Un **motor de señales** operativas con Stop-Loss y Take-Profit basados en ATR.
- **Backtesting** histórico con partición cronológica estricta.
- Un **screener** de mercado y un **dashboard web** interactivo de **3 vistas** (Descriptiva, Predictiva, Prescriptiva) con una **decisión única por vista**.
- Un **ETL programado** (GitHub Actions) que persiste todo en **Supabase Postgres** a las **18:00 h (hora Perú / 23:00 UTC)**.

Es un **prototipo académico de investigación** bajo la metodología **TDSP (Team Data Science Process)** de Microsoft, fase de prototipado. **Costo total: S/ 0.00** (todo con herramientas open source y capas gratuitas).

**Límites éticos:** el sistema **no** ejecuta órdenes con dinero real, no se conecta a brokers y **no constituye asesoría de inversión personalizada**. Las señales son simulaciones de apoyo al análisis humano.

**Vocabulario de decisión:** las decisiones de cada vista usan **INVERTIR / MANTENER / RETIRAR** (la vista predictiva además reporta dirección **ALCISTA / NEUTRAL / BAJISTA** y niveles de confianza/riesgo como dato secundario). Las vistas **no** repiten gráficos ni cadenas de decisión.

---

## 2. Requisitos funcionales

### RF-1. Indicadores técnicos
Para cualquier ticker y periodo (`1mo`, `3mo`, `6mo`, `1y`) se descarga OHLCV ajustado en vivo desde Yahoo Finance (vía `yfinance`) y se calcula:

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
- El resultado se guarda como **snapshot diario** en Supabase (`forecast_snapshots`); si existe un snapshot reciente, la API lo sirve en lugar de recalcular (`fuente: "supabase"`).

### RF-3. IA cualitativa (Google Gemini, solo texto)
- Enviar el contexto técnico+econométrico del activo y el **resumen de sentimiento de noticias** como texto. No se procesan imágenes (la modalidad de imagen fue retirada del MVP).
- El modelo debe responder **solo JSON** (forzado con `response_mime_type: "application/json"`) con este esquema exacto:

```json
{
  "prediccion": "ALCISTA" | "NEUTRAL" | "BAJISTA",
  "probabilidad": 0.0–1.0,
  "nivel_riesgo": "BAJO" | "MEDIO" | "ALTO",
  "recomendacion": "RETIRAR" | "AUMENTAR" | "MANTENER",
  "conclusion_cualitativa": "2 a 3 oraciones con la lectura laica del contexto",
  "justificacion_tecnica": "2 a 3 oraciones sobre la confluencia indicadores + ARIMA"
}
```

- **Degradación elegante:** si no hay `GEMINI_API_KEY`, no hay red o la respuesta no cumple el esquema, el sistema devuelve `prediccion="NEUTRAL"`, `probabilidad=0.5`, `nivel_riesgo="MEDIO"`, `recomendacion="MANTENER"`, con `conclusion_cualitativa` y `justificacion_tecnica` que aclaran que la señal se basa solo en contexto técnico + ARIMA. Se reporta `fuente: "gemini" | "degradado"`.

### RF-4. Motor de señales
A partir del análisis de Gemini + contexto técnico devolver `BUY / HOLD / SELL`:

- Mapeo directo: `AUMENTAR → BUY`, `RETIRAR → SELL`, `MANTENER → HOLD`.
- Confluencia para BUY: si la recomendación es `AUMENTAR` pero **no** coinciden `close > SMA50`, `RSI14 ≤ 65` y `probabilidad ≥ 0.65`, se mantiene BUY pero se agrega una **advertencia** ("vigila el punto de entrada").
- Cálculo de riesgo:
  - `stop_loss = round(close − 1.5 × ATR14, 4)`
  - `take_profit = round(close + 3.0 × ATR14, 4)`
  - `ratio_riesgo_beneficio = 2.0`
- **Factor noticias:** se agrega `sentimiento_noticias` (POSITIVO / NEGATIVO / NEUTRAL / LIGERAMENTE_POSITIVO / LIGERAMENTE_NEGATIVO) según el balance POS−NEG del repo en Supabase y, si es significativo (share ≥ ±0.4), una razón adicional.
- Incluir en la respuesta: predicción/probabilidad/nivel de riesgo IA, `recomendacion_ia`, `conclusion_cualitativa`, `justificacion_tecnica`, `sentimiento_noticias`, lista de **razones** y **advertencias** en lenguaje natural.

### RF-5. Backtesting
Simulación histórica sobre el mismo activo:

- Partición cronológica estricta: **70% entrenamiento/calibración, 15% validación, 15% prueba fuera de muestra** (sin data leakage).
- **Fricción transaccional: 0.1%** por operación.
- Entrada: precio sobre `SMA50` y (recuperación de sobreventa `RSI <= 35 → > 35` o breakout de momentum `RSI > 35 y ≤ 70 y MACD_HIST > 0`).
- Salida: tocar `SL` (1.5×ATR), tocar `TP` (3×ATR) o **máximo 10 velas** de permanencia.
- Si la serie tiene menos de 60 velas válidas, devolver `disponible: false` con mensaje.
- Métricas: win rate, % retorno total, % retorno Buy & Hold, maximum drawdown %, Sharpe anualizado (×√252), exceso de retorno vs Buy & Hold, detalle de operaciones (últimas 20) y curva de capital de estrategia vs Buy & Hold.
- La API responde **anidado**: `{ticker, period, backtest: {..., asesoria}}`; el frontend resuelve con `const b = bt?.backtest || bt || {}`.

### RF-6. Screener de mercado
Analizar 8 activos (`SPY, AAPL, NVDA, MSFT, AMZN, TSLA, GOOGL, META`) con señal por reglas locales y **volumen**:

- `score` inicial 0.
- `+1` si `close > SMA50`, `−1` si `close < SMA50`.
- `+1` si `40 ≤ RSI14 ≤ 65`, `−1` si `RSI14 ≥ 75`.
- `+1` si `MACD_HIST > 0`, `−1` si `MACD_HIST < 0`.
- `score ≥ 2` → **BUY**; `score ≤ −2` → **SELL**; si no → **HOLD**.
- Cada fila incluye nombre de la empresa, cierre, variación %, **volumen**, RSI, MACD hist, ATR, SMA20/50, fecha y consejo de precio.

### RF-7. Decisiones por vista y diagnóstico por indicador
El dashboard **no** muestra recomendaciones "Apto/Precaución/No invertir" por gráfico. Cada gráfico muestra solo **diagnóstico** (`{descripcion, nota}`) y **cada vista tiene UNA decisión única**:

- **Diagnósticos (`describe_precio`, `describe_rsi`, `describe_macd`)** en `app/advisor.py`: explican el estado del indicador en español sin dar acción. `nota` puede llevar aclaraciones de riesgo.
- **Decisión descriptiva** (`resumen_descriptiva`): voto por score técnico (SMA50 ±1, SMA20 ±1, RSI 40–65 +1 / ≥75 −1 / ≤25 −1, MACD hist ±1, MACD>señal ±1). `score ≥ 2 → INVERTIR`, `≤ −2 → RETIRAR`, si no `MANTENER`. Se expone como `asesoria.decision` en `/api/indicators`.
- **Decisión predictiva** (`resumen_predictiva`): voto ponderado ARIMA (diff ±0.5% → ±0.4) + IA (`prediccion` × `probabilidad` × 0.6) + noticias (pos−neg clamp ±1 × 0.3). Umbrales ±0.25 → INVERTIR/RETIRAR (con dirección ALCISTA/BAJISTA), resto MANTENER/NEUTRAL. Reporta `confianza` (0–99; `None` si NEUTRAL) y `nivel_riesgo` (del modelo o derivado). Se expone como `decision_predictiva` en `/api/signal`.
- **Narración integral**: los gráficos de la vista Predictiva muestran la lectura de ARIMA y de IA por separado (solo explicación, sin repetir dirección/probabilidad/riesgo que ya están en el banner de decisión ni del hero).

### RF-8. Dashboard web
Frontend estático (HTML + Vanilla JS + Chart.js) con **3 vistas** en pestañas y **metodología en el pie**:

1. **Descriptiva** — banner de decisión técnica al inicio, gráficos de precio (SMA20/SMA50), RSI, MACD e interpretación por reglas (solo diagnóstico).
2. **Predictiva** — banner de decisión predictiva al inicio, panel IA (conclusión/justificación, sin repetir pill de dirección), pronóstico ARIMA, sentimiento de noticias.
3. **Prescriptiva** — hero con señal BUY/HOLD/SELL + SL/TP + razón principal, análisis de riesgo, backtesting (métricas + curva de capital vs Buy & Hold + consejo) y KPIs podados (Recomendación IA, Probabilidad IA, Ratio R/B, Riesgo, Acierto histórico). La fila de KPIs no duplica Señal/SL/TP (ya están en el hero).
4. **Footer** — Metodología TDSP (paso a paso en 5 fases interactivas) y Diccionario de términos.

- El bis utilización de datos: como la serie OHLCV puede venir de **Supabase** (`fuente: "supabase"`) o de **yfinance** (`fuente: "yfinance"`), el UI lo indica en `_data_meta.proveedor`.

### RF-9. ETL programado a Supabase + sentimiento ML
- **Cron diario** en GitHub Actions (`ingest.yml`) a `0 23 * * *` = **18:00 h hora Perú**, además en `workflow_dispatch` y `push` a `main`.
- Orden del workflow: instalar deps → **entrenar el modelo de sentimiento** (`scripts/train_sentiment.py`, TF-IDF + LogisticRegression multinomial) → **ingestar 8 tickers** (`scripts/ingest.py`: OHLCV 1y + ARIMA snapshot + noticias con clasificación de sentimiento) → verificar filas en Supabase → smoke test de la API desplegada (`scripts/smoke_remote.py`).
- `vercel.json` queda con `"crons": []` (la automatización se movió a GitHub Actions).

---

## 3. Arquitectura técnica y stack

| Capa | Tecnología |
|------|-----------|
| Backend | **Python ≥ 3.12** + **FastAPI** + Uvicorn |
| Datos | **yfinance** (`>=1.7.0,<2`) + pandas + numpy |
| Econometría | **statsmodels** (ADF, ARIMA) |
| IA cualitativa | **google-genai** (Gemini Flash, solo texto) |
| ML clásico | **scikit-learn** (TF-IDF + LogisticRegression) — sentimiento de noticias |
| Persistencia | **Supabase Postgres** vía **psycopg** (transaction pooler, puerto 6543) |
| Frontend | HTML + Vanilla JS + **Chart.js** (CDN) |
| CI/CD | **GitHub Actions**: ETL diario 23:00 UTC + entrenamiento de sentimiento + smoke |
| Despliegue | **Vercel** (plan free), estáticos + API serverless |
| Tiempo de vida | Caché LRU en memoria **TTL 1 hora** (máx 128 entradas) anti rate-limit de Yahoo |

### Pipelines
- **A) Ingesta (GitHub Actions, 18:00 h Perú):** `yfinance` (1y) → limpieza → `augment` (indicadores) → **upsert** OHLCV en Supabase (PK `(ticker,date)`) → estimar ARIMA y guardar snapshot → descargar hasta 25 noticias por ticker → clasificar sentimiento → **upsert** en `news` (UNIQUE `(ticker,url)`).
- **B) Consulta (API):** leer de Supabase si hay datos frescos (≤ 10 días) o descargar en vivo de yfinance y persistir de paso; servir desde caché TTL 1 h; `force=True` fuerza recarga Yahoo.
- **C) Modelo de sentimiento:** `train_sentiment.py` descarga corpus etiquetado (FinBERT ESG / no-PII) de Hugging Face, realiza TF-IDF + LogisticRegression y guarda `models/sentiment_model.joblib` + `sentiment_meta.json` (re-entrenado cada día en CI).

---

## 4. Estructura de archivos

```
main.py                        # FastAPI (entrypoint para Vercel)
vercel.json                    # crons vacíos (ETL vía GitHub Actions)
pyproject.toml                 # Empacado e instalación editable
README.md                      # Documentación de ejecución y despliegue
.gitignore                     # Exclusiones de control de versiones
.python-version                # Python 3.12
.vercelignore                  # Exclusiones para el build de Vercel
KPIS_dashboard.txt             # KPIs de referencia del dashboard
GUIA_CONSTRUCCION_MVP.md       # Este documento
.github/
  workflows/ingest.yml         # Cron 0 23 * * *: ML + ETL + verificación + smoke
app/
  __init__.py
  cache.py                     # Caché TTL en memoria (thread-safe)
  data.py                      # OHLCV: Supabase-first + yfinance + persistencia
  indicators.py                # SMA, RSI, MACD, ATR + latest_values
  advisor.py                   # Diagnósticos por indicador + decisiones por vista
  arima_benchmark.py           # ADF + ARIMA (con fallback tendencial)
  gemini_client.py             # Análisis IA solo texto + narrativa enriquecida
  signal_engine.py             # Reglas BUY/HOLD/SELL + SL/TP + factor noticias
  backtest.py                  # Simulación 70/15/15 con fricción
  companies.py                 # Catálogo de empresas y resolución de nombres
  narrator.py                  # Narración en lenguaje humano por reglas
  db.py                        # Capa Supabase: esquema y upserts
  sentiment.py                 # Carga del modelo joblib + classify_texts
models/
  sentiment_model.joblib       # Generado por train_sentiment.py (CI)
  sentiment_meta.json          # Metadatos del modelo
public/
  index.html                   # Dashboard 3 vistas + footer TDSP
  app.js                       # Lógica del frontend (fetch a la API + Chart.js)
  style.css                    # Estilos
scripts/
  ingest.py                    # ETL: OHLCV + ARIMA + noticias + sentimiento
  train_sentiment.py           # Entrenamiento TF-IDF + LogisticRegression
  smoke.py                     # Smoke test local del pipeline completo
  smoke_remote.py              # Smoke test contra el despliegue (CI)
docs/
  arquitectura.html            # Diagrama de arquitectura (referencia visual)
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
    "yfinance>=1.7.0,<2",
    "pandas",
    "numpy",
    "statsmodels",
    "google-genai",
    "psycopg[binary]",
    "scikit-learn",
]

[tool.setuptools]
py-modules = ["main"]

[tool.setuptools.packages.find]
include = ["app*"]
```

> **Nota `yfinance>=1.7.0,<2`:** desde 1.7.0 el formato de `.news` cambió a ítems del tipo `{"id", "content": {...}}` (con `content.title`, `content.canonicalUrl.url`, `content.provider.displayName`, `content.pubDate`). `scripts/ingest.py._fetch_news` maneja esta forma y variantes con los helpers `_unwrap` (evalúa cadenas estilo dict) y `_dig` (navegación encadenada).

### Variables de entorno
```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_NARRATIVE_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql://postgres.xxxx:pass@aws-0-region.pooler.supabase.com:6543/postgres
# VERCEL_HOST (variable de GitHub Actions) = https://tu-app.vercel.app
```

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `GEMINI_API_KEY` | No | Key de Google AI Studio. Sin ella el sistema degrada a análisis técnico. |
| `GEMINI_MODEL` | No | Modelo de análisis (default: `gemini-2.5-flash`). |
| `GEMINI_NARRATIVE_MODEL` | No | Modelo de narración humana (default: `gemini-2.5-flash`). |
| `DATABASE_URL` | No* | URL de Supabase (transaction pooler, puerto 6543). Sin ella la API cae a yfinance en vivo y no persiste. *Obligatoria para el ETL. |
| `VERCEL_HOST` | No | Host del despliegue para el smoke remoto en CI. |
| `VERCEL` | No | Si está definida, la app no monta `public/` (Vercel sirve los estáticos). |

Notas:
- El archivo `.env` **nunca** debe commitearse. En GitHub Actions la URL se inyecta como **secret** `DATABASE_URL`.
- No existe `.env.example` versionado; la tabla anterior es la referencia canónica de variables.

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

`latest_values(df)`: devuelve el último cierre con `date, close, change_pct, volume, high, low, open, sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14` (NaN/inf → `None`; redondeados a 6 dígitos).

### 5.2 Carga de datos (`app/data.py`)
```python
PERIOD_LOOKBACK = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 360}
FRESH_DAYS = 10
fetch_ohlcv(ticker, period="6mo", force=False)
```
- Consulta `DATA_CACHE` (TTL 1 h) a menos que `force=True`.
- **Supabase-first:** si `db.available()`, lee `db.read_ohlcv()` y usa el frame solo si es **fresco** (última velas ≤ 10 días de antigüedad).
- Si no hay base o los datos no están frescos: descarga con `yf.Ticker(ticker).history(period, auto_adjust=True)`, 2 intentos con espera de 1 s, limpia (dropna en Close, zona horaria neutralizada), recorta a `PERIOD_LOOKBACK`, aplica `augment`, **persiste** en Supabase (`_persist_to_db`) y marca `source = "yfinance"`.
- Guarda en caché y devuelve el frame con `attrs["source"]` (`"supabase"` | `"yfinance"`).

`series_payload(frame, limit=180)`: serie de `dates` y listas `close, open, high, low, volume, sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14` (6 decimales, volúmenes enteros, `None` para NaN).

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
- Fallback tendencial: `np.polyfit` sobre últimos 20 cierres, proyectar horizontes 1..5.
- La ingesta guarda el resultado en `forecast_snapshots`; la API sirve el snapshot si existe (con `fuente` según origen).

### 5.5 Gemini (`app/gemini_client.py`)
- `analyze(context)` (solo texto):
  - Construye `_build_text_part(context)`: ticker, fecha, close, change_pct, SMA20/50, RSI14, MACD triplete, ATR14, pronóstico ARIMA 5 ruedas y precio proyectado.
  - Llama `_gemini_text` con `response_mime_type="application/json"` y `SYSTEM_PROMPT` que exige el esquema de RF-3 (predicción, probabilidad, nivel_riesgo, recomendación RETIRAR/AUMENTAR/MANTENER, conclusión_cualitativa, justificacion_tecnica).
  - Cualquier fallo o respuesta fuera de esquema → payload degradado (RF-3).
  - Devuelve `{prediccion, probabilidad, nivel_riesgo, recomendacion, conclusion_cualitativa, justificacion_tecnica, fuente}`.
- `enrich_narrative(paragraph_reglas, context)`: si hay API key, pide al modelo una narración humana de 4–7 oraciones en español (sin títulos/markdown/tablas); ante cualquier error devuelve `None` (se conserva la narración por reglas).

### 5.6 Motor de señales (`app/signal_engine.py`)
```python
SL_MULTIPLER = 1.5; TP_MULTIPLER = 3.0
MIN_ALCISTA_PROBABILITY = 0.65; MAX_RSI_BUY = 65.0
RECOMENDACION_TO_SEÑAL = {"AUMENTAR": "BUY", "RETIRAR": "SELL", "MANTENER": "HOLD"}
```
- `decide(context, gemini)` arma el payload de señal (ver RF-4 y contrato §6). Agrega razones técnicas (predicción/probabilidad, precio vs SMA50, RSI zona saludable, proyección ARIMA ±0.5%) y advertencias (RSI ≥ 70 / ≤ 30, probabilidad moderada, confluencia incompleta en BUY).
- `_news_factor(context)`: a partir de `noticias.counts {POS, NEU, NEG}` calcula `share = (POS−NEG)/total`; ≥ +0.4 → POSITIVO, ≤ −0.4 → NEGATIVO, > 0 → LIGERAMENTE_POSITIVO, < 0 → LIGERAMENTE_NEGATIVO, si no NEUTRAL. Si el factor es ±, se agrega una razón.

### 5.7 Backtest (`app/backtest.py`)
```python
TRAIN_RATIO = 0.70; FRICTION = 0.001; MAX_HOLD_BARS = 10
SL_MULTIPLIER = 1.5; TP_MULTIPLIER = 3.0; RSI_ENTRY_FLOOR = 35.0
```
- Igual que RF-5. Métricas anidadas bajo `bt.backtest` en la API.
- Si `arima_forecast` se pasa y existe, compara dirección del pronóstico contra el movimiento real de los últimos 5 cierres (`arima_coincide`).

### 5.8 Asesoría y decisiones (`app/advisor.py`)

**Diagnóstico por indicador (vista Descriptiva)** — devuelven `{descripcion, nota}` sin recomendación de acción:
- `describe_precio(close, sma20, sma50, change_pct)`: tendencia vs SMA50/SMA20 + lectura de la variación diaria.
- `describe_rsi(rsi14)`: `≥ 70` sobrecompra, `≤ 30` sobreventa, `≥ 55` media-alta, resto media-baja (con `nota`).
- `describe_macd(macd, macd_signal, macd_hist)`: histograma (positivo/negativo/cero) y posición de la línea vs señal.

**Decisión descriptiva** `resumen_descriptiva(...)` → `{recomendacion: INVERTIR|MANTENER|RETIRAR, titulo, descripcion, nota}` (ver RF-7). Se expone como `asesoria.decision`.

**Decisión predictiva** `resumen_predictiva(arima_next, last_close, prediccion, probabilidad, nivel_riesgo, noticias)` → `{recomendacion, direccion, confianza, nivel_riesgo, titulo, descripcion, nota}` (ver RF-7). `confianza` es `None` cuando `direccion == "NEUTRAL"`. Se expone como `decision_predictiva`.

> Las funciones `advise_precio/rsi/macd/arima/backtest` (`{descripcion, recomendacion, advertencia}`, green/amber/red) siguen disponibles y son usadas por `/api/screener`, `/api/forecast` y `/api/backtest`; en el dashboard ya no se renderizan como recomendación por gráfico.

### 5.9 Narrador (`app/narrator.py`)
Genera un párrafo con bullets: tendencia (vs SMA50/SMA20 + change_pct), RSI (≥70 corrección, ≤30 rebote, ≥55 media-alta, resto media-baja), MACD (hist + posición de línea), volatilidad (ATR % del precio: >3% alta, >1.5% moderada, resto baja), sección ARIMA (proyección + diff_pct con umbral ±0.5%) y conclusión con señal (compra/venta/mantenerse) + SL/TP + `razones[0]`. Devuelve `{parrafo, bullets, fuente: "reglas"}`; `main.py` intenta enriquecer con Gemini (`fuente: "gemini"`).

### 5.10 Persistencia (`app/db.py`, Supabase)
- `available()` = existe `DATABASE_URL`. `connect()` usa `psycopg` con `row_factory=dict_row`.
- Tablas (se crean con `init_schema()`):
  - `ohlcv(ticker, date, open, high, low, close, volume, sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14)` — **PK (ticker, date)**; `upsert_ohlcv` hace `ON CONFLICT DO UPDATE`.
  - `news(id, ticker, titulo, url, publisher, fecha, fecha_extraido, sentimiento, prob_pos, prob_neu, prob_neg)` — **UNIQUE (ticker, url)**; `upsert_news` actualiza sentimiento/probabilidades.
  - `forecast_snapshots(ticker, fecha_generado, horizonte, forecast_json, next_close, order_json, aic, method)` — **PK (ticker, fecha_generado)**; `upsert_forecast` con `ON CONFLICT DO NOTHING`.
  - `inference_log(id, ticker, fecha, prediccion, probabilidad, nivel_riesgo, fuente)` — log de inferencias.
- `read_ohlcv` devuelve un `DataFrame` con el estándar de columnas (`OHLCV_COLUMNS`) indexado por fecha; `read_news` y `read_latest_forecast` devuelven filas dict.

### 5.11 Sentimiento de noticias (`app/sentiment.py` + `scripts/train_sentiment.py`)
- `sentiment.classify_texts(texts)` carga `models/sentiment_model.joblib` (lazy) y devuelve `{sentimiento: POS|NEU|NEG, prob_pos, prob_neu, prob_neg}` por titular; sin modelo → todo NEU con 1/3 de probabilidad.
- `train_sentiment.py`: descarga corpus etiquetado (portugués/inglés/…) desde Hugging Face, filtra por idioma, contruye pipeline **TF-IDF + LogisticRegression**, valida y guarda el joblib + metadatos. Corre diariamente en CI **antes** de la ingesta para que las noticias del día se clasifiquen con el modelo recién entrenado.

---

## 6. Contratos de la API (endpoints)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado de la app, base de datos, modelo de sentimiento y key de Gemini. |
| GET | `/api/indicators?ticker=&period=` | OHLCV + indicadores + series + `asesoria {precio, rsi, macd, decision}`. |
| GET | `/api/forecast?ticker=&period=` | Pronóstico ARIMA 5 ruedas (snapshot de Supabase o en vivo) + asesoría. |
| GET | `/api/signal?ticker=&period=` | Señal final + SL/TP + narración + `decision_predictiva`. |
| GET | `/api/news?ticker=&limit=` | Noticias con sentimiento desde Supabase. |
| GET | `/api/interpret?ticker=&period=` | Narración en lenguaje humano. |
| GET | `/api/backtest?ticker=&period=1y` | Métricas de la simulación + consejo (anidado). |
| GET | `/api/refresh?tickers=SPY,AAPL,...` | Pre-cálculo/refresco de Yahoo (manual). |
| GET | `/api/screener?tickers=&period=` | Empresas analizadas con señal BUY/HOLD/SELL y volumen. |
| GET | `/favicon.ico` · `/favicon.png` | Favicon SVG (emoji de gráfico). |

Detalles por endpoint:

- **`/api/health`** → `{"status": "ok", "base_de_datos": bool, "sentimiento_modelo": bool, "gemini_key_present": bool}`.
- **`/api/indicators`** → `{ticker, nombre, period, ultimo, series, meta, asesoria}` donde `meta` incluye `proveedor ("Supabase Postgres" | "Yahoo Finance (recarga en vivo)"), tipo, period_solicitado, n_velas, ultima_fecha` y `asesoria` trae `{precio, rsi, macd, decision}` con los diagnósticos y la decisión descriptiva. Errores → **HTTP 502** con `{error: true, mensaje}`.
- **`/api/forecast`** → `{ticker, period, forecast}` donde `forecast` viene de `_forecast_snapshot` (snapshot de Supabase con `fuente: "supabase"`, o `arima_benchmark.estimate` con `fuente: "en_vivo"`) + `forecast_dates` (5 hábiles desde hoy) + `asesoria` (consejo ARIMA `{descripcion, recomendacion, advertencia}`).
- **`/api/signal`** (GET) → `{ticker, nombre, contexto_tecnico, analisis_ia, senal, narracion, decision_predictiva}`.
- **`/api/news`** → `{ticker, noticias: [{titulo, url, publisher, fecha, fecha_extraido, sentimiento, prob_pos, prob_neu, prob_neg}]}` (de Supabase; vacío si no hay base).
- **`/api/interpret`** → `{ticker, nombre, narracion}`.
- **`/api/backtest`** → `{ticker, period, backtest}` donde `backtest` incorpora `asesoria`. **El frontend debe desanidar** (`bt?.backtest || bt`).
- **`/api/refresh`** → `{evento: "manual"|"vercel-cron", resultados: [{ticker, status, datos: {close, rsi14, forecast_next}}]}`. Descarga forzada (`force=True`) por ticker; fallo por ticker → `status: "error"`.
- **`/api/screener`** → `{period, companies: [{ticker, nombre, close, change_pct, volume, rsi14, macd_hist, atr14, sma20, sma50, ultima_fecha, senal, asesoria, error?}]}`.
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
  "recomendacion_ia": "AUMENTAR|RETIRAR|MANTENER",
  "conclusion_cualitativa": "...",
  "justificacion_tecnica": "...",
  "sentimiento_noticias": "POSITIVO|NEGATIVO|NEUTRAL|LIGERAMENTE_POSITIVO|LIGERAMENTE_NEGATIVO",
  "razones": ["..."],
  "advertencias": ["..."],
  "regla_sl": "Cierre - 1.5 * ATR",
  "regla_tp": "Cierre + 3.0 * ATR"
}
```

**Estructura de `decision_predictiva`:**
```json
{
  "recomendacion": "INVERTIR|MANTENER|RETIRAR",
  "direccion": "ALCISTA|NEUTRAL|BAJISTA",
  "confianza": 78,
  "nivel_riesgo": "BAJO|MEDIO|ALTO",
  "titulo": "Decisión predictiva de la vista",
  "descripcion": "Síntesis del panorama esperado: ...",
  "nota": "El voto de decisión combina ..."
}
```
`confianza` es `null` cuando `direccion == "NEUTRAL"`.

**Estructura de la narración (`narracion`):**
```json
{
  "parrafo": "texto completo...",
  "bullets": ["...", "..."],
  "fuente": "reglas" | "gemini"
}
```

**`contexto_tecnico`:** `latest_values` + `ticker` + `noticias {total, counts, pos_ratio, neg_ratio}` + `arima_forecast`, `arima_next`, `arima_order`, `arima_adf_pvalue` (con fallback `None` si ARIMA falla).

---

## 7. Configuración de despliegue

### `vercel.json`
```json
{
  "crons": []
}
```
La automatización se movió a GitHub Actions (ver `ingest.yml`). El cron de Vercel quedó desactivado para no duplicar la ingesta.

### GitHub Actions (`.github/workflows/ingest.yml`)
- **Trigerrings:** `schedule: cron "0 23 * * *"` (18:00 h Perú), `workflow_dispatch` y `push` a `main`.
- **Job `train-e-ingest`:** checkout → Python 3.12 → `pip install -e .` → `python scripts/train_sentiment.py` → `python scripts/ingest.py` (timeout 30 min) → verificación de presencia de velas/noticias/forecast en Supabase.
- **Job `smoke`:** tras la ingesta (`if: always()`), `continue-on-error`, corre `scripts/smoke_remote.py --base $VERCEL_HOST` contra el despliegue y valida la base.
- Secret requerido: `DATABASE_URL`. Variable opcional: `VERCEL_HOST`.

### `vercelignore`
Excluir del build: `.venv`, `__pycache__`, `*.py[co]`, `*.egg-info`, `build/`, `dist/`, `wheels/`, `.env`, `*.log`, `.git`, `.github`, `models/`, `scripts/`, `docs/`.

### Ejecución local
```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e .        # Windows
# .venv/bin/python -m pip install -e .          # Linux/macOS
# opcional: entrenar el modelo de sentimiento
.venv\Scripts\python scripts/train_sentiment.py
# con o sin DATABASE_URL (sin base usa yfinance en vivo)
$env:DATABASE_URL = "postgresql://...@...pooler.supabase.com:6543/postgres"
.venv\Scripts\python -m uvicorn main:app --port 8000
# Abrir http://localhost:8000  ·  API docs en http://localhost:8000/docs
```

### Despliegue en Vercel (free)
1. `npm i -g vercel && vercel`.
2. Variables de entorno: `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_NARRATIVE_MODEL`, `DATABASE_URL` (o desde *Project → Settings → Environment Variables*).
3. Desplegar `vercel --prod`.
4. Configurar el secret `DATABASE_URL` en GitHub → *Settings → Secrets* para el workflow.
5. Verificar: dashboard en `/`, docs en `/docs`, smoke local (`python scripts/smoke.py`) y smoke remoto contra producción.

---

## 8. Criterios de aceptación

### 8.1 Smoke test (`scripts/smoke.py`)
Validar en este orden y reportar `[PASS]/[FAIL]` con tiempos:

1. **Reglas locales:** `advisor.advise_rsi(78) → "No invertir"`; nombres reales de AAPL; presencia de AMZN/TSLA/GOOGL/META en el catálogo.
2. **Pipeline por ticker** (`SPY`, `AAPL`, `NVDA`, period `6mo`):
   - `fetch_ohlcv` devuelve ≥ 50 velas.
   - `latest_values` tiene `rsi14, macd, atr14, sma20` no `None`.
   - `series_payload` con `len(dates) == len(close) > 0`.
   - `arima_benchmark.estimate` devuelve `forecast` no vacío y `next_close` definido.
3. **Degradación sin API key:** `gemini_client.analyze` (sin key) → `prediccion == "NEUTRAL"`, `probabilidad == 0.5`, `recomendacion == "MANTENER"` y `conclusion_cualitativa` presente; `signal_engine.decide` → `HOLD`; `narrator.explain` → párrafo/bullets no vacíos; `sentiment.classify_texts` → POS/NEG si el modelo está disponible (corre `train_sentiment.py`).
4. **DB:** si `DATABASE_URL` está configurada, `db.init_schema()` y `db.connected()` → PASS; si no, reportar FAIL informativo ("fallback a yfinance en vivo").
5. **Backtest SPY** (`1y`): `disponible` es `true` o hay `mensaje`.
6. **Endpoints HTTP** con `TestClient(fastapi)`:
   - `/api/health` → 200 con `base_de_datos` no `None`.
   - `/api/indicators?ticker=SPY&period=3mo` → 200, `series.dates` no vacío, `asesoria` ⊇ `{precio, rsi, macd}` (y `decision`).
   - `/api/forecast?ticker=SPY&period=3mo` → 200 con `forecast.fuente ∈ {supabase, en_vivo}` y `forecast.asesoria.recomendacion`.
   - `/api/signal?ticker=SPY&period=3mo` → 200 con `senal.direccion ∈ {BUY, HOLD, SELL}`, `senal.recomendacion_ia ∈ {AUMENTAR, RETIRAR, MANTENER}`, `narracion.parrafo` y `nombre`.
   - `/api/news?ticker=SPY` → 200 y contiene `noticias`.
   - `/api/backtest?ticker=SPY` → 200.
   - `/api/screener?tickers=SPY,AAPL&period=3mo` → 200, 2 companies, cada una con `nombre` y `senal ∈ {BUY, HOLD, SELL}`.
   - `/api/interpret?ticker=AAPL&period=3mo` → 200 con `narracion.parrafo`.
   - `/favicon.ico` → 200.

### 8.2 Smoke de producción (`scripts/smoke_remote.py`)
- Replica los checks HTTP contra `--base` (Vercel) sin causar recargas pesadas; usado en CI (`job smoke`).

### 8.3 Checklist de producto
- [ ] Los 10+ endpoints responden según sus contratos y los errores devuelven 502 con `{error, mensaje}`.
- [ ] Sin `GEMINI_API_KEY`, todo el sistema funciona degradando con elegancia (señal HOLD coherente, narrativa por reglas, todos los diagnósticos y decisiones visibles).
- [ ] Cada vista muestra **una única decisión** (INVERTIR/MANTENER/RETIRAR) y los gráficos solo diagnostican; no hay recomendaciones duplicadas ni banners repetidos.
- [ ] El dashboard carga las 3 vistas y consume únicamente la API descrita.
- [ ] El ETL de GitHub Actions corre a las **23:00 UTC (18:00 h Perú)** y persiste OHLCV + ARIMA + noticias con sentimiento en Supabase.
- [ ] El modelo de sentimiento se re-entrena en CI antes de la ingesta (TF-IDF + LogisticRegression).
- [ ] `vercel.json` no tiene crons que dupliquen la ingesta.
- [ ] `README.md` documenta funcionalidades, estructura, ejecución local, variables de entorno, despliegue y endpoints (incluye el despliegue del workflow).

---

## 9. Instrucciones para el agente (orden de implementación)

Si se parte de cero, implementar en este orden (para modificar, seguir la misma progresión lógica):

1. **Esqueleto y config:** `pyproject.toml`, `.gitignore`, `.python-version`, `.vercelignore`, `vercel.json` (crons vacíos), `README.md`, carpeta `app/` con `__init__.py`.
2. **Datos e indicadores:** `cache.py` → `indicators.py` → `data.py` (Supabase-first + yfinance + persistencia) → `companies.py`.
3. **Persistencia:** `db.py` (esquema y upserts) y `sentiment.py`.
4. **Modelos:** `arima_benchmark.py` → `advisor.py` (diagnósticos + decisiones por vista).
5. **IA y señales:** `gemini_client.py` (solo texto) → `signal_engine.py` → `narrator.py`.
6. **ETL y ML:** `scripts/train_sentiment.py` → `scripts/ingest.py` → `.github/workflows/ingest.yml`.
7. **Backtesting:** `backtest.py`.
8. **API:** `main.py` con todos los endpoints, CORS, favicon y montaje de estáticos condicional a `VERCEL`.
9. **Frontend:** `public/index.html`, `style.css`, `app.js` con las 3 vistas (banner de decisión al inicio de cada una, gráficos con diagnóstico, KPIs sin duplicar el hero) y footer TDSP + diccionario.
10. **Validación:** `scripts/smoke.py`, `scripts/smoke_remote.py` y ejecutar el smoke local hasta que todo pase en verde (los únicos FAIL tolerables sin infraestructura son `DATABASE_URL` y `sentimiento_modelo` sin modelo entrenado).

**Reglas de escritura:**
- Sin comentarios en el código salvo que se pidan; nombres de funciones/variables autocontenidos en inglés o español consistente.
- No commitear `.env`, secrets ni el archivo `models/*.joblib` (se regenera en CI).
- Todo texto visible al usuario (dashboard, narrativas, consejos, paneles) en español.
- Vocabulario de decisión consistente: **INVERTIR / MANTENER / RETIRAR** (vista predictiva además: ALCISTA/NEUTRAL/BAJISTA, confianza, riesgo).
- Mantener el costo en S/0: sin servicios de pago ni dependencias privativas.