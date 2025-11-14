FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    autoconf \
    automake \
    libtool \
    pkg-config \
    libfftw3-dev \
    libsndfile1-dev \
    git \
    python3 \
    python3-pip

# Clone and build audiowmark
RUN git clone https://github.com/swesterfeld/audiowmark.git /audiowmark
WORKDIR /audiowmark
RUN ./autogen.sh && ./configure && make && make install

# Install Python dependencies for API
RUN pip3 install flask gunicorn

# Copy API server
COPY audiowmark-api.py /app/server.py
WORKDIR /app

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "4", "--timeout", "120", "server:app"]
