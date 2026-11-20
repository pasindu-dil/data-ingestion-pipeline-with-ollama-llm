FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        privoxy \
        curl && \
    rm -rf /var/lib/apt/lists/*

COPY config/config /etc/privoxy/config

EXPOSE 8118

CMD ["privoxy", "--no-daemon", "/etc/privoxy/config"]