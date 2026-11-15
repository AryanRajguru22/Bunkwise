# BunkWise - production image (no secrets, no database, no build tools needed at runtime).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8501

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py bunk_meter.py insights.py attendance_policy.py ./
COPY .streamlit ./.streamlit

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 bunkwise && chown -R bunkwise /app
USER bunkwise

EXPOSE 8501

# Streamlit's built-in liveness endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/_stcore/health' % os.environ.get('PORT', '8501'), timeout=4)"

# Hosts such as Render, Railway or Cloud Run inject $PORT; locally it defaults to 8501.
CMD ["sh", "-c", "exec streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501}"]
