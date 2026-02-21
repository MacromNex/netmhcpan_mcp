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

# Copy NetMHCpan binary distribution if available (gitignored, so only in local builds)
# For CI/CD: NetMHCpan can be provided via artifact storage or skipped
RUN mkdir -p /app/repo && \
    if [ -d repo/netMHCpan-4.2 ]; then \
      echo "Copying local NetMHCpan binary"; \
      cp -r repo/netMHCpan-4.2 /app/repo/ && \
      sed -i 's|setenv\tNMHOME\t.*|setenv\tNMHOME\t/app/repo/netMHCpan-4.2|' \
          /app/repo/netMHCpan-4.2/netMHCpan && \
      chmod +x /app/repo/netMHCpan-4.2/netMHCpan && \
      chmod +x /app/repo/netMHCpan-4.2/Linux_x86_64/bin/*; \
    else \
      echo "WARNING: NetMHCpan binary directory not found at repo/netMHCpan-4.2"; \
      echo "For local builds: extract netMHCpan-4.2bstatic.Linux.tar.gz into repo/"; \
      echo "For GitHub Actions: use artifact storage or external configuration"; \
    fi

# Set environment variables for NetMHCpan
ENV NMHOME=/app/repo/netMHCpan-4.2
ENV TMPDIR=/tmp

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
