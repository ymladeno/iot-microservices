
# Stage 1: Build the application
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libasio-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY CMakeLists.txt .
COPY src/ ./src/

RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j2


# Stage 2: Run the application
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    libstdc++6 \
    libgcc-s1 \
    ca-certificates \
    libcurl4 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/build/telemetry /app/telemetry

EXPOSE 8000

CMD ["./telemetry"]
