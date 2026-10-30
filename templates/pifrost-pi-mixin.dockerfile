# syntax=docker/dockerfile:1.7
# Pi 1.5.0 overlay based on Docker's published pi-mixin recipe.
ARG BASE_IMAGE=docker/sandbox-templates:shell-docker
FROM ${BASE_IMAGE} AS build

USER root

# Pi 1.5.0's find integration accepts Ubuntu's fdfind name. Copy both the
# packaged binary and the fd convenience symlink into the overlay.
RUN apt-get update && \
    apt-get install -y --no-install-recommends fd-find && \
    rm -rf /var/lib/apt/lists/*

ARG PI_VERSION
ADD --chmod=644 https://registry.npmjs.org/@earendil-works%2Fpi-coding-agent/${PI_VERSION} /tmp/pi-release.json

ARG BIFROST_PROVIDER_VERSION=0.2.0
ADD --chmod=644 https://registry.npmjs.org/pi-bifrost-provider/-/pi-bifrost-provider-${BIFROST_PROVIDER_VERSION}.tgz /tmp/pi-bifrost-provider.tgz

USER agent
RUN version="$(node -p 'require("/tmp/pi-release.json").version')" && \
    npm install -g "@earendil-works/pi-coding-agent@${version}" && \
    pi --version

USER root
RUN set -eu; \
    prefix="$(npm prefix -g)"; \
    mkdir -p "/out${prefix}/lib/node_modules" "/out${prefix}/bin" /out/usr/local/bin /out/usr/bin; \
    for d in "${prefix}" "${prefix}/bin" "${prefix}/lib" "${prefix}/lib/node_modules"; do \
      if [ -d "$d" ]; then chown --reference="$d" "/out${d}"; fi; \
    done; \
    cp -a "${prefix}/lib/node_modules/@earendil-works" "/out${prefix}/lib/node_modules/@earendil-works"; \
    cp -a "${prefix}/bin/pi" "/out${prefix}/bin/pi"; \
    [ "${prefix}/bin/pi" = /usr/local/bin/pi ] || ln -s "${prefix}/bin/pi" /out/usr/local/bin/pi; \
    cp -aL "$(command -v fdfind)" /out/usr/bin/fdfind; \
    ln -s /usr/bin/fdfind /out/usr/local/bin/fd; \
    provider_dir=/out/home/agent/.pi/agent/extensions/pi-bifrost-provider; \
    mkdir -p "$provider_dir"; \
    tar -xzf /tmp/pi-bifrost-provider.tgz -C "$provider_dir" --strip-components=1; \
    # Pi refreshes models-store.json and trust state under this directory. \
    chown -R --reference=/home/agent /out/home/agent/.pi; \
    mkdir -p /out/home/agent/.agents; \
    for d in /home /home/agent; do chown --reference="$d" "/out${d}"; done; \
    chown --reference=/home/agent /out/home/agent/.agents

FROM scratch
COPY --from=build /out /
