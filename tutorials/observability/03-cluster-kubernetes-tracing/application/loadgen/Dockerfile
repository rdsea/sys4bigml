FROM debian:stable-slim

WORKDIR /client

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./image/ ./image/

COPY ./*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./entrypoint.sh ./

COPY ./load_test.py .

WORKDIR /client

ENV PATH="/client/.venv/bin:$PATH"

ENTRYPOINT ["./entrypoint.sh"]
CMD []

