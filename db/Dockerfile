FROM postgres:18-alpine

COPY schema.sql /docker-entrypoint-initdb.d/01-schema.sql
COPY indexes.sql /docker-entrypoint-initdb.d/02-indexes.sql
