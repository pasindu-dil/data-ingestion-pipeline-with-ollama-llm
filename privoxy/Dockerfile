FROM debian:bookworm-slim

# Use HTTP repositories initially to bootstrap CA certificates
RUN sed -i 's|https://deb.debian.org|http://deb.debian.org|g' \
    /etc/apt/sources.list.d/debian.sources

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        privoxy \
        curl && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Listen on all container interfaces
RUN sed -i \
    's/^listen-address.*/listen-address  0.0.0.0:8118/' \
    /etc/privoxy/config

EXPOSE 8118

CMD ["privoxy", "--no-daemon", "/etc/privoxy/config"]