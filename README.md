# netMHCpan-4.2 MCP

> Model Context Protocol (MCP) server for NetMHCpan-4.2, enabling AI-powered MHC Class I binding prediction and epitope analysis through Claude Code and other MCP-compatible tools.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Using with Gemini CLI](#using-with-gemini-cli)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

This MCP server provides comprehensive access to NetMHCpan-4.2 for predicting MHC Class I binding affinity and identifying T-cell epitopes. It enables both quick interactive analysis and large-scale batch processing through AI assistants like Claude Code.

### Features
- **Dual API Architecture**: Fast sync operations (<1 min) + background batch processing
- **Comprehensive Prediction**: Peptide binding, protein epitope scanning, custom MHC analysis
- **Multiple Export Formats**: Text results, Excel spreadsheets for analysis
- **Job Management**: Full lifecycle tracking for long-running analyses
- **AI Integration**: Natural language interface through Claude Code and compatible tools

### Directory Structure
```
./
├── README.md               # This file
├── env/                    # Conda environment
├── src/
│   └── server.py           # MCP server with 15 tools
├── scripts/
│   ├── peptide_prediction.py          # Individual peptide analysis
│   ├── protein_prediction.py          # Protein epitope scanning
│   ├── custom_mhc_prediction.py       # Novel MHC allele analysis
│   ├── binding_affinity_prediction.py # Enhanced EL+BA predictions
│   ├── excel_export.py                # Multi-allele Excel export
│   └── lib/                           # Shared utilities
├── examples/
│   └── data/               # Demo data (peptides, proteins, MHC sequences)
├── configs/                # Configuration files with examples
└── repo/                   # Original NetMHCpan-4.2 repository
```

---

## Installation

### Quick Setup (Recommended)

Run the automated setup script:

```bash
cd netmhcpan_mcp
bash quick_setup.sh
```

The script will create the conda environment, install all dependencies, and display the Claude Code configuration. See `quick_setup.sh --help` for options like `--skip-env`.

### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python 3.10+
- Linux x86_64 (for NetMHCpan binary compatibility)

### Manual Installation (Alternative)

If you prefer manual installation or need to customize the setup, follow `reports/step3_environment.md`:

```bash
# Navigate to the MCP directory
cd /home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/netmhcpan_mcp

# Create conda environment (use mamba if available)
mamba create -p ./env python=3.10 -y
# or: conda create -p ./env python=3.10 -y

# Activate environment
mamba activate ./env
# or: conda activate ./env

# Install Dependencies
pip install fastmcp==2.14.1 loguru==0.7.3 pandas==2.3.3 numpy==2.4.0 tqdm==4.67.1 click==8.3.1

# Install MCP dependencies
pip install --ignore-installed mcp pydantic uvicorn websockets rich
```

### Verify Installation
```bash
# Test NetMHCpan availability
./repo/netMHCpan-4.2/Linux_x86_64/bin/netMHCpan-4.2 -h

# Test environment
python -c "import fastmcp, loguru, pandas; print('✅ All dependencies installed')"
```

---

## Local Usage (Scripts)

You can use the scripts directly without MCP for local processing.

### Available Scripts

| Script | Description | Example |
|--------|-------------|---------|
| `scripts/peptide_prediction.py` | Predict MHC binding for individual peptides | See below |
| `scripts/protein_prediction.py` | Scan protein sequences for epitopes | See below |
| `scripts/custom_mhc_prediction.py` | Analyze binding to custom MHC alleles | See below |
| `scripts/binding_affinity_prediction.py` | Enhanced EL+BA predictions with IC50 values | See below |
| `scripts/excel_export.py` | Multi-allele analysis with Excel export | See below |

### Script Examples

#### Peptide Binding Prediction

```bash
# Activate environment
mamba activate ./env

# Run script
python scripts/peptide_prediction.py \
  --input examples/data/test.pep \
  --output results/peptide_analysis.txt \
  --allele HLA-A02:01 \
  --rank-threshold 2.0
```

**Parameters:**
- `--input, -i`: Peptide file with one peptide per line (required)
- `--output, -o`: Output file path (default: auto-generated)
- `--allele, -a`: HLA allele identifier (default: HLA-A02:01)
- `--rank-threshold, -t`: Filter by rank threshold (optional)
- `--config, -c`: Configuration file (optional)

#### Protein Epitope Scanning

```bash
python scripts/protein_prediction.py \
  --input examples/data/test.fsa \
  --output results/epitope_scan.txt \
  --length 8,9,10 \
  --allele HLA-A24:02 \
  --sort
```

**Parameters:**
- `--input, -i`: FASTA protein sequence file (required)
- `--output, -o`: Output file path (default: auto-generated)
- `--length, -l`: Comma-separated peptide lengths (default: 9)
- `--allele, -a`: HLA allele identifier (default: HLA-A02:01)
- `--sort, -s`: Sort results by binding affinity (optional)

#### Custom MHC Analysis

```bash
python scripts/custom_mhc_prediction.py \
  --input examples/data/test.pep \
  --mhc-seq examples/data/B0702.fsa \
  --mhc-name CUSTOM_B0702 \
  --output results/custom_mhc.txt
```

#### Enhanced Binding Affinity Prediction

```bash
python scripts/binding_affinity_prediction.py \
  --input examples/data/test.pep \
  --output results/binding_affinity.txt \
  --allele HLA-A02:01 \
  --mode both
```

#### Multi-Allele Excel Export

```bash
python scripts/excel_export.py \
  --input examples/data/test.pep \
  --alleles HLA-A01:01,HLA-A02:01,HLA-B07:02 \
  --excel-file results/comparison.xlsx \
  --binding-affinity
```

---

## MCP Server Installation

### Option 1: Using fastmcp (Recommended)

```bash
# Install MCP server for Claude Code
fastmcp install src/server.py --name netMHCpan-4.2
```

### Option 2: Manual Installation for Claude Code

```bash
# Add MCP server to Claude Code
claude mcp add netmhcpan_4_2 -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify installation
claude mcp list
```

### Option 3: Configure in settings.json

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "netmhcpan_4_2": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/netmhcpan_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/netmhcpan_mcp/src/server.py"]
    }
  }
}
```

---

## Using with Claude Code

After installing the MCP server, you can use it directly in Claude Code.

### Quick Start

```bash
# Start Claude Code
claude
```

### Example Prompts

#### Tool Discovery
```
What tools are available from netMHCpan-4.2?
```

#### Basic Usage
```
Use predict_peptide_binding with input file @examples/data/test.pep
```

#### Protein Analysis
```
Run predict_protein_epitopes on @examples/data/test.fsa for peptide lengths 8,9,10 using HLA-A24:02
```

#### Long-Running Tasks (Submit API)
```
Submit batch_protein_analysis for multiple FASTA files and check the job status
```

#### Batch Processing
```
Process these peptide files for multiple HLA alleles:
- @examples/data/test.pep for HLA-A02:01, HLA-A01:01, HLA-B07:02
Export results to Excel format
```

### Using @ References

In Claude Code, use `@` to reference files and directories:

| Reference | Description |
|-----------|-------------|
| `@examples/data/test.pep` | Reference peptide input file |
| `@examples/data/test.fsa` | Reference protein FASTA file |
| `@examples/data/B0702.fsa` | Reference custom MHC sequence |
| `@configs/default_config.json` | Reference configuration file |
| `@results/` | Reference output directory |

---

## Using with Gemini CLI

### Configuration

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "netmhcpan_4_2": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/netmhcpan_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/netmhcpan_mcp/src/server.py"]
    }
  }
}
```

### Example Prompts

```bash
# Start Gemini CLI
gemini

# Example prompts (same as Claude Code)
> What tools are available for MHC binding prediction?
> Use predict_peptide_binding with file examples/data/test.pep
> Submit large_peptide_screening for batch processing
```

---

## Available Tools

### Quick Operations (Sync API)

These tools return results immediately (< 1 minute):

| Tool | Description | Parameters | Key Features |
|------|-------------|------------|--------------|
| `predict_peptide_binding` | Basic MHC Class I binding | `input_file`, `allele`, `rank_threshold` | Individual peptides, rank filtering |
| `predict_protein_epitopes` | Epitope scanning from FASTA | `input_file`, `peptide_lengths`, `allele` | Multi-length scanning, sorting |
| `predict_binding_affinity` | Enhanced EL+BA predictions | `input_file`, `allele`, `prediction_mode` | IC50 values, dual scoring |
| `predict_custom_mhc_binding` | Custom MHC allele predictions | `input_file`, `mhc_sequence_file`, `mhc_name` | Novel alleles, research use |
| `export_predictions_to_excel` | Multi-allele Excel export | `input_file`, `alleles`, `excel_file` | Comparison tables, publication-ready |

### Long-Running Tasks (Submit API)

These tools return a job_id for tracking (> 1 minute):

| Tool | Description | Parameters | Use Case |
|------|-------------|------------|----------|
| `submit_batch_protein_analysis` | Multiple protein analysis | `input_files`, `peptide_lengths`, `allele` | Proteome screening |
| `submit_multi_allele_screening` | HLA diversity screening | `input_file`, `alleles`, `prediction_mode` | Population coverage |
| `submit_large_peptide_screening` | Large-scale screening | `input_file`, `allele`, `chunk_size` | Library analysis |

### Job Management Tools

| Tool | Description |
|------|-------------|
| `get_job_status` | Check job progress and status |
| `get_job_result` | Get results when completed |
| `get_job_log` | View execution logs with tail option |
| `cancel_job` | Cancel running job |
| `list_jobs` | List all jobs with status filtering |

### Utility Tools

| Tool | Description |
|------|-------------|
| `analyze_netmhcpan_output` | Parse raw NetMHCpan output |
| `get_server_info` | Server capabilities and allele list |

---

## Examples

### Example 1: Quick Peptide Analysis

**Goal:** Analyze a list of peptides for HLA-A02:01 binding

**Using Script:**
```bash
python scripts/peptide_prediction.py \
  --input examples/data/test.pep \
  --allele HLA-A02:01 \
  --output results/example1/
```

**Using MCP (in Claude Code):**
```
Use predict_peptide_binding to process @examples/data/test.pep for HLA-A02:01 and save results to results/example1/
```

**Expected Output:**
- Binding predictions with ranks and scores
- Strong/weak binder classification
- Statistical summary

### Example 2: Protein Epitope Discovery

**Goal:** Find potential epitopes in a protein sequence

**Using Script:**
```bash
python scripts/protein_prediction.py \
  --input examples/data/test.fsa \
  --length 8,9,10 \
  --allele HLA-A24:02 \
  --sort
```

**Using MCP (in Claude Code):**
```
Run predict_protein_epitopes on @examples/data/test.fsa with peptide_lengths 8,9,10 for HLA-A24:02, sort by binding affinity
```

**Expected Output:**
- All possible peptides of specified lengths
- Binding predictions sorted by affinity
- Epitope count summary

### Example 3: Custom MHC Research

**Goal:** Analyze peptide binding to a custom MHC allele

**Using Script:**
```bash
python scripts/custom_mhc_prediction.py \
  --input examples/data/test.pep \
  --mhc-seq examples/data/B0702.fsa \
  --mhc-name RESEARCH_ALLELE
```

**Using MCP (in Claude Code):**
```
Use predict_custom_mhc_binding with peptides from @examples/data/test.pep and custom MHC sequence @examples/data/B0702.fsa
```

### Example 4: Multi-Allele Population Coverage

**Goal:** Assess binding across multiple HLA alleles

**Using MCP (in Claude Code):**
```
Use export_predictions_to_excel with @examples/data/test.pep for alleles ["HLA-A02:01", "HLA-A01:01", "HLA-B07:02"] and export to Excel
```

### Example 5: Large-Scale Batch Processing

**Goal:** Process multiple protein files in background

**Using MCP (in Claude Code):**
```
Submit submit_batch_protein_analysis for all FASTA files in @examples/data/ with peptide lengths 9,10
Then monitor the job status and get results when completed
```

---

## Demo Data

The `examples/data/` directory contains sample data for testing:

| File | Description | Use With | Content |
|------|-------------|----------|---------|
| `test.pep` | 10 test peptides with binding scores | Peptide prediction tools | 9-mer peptides |
| `test.fsa` | 14-3-3 protein FASTA sequence | Protein analysis tools | 245 amino acids |
| `B0702.fsa` | HLA-B*07:02 MHC sequence | Custom MHC tools | Full-length MHC |
| `test_predictions.txt` | Sample NetMHCpan output | Analysis tools | Formatted results |
| `test_binding_both.txt` | EL+BA prediction results | Utility tools | Enhanced format |

---

## Configuration Files

The `configs/` directory contains configuration templates:

| Config | Description | Example Parameters |
|--------|-------------|-------------------|
| `default_config.json` | Common default values | Standard alleles, thresholds |
| `peptide_prediction_config.json` | Peptide analysis settings | Rank thresholds, output formats |
| `protein_prediction_config.json` | Protein scanning options | Peptide lengths, sorting preferences |
| `custom_mhc_config.json` | Custom MHC requirements | MHC naming, sequence validation |
| `binding_affinity_config.json` | BA prediction modes | EL/BA options, IC50 settings |
| `excel_export_config.json` | Export configurations | Common allele sets, formatting |

### Config Example

```json
{
  "allele": "HLA-A02:01",
  "rank_threshold": 2.0,
  "peptide_lengths": [8, 9, 10],
  "prediction_mode": "both",
  "sort_output": true,
  "common_alleles": [
    "HLA-A01:01", "HLA-A02:01", "HLA-A03:01",
    "HLA-B07:02", "HLA-B08:01", "HLA-B27:05"
  ]
}
```

---

## Troubleshooting

### Environment Issues

**Problem:** Environment not found
```bash
# Recreate environment
mamba create -p ./env python=3.10 -y
mamba activate ./env
pip install fastmcp loguru pandas numpy tqdm click
```

**Problem:** Import errors
```bash
# Verify installation
python -c "from src.server import mcp; print('✅ Server imports correctly')"
```

**Problem:** NetMHCpan binary not found
```bash
# Check binary availability
ls -la repo/netMHCpan-4.2/Linux_x86_64/bin/netMHCpan-4.2
# Verify executable permissions
chmod +x repo/netMHCpan-4.2/Linux_x86_64/bin/netMHCpan-4.2
```

### MCP Issues

**Problem:** Server not found in Claude Code
```bash
# Check MCP registration
claude mcp list

# Re-add if needed
claude mcp remove netmhcpan_4_2
claude mcp add netmhcpan_4_2 -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

**Problem:** Tools not working
```bash
# Test server directly
mamba activate ./env
python src/server.py
# Should show: Server running with 15 tools
```

**Problem:** Path issues in MCP
```bash
# Use absolute paths in Claude Code settings
{
  "command": "/full/path/to/env/bin/python",
  "args": ["/full/path/to/src/server.py"]
}
```

### Job Issues

**Problem:** Job stuck in pending
```bash
# Check job directory
ls -la jobs/

# Verify job manager
python -c "from src.jobs.manager import job_manager; print(job_manager.list_jobs())"
```

**Problem:** Job failed
```
Use get_job_log with job_id "<job_id>" and tail 100 to see error details
```

**Problem:** Batch processing errors
```bash
# Check available disk space
df -h .
# Check file permissions
ls -la examples/data/
```

### Performance Issues

**Problem:** Slow predictions
- **Solution**: Use submit API for large datasets
- **Monitor**: Check system resources during processing

**Problem:** Memory usage
- **Solution**: Adjust chunk_size in large_peptide_screening
- **Monitor**: Use batch processing for multiple files

---

## Development

### Running Tests

```bash
# Activate environment
mamba activate ./env

# Test individual scripts
python scripts/peptide_prediction.py --help
python scripts/protein_prediction.py --input examples/data/test.fsa --length 9

# Test MCP server
python src/server.py
# Test with sample data
```

### Starting Dev Server

```bash
# Run MCP server in development mode
fastmcp dev src/server.py

# Test with MCP inspector
npx @anthropic/mcp-inspector src/server.py
```

### Adding New Tools

1. Create script in `scripts/` directory
2. Add main function following existing patterns
3. Import function in `src/server.py`
4. Add `@mcp.tool()` decorator with proper documentation

---

## Performance Benchmarks

| Operation | Input Size | Time | Memory |
|-----------|------------|------|---------|
| Peptide Prediction | 10 peptides | <1s | ~50MB |
| Protein Scanning | 245 AA protein | <1s | ~100MB |
| Multi-allele Analysis | 10 peptides × 3 alleles | ~2s | ~150MB |
| Batch Processing | 1000 peptides | ~30s | ~200MB |

---

## License

Based on NetMHCpan-4.2 (Academic License). This MCP wrapper is provided for research and educational use.

## Credits

- **NetMHCpan-4.2**: Original software by DTU Bioinformatics
- **MCP Integration**: Built with FastMCP framework
- **Original Repository**: [NetMHCpan-4.2](https://services.healthtech.dtu.dk/services/NetMHCpan-4.2/)

---

## Quick Reference

### Essential Commands
```bash
# Install
mamba activate ./env && fastmcp install src/server.py --name netMHCpan-4.2

# Test
python scripts/peptide_prediction.py --input examples/data/test.pep

# Use in Claude
"Use predict_peptide_binding with @examples/data/test.pep"
```

### Key Files
- **Server**: `src/server.py` (15 MCP tools)
- **Scripts**: `scripts/*.py` (5 standalone scripts)
- **Demo Data**: `examples/data/*.{pep,fsa}` (test files)
- **Configs**: `configs/*.json` (configuration templates)

For detailed usage examples, see the [Examples](#examples) section above.
