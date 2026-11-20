FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends privoxy ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Allow other containers to connect to Privoxy
RUN sed -i \
    's/^listen-address.*/listen-address  0.0.0.0:8118/' \
    /etc/privoxy/config

EXPOSE 8118

CMD ["privoxy", "--no-daemon", "/etc/privoxy/config"]