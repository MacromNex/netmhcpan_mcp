FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    tcsh \
    gawk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (matching quick_setup.sh)
RUN pip install --no-cache-dir \
    fastmcp==2.14.1 \
    loguru==0.7.3 \
    pandas==2.3.3 \
    numpy==2.4.0 \
    tqdm==4.67.1 \
    click==8.3.1

RUN pip install --no-cache-dir \
    mcp \
    pydantic \
    uvicorn \
    websockets \
    rich

# Download and extract NetMHCpan binary distribution
# Source: http://www.cbs.dtu.dk/services/NetMHCpan/
# License: Free for academic/non-commercial use
# See: http://www.cbs.dtu.dk/services/NetMHCpan/license.php
RUN mkdir -p /app/repo && \
    if [ -d repo/netMHCpan-4.2 ]; then \
      echo "Using cached NetMHCpan binary"; \
      cp -r repo/netMHCpan-4.2 /app/repo/; \
    else \
      echo "Downloading NetMHCpan from official source..."; \
      for attempt in 1 2 3; do \
        echo "Download attempt $attempt/3"; \
        wget --no-verbose -O /tmp/netMHCpan-4.2.tar.gz \
          "http://www.cbs.dtu.dk/services/NetMHCpan/netMHCpan-4.2b.Linux.tar.gz" && \
          tar -xzf /tmp/netMHCpan-4.2.tar.gz -C /app/repo/ && \
          rm /tmp/netMHCpan-4.2.tar.gz && \
          break; \
        if [ $attempt -lt 3 ]; then \
          echo "Retry in 5 seconds..."; \
          sleep 5; \
        else \
          echo "ERROR: Failed to download NetMHCpan after 3 attempts"; \
          echo "Please check your internet connection or download manually from:"; \
          echo "  http://www.cbs.dtu.dk/services/NetMHCpan/"; \
          exit 1; \
        fi; \
      done; \
    fi && \
    sed -i 's|setenv\tNMHOME\t.*|setenv\tNMHOME\t/app/repo/netMHCpan-4.2|' \
        /app/repo/netMHCpan-4.2/netMHCpan && \
    chmod +x /app/repo/netMHCpan-4.2/netMHCpan && \
    chmod +x /app/repo/netMHCpan-4.2/Linux_x86_64/bin/*

# Set environment variables for NetMHCpan
ENV NMHOME=/app/repo/netMHCpan-4.2
ENV TMPDIR=/tmp

# ====== LICENSE NOTICE ======
# NetMHCpan is developed by CBS (Center for Biological Sequence Analysis),
# Technical University of Denmark (DTU).
# It is free for academic/non-commercial use.
# For commercial use or license details, visit:
#   http://www.cbs.dtu.dk/services/NetMHCpan/
# =============================

# Copy source code
COPY src/ ./src/
RUN chmod -R a+r /app/src/
COPY scripts/ ./scripts/
RUN chmod -R a+r /app/scripts/
COPY configs/ ./configs/
RUN chmod -R a+r /app/configs/

# Create working directories
RUN mkdir -p /app/jobs /app/results /tmp

ENV PYTHONPATH=/app

# Verify installation
RUN python -c "import fastmcp; import loguru; print('Core packages OK')"

CMD ["python", "src/server.py"]
