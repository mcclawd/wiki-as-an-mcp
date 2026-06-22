FROM rocker/r-ver:4.5.1

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        libcurl4-openssl-dev libssl-dev libxml2-dev libsodium-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Core API + metric deps, then CASdatasets (archived; served from its own repo, with a
# CRAN fallback for its dependencies). Most of the datasets are CASdatasets r_packages,
# and arrow is needed for any parquet source.
RUN R -e "install.packages(c('plumber','jsonlite','yaml','cplm','arrow','sp','xts','zoo'), repos='https://cloud.r-project.org')" \
 && R -e "install.packages('CASdatasets', repos=c('http://cas.uqam.ca/pub/R/','https://cloud.r-project.org'), type='source')" \
 && R -e "stopifnot(requireNamespace('CASdatasets', quietly=TRUE))"

WORKDIR /opt/eval-api
COPY app.R ./
COPY datasets/ ./datasets/

ENV EVAL_DATASETS_DIR=/opt/eval-api/datasets \
    EVAL_SECRET_DIR=/opt/eval-api/secrets \
    EVAL_LOG_PATH=/opt/eval-api/logs/submissions.jsonl \
    EVAL_ADMIN_TOKEN= \
    PORT=8765 \
    HOST=0.0.0.0

# HOST=0.0.0.0 is correct INSIDE the container (the port is mapped out); app.R itself
# defaults to 127.0.0.1 for a direct host run. EVAL_ADMIN_TOKEN must be supplied at runtime:
#   docker run -e EVAL_ADMIN_TOKEN=$(openssl rand -hex 32) -p 8765:8765 ...

EXPOSE 8765
CMD ["Rscript", "app.R"]
