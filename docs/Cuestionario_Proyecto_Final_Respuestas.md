# Cuestionario de Evaluación — Proyecto Final de Fundamentos de Business Analytics / BI (Inversiones)

> **Entregable del Equipo 7.** Este archivo debe ser **idéntico en los tres envíos** (cada integrante lo envía tal cual).
> Todo lo afirmado se respalda con enlaces al repositorio o al tablero público.
> Los campos marcados como `[[COMPLETAR]]` deben ser rellenados por el equipo (son datos que solo ustedes poseen) antes de enviar.
>
> **Regla de seguridad:** en este documento **no** se escribe ninguna clave, contraseña ni token; solo se nombran las **variables de entorno**.

---

## A. Datos del integrante y del equipo

| Campo | Respuesta |
| :---- | :---- |
| A1. Código y nombres completos del integrante | `[[COMPLETAR]]` — Isidro Avalos, Waldir Zosani · `[[COMPLETAR: código]]`<br>`[[COMPLETAR]]` — Alvitrez Daviran, Josmell Kevin · `[[COMPLETAR: código]]`<br>`[[COMPLETAR]]` — Ilares Llanos, Erick · `[[COMPLETAR: código]]` |
| A2. Número de equipo | **7** |
| A3. Integrantes y rol de cada uno | Ver roles en D3. Propuesta de roles: **Product Owner / Analista de negocio** (definición de reglas de Swing Trading y KPIs); **Data Engineer** (ETL, Supabase, GitHub Actions); **Data Scientist / ML Engineer** (indicadores, ARIMA, modelo de sentimiento, backtesting); **Desarrollador Backend/Frontend** (API FastAPI y tablero). `[[COMPLETAR: asignar un rol por nombre]]` |
| A4. Tema de inversión | **Swing Trading** (posiciones de 3 a 10 ruedas bursátiles) |
| A5. Nombre del proyecto / producto | **Swing Trading Consultor IA** — Sistema de Soporte a la Toma de Decisiones (DSS) |
| A6. URL pública del tablero en línea | `[[COMPLETAR]]` — por defecto `https://swing-trading-consultor-ia.vercel.app` (confirmar dominio real) |
| A7. URL del repositorio de GitHub | <https://github.com/KCIRE17/Swing_Trading_consultor_ia> |
| A8. URL del video demostrativo (3 a 5 minutos) | `[[COMPLETAR]]` |

Curso: **Analítica de Negocios** · Carrera: **Ingeniería de Sistemas** · Metodología: **TDSP (Microsoft)** · Presupuesto: **S/ 0.00**.

---

## B. Problema de negocio y usuario

**B1. Decisión de inversión y usuario.**
El sistema ayuda a decidir **si conviene abrir, mantener o cerrar una posición de swing trading** en un activo de alta liquidez, con nivel de entrada, Stop-Loss y Take-Profit sugeridos. El usuario es un **inversionista individual o analista novel/intermedio** (sin terminales profesionales tipo Bloomberg/Refinitiv), con **capital típico pequeño** y sin capacidad de monitorear el mercado todo el día. Hoy sufre **sobrecarga cognitiva**: debe cruzar gráficos técnicos con noticias dispersas, lo que genera fatiga decisional y sesgos emocionales.

**B2. Perfil de riesgo y horizonte.**
Atiende un perfil de **riesgo medio** y un horizonte de **corto plazo (3 a 10 ruedas bursátiles)**, coherente con la modalidad de swing trading. La gestión de riesgo es explícita mediante ATR (Stop-Loss y Take-Profit).

**B3. Preguntas de negocio por reporte (mínimo 2 cada uno).**
- **Descriptivo (¿qué pasó?):**
  1. ¿El precio del activo opera por encima o por debajo de sus medias de 20 y 50 días (tendencia)?
  2. ¿El activo está sobrecomprado o sobrevendido según el RSI y qué dice el volumen?
- **Predictivo (¿qué pasará?):**
  1. ¿Cuál es el precio proyectado del activo para las próximas 5 ruedas (ARIMA) y cuál es la dirección esperada (ALCISTA/NEUTRAL/BAJISTA) con su probabilidad?
  2. ¿Cuál es el tono predominante (POSITIVO/NEGATIVO/NEUTRAL) de las noticias recientes, clasificado por el modelo de Machine Learning del equipo?
- **Prescriptivo (¿qué hacer?):**
  1. ¿Cuál es la acción recomendada (BUY/HOLD/SELL) y en qué nivel de entrada, Stop-Loss y Take-Profit?
  2. ¿La recomendación es coherente con la predicción y los indicadores (confluencia), y qué riesgos/salvedades se advierten?

**B4. Indicadores de éxito del proyecto.**
- **Rentabilidad simulada** de la estrategia frente a la línea base **Buy & Hold** (retorno total % y exceso de retorno) en el backtesting.
- **Caída máxima (Maximum Drawdown %)** y **Sharpe Ratio** de la estrategia.
- **Tasa de acierto (Win Rate)** de las operaciones simuladas (meta > 55%).
- **Desempeño del modelo de Machine Learning** (Accuracy y F1-macro del clasificador de sentimiento) por encima de la **clase mayoritaria** (línea base ingenua).

**B5. Objetivo general y objetivos específicos.**
- **General:** Diseñar e implementar un DSS desplegado en línea que apoye decisiones de swing trading combinando análisis descriptivo, predicción con Machine Learning/econometría y recomendación con la API de un LLM, a costo cero.
- **Específicos (3):**
  1. Construir un pipeline ETL automatizado (GitHub Actions → Supabase) que ingiera OHLCV y noticias y las mantenga actualizadas.
  2. Entrenar y servir un modelo de Machine Learning de análisis de sentimiento de noticias y una línea base econométrica ARIMA a 5 ruedas.
  3. Publicar un tablero web interactivo de 3 reportes (descriptivo, predictivo y prescriptivo) con señales BUY/HOLD/SELL y gestión de riesgo ATR.

---

## C. Datos, calidad y las 3V

**C1. Tabla de fuentes de datos.**

| Fuente (nombre y enlace) | Tipo | Variables o campos | Frecuencia de actualización | Límite o costo de la API | Licencia / permiso de uso |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Yahoo Finance** vía `yfinance` (<https://pypi.org/project/yfinance/>) | Estructurado (serie tabular) | OHLCV: `Open, High, Low, Close, Volume` (precios ajustados con `auto_adjust=True`) | Diaria (al cierre de mercado); en cada corrida del ETL | Gratuito, sin clave; uso no oficial, con límite de *rate-limit* (mitigado con caché TTL 1 h y reintentos) | Datos de uso académico/personal; `yfinance` es código abierto (Apache-2.0) |
| **Noticias financieras** (cabeceras enlazadas de Yahoo/medios) vía `yfinance.Ticker.news` | No estructurado (texto) | `title, url, publisher, pubDate` (+ clasificación `sentimiento`, `prob_pos/neu/neg`) | Diaria (hasta 25 titulares por ticker en cada corrida) | Gratuito, misma fuente que yfinance | Titulares con enlace a la fuente original |
| **Corpus de sentimiento financiero multilingüe** `Kenpache/multilingual-financial-sentiment` (<https://huggingface.co/datasets/Kenpache/multilingual-financial-sentiment>) | No estructurado (texto etiquetado) | `text`, `sentiment` (POS/NEU/NEG) | Fija (dataset de entrenamiento, se descarga en cada entrenamiento del CI) | Gratuito (Hugging Face Hub) | Dataset público (uso académico) |

**C2. Cumplimiento de las 3V (cifras reales).**
- **Volumen:** por corrida del ETL se almacenan **≈ 250 velas OHLCV por ticker** (histórico de 1 año) para **3 tickers** → **≈ 750 registros OHLCV** con 13 columnas cada uno, más **hasta 25 noticias × 3 tickers = hasta 75 noticias** (con sus 3 probabilidades de sentimiento) y **3 snapshots de pronóstico ARIMA** por día. El modelo de sentimiento se entrena sobre **12 831 titulares** (`models/sentiment_meta.json`: `n_total = 12831`).
- **Velocidad:** los datos se **actualizan a diario** con el cron de GitHub Actions (`0 23 * * *` = **18:00 h hora de Perú**), alineado con el cierre del mercado; también bajo demanda (`workflow_dispatch`, `push` a `main` y el botón "Analizar" del tablero, que recarga en vivo si la serie no está fresca).
- **Variedad:** conviven en el mismo flujo (a) **datos estructurados numéricos** (OHLCV continuo), (b) **datos no estructurados de texto** (titulares de noticias, convertidos a variable `sentimiento ∈ {POS,NEU,NEG}`), y (c) **salida estructurada JSON** del LLM. *(Nota de evolución: la versión previa de la propuesta planteaba imágenes de prensa; el MVP desplegado usa noticias en texto como dato no estructurado y el LLM en modo solo-texto.)*

**C3. Proceso ETL (`scripts/ingest.py`).**
- **Extracción:** `yfinance` descarga OHLCV (`history(period="1y", auto_adjust=True)`) y las noticias del ticker. El OHLCV ya viene **ajustado por splits y dividendos** gracias a `auto_adjust=True` (no se hace ajuste manual).
- **Limpieza:** se validan las columnas OHLCV, se **neutraliza la zona horaria** (`tz_localize(None)`), se **eliminan filas con `Close` nulo** y se recorta la longitud según el periodo solicitado (`PERIOD_LOOKBACK`).
- **Valores atípicos:** no se descartan velas extremas (serían movimientos reales de mercado); en el frontend el histograma de retornos **excluye |r| ≥ 15 %** solo para el gráfico de distribución.
- **Duplicados:** se evitan a nivel de base de datos con **clave primaria `(ticker, date)`** y **`UNIQUE (ticker, url)`** para noticias; los inserts usan `ON CONFLICT ... DO UPDATE` (upsert), por lo que reprocesar no duplica.
- **Transformación:** se calculan los indicadores (SMA20/50, RSI14, MACD, ATR14) con `app/indicators.py::augment`, se estima ARIMA a 5 ruedas y se clasifica el sentimiento de cada titular con el modelo de ML.

**C4. Almacenamiento y actualización automática.**
Los datos se almacenan en **Supabase (PostgreSQL)** en las tablas `ohlcv`, `news`, `forecast_snapshots` e `inference_log` (esquema definido en `app/db.py::init_schema`). La actualización es **automática** mediante el workflow de **GitHub Actions** (`.github/workflows/ingest.yml`): reentrena el modelo de sentimiento, corre el ETL, **verifica con `SELECT MAX(date)`** que cada ticker tenga datos frescos (≤ 4 días) y falla el job si no es así.

**C5. Calidad de datos.**
Validaciones aplicadas: (1) columnas OHLCV obligatorias presentes; (2) descarte de filas con `Close` nulo; (3) unicidad por `(ticker, date)` / `(ticker, url)`; (4) verificación de frescura por ticker en el CI; (5) en la API, si la serie de Supabase **no está fresca** (última vela > `FRESH_DAYS = 10` días) se hace *fallback* a Yahoo en vivo. **Porcentaje descartado:** `[[COMPLETAR: pegar el % de filas con Close nulo descartadas en la última corrida]]` (habitualmente muy bajo, al ser índices de alta liquidez).

**C6. Conversión de datos no estructurados.**
Las noticias (texto libre) se convierten en una **variable utilizable** mediante un clasificador de **Machine Learning**: TF-IDF + Regresión Logística (ver F). Cada titular obtiene una etiqueta `sentimiento ∈ {POS, NEU, NEG}` y tres probabilidades. Esa variable se **agrega** por ticker (`counts` POS/NEU/NEG) y alimenta la **decisión predictiva** y el **factor noticias** de la señal operativa (`app/signal_engine.py::_news_factor`).

---

## D. Metodología y gestión

**D1. Metodología aplicada (TDSP — Team Data Science Process, Microsoft).**
- **Fase 1 · Comprensión del negocio:** se definieron reglas de swing trading (3–10 ruedas), vocabulario de decisión (INVERTIR/MANTENER/RETIRAR y BUY/HOLD/SELL), gestión de riesgo (ATR) y KPIs.
- **Fase 2 · Adquisición y comprensión de datos:** ingesta de OHLCV (1 año) y noticias con `yfinance`; corpus de sentimiento desde Hugging Face; análisis de calidad y frescura.
- **Fase 3 · Modelado:** ingeniería de variables técnicas; línea base econométrica ARIMA(p,d,q) con ADF + AIC; entrenamiento del modelo de ML de sentimiento; integración del LLM (Gemini) para la capa prescriptiva.
- **Fase 4 · Despliegue:** motor de señales con SL/TP; backtesting 70/30; API FastAPI; tablero web de 3 vistas; publicación en Vercel y automatización del ETL en GitHub Actions.
- **Fase 5 · Aceptación:** validación de métricas (Win Rate, Drawdown, Sharpe, retorno vs Buy & Hold) y del desempeño del clasificador; verificación en línea del tablero.

**D2. Cronograma real (semanas 4 a 14).** `[[COMPLETAR: marcar semanas exactas y estado entregado/pendiente. Esqueleto sugerido:]]`
- Semanas 4–6: ingesta OHLCV + noticias, modelo de datos en Supabase. *(entregado)*
- Semanas 7–10: indicadores, ARIMA, modelo de sentimiento ML, motor de señales. *(entregado)*
- Semanas 11–13: backtesting, API FastAPI, tablero de 3 vistas. *(entregado)*
- Semana 14: despliegue en Vercel + GitHub Actions, pruebas y ajustes. *(entregado)*

**D3. Aportes por integrante.** `[[COMPLETAR: enlazar commits/PRs por persona. Guía sugerida de reparto:]]`
- **Isidro Avalos, Waldir Zosani:** `[[COMPLETAR: p. ej. frontend/tablero, narrativa, documentación]]`
- **Alvitrez Daviran, Josmell Kevin:** `[[COMPLETAR: p. ej. ETL, Supabase, GitHub Actions]]`
- **Ilares Llanos, Erick:** `[[COMPLETAR: p. ej. modelos (ARIMA, ML de sentimiento), backtesting, API]]`
- Enlace al historial: <https://github.com/KCIRE17/Swing_Trading_consultor_ia/commits/main>

---

## E. Reporte DESCRIPTIVO (¿qué pasó?)

**E1. KPIs del reporte (≥ 6, con fórmula y pregunta de negocio).**

| KPI | Fórmula | Pregunta de negocio que responde |
| :---- | :---- | :---- |
| Precio de cierre y variación diaria | `change_pct = (close_t / close_{t-1} − 1) × 100` | ¿Cuánto y en qué dirección se movió el activo hoy? |
| Tendencia (SMA20 / SMA50) | Media móvil simple de los últimos 20 / 50 cierres; comparación `close > SMA` | ¿La tendencia de corto y mediano plazo es alcista o bajista? |
| RSI (14) | `RSI = 100 − 100/(1+RS)`, `RS = avg_gain/avg_loss` (suavizado de Wilder, α=1/14) | ¿El activo está sobrecomprado (≥70) o sobrevendido (≤30)? |
| MACD (12,26,9) e histograma | `MACD = EMA12 − EMA26`; `señal = EMA9(MACD)`; `hist = MACD − señal` | ¿El momentum se está acelerando o agotando? |
| ATR (14) | Media EWMA (α=1/14) del rango verdadero | ¿Cuánta volatilidad diaria tiene el activo (para dimensionar riesgo)? |
| Volumen | Volumen negociado de la rueda (y variación vs promedio) | ¿El movimiento está respaldado por liquidez? |
| Retorno diario (histograma) | `r_t = (close_t/close_{t-1} − 1)` agrupado en buckets de 1 % | ¿Cómo se distribuyen los retornos y qué tan riesgoso es el activo? |

**E2. Visualizaciones y por qué son adecuadas.**
Series de tiempo (velas japonesas OHLCV) para ver la evolución del precio; **SMA20/SMA50** superpuestas para tendencia; bandas **±1·ATR** para volatilidad; oscilador **RSI** con zonas 30/70; **histograma MACD** (barras por signo) para momentum; **volumen** para confirmación; **histograma de retornos** para distribución de riesgo; **tablero (screener) de 3 activos** con color por variación y borde por señal para comparación rápida.

**E3. Filtros e interacción.** Selector de **activo** (NVDA, AAPL, MSFT), selector de **periodicidad** (3mo, 6mo, 1y), pestañas de **vista** (Descriptiva / Predictiva / Prescriptiva), botón **"Analizar"** que refresca en vivo, y en la vista prescriptiva un **slider de capital** para el dimensionamiento de posición (riesgo 1 %). El perfil de riesgo se refleja en el nivel de riesgo y en los umbrales de la señal.

**E4. Herramienta y publicación en línea.**
Herramienta: **tablero web propio** (HTML + Vanilla JS + **Chart.js 4.x** por CDN) servido como sitio estático, con **API FastAPI** como backend. Publicación: desplegado en **Vercel (plan free)**; el docente lo abre desde la **URL pública** (A6) **sin instalar nada**. La API es serverless y el dashboard estático se sirve en `/`.

**E5. Frecuencia de actualización y origen de datos.**
El tablero se actualiza **a diario** (ETL en GitHub Actions a las 23:00 UTC = 18:00 h Perú) desde **Supabase (PostgreSQL)**; si la serie no está fresca (≤ 10 días) o no hay base, la API **recarga en vivo desde Yahoo Finance**. La interfaz indica el origen en el campo `proveedor`.

**E6. Tres hallazgos de negocio.** `[[COMPLETAR: pegar capturas de la URL pública. Guía:]]`
1. **`[[COMPLETAR: captura]]`** — p. ej., NVDA opera por encima de SMA20/SMA50 con RSI en zona saludable → estructura alcista de mediano plazo.
2. **`[[COMPLETAR: captura]]`** — p. ej., divergencia entre la proyección ARIMA y el sentimiento de noticias en alguno de los activos → señal de cautela.
3. **`[[COMPLETAR: captura]]`** — p. ej., el backtesting muestra si la estrategia supera o no a Buy & Hold y con qué drawdown.

---

## F. Reporte PREDICTIVO (¿qué pasará?) con Machine Learning

> **Honestidad metodológica (importante):** el proyecto tiene **dos motores de predicción**: (1) un **modelo de Machine Learning entrenado por el equipo** que clasifica el **sentimiento de las noticias** y alimenta la decisión predictiva; y (2) la **línea base econométrica ARIMA** que proyecta el **precio** numérico a 5 ruedas. La dirección del precio se refuerza con la lectura cualitativa del LLM (capa G). No ocultamos esta composición.

**F1. Variable objetivo y horizonte.**
- **ML del equipo:** clasificar cada titular en **`sentimiento ∈ {POS, NEU, NEG}`** (variable categórica de 3 clases).
- **Proyección de precio (línea base ARIMA):** el **cierre** del activo a **5 ruedas bursátiles** de horizonte; la dirección esperada se reporta como **ALCISTA / NEUTRAL / BAJISTA**.

**F2. Variables predictoras (features) e indicadores.**
Para el modelo de ML: **TF-IDF** del texto del titular (`ngram_range=(1,2)`, `max_features=20000`, `sublinear_tf=True`). Para el análisis de precio (descriptivo/predictivo): **SMA20, SMA50, RSI14, MACD (línea, señal, histograma), ATR14** más el cierre y el volumen, construidos en `app/indicators.py`.

**F3. Modelo(s) de ML y justificación.**
**Pipeline: `TfidfVectorizer` + `LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000)`** (ver `scripts/train_sentiment.py`). Se eligió por ser **robusto, rápido, interpretable y de bajo costo** para clasificación de texto breve, entrenable **a diario en CI** sin GPU. Código de entrenamiento: [`scripts/train_sentiment.py`](https://github.com/KCIRE17/Swing_Trading_consultor_ia/blob/main/scripts/train_sentiment.py). La línea base econométrica es **ARIMA(p,d,q)** seleccionada por **AIC** tras la prueba **ADF** ([`app/arima_benchmark.py`](https://github.com/KCIRE17/Swing_Trading_consultor_ia/blob/main/app/arima_benchmark.py)).

**F4. Estrategia de validación y prevención de fuga.**
- **ML de sentimiento:** **split estratificado 80/20** (`random_state=7`) sobre el corpus; el 20 % (`n_test = 2567`) no se usa en entrenamiento. Se deduplican textos y se balancean clases (`CLASS_CAP = 6000`) para evitar sesgo.
- **Estrategia de trading (backtesting):** **partición cronológica estricta 70/30** (`TRAIN_RATIO = 0.70`): la estrategia se calibra con el 70 % inicial y **solo se evalúa en el 30 % final** (fuera de muestra), sin observar el futuro → sin *data leakage*.

**F5. Tabla de métricas (datos no vistos en entrenamiento).**

| Métrica | Modelo del equipo | Línea base |
| :---- | :---- | :---- |
| Exactitud (accuracy) | **0.6642** (clasificador de sentimiento, test 2567) | Clase mayoritaria (NEU: 1200/2567 ≈ **0.467**) |
| Precisión / sensibilidad (recall) | Macro **0.6533 / 0.6664** (por clase: NEG 0.59/0.65, NEU 0.75/0.65, POS 0.62/0.69) | Mayoritaria: precisión ≈ 0.47 |
| F1 / AUC-ROC | **F1-macro 0.6577** | ≈ 0.47 |
| Error (MAE / RMSE) | No aplica (clasificación). Para el precio: `[[COMPLETAR: MAE/RMSE de ARIMA vs cierre real, si se calculó]]` | — |
| Retorno simulado (con comisiones 0.1 %) | `[[COMPLETAR: pegar del dashboard el retorno % de la estrategia vs Buy & Hold]]` | Buy & Hold: `[[COMPLETAR]]` |
| Caída máxima (max drawdown) | `[[COMPLETAR: pegar del dashboard]]` | `[[COMPLETAR]]` |

**F6. ¿Supera la línea base?**
**Sí**, el clasificador de sentimiento (0.6642) **supera a la clase mayoritaria** (~0.467). El backtesting reporta Win Rate, retorno y drawdown frente a **Buy & Hold**; en la interfaz se muestra el **exceso de retorno** respecto a Buy & Hold y si la dirección del pronóstico ARIMA coincidió con el movimiento real. `[[COMPLETAR: indicar si la estrategia superó a Buy & Hold en el último backtest y comentar el resultado, aunque sea modesto]]`.

**F7. Servicio del modelo.**
El modelo de sentimiento se guarda como artefacto (`models/sentiment_model.joblib`) y se **sirve en línea a través de la API FastAPI**; el clasificador se carga de forma perezosa en `app/sentiment.py`. El pronóstico ARIMA se sirve vía `/api/forecast` (snapshot en Supabase o cálculo en vivo). En el tablero, el resultado se ve en los **KPIs de la vista Predictiva** (pronóstico 5 ruedas, dirección y probabilidad, nivel de riesgo, y sentimiento de noticias).

**F8. Limitaciones, reentrenamiento y monitoreo.**
Limitaciones: datos de **una sola fuente** (Yahoo), horizonte corto, mercado ruidoso, y un clasificador de sentimiento con desempeño **moderado** (F1 ≈ 0.66) sensible a textos financieros ambiguos. **Reentrenamiento:** el modelo de sentimiento se **reentrena en cada corrida del ETL** (diario) en CI. **Detección de degradación:** las métricas (accuracy/F1) se registran en `models/sentiment_meta.json` en cada entrenamiento; la verificación de frescura y el smoke remoto del workflow detectan fallos de pipeline. `[[COMPLETAR: describir si hay umbral mínimo de métricas para alertar]]`.

---

## G. Reporte PRESCRIPTIVO (¿qué hacer?) con LLM por API

**G1. Modelo, proveedor y por qué.**
**Google Gemini** (`gemini-2.5-flash`) del proveedor **Google AI Studio**, consumido vía `google-genai` con una **API Key gratuita**. Se eligió por: **capa gratuita** para desarrolladores/estudiantes (costo S/ 0.00), **baja latencia**, soporte de **salida JSON forzada** (`response_mime_type="application/json"`) y calidad del razonamiento en español. **Variable de entorno de la clave:** `GEMINI_API_KEY` (y `GEMINI_MODEL` / `GEMINI_NARRATIVE_MODEL` para el modelo). **La clave no se escribe aquí ni en el repositorio.**

**G2. Entradas del LLM (ejemplo real).** El LLM recibe el contexto técnico-económico del activo como **texto** (construido en `app/gemini_client.py::_build_text_part`):

```text
Contexto del analisis tecnico y econometrico del activo:
- Ticker: NVDA
- Fecha del ultimo cierre: 2026-10-09
- Precio de cierre: 182.14
- Variacion diaria: 1.23%
- SMA20: 178.5
- SMA50: 170.2
- RSI14: 58.4
- MACD: 2.1 (senal 1.4, histograma 0.7)
- ATR14: 5.6
- Pronostico ARIMA 5 ruedas: [183.1, 184.0, 184.8, 185.6, 186.3]
- Precio proyectado por ARIMA: 186.3
```

Además se le pasa el **resumen de sentimiento de noticias** (POS/NEU/NEG). *(Los valores numéricos exactos se toman de la respuesta real de `/api/signal`.)*

**G3. Prompt de sistema completo.** (Texto exacto de `app/gemini_client.py`.)

```text
Eres un analista senior de inversiones especializado en Swing Trading (posiciones de 3 a 10 ruedas bursatiles). Recibes el estado tecnico cuantitativo de un activo (precio, medias moviles SMA20/SMA50, RSI14, MACD, ATR14) y el pronostico econometrico ARIMA a 5 dias. Debes responder SOLO en JSON valido sin texto adicional, con la siguiente estructura exacta: {"prediccion": "ALCISTA"|"NEUTRAL"|"BAJISTA", "probabilidad": numero entre 0.0 y 1.0, "nivel_riesgo": "BAJO"|"MEDIO"|"ALTO", "recomendacion": "RETIRAR"|"AUMENTAR"|"MANTENER", "conclusion_cualitativa": "2 a 3 oraciones con tu lectura laica del contexto", "justificacion_tecnica": "explica en 2 a 3 oraciones la confluencia entre indicadores tecnicos y el pronostico ARIMA"} Reglas: 'AUMENTAR' solo cuando indicadores y ARIMA coinciden con alta conviccion; 'RETIRAR' cuando varios indicadores contradicen la posicion; 'MANTENER' en condiciones ambiguas o de espera.
```

Diseño y pruebas: el prompt se redactó para **forzar JSON válido** y **acotar el vocabulario** (enumeraciones cerradas), y se validó con el smoke test (`scripts/smoke.py`) verificando el **esquema** de la respuesta y el **comportamiento degradado** sin clave (prediccion=NEUTRAL, probabilidad=0.5, recomendacion=MANTENER).

**G4. Salida estructurada y validación del formato.** El LLM devuelve (`app/gemini_client.py::analyze`):

```json
{
  "prediccion": "ALCISTA|NEUTRAL|BAJISTA",
  "probabilidad": 0.0,
  "nivel_riesgo": "BAJO|MEDIO|ALTO",
  "recomendacion": "RETIRAR|AUMENTAR|MANTENER",
  "conclusion_cualitativa": "2 a 3 oraciones",
  "justificacion_tecnica": "2 a 3 oraciones"
}
```

**Validación** (`_is_valid`): es un `dict` con `prediccion ∈ {ALCISTA,NEUTRAL,BAJISTA}`, `recomendacion ∈ {RETIRAR,AUMENTAR,MANTENER}` y `probabilidad` numérica. Si falla la llamada o el esquema, se usa un **payload degradado** (`fuente="degradado"`).

**G5. Reglas fijas vs LLM.**
- **Reglas fijas (deterministas):** el **mapeo** `AUMENTAR→BUY`, `RETIRAR→SELL`, `MANTENER→HOLD`; el cálculo de **Stop-Loss = cierre − 1.5·ATR** y **Take-Profit = cierre + 3.0·ATR** (R:B = 2.0); la **confluencia para BUY** (precio > SMA50, RSI ≤ 65, probabilidad ≥ 0.65); el **factor noticias** y el **tamaño de posición** (riesgo 1 % del capital sobre la distancia al SL). `app/signal_engine.py`.
- **LLM:** la **lectura cualitativa** (predicción, probabilidad, nivel de riesgo, recomendación y su justificación). Se separa así porque **el dinero y el riesgo no se delegan a un modelo probabilístico de texto**: las reglas garantizan límites auditables y el LLM aporta el contexto explicable.

**G6. Coherencia y anti-alucinación.**
- El LLM **no calcula cifras**: recibe los números ya calculados (SMA, RSI, MACD, ATR, pronóstico ARIMA) y solo los interpreta en texto; los **niveles de SL/TP se recalculan con reglas fijas**, nunca con la salida del LLM.
- La salida se **valida contra un esquema cerrado** (`_is_valid`); si no lo cumple, se **degrada** y la señal operativa se mantiene coherente (HOLD con contexto técnico).
- La **decisión predictiva** combina explícitamente ARIMA + IA + noticias con pesos fijos, y el **checklist de confluencia** de 5 ítems del tablero permite verificar visualmente si la recomendación empata con los datos.

**G7. Tres casos reales.** `[[COMPLETAR: pegar 3 ejemplos reales de /api/signal (entrada + recomendación del LLM + análisis crítico)]. Esqueleto:]]`
1. `[[COMPLETAR: ticker/fecha, entrada resumida, salida JSON, ¿era razonable?]]`
2. `[[COMPLETAR]]`
3. `[[COMPLETAR]]`

**G8. Medidas de protección.**
- **Aviso de no asesoría:** el tablero y el repositorio declaran que es un **prototipo académico** y que nada constituye asesoría financiera personalizada ni ejecuta órdenes reales.
- **Límite de uso del LLM:** una llamada por análisis (prompt acotado con `TIMEOUT_SECONDS = 20`); la salida es un JSON pequeño → control de tokens. `[[COMPLETAR: confirmar si se aplicó algún tope diario de llamadas]]`
- **Tratamiento de errores:** todo fallo de red/API o esquema inválido se captura y **degrada con elegancia** (sin romper la app).
- **Registro:** la tabla `inference_log` existe en el esquema para registrar cada recomendación (`ticker, fecha, prediccion, probabilidad, nivel_riesgo, fuente`). `[[COMPLETAR: aclarar si hoy se puebla; en el esquema está definida]]`

**G9. Costo estimado por 100 recomendaciones.**
Con la **capa gratuita de Google AI Studio** para `gemini-2.5-flash`, el costo es **S/ 0.00** dentro de las cuotas gratuitas (100 recomendaciones = 100 llamadas cortas de ~pocos cientos de tokens). `[[COMPLETAR: si se desea un estimado pagado, usar el pricing oficial de Gemini Flash y multiplicar por los tokens de entrada/salida]]`.

---

## H. Integración de punta a punta y despliegue en línea

**H1. Diagrama de arquitectura.**
Adjunto en el repositorio: [`docs/arquitectura.html`](https://github.com/KCIRE17/Swing_Trading_consultor_ia/blob/main/docs/arquitectura.html) (abrir en navegador). Flujo: **Yahoo Finance (datos) → GitHub Actions (ETL + entrenamiento ML) → Supabase Postgres (almacén) → API FastAPI + modelos ML/ARIMA (Vercel) → Gemini (LLM) → Tablero web de 3 vistas (Vercel)**.

**H2. Flujo al abrir el tablero.**
1. El navegador carga el sitio estático (Vercel). 2. Al pulsar **"Analizar"**, el frontend dispara en paralelo `/api/indicators`, `/api/screener`, `/api/signal`, `/api/forecast`, `/api/news` y `/api/backtest`. 3. La API lee de **Supabase**; si la serie no está fresca, descarga de **Yahoo** en vivo y persiste. 4. `signal_engine` combina confluencia técnica + recomendación de Gemini + sentimiento de noticias → señal BUY/HOLD/SELL. 5. El tablero renderiza las 3 vistas.
**Si falla un componente:** sin `DATABASE_URL` la app usa Yahoo en vivo; sin `GEMINI_API_KEY` degrada a reglas cuantitativas (HOLD coherente); un error de endpoint responde **HTTP 502** con `{error, mensaje}` sin romper el tablero.

**H3. Dónde está desplegado cada componente.**

| Componente | Servicio | Actualización |
| :---- | :---- | :---- |
| Datos (OHLCV, noticias, snapshots) | **Supabase Postgres** (free) | ETL diario |
| ETL + entrenamiento ML | **GitHub Actions** (`ingest.yml`) | cron `0 23 * * *` + manual + push a `main` |
| API + modelos (ML/ARIMA/reglas) | **Vercel** (FastAPI serverless) | en cada deploy |
| LLM | **Google AI Studio (Gemini)** | por llamada |
| Tablero | **Vercel** (estático) | en cada deploy |

**H4. Tipo de proyecto.** ☐ Web estática ☑ **Aplicación web con IA** ☐ Proceso en segundo plano ☐ Otro.
*(Incluye además un proceso en segundo plano: el ETL diario de GitHub Actions.)*

**H5. Dockerfile, `.env.example` y README.** **Sí.** `Dockerfile` (imagen de 2 etapas), `.env.example` (plantilla de variables) y `README.md` (pasos de reproducción y despliegue) están en la raíz del repositorio.

**H6. Variables de entorno (solo nombres).**
`DATABASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_NARRATIVE_MODEL`, `SENTIMENT_MODEL_DIR`, `VERCEL_HOST` (variable de GitHub Actions), `VERCEL` (la define Vercel automáticamente).

**H7. Acceso para el docente.** `[[COMPLETAR: URL pública o usuario de prueba. Sin contraseñas reales de integrantes; el tablero es de acceso abierto, no requiere login.]]`

**H8. Tiempos en línea.** `[[COMPLETAR: medir y pegar. Guía:]]`
- Carga del tablero: `[[COMPLETAR]]` s.
- Respuesta de `/api/indicators`: `[[COMPLETAR]]` s.
- Recomendación (`/api/signal`, incluye LLM): `[[COMPLETAR]]` s.

---

## I. Riesgos, ética y cumplimiento

**I1. Límites de las APIs (plan gratuito).**
- **Yahoo (yfinance):** sin clave, pero con **rate-limit**; se mitiga con **caché TTL 1 h**, reintentos y persistencia en Supabase.
- **Gemini (Google AI Studio):** **cuotas gratuitas** de peticiones/minuto y por día; si se excede, la app **degrada** a reglas cuantitativas (no falla).
- **Supabase (free):** límite de almacenamiento y **pausa del proyecto tras 7 días sin actividad** → el **cron diario lo mantiene activo**.
- **Vercel (free):** funciones serverless con límite de tiempo de ejecución → por eso el ETL se movió a GitHub Actions (y `vercel.json` quedó con `crons: []`).

**I2. Riesgos del sistema y comunicación al usuario.**
Riesgos: (1) **resultados pasados no garantizan resultados futuros**; (2) **sesgos/limitaciones del modelo** (F1 ≈ 0.66) y de una sola fuente de datos; (3) **dependencia del LLM** (puede degradarse o alucinar texto). Comunicación: avisos visibles en el tablero y en el README de que es un **prototipo académico de investigación**, no asesoría financiera, y que las señales son **simulaciones de apoyo al juicio humano**.

**I3. Prevención de decisiones imprudentes.**
El sistema **no incluye apalancamiento**, **no opera penny stocks ni cripto**, y se restringe a **3 acciones de alta liquidez** (NVDA, AAPL, MSFT). **No ejecuta órdenes reales** ni se conecta a brokers; solo sugiere BUY/HOLD/SELL con **Stop-Loss obligatorio** y **tamaño de posición con riesgo máximo del 1 %** del capital.

---

## J. Pruebas y evidencias

**J1. Matriz de pruebas (≥ 6 casos, cubre los 3 reportes).** Ejecutada por `scripts/smoke.py` (**34/34 PASS** en la última corrida local).

| # | Caso | Reporte | Resultado esperado | Verificación |
| :-- | :---- | :-- | :---- | :---- |
| 1 | `advisor.advise_rsi(78)` → "No invertir" | Descriptivo | Regla de sobrecompra | `smoke.py` PASS |
| 2 | `/api/indicators` devuelve `series` e `asesoria {precio,rsi,macd}` | Descriptivo | 200 + series | `smoke.py` PASS |
| 3 | ARIMA: `forecast` no vacío y `next_close` definido (NVDA/AAPL/MSFT) | Predictivo | Pronóstico 5 ruedas | `smoke.py` PASS |
| 4 | Sentimiento ML clasifica POS/NEG | Predictivo | Etiquetas correctas | `smoke.py` PASS |
| 5 | Degradación sin `GEMINI_API_KEY` → NEUTRAL/0.5/MANTENER y señal HOLD | Prescriptivo | Degradación elegante | `smoke.py` PASS |
| 6 | `/api/signal` devuelve `senal.direccion ∈ {BUY,HOLD,SELL}` + narración + nombre | Prescriptivo | 200 + campos | `smoke.py` PASS |
| 7 | `/api/forecast` con `fuente ∈ {supabase, en_vivo}` y `asesoria` | Predictivo | 200 | `smoke.py` PASS |
| 8 | `/api/screener` con 2 empresas, `nombre` y `senal` | Descriptivo | 200 | `smoke.py` PASS |
| 9 | Round-trip Supabase (upsert/read OHLCV y forecast) | Integración | Datos persisten | `smoke.py` PASS |

**J2. Capturas del tablero en la URL pública.** `[[COMPLETAR: 3 capturas — Descriptiva, Predictiva, Prescriptiva (URL de A6).]]`

**J3. Un error encontrado y cómo se corrigió.**
Durante el ETL, el upsert a Supabase fallaba con **`_row() takes 2 positional arguments but 3 were given`** en `app/db.py`, y `main()` **tragaba la excepción** saliendo con código 0 (falso verde). Se corrigió: (1) se ajustó la llamada `_row(ticker, r)` (parámetro sobrante); (2) `executemany` se ejecutó a través de `conn.cursor()` (psycopg 3 no lo expone en `Connection`); (3) se agregó `prepare_threshold=None` para evitar choques de *prepared statements* con el **pooler** de Supabase. Además, el ETL ahora **falla ruidosamente** si ningún ticker persiste (`scripts/ingest.py`), y el workflow verifica la frescura con `SELECT MAX(date)`.

**J4. Enlaces para reproducir resultados.** `[[COMPLETAR: si se agregan notebooks]]`
- Entrenamiento del modelo ML: <https://github.com/KCIRE17/Swing_Trading_consultor_ia/blob/main/scripts/train_sentiment.py>
- ETL: <https://github.com/KCIRE17/Swing_Trading_consultor_ia/blob/main/scripts/ingest.py>
- Pruebas: <https://github.com/KCIRE17/Swing_Trading_consultor_ia/blob/main/scripts/smoke.py>
- API: <https://github.com/KCIRE17/Swing_Trading_consultor_ia/blob/main/main.py>
- Indicadores / ARIMA / señales / backtest: carpeta [`app/`](https://github.com/KCIRE17/Swing_Trading_consultor_ia/tree/main/app)

---

## K. Declaración final

- [ ] **K1.** Declaro que mis respuestas coinciden con las de mi equipo y que el proyecto está **en línea y funcionando** en la URL indicada.
- [ ] **K2.** Declaro que no incluí claves, contraseñas ni datos personales reales en el repositorio.
- [ ] **K3.** Declaro que el modelo de Machine Learning fue entrenado por nuestro equipo y que el reporte prescriptivo llama realmente a la API de un LLM.
- [ ] **K4.** Puedo explicar en una sustentación oral el funcionamiento de los tres reportes.

> *El proyecto es académico. Ninguna recomendación del sistema constituye asesoría financiera personalizada y nunca ejecuta operaciones reales de compra o venta.*
