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

# Copy NetMHCpan binary distribution and bake it into the image
# This avoids repetitive downloading of the checkpoint/data files
COPY repo/netMHCpan-4.2/ /app/repo/netMHCpan-4.2/

# Patch the netMHCpan wrapper script to use the container path
RUN sed -i 's|setenv\tNMHOME\t.*|setenv\tNMHOME\t/app/repo/netMHCpan-4.2|' \
    /app/repo/netMHCpan-4.2/netMHCpan && \
    chmod +x /app/repo/netMHCpan-4.2/netMHCpan && \
    chmod +x /app/repo/netMHCpan-4.2/Linux_x86_64/bin/*

# Set environment variables for NetMHCpan
ENV NMHOME=/app/repo/netMHCpan-4.2
ENV TMPDIR=/tmp

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY configs/ ./configs/
COPY examples/ ./examples/

# Create working directories
RUN mkdir -p /app/jobs /app/results /tmp

ENV PYTHONPATH=/app

# Verify installation
RUN python -c "import fastmcp; import loguru; print('Core packages OK')"

CMD ["python", "src/server.py"]
