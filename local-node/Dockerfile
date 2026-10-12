# Node version is resolved from rust-sdk v0.17.2 Cargo.lock, not its release number.
FROM ghcr.io/0xmiden/miden-node:v0.17.0@sha256:6fd0c5af3912ff343287f4549d81769d10939ae925da7498cc339b8ce9b95a50 AS node
FROM ghcr.io/0xmiden/miden-validator:v0.17.0@sha256:76b4804b9ba53c5f905ef5e4f6ee80ff4f793c9fa77bcb00777e21d6c65855e8 AS validator
FROM ghcr.io/0xmiden/miden-ntx-builder:v0.17.0@sha256:94643931c23d216de3b7efb25bea6286840eb28ffbf26bca4c737fa4369ef958 AS ntx
FROM ghcr.io/0xmiden/miden-remote-prover:v0.17.0@sha256:481182316d294d37ce24f7bb79de54f59148f73c1d7a0b751e9e1b32c1820bc3 AS prover
FROM ghcr.io/0xmiden/miden-usdcx-genesis:v0.17.0@sha256:7990590ec065b7bd2a3321661b9dffa81b14df33ef6d1542849db88e65d70cda AS genesis
FROM python:3.13-slim-trixie@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
COPY --from=node /usr/local/bin/miden-node /usr/local/bin/
COPY --from=validator /usr/local/bin/miden-validator /usr/local/bin/
COPY --from=ntx /usr/local/bin/miden-ntx-builder /usr/local/bin/
COPY --from=prover /usr/local/bin/miden-remote-prover /usr/local/bin/
COPY --from=genesis /usr/local/bin/miden-usdcx-genesis /usr/local/bin/
COPY fixtures /fixtures
COPY node.py /app/node.py
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/app/node.py"]
