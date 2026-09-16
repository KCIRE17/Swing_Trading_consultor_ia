# DSS Swing Trading con Business Analytics e IA (MVP)

Prototipo (MVP) desplegable en **Vercel (plan free)** del sistema de soporte a la toma de
decisiones para inversiones en la modalidad de **Swing Trading**, descrito en la
documentación del Equipo 7.

**Costo total: S/ 0.00** · Metodología: TDSP (Fase de prototipado) · **Sin servicios locales persistidos**.

Toda la persistencia y el procesamiento viven en la nube: **Supabase (Postgres)**, **GitHub
Actions (ETL + entrenamiento ML)** y **Vercel (API + dashboard)**.

---

## Funcionalidades

- **Dashboard 3 vistas** (Descriptiva, Predictiva, Prescriptiva) con Chart.js:
  - *Descriptiva*: KPIs, tablero de 8 activos, velas japonesas, SMA/ATR, RSI, MACD, volumen e histograma de retornos.
  - *Predictiva*: pronóstico ARIMA 5 ruedas con cono ±1·ATR, tarjeta cualitativa de la IA (Gemini) y sentimiento de las noticias (ML).
  - *Prescriptiva*: señal BUY/HOLD/SELL con SL/TP, recomendación de la IA (AUMENTAR/MANTENER/RETIRAR), checklist de confluencia, matriz de decisión, dimensionamiento de posición y backtesting.
- **Indicadores técnicos**: SMA20/SMA50, RSI14, MACD (12,26,9) y ATR14.
- **Benchmark econométrico ARIMA**: test ADF, orden `(p,d,q)` por AIC y pronóstico a 5 ruedas.
- **Sentimiento de noticias con Machine Learning**: clasificador **TF-IDF + Regresión Logística** reentrenado en cada corrida del ETL con \(12\,000+\) titulares financieros.
- **Inferencia cualitativa con Google Gemini Flash** (solo texto): devuelve `prediccion` (ALCISTA/NEUTRAL/BAJISTA), `probabilidad`, `nivel_riesgo`, `recomendacion`, `conclusion_cualitativa` y `justificacion_tecnica`. Sin clave, degrada a reglas cuantitativas.
- **Motor de señales**: BUY/HOLD/SELL con Stop-Loss (`cierre - 1.5·ATR`) y Take-Profit (`cierre + 3·ATR`), alimentado por la confluencia técnica + recomendación de la IA + tono de las noticias.
- **Backtesting** con partición 70/15/15, fricción del 0.1%, Win Rate, Maximum Drawdown, Sharpe y comparación contra Buy & Hold.
- **Screener de mercado**: 8 empresas analizadas con señal por activo.
- **Persistencia en Supabase**: tablas `ohlcv`, `news`, `forecast_snapshots` e `inference_log`.

## Estructura

```
main.py               # FastAPI (entrypoint Vercel)
vercel.json           # Config de despliegue (crons trasladados a GitHub Actions)
pyproject.toml        # Dependencias (psycopg, scikit-learn, statsmodels, …)
app/
  db.py               # Adaptador Supabase Postgres (upserts + lecturas)
  cache.py            # Caché LRU en memoria (1h) anti rate-limit de Yahoo
  data.py             # OHLCV: lee Supabase (fresh) con fallback yfinance + persistencia
  indicators.py       # SMA, RSI, MACD, ATR
  advisor.py          # Consejos por gráfico (reglas locales) + screener
  arima_benchmark.py  # ADF + ARIMA (con fallback de tendencia)
  sentiment.py        # Modelo TF-IDF + LogisticRegression (carga para inferencia)
  gemini_client.py    # Lectura cualitativa textual (degradación elegante)
  signal_engine.py    # Reglas BUY/HOLD/SELL + SL/TP + recomendación IA
  backtest.py         # Simulación con fricción
scripts/
  train_sentiment.py  # Entrena el modelo de sentimiento (corre en CI)
  ingest.py           # ETL diario → Supabase (OHLCV, ARIMA, noticias)
  smoke.py            # Smoke test local del pipeline
  smoke_remote.py     # Smoke test contra el despliegue
public/               # Dashboard 3 vistas (estático servido por Vercel)
.github/workflows/ingest.yml  # Cron diario + entrenamiento + ETL + smoke
docs/arquitectura.html        # Diagrama de arquitectura (abrir en navegador)
```

## Arquitectura de datos

1. **GitHub Actions** (cron `0 22 * * *`, manual o push a `main`) reentrena el modelo de
   sentimiento y ejecuta el ETL: descarga OHLCV + noticias con `yfinance`, calcula
   indicadores, pronostica ARIMA 5 días y persiste todo en **Supabase**.
2. **Vercel** sirve la API (FastAPI) y el dashboard estático. La API lee de Supabase;
   cuando una serie no está disponible (ej. periodo corto recién cargado) hace *fallback*
   a `yfinance` en vivo e intenta persistir.
3. **Inferencia**: `signal_engine` combina la confluencia técnica, la recomendación de
   Gemini y el sentimiento de las noticias para emitir la señal final.

## Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -e .        # Windows
# .venv/bin/python -m pip install -e .          # Linux/macOS

.venv\Scripts\python -m uvicorn main:app --port 8000
# Abrir http://localhost:8000  (API docs en http://localhost:8000/docs)
```

Validación rápida del pipeline (usa red real si no hay `DATABASE_URL`):

```bash
.venv\Scripts\python scripts\smoke.py
```

## Variables de entorno

| Variable           | Requerida | Descripción                                                       |
|--------------------|-----------|---------------------------------------------------------------------|
| `DATABASE_URL`     | Sí        | Cadena `postgresql://` de **Supabase (Transaction pooler, puerto 6543)**. Sin ella, la app lee de `yfinance` en vivo y no persiste. |
| `GEMINI_API_KEY`   | No        | Key de Google AI Studio. Sin ella el sistema degrada a reglas cuantitativas. |
| `GEMINI_MODEL`     | No        | Modelo (default: `gemini-2.5-flash`)                             |

## Despliegue en la nube (pasos)

### 1. Supabase (base de datos)

1. Crea un proyecto en <https://supabase.com> (plan Free).
2. En *Project Settings → Database → Connection string* copia la cadena **Transaction pooler**
   (puerto `6543`), reemplazando `[YOUR-PASSWORD]`.
3. El esquema (`ohlcv`, `news`, `forecast_snapshots`, `inference_log`) se crea automáticamente
   la primera vez que corre el ETL (consulta `app/db.py::init_schema`).

### 2. GitHub (ETL + entrenamiento)

```bash
gh secret set DATABASE_URL          # misma cadena Supabase (transaction pooler)
gh variable set VERCEL_HOST         # ej: https://tu-proyecto.vercel.app (opcional)
```

El workflow `.github/workflows/ingest.yml` corre al hacer push a `main` (siembra inicial),
manualmente (`workflow_dispatch`) o con el cron diario. Reentrena el modelo de sentimiento y
puebla Supabase.

### 3. Vercel (API + dashboard)

```bash
npm i -g vercel
vercel
vercel env add DATABASE_URL
vercel env add GEMINI_API_KEY       # opcional
vercel --prod
```

También puede configurarse desde el panel *Project → Settings → Environment Variables* y luego *Redeploy*.

Verifica:
- Dashboard: `https://<tu-proyecto>.vercel.app/`
- API docs: `https://<tu-proyecto>.vercel.app/docs`
- Smoke test contra producción: `python scripts/smoke_remote.py --base https://<tu-proyecto>.vercel.app`

## Endpoints de la API

| Método | Ruta                          | Descripción                                        |
|--------|-------------------------------|----------------------------------------------------|
| GET    | `/api/health`                 | Estado, presencia de base de datos y modelo de sentimiento |
| GET    | `/api/indicators?ticker=&period=` | OHLCV + indicadores + series para gráficos       |
| GET    | `/api/forecast?ticker=&period=`  | Pronóstico ARIMA 5 ruedas (snapshot Supabase con fallback en vivo) |
| GET    | `/api/signal?ticker=&period=`    | Señal final + SL/TP + contexto + recomendación IA + narración |
| GET    | `/api/news?ticker=`           | Noticias clasificadas por el modelo de sentimiento |
| GET    | `/api/interpret?ticker=&period=` | Interpretación en lenguaje natural                |
| GET    | `/api/backtest?ticker=`       | Métricas de la simulación histórica + consejo     |
| GET    | `/api/refresh?tickers=SPY,AAPL,NVDA,MSFT` | Disparo manual del ETL (en local/Vercel) |
| GET    | `/api/screener?tickers=&period=` | Empresas del panel con señal BUY/HOLD/SELL        |

> El cron de refresco vino en `vercel.json`; se trasladó a GitHub Actions (job `ingest.yml`)
> para no depender del plan Hobby de Vercel.

## Alcance ético

Prototipo académico de investigación. Las señales son simulaciones cuantitativas de apoyo al
análisis humano; no constituye asesoría de inversión personalizada y no ejecuta órdenes con
dinero real.