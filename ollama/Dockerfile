FROM ollama/ollama:latest

# ARG MODELS="qwen2.5-coder:7b qwen2.5-coder:14b sqlcoder:7b"
ARG MODELS="qwen2.5-coder:14b"

RUN set -e; \
    ollama serve & pid=$!; \
    until ollama list >/dev/null 2>&1; do sleep 1; done; \
    for m in $MODELS; do ollama pull "$m"; done; \
    kill $pid; wait $pid || true