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

**Vocabulario de decisión:** las decisiones de cada vista usan **INVERTIR / MANTENER / RETIRAR** (la decisión predictiva además reporta dirección **ALCISTA / NEUTRAL / BAJISTA** y niveles de confianza/riesgo como dato secundario). Las vistas **no** repiten gráficos ni cadenas de decisión: descriptiva y predictiva muestran su banner de decisión al inicio; prescriptiva muestra hero de señal (sin banner) más los KPIs podados.

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
- Determinar el grado de diferenciación `d`: iterar mientras `p-value > 0.05` (hasta **3 pasadas** de diferenciación; el `d` resultante queda entre 0 y 2). Primera prueba sin diferenciar; por cada pasada se resta 1.
- Probar grid `p,q ∈ {0,1,2}` (excluyendo `(0,0)`), calibrar con `statsmodels.tsa.arima.model.ARIMA` y elegir el orden de **menor AIC**.
- Pronosticar **5 ruedas bursátiles**.
- **Fallback:** si ARIMA falla, ajustar una recta por mínimos cuadrados sobre los últimos 20 cierres (`np.polyfit`) y proyectar 5 puntos (reportar `method: "trend"` y un `order` sintético). Si hay menos de 30 cierres válidos, lanzar `ValueError`.
- El resultado se guarda como **snapshot diario** en Supabase (`forecast_snapshots`); si existe un snapshot, la API lo sirve tal cual (`fuente: "supabase"`, **sin validación de frescura**; la validación de frescura solo aplica a la serie OHLCV). Si no hay snapshot, se recalcula en vivo (`fuente: "en_vivo"`).

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

- Partición cronológica estricta: **70% entrenamiento/calibración, 30% prueba fuera de muestra** (sin data leakage; **no existe** split de validación separado en la implementación actual).
- **Fricción transaccional: 0.1%** por operación.
- Entrada: precio sobre `SMA50` y (recuperación de sobreventa `RSI <= 35 → > 35` o breakout de momentum `RSI > 35 y ≤ 70 y MACD_HIST > 0`).
- Salida: tocar `SL` (1.5×ATR), tocar `TP` (3×ATR) o **máximo 10 velas** de permanencia.
- Si la serie tiene menos de 60 velas válidas, devolver `disponible: false` con mensaje.
- Métricas: win rate, % retorno total, % retorno Buy & Hold, maximum drawdown %, Sharpe anualizado (×√252), exceso de retorno vs Buy & Hold, detalle de operaciones (últimas 20) y curva de capital de estrategia vs Buy & Hold.
- La API responde **anidado**: `{ticker, period, backtest: {..., asesoria}}`; el frontend resuelve con `const b = bt?.backtest || bt || {}`.

### RF-6. Screener de mercado
Analizar 3 empresas (`NVDA, AAPL, MSFT`) con señal por reglas locales y **volumen**:

- `score` inicial 0.
- `+1` si `close > SMA50`, `−1` si `close < SMA50`.
- `+1` si `40 ≤ RSI14 ≤ 65`, `−1` si `RSI14 ≥ 75`.
- `+1` si `MACD_HIST > 0`, `−1` si `MACD_HIST < 0`.
- `score ≥ 2` → **BUY**; `score ≤ −2` → **SELL**; si no → **HOLD**.
- Cada fila incluye nombre de la empresa, cierre, variación %, **volumen**, RSI, MACD hist, ATR, SMA20/50, fecha y consejo de precio.

### RF-7. Decisiones por vista y diagnóstico por indicador
El dashboard **no** muestra recomendaciones "Apto/Precaución/No invertir" por gráfico. Cada gráfico muestra solo **diagnóstico** (`{descripcion, nota}`) y **cada vista tiene UNA decisión única**:

- **Diagnósticos (`describe_precio`, `describe_rsi`, `describe_macd`)** en `app/advisor.py`: explican el estado del indicador en español sin dar acción. `nota` puede llevar aclaraciones de riesgo.
- **Decisión descriptiva** (`resumen_descriptiva`): voto por **5 reglas de score técnico** — (1) `close > SMA50` → +1, si no −1; (2) `close > SMA20` → +1, si no −1; (3) RSI en 40–65 → +1, RSI ≥ 75 → −1, RSI ≤ 25 → −1; (4) `MACD_HIST > 0` → +1, si no −1; (5) `MACD > MACD_SIGNAL` → +1, si no −1. `score ≥ 2 → INVERTIR`, `≤ −2 → RETIRAR`, si no `MANTENER`. Se expone como `asesoria.decision` (con `titulo`, `descripcion` y `nota`) en `/api/indicators`.
- **Decisión predictiva** (`resumen_predictiva`): voto ponderado ARIMA (diff ±0.5% → ±0.4) + IA (`prediccion` × `probabilidad` × 0.6) + noticias (pos−neg clamp ±1 × 0.3). Umbrales ±0.25 → INVERTIR/RETIRAR (con dirección ALCISTA/BAJISTA), resto MANTENER/NEUTRAL. Reporta `confianza` (0–99; `null` si NEUTRAL) y `nivel_riesgo` (del modelo o derivado por `|score|`: ≥0.7 BAJO, ≥0.45 MEDIO, resto ALTO; NEUTRAL → MEDIO). Se expone como `decision_predictiva` en `/api/signal`.
- **Narración integral**: los gráficos de la vista Predictiva muestran la lectura de ARIMA y de IA por separado (solo explicación, sin repetir dirección/probabilidad/riesgo que ya están en el banner de decisión ni del hero).
- La **señal operativa** (RF-4) es la que usa el vocabulario **BUY/HOLD/SELL** (con SL/TP, razones y advertencias); las decisiones por vista se expresan en **INVERTIR/MANTENER/RETIRAR**.

### RF-8. Dashboard web
Frontend estático (HTML + Vanilla JS + Chart.js 4.x vía CDN) con **3 vistas** en pestañas y **metodología en el pie**. Cada tarjeta de gráfico muestra su párrafo de ayuda ("chart-hint") en español. El detalle de componentes por vista está en §5.12.

1. **Descriptiva** — banner de decisión técnica al inicio (`decisionDescr`), KPIs (precio, variación diaria, RSI, ATR, volumen, media 20/50, proveedor), **tablero de mercado de 8 activos**, **velas japonesas** (canvas propio), precio con SMA20/SMA50 y bandas ±1 ATR, RSI, MACD, volumen, histograma de retornos diarios, y al pie de cada gráfico su diagnóstico (`describe_precio`, `describe_rsi`, `describe_macd`). Consume `/api/indicators` y `/api/screener`.
2. **Predictiva** — banner de decisión predictiva al inicio (`decisionPred`), KPIs (pronóstico 5 días, variación esperada, dirección IA, probabilidad IA, nivel de riesgo, sentimiento de noticias), **pronóstico ARIMA a 5 días con cono de incertidumbre ±1·ATR**, chips de pronóstico, asesoría ARIMA, **tarjeta cualitativa de la IA** (conclusión + justificación, sin repetir pill de dirección), **sentimiento de noticias** (agregación por conteos + lista con enlaces) y **comparativo multi-ticker** del pronóstico. Consume `/api/forecast`, `/api/signal` y `/api/news`.
3. **Prescriptiva** — KPIs podados (Recomendación IA, Probabilidad IA, Ratio R/B, Riesgo, Acierto histórico; **no** duplican Señal/SL/TP) → **hero de señal** (BUY/HOLD/SELL + Entrada + SL/TP) → **recomendación de la IA** (pill + razones + advertencias + justificación) → **checklist de confluencia (5 ítems auditable)** → **matriz de decisión 3×3 (señal × recomendación IA) con celda actual resaltada** → **dimensionamiento de posición** (riesgo 1% del capital sobre la distancia al SL; solo para señales de compra) → **explicación en lenguaje humano** (narración) → **backtesting** (métricas + curva vs Buy & Hold + consejo) → **últimas operaciones simuladas** (tabla). Consume `/api/signal` y `/api/backtest`.
4. **Footer** — Metodología TDSP (paso a paso en 5 fases interactivas), pipeline analítico, cadena de valor, 3Vs del Big Data, herramientas, alcance ético y Diccionario de términos (glosario en acordeones).

- El uso de datos: como la serie OHLCV puede venir de **Supabase** (`fuente: "supabase"`) o de **yfinance** (`fuente: "yfinance"`), el UI lo indica en `_data_meta.proveedor` (KPIs y meta del activo).
- Flujo: al pulsar "Analizar", el frontend dispara en paralelo `indicators`, `screener` (8 activos), `signal`, `forecast`, `news` y `backtest`, y además un `forecast` por cada activo del panel (para el comparativo).

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
- **C) Modelo de sentimiento:** `train_sentiment.py` descarga el corpus `Kenpache/multilingual-financial-sentiment` (CSV o API de filas) de Hugging Face (con `FALLBACK_CORPUS` embebido si falla), realiza TF-IDF + LogisticRegression y guarda `models/sentiment_model.joblib` + `sentiment_meta.json` (re-entrenado cada día en CI).

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
  backtest.py                  # Simulación 70/30 con fricción
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
| `VERCEL_HOST` | No | Host del despliegue para el smoke remoto en CI (ej. `https://tu-app.vercel.app`). |
| `VERCEL` | No | Si está definida (presente en el entorno de Vercel), la app no monta `public/` (Vercel sirve los estáticos). |

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
- **Supabase-first:** si `db.available()`, lee `db.read_ohlcv()` (limit = `PERIOD_LOOKBACK[period]`) y usa el frame solo si es **fresco** (última velas ≤ 10 días de antigüedad).
- Si no hay base o los datos no están frescos: descarga con `yf.Ticker(ticker).history(period, auto_adjust=True)`, **2 intentos con espera de 1 s**, valida columnas OHLCV, neutraliza zona horaria (`tz_localize(None)`), elimina filas con `Close` nulo, recorta a `PERIOD_LOOKBACK`, aplica `augment`, **persiste** en Supabase (`_persist_to_db`, silenciando fallos) y marca `source = "yfinance"`.
- Guarda en caché y devuelve el frame con `attrs["source"]` (`"supabase"` | `"yfinance"`). También recibe `attrs["ticker"]` y `attrs["period"]` (los consume `latest_values` y `_data_meta`).

`series_payload(frame, limit=180)`: serie de `dates` y listas `close, open, high, low, volume, sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14` (6 decimales, volúmenes enteros, `None` para NaN).

### 5.3 Catálogo de empresas (`app/companies.py`)
```python
COMPANIES = {
    "NVDA": {"ticker": "NVDA", "name": "NVIDIA Corporation"},
    "AAPL": {"ticker": "AAPL", "name": "Apple Inc."},
    "MSFT": {"ticker": "MSFT", "name": "Microsoft Corporation"},
}
SCREENER_TICKERS = ["NVDA", "AAPL", "MSFT"]
resolve(ticker)  # UPPER + strip, devuelve {"ticker", "name"} con fallback al propio ticker
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
- Determinación de `d`: iterar ADF hasta `p-value ≤ 0.05` (máximo **3 pasadas**); al fallar las 3, devolver `d=2` con el p-value de la última pasada.
- Selección de `(p,d,q)` por menor AIC entre el grid `p,q ∈ {0,1,2}` (excluyendo `(0,0)`); cada candidato se ajusta en un `try/except` (los que fallan se saltan).
- Fallback tendencial: `np.polyfit` sobre últimos 20 cierres, proyectar horizontes 1..5, `order` sintético `(1,1,0)` y `aic=None`.
- Valores devueltos redondeados a 4 decimales (6 para `adf_pvalue`).
- La ingesta guarda el resultado en `forecast_snapshots` con la estructura completa (`forecast` como lista, `order` como dict, más `aic`, `method`, `next_close`, `horizonte`); la API sirve el snapshot transformado a `{adf_pvalue: null, d, order, aic, forecast (floats), forecast_dates: [], last_close, next_close, method, points, fecha_generado, fuente: "supabase"}`.

### 5.5 Gemini (`app/gemini_client.py`)
Constantes: `MODEL_DEFAULT = "gemini-2.5-flash"`, `TIMEOUT_SECONDS = 20`, `NARRATIVE_MODEL_DEFAULT = "gemini-2.5-flash"`.

`analyze(context)` (solo texto):
- Construye `_build_text_part(context)`: ticker, fecha, close, change_pct, SMA20/SMA50, RSI14, MACD triplete, ATR14, pronóstico ARIMA 5 ruedas y precio proyectado.
- Llama `_gemini_text` con `response_mime_type="application/json"` y este `SYSTEM_PROMPT` exacto (reproducirlo textual):

```text
Eres un analista senior de inversiones especializado en Swing Trading (posiciones de 3 a 10 ruedas bursatiles). Recibes el estado tecnico cuantitativo de un activo (precio, medias moviles SMA20/SMA50, RSI14, MACD, ATR14) y el pronostico econometrico ARIMA a 5 dias. Debes responder SOLO en JSON valido sin texto adicional, con la siguiente estructura exacta: {"prediccion": "ALCISTA"|"NEUTRAL"|"BAJISTA", "probabilidad": numero entre 0.0 y 1.0, "nivel_riesgo": "BAJO"|"MEDIO"|"ALTO", "recomendacion": "RETIRAR"|"AUMENTAR"|"MANTENER", "conclusion_cualitativa": "2 a 3 oraciones con tu lectura laica del contexto", "justificacion_tecnica": "explica en 2 a 3 oraciones la confluencia entre indicadores tecnicos y el pronostico ARIMA"} Reglas: 'AUMENTAR' solo cuando indicadores y ARIMA coinciden con alta conviccion; 'RETIRAR' cuando varios indicadores contradicen la posicion; 'MANTENER' en condiciones ambiguas o de espera.
```

- **Validación** `_is_valid(payload)`: dict con `prediccion ∈ {ALCISTA, NEUTRAL, BAJISTA}`, `recomendacion ∈ {RETIRAR, AUMENTAR, MANTENER}` y `probabilidad` numérica. Si falla la llamada o el esquema → payload degradado (RF-3).
- `fuente` se setea a `"gemini"` si `prediccion` es válida, si no `"degradado"`.
- Devuelve `{prediccion, probabilidad, nivel_riesgo, recomendacion, conclusion_cualitativa, justificacion_tecnica, fuente}`.

`enrich_narrative(paragraph_reglas, context)`: si no hay `GEMINI_API_KEY` devuelve `None`. Con key, llama con `NARRATIVE_INSTRUCTION` (textual):

```text
Actua como un analista senior que explica en lenguaje humano, claro y para inversionistas no tecnicos, el estado tecnico del activo descrito. Escribe de 4 a 7 oraciones en espanol, sin titulos, sin markdown y sin tablas. Menciona tendencia, RSI, MACD, volatilidad (ATR) y el pronostico econometrico. Termina con una frase de lectura practica para Swing Trading (horizonte de 3 a 10 ruedas bursatiles).
```

Ante cualquier error devuelve `None` (se conserva la narración por reglas).

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

**Decisión descriptiva** `resumen_descriptiva(close, sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14, change_pct)` → `{recomendacion: INVERTIR|MANTENER|RETIRAR, titulo, descripcion, nota}`. Reglas exactas (5 votos, ver RF-7): `close > sma50` +1/−1; `close > sma20` +1/−1; RSI 40–65 +1, ≥75 −1, ≤25 −1; `macd_hist > 0` +1/−1; `macd > macd_signal` +1/−1. `score ≥ 2 → INVERTIR`, `≤ −2 → RETIRAR`, resto `MANTENER`. Se expone como `asesoria.decision`.

**Decisión predictiva** `resumen_predictiva(arima_next, last_close, prediccion, probabilidad, nivel_riesgo, noticias)` → `{recomendacion, direccion, confianza, nivel_riesgo, titulo, descripcion, nota}` (ver RF-7). Detalle exacto: voto ARIMA `±0.4` si `|diff_pct| > 0.5`; voto IA `±1 × probabilidad × 0.6` (predict `ALCISTA`/`BAJISTA`; NEUTRAL suma 0); voto noticias `clamp(pos−neg, −1, 1) × 0.3`; umbrales `±0.25`. `confianza = clamp(|score|×100, 0, 99)` redondeada, y si hay `probabilidad` de IA y la dirección es direccional, se toma el mayor entre ese valor y `probabilidad×100`; `confianza` es `None` cuando `direccion == "NEUTRAL"`. Riesgo: el del modelo si existe, si no NEUTRAL→MEDIO, `|score|≥0.7→BAJO`, `≥0.45→MEDIO`, resto→ALTO. Se expone como `decision_predictiva`.

> Las funciones `advise_precio/rsi/macd/arima/backtest` (`{descripcion, recomendacion, advertencia}`, green/amber/red) siguen disponibles y son usadas por `/api/screener`, `/api/forecast` y `/api/backtest`; en el dashboard ya no se renderizan como recomendación por gráfico.

### 5.9 Narrador (`app/narrator.py`)
`explain(context, signal)` genera un párrafo con bullets: tendencia (vs SMA50/SMA20 + change_pct), RSI (≥70 corrección, ≤30 rebote, ≥55 media-alta, resto media-baja), MACD (hist + posición de línea), volatilidad (ATR % del precio: >3% alta, >1.5% moderada, resto baja), sección ARIMA (proyección + diff_pct con umbral ±0.5%) y conclusión con señal (compra/venta/mantenerse) + SL/TP (con la frase "relación riesgo-beneficio de 1:2") + `razones[0]`. Devuelve `{parrafo, bullets, fuente: "reglas"}`. El **intento de enriquecido con Gemini** (`fuente: "gemini"`) lo hace `main.py` vía `gemini_client.enrich_narrative`, sustituyendo solo el párrafo y conservando los bullets de reglas.

### 5.10 Persistencia (`app/db.py`, Supabase)
- `available()` = existe `DATABASE_URL` no vacía. `connect()` usa `psycopg` con `row_factory=dict_row` (contextmanager que hace commit al salir).
- `init_schema()` ejecuta estas sentencias DDL exactas (reproducir textual):

```sql
CREATE TABLE IF NOT EXISTS ohlcv (
    ticker TEXT NOT NULL, date DATE NOT NULL,
    open DOUBLE PRECISION, high DOUBLE PRECISION, low DOUBLE PRECISION,
    close DOUBLE PRECISION, volume BIGINT,
    sma20 DOUBLE PRECISION, sma50 DOUBLE PRECISION, rsi14 DOUBLE PRECISION,
    macd DOUBLE PRECISION, macd_signal DOUBLE PRECISION, macd_hist DOUBLE PRECISION,
    atr14 DOUBLE PRECISION, PRIMARY KEY (ticker, date));

CREATE TABLE IF NOT EXISTS news (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL, titulo TEXT NOT NULL, url TEXT NOT NULL,
    publisher TEXT, fecha TIMESTAMPTZ, fecha_extraido DATE NOT NULL,
    sentimiento TEXT, prob_pos DOUBLE PRECISION,
    prob_neu DOUBLE PRECISION, prob_neg DOUBLE PRECISION,
    UNIQUE (ticker, url));

CREATE TABLE IF NOT EXISTS forecast_snapshots (
    ticker TEXT NOT NULL, fecha_generado TIMESTAMPTZ NOT NULL DEFAULT now(),
    horizonte INTEGER NOT NULL, forecast_json JSONB, next_close DOUBLE PRECISION,
    order_json JSONB, aic DOUBLE PRECISION, method TEXT,
    PRIMARY KEY (ticker, fecha_generado));

CREATE TABLE IF NOT EXISTS inference_log (
    id BIGSERIAL PRIMARY KEY, ticker TEXT NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
    prediccion TEXT, probabilidad DOUBLE PRECISION,
    nivel_riesgo TEXT, fuente TEXT);
```

- Semántica de upserts (los nombres de parámetros son los del código): `upsert_ohlcv` → `ON CONFLICT (ticker, date) DO UPDATE SET` (14 columnas); `upsert_news` → `ON CONFLICT (ticker, url) DO UPDATE SET` (fecha_extraido, sentimiento, prob_*); `upsert_forecast` → `ON CONFLICT (ticker, fecha_generado) DO NOTHING` (inserción única diaria). `inference_log` está definida pero **ningún flujo la inserta hoy**.
- `read_ohlcv(ticker, limit)` renombra columnas al estándar `OHLCV_COLUMNS = ["Open","High","Low","Close","Volume","SMA20","SMA50","RSI14","MACD","MACD_SIGNAL","MACD_HIST","ATR14"]` e indexa por fecha; `read_news` y `read_latest_forecast` (con `json_loads` sobre `forecast_json`/`order_json`) devuelven filas dict.

### 5.11 Sentimiento de noticias (`app/sentiment.py` + `scripts/train_sentiment.py`)
- `sentiment.available()` = `models/sentiment_model.joblib` existe (o ya cargado). `classify_texts(texts)` carga el joblib (lazy) y devuelve `{sentimiento: POS|NEU|NEG, prob_pos, prob_neu, prob_neg}` por titular; sin modelo → todo NEU con 1/3 de probabilidad. El texto se normaliza (`join(split)`) y se trunca a 400 caracteres. `sentimiento` sale de `model.classes_` mapeando prefijos (`POS`→POS, `NEG`→NEG, resto→NEU).
- `train_sentiment.py` construye el pipeline exacto: `TfidfVectorizer(ngram_range=(1,2), max_features=20000, sublinear_tf=True)` + `LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000)`. Parámetros del corpus: `MAX_ROWS=20000`, `CLASS_CAP=6000` por clase, `KEEP_LANGS = {en, es, eng, spa, english, spanish, en-us, es-es, english_us}`, y se deduplican textos y se balancean 6000 por clase (`random_state=7`). Split 80/20 estratificado (`random_state=7`).
- **Corpus (fiel al código):** primero intenta el CSV `https://huggingface.co/datasets/Kenpache/multilingual-financial-sentiment/resolve/main/all_languages_clean.csv` y si no alcanza 500 filas válidas, la API `https://datasets-server.huggingface.co/rows?dataset=Kenpache%2Fmultilingual-financial-sentiment&config=default&split=train&offset={offset}&length=100`. Si ambas fallan, usa el **corpus de respaldo embebido `FALLBACK_CORPUS`** (~65 frases POS/NEG/NEU en inglés y español).
- Guarda `models/sentiment_model.joblib` + `models/sentiment_meta.json` (fecha, clase, n_total/n_train/n_test, accuracy, f1_macro, classes, report). Corre diariamente en CI **antes** de la ingesta para que las noticias del día se clasifiquen con el modelo recién entrenado.

### 5.12 Frontend (`public/`) — descripción fiel al código
HTML estático (`index.html`) + `style.css` + `app.js` (Vanilla JS + Chart.js 4.4.9 por CDN). Índices de acceso: `series.dates/close/open/high/low/volume/sma20/sma50/rsi14/macd/macd_signal/macd_hist/atr14`; `asesoria.{precio,rsi,macd,decision}`; `forecast.{forecast,forecast_dates,next_close,last_close,method,aic,asesoria}`; `senal.{señal,direccion,stop_loss,take_profit,razones,advertencias,sentimiento_noticias,ratio_riesgo_beneficio}`; `analisis_ia.{prediccion,probabilidad,nivel_riesgo,recomendacion,conclusion_cualitativa,justificacion_tecnica,fuente}`; `backtest.{disponible,mensaje,win_rate,n_trades,total_return_pct,buy_hold_return_pct,max_drawdown_pct,sharpe_ratio,curva,asesoria,trades}` (desanidar con `bt?.backtest || bt`).

Vista 1 · **Descriptiva** (`renderDescriptiva`): banner `decisionDescr` (de `asesoria.decision`) · 7 KPIs · tablero de mercado (`screener.companies`, color por variación y borde por señal) · velas japonesas en canvas propio (`chartCandle`, últimos 80 días, tooltip OHLC con hover y redibujado en resize) · gráficos: precio+bandas ±1 ATR, RSI (con bandas pintadas 70/30 y líneas de referencia), MACD (barras coloreadas por signo), volumen, histograma de retornos (buckets de 1%, excluye |r|≥15% y rango>18) · asesorías `advicePrecio/adviceRsi/adviceMacd` (diagnóstico, sin acción) + decisión.

Vista 2 · **Predictiva** (`renderPredictiva`): banner `decisionPred` (de `decision_predictiva`) · 6 KPIs · pronóstico (`chartForecast`) con **cono ±1·ATR** (banda inferior/cono/pronóstico punteado/histórico últimos 10 velas, `labels` = históricos + `forecast_dates` truncado al largo del pronóstico) · chips día 1..5 · asesoría ARIMA (`adviceArima`) · tarjeta IA (`iaBox`: conclusión + justificación + badge "Gemini"/"Reglas cuantitativas") · sentimiento de noticias (barras de conteo POS/NEU/NEG + lista con enlace, badge y probabilidades) · comparativo multi-ticker (`compareBox`, tabla con cierre, pronóstico 5d, var. esperada, método, AIC).

Vista 3 · **Prescriptiva** (`renderPrescriptiva`): 4-5 KPIs (Recomendación IA, Probabilidad IA, Ratio R/B, Riesgo, Acierto histórico); **hero de señal** (pill Señal + empresa · direccion + niveles SL/Entrada/TP); **recomendación IA** (`recommendBox`: pill, dirección, probabilidad, riesgo, conclusión, razones ✓, advertencias ⚠, justificación); **checklist de confluencia** (`checklistBox`, 5 ítems ✓/✗: precio sobre SMA50 · RSI<70 · probabilidad IA ≥65% · ARIMA var ≥ ±0.5% · noticias sin sesgo claramente negativo); **matriz de decisión** (`matrixBox`, 3×3 señal×IA con colores y celda actual resaltada); **dimensionamiento** (`positionBox`, slider de capital S/ con riesgo 1% sobre distancia SL → unidades y monto; solo señales de compra); **narración** (`narracionBox`, párrafo + bullets + badge de fuente); **backtest** (métricas KPI, curva vs Buy & Hold, consejo `asesoria`, tabla de últimas operaciones).

Footer: stepper TDSP de **5 fases** interactivo; pipeline analítico en 5 pasos; cadena de valor; 3Vs; herramientas y presupuesto; alcance ético; glosario (acordeones). Tema claro/dark con variables CSS y paleta: `up=#26a269`, `down=#f14c4c`, `accent=#58a6ff`, `cyan=#6fddff`, `yellow=#d29922`, `purple=#bc4c9a`. El selector de empresa (8 activos) y periodicidad (3mo/6mo/1y) aparecen en la cabecera; un solo botón "Analizar" dispara las 6 llamadas de la vista activa + 7 `forecast` adicionales para el comparativo. Los textos visibles son todos en español.

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
| GET | `/api/refresh?tickers=NVDA,AAPL,MSFT` | Pre-cálculo/refresco de Yahoo (manual). |
| GET | `/api/screener?tickers=&period=` | Empresas analizadas con señal BUY/HOLD/SELL y volumen. |
| GET | `/favicon.ico` · `/favicon.png` | Favicon SVG (emoji de gráfico). |

Detalles por endpoint:

- **`/api/health`** → `{"status": "ok", "base_de_datos": bool, "sentimiento_modelo": bool, "gemini_key_present": bool}`. `base_de_datos` es `False` si no hay `DATABASE_URL`.
- **`/api/indicators`** → `{ticker, nombre, period, ultimo, series, meta, asesoria}` donde `meta` incluye `proveedor ("Supabase Postgres" | "Yahoo Finance (recarga en vivo)"), tipo, period_solicitado, n_velas, ultima_fecha`; `ultimo` trae `date, close, change_pct, volume, high, low, open, sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14`; y `asesoria` trae `{precio, rsi, macd, decision}` con los diagnósticos `{descripcion, nota}` y la decisión descriptiva. Errores → **HTTP 502** con `{error: true, mensaje}`.
- **`/api/forecast`** → `{ticker, period, forecast}` donde `forecast` viene de `_forecast_snapshot` y trae: `{adf_pvalue, d, order {p,d,q}, aic, forecast [5 floats], forecast_dates [5 fechas hábiles desde hoy], last_close, next_close, method ("arima"|"trend"), points, fecha_generado (null en vivo), fuente ("supabase"|"en_vivo")}` + `asesoria` (consejo ARIMA `{descripcion, recomendacion, advertencia}`). Regla de fuente: si `db.read_latest_forecast(ticker)` devuelve un snapshot con `forecast` no vacío → `fuente: "supabase"` (sin filtro de frescura); si no → `arima_benchmark.estimate` con `fuente: "en_vivo"`.
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
Notas de la clave acentuada: el campo se llama literalmente `"señal"` (acento) en la respuesta, igual `regla_sl`/`regla_tp`.

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
- **Triggers:** `schedule: cron "0 23 * * *"` (18:00 h Perú), `workflow_dispatch` y `push` a `main`.
- **Job `train-e-ingest`:** checkout → Python 3.12 → `pip install -e .` → `python scripts/train_sentiment.py` → `python scripts/ingest.py` (timeout 30 min) → verificación en Python de velas/noticias/forecast por ticker (NVDA, AAPL, MSFT). `DATABASE_URL` se inyecta como secret en el `env` del job.
- **Job `smoke`:** `needs: train-e-ingest`, `if: always()`, `continue-on-error: true`; corre `scripts/smoke_remote.py --base "$VERCEL_HOST"` (con fallback a `https://swing-trading-consultor-ia.vercel.app` si la variable no existe) y valida también `db.connected()`.
- Secret requerido: `DATABASE_URL`. Variable opcional del repo: `VERCEL_HOST`.

### `vercelignore`
Excluir del build (contenido real): `.venv`, `__pycache__`, `*.py[co]`, `*.egg-info`, `build/`, `dist/`, `wheels/`, `.env`, `*.log`, `log.json`, `*-log-export-*.json`, `.git`, `.github`, `models/`, `scripts/`, `docs/`.

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

1. **Reglas locales:** `advisor.advise_rsi(78) → "No invertir"`; nombres reales de AAPL, NVDA y MSFT en el catálogo.
2. **Pipeline por ticker** (`NVDA`, `AAPL`, `MSFT`, period `6mo`, con `force=True`):
   - `fetch_ohlcv` devuelve ≥ 50 velas.
   - `latest_values` tiene `rsi14, macd, atr14, sma20` no `None`.
   - `series_payload` con `len(dates) == len(close) > 0`.
   - `arima_benchmark.estimate` devuelve `forecast` no vacío y `next_close` definido.
3. **Degradación sin API key:** con un contexto técnico mínimo (`ticker, close, sma20, sma50, rsi14, macd, macd_signal, noticias {total, counts}`): `gemini_client.analyze` (sin key) → `prediccion == "NEUTRAL"`, `probabilidad == 0.5`, `recomendacion == "MANTENER"` y `conclusion_cualitativa` presente; `signal_engine.decide` → `direccion == "HOLD"` y mapeo `AUMENTAR→BUY`, `RETIRAR→SELL`; `narrator.explain` → párrafo/bullets no vacíos; `sentiment.classify_texts` devuelve POS/NEG si el modelo está disponible (corre `train_sentiment.py`).
4. **DB:** si `DATABASE_URL` está configurada, `db.init_schema()` y `db.connected()` → PASS; si no, reportar FAIL informativo ("no configurada; el fallback usa yfinance en vivo").
5. **Backtest NVDA** (`1y`): `disponible` es `true` o hay `mensaje`.
6. **Endpoints HTTP** con `TestClient(fastapi)`:
   - `/api/health` → 200 con `base_de_datos` no `None`.
   - `/api/indicators?ticker=NVDA&period=3mo` → 200, `series.dates` no vacío, `asesoria` contiene `{precio, rsi, macd}` (y `decision`).
   - `/api/forecast?ticker=NVDA&period=3mo` → 200 con `forecast.fuente ∈ {supabase, en_vivo}` y `forecast.asesoria.recomendacion`.
   - `/api/signal?ticker=NVDA&period=3mo` → 200 con `senal.direccion ∈ {BUY, HOLD, SELL}`, `senal.recomendacion_ia ∈ {AUMENTAR, RETIRAR, MANTENER}`, `narracion.parrafo` y `nombre`.
   - `/api/news?ticker=NVDA` → 200 y contiene `noticias`.
   - `/api/backtest?ticker=NVDA` → 200.
   - `/api/screener?tickers=NVDA,AAPL&period=3mo` → 200, 2 companies, cada una con `nombre` y `senal ∈ {BUY, HOLD, SELL}`.
   - `/api/interpret?ticker=AAPL&period=3mo` → 200 con `narracion.parrafo`.
   - `/favicon.ico` → 200.

### 8.2 Smoke de producción (`scripts/smoke_remote.py`)
- Usa `urllib` contra `--base` (default `https://swing-trading-consultor-ia.vercel.app`): `/api/health`, `db.connected()`, y `{indicators, forecast, signal, backtest, news, screener}` validando el campo clave de cada respuesta (`series`, `forecast`, `senal`, `backtest`, `noticias`, `companies`). Termina con `sys.exit(0/1)`; usado en CI (`job smoke`).

### 8.3 Checklist de producto
- [ ] Los 10+ endpoints responden según sus contratos y los errores devuelven 502 con `{error, mensaje}`.
- [ ] Sin `GEMINI_API_KEY`, todo el sistema funciona degradando con elegancia (señal HOLD coherente, narrativa por reglas, todos los diagnósticos y decisiones visibles).
- [ ] Cada vista muestra **una única decisión** (INVERTIR/MANTENER/RETIRAR; prescriptiva usa hero de señal) y los gráficos solo diagnostican; no hay recomendaciones duplicadas ni banners repetidos.
- [ ] El dashboard carga las 3 vistas, consume únicamente la API descrita e incluye el comparativo multi-ticker, checklist de confluencia, matriz de decisión y dimensionamiento de posición.
- [ ] El ETL de GitHub Actions corre a las **23:00 UTC (18:00 h Perú)** y persiste OHLCV + ARIMA + noticias con sentimiento en Supabase.
- [ ] El modelo de sentimiento se re-entrena en CI antes de la ingesta (TF-IDF + LogisticRegression) con el corpus documentado y su fallback embebido.
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
8. **API:** `main.py` con todos los endpoints, CORS, favicon y montaje de estáticos condicional a `VERCEL`. El forecast arma `_forecast_snapshot` (snapshot de Supabase sin filtro de frescura → `fuente: "supabase"`; si no, ARIMA en vivo → `fuente: "en_vivo"`).
9. **Frontend:** `public/index.html`, `style.css`, `app.js` con las 3 vistas descritas en §5.12 (banner de decisión al inicio de descriptiva/predictiva, hero de señal en prescriptiva, gráficos con diagnóstico, KPIs sin duplicar el hero, checklist de confluencia, matriz de decisión, dimensionamiento y comparativo) y footer TDSP + diccionario.
10. **Validación:** `scripts/smoke.py`, `scripts/smoke_remote.py` y ejecutar el smoke local hasta que todo pase en verde (los únicos FAIL tolerables sin infraestructura son `DATABASE_URL` (base de datos) y `sentimiento_modelo` sin modelo entrenado). También pasar `scripts/train_sentiment.py` y, si se cuenta con Supabase, `scripts/ingest.py`.

**Reglas de escritura:**
- Sin comentarios en el código salvo que se pidan; nombres de funciones/variables autocontenidos en inglés o español consistente.
- No commitear `.env`, secrets ni el archivo `models/*.joblib` (se regenera en CI).
- Todo texto visible al usuario (dashboard, narrativas, consejos, paneles) en español.
- Vocabulario de decisión consistente: **INVERTIR / MANTENER / RETIRAR** (decisión predictiva además: ALCISTA/NEUTRAL/BAJISTA, confianza, riesgo); la señal operativa usa **BUY/HOLD/SELL**.
- Mantener el costo en S/0: sin servicios de pago ni dependencias privativas.