FROM python:3.13-alpine3.23


#TODO: update uv to a later version (or redo the entire container to use uv only and not python as uv can handle installing python itself)
RUN mkdir -p /app/cogs && mkdir /app/.venv && apk add --no-cache sqlite=~3.51 && apk add --no-cache uv=~0.10

WORKDIR /app

RUN addgroup -S appuser && adduser -S -G appuser appuser


# Kubernetes (and by extension OKD) won't read python standardout if python's
# buffer is allowed to do stuff. Here we turn it off
ENV PYTHONUNBUFFERED=1

# Disable development dependencies
ENV UV_NO_DEV=1

# Disable UV cache since it'll be re-build on startup anyway
ENV UV_NO_CACHE=1

# Compile everything to bytecode
ENV UV_COMPILE_BYTECODE=1

LABEL se.dsek.volumes.mountpoint="/app/db/"
LABEL se.dsek.volumes.description="Mount folder with runtime database here."
LABEL se.dsek.env.required="TOKEN"
LABEL se.dsek.env.sqlite="DB_FILE"
LABEL se.dsek.env.token.description="Discord bot token"
LABEL se.dsek.env.sqlite.db_file.description="Database file search path (sane default is db/db.sqlite, if you change this also change mount path"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY ./*.py ./
COPY ./cogs/*.py ./cogs/

RUN uv sync --locked --no-editable --no-dev && chmod -R g+r /app

USER appuser
CMD [ "uv", "run", "/app/main.py"]

