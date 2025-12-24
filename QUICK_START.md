# NetMHCpan MCP Server - Quick Start Guide

## ✅ Installation Complete - Ready for Production Use

This NetMHCpan MCP server has been **fully tested and validated** for production use with Claude Code.

## Quick Reference Commands

### Pre-flight Validation
```bash
# Check server imports
python -c "import sys; sys.path = ['.', './src'] + [p for p in sys.path if 'bio-mcp-interpro' not in p]; from src.server import mcp; print('✅ Server imports OK')"

# List tools
grep -A 1 "@mcp\.tool()" src/server.py | grep "def " | wc -l
# Should return: 15
```

### Claude Code Installation
```bash
# Add MCP server
claude mcp add netmhcpan_4_2 -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify
claude mcp list
# Look for: netmhcpan_4_2 - ✓ Connected

# Remove if needed
claude mcp remove netmhcpan_4_2
```

### Testing Commands
```bash
# Test sync tools
python scripts/peptide_prediction.py --input examples/data/test.pep
python scripts/protein_prediction.py --input examples/data/test.fsa --length 9

# Test job submission
python -c "
import sys; sys.path = ['.', './src'] + [p for p in sys.path if 'bio-mcp-interpro' not in p]
from jobs.manager import job_manager
result = job_manager.submit_job('scripts/peptide_prediction.py', {'input': 'examples/data/test.pep'})
print(f'Job ID: {result[\"job_id\"]}')
"

# Check job status
python -c "
import sys; sys.path = ['.', './src'] + [p for p in sys.path if 'bio-mcp-interpro' not in p]
from jobs.manager import job_manager
print(job_manager.list_jobs())
"
```

### Debugging Commands
```bash
# Check server startup
timeout 10 python src/server.py &
# Should show FastMCP banner

# Check job logs
tail -50 jobs/*/job.log

# View job results
python -c "
import sys; sys.path = ['.', './src'] + [p for p in sys.path if 'bio-mcp-interpro' not in p]
from jobs.manager import job_manager
import json
result = job_manager.get_job_result('<job_id>')
print(json.dumps(result, indent=2))
"
```

## Example Claude Code Prompts

Once installed in Claude Code, try these prompts:

### 1. Tool Discovery
```
What tools are available from netmhcpan_4_2? Give me a brief description of each.
```

### 2. Basic Peptide Analysis
```
Use predict_peptide_binding to analyze the peptides in examples/data/test.pep with allele HLA-A02:01
```

### 3. Protein Epitope Scanning
```
Use predict_protein_epitopes to scan examples/data/test.fsa for 9-mer epitopes using HLA-A02:01
```

### 4. Enhanced Binding Prediction
```
Run predict_binding_affinity on examples/data/test.pep with prediction_mode='both' to get IC50 and elution likelihood
```

### 5. Batch Processing
```
Submit batch protein analysis for multiple files using submit_batch_protein_analysis with input_files=['examples/data/test.fsa', 'examples/data/B0702.fsa']
```

### 6. Job Management
```
List all submitted jobs and their status using list_jobs
```

### 7. Multi-Allele Analysis
```
Submit multi-allele screening for examples/data/test.pep against alleles ['HLA-A02:01', 'HLA-B07:02', 'HLA-C07:02']
```

### 8. Export to Excel
```
Export predictions for examples/data/test.pep to Excel format comparing alleles HLA-A02:01 and HLA-B07:02
```

### 9. Server Information
```
Get server info including supported alleles and version information
```

### 10. Error Handling Test
```
Try running predict_peptide_binding with a non-existent file '/fake/path.pep' to test error handling
```

## Expected Performance

- **Server Startup**: < 1 second
- **Sync Tools** (predict_*): < 1 second for small inputs
- **Job Submission**: < 1 second
- **Job Status Check**: < 1 second

## File Locations

- **Server**: `src/server.py`
- **Scripts**: `scripts/`
- **Demo Data**: `examples/data/`
- **Test Results**: `reports/step7_integration.md`
- **Job Outputs**: `jobs/<job_id>/`

## Tool Categories

### Job Management (5 tools)
- `get_job_status` - Check job progress
- `get_job_result` - Get completed job results
- `get_job_log` - View job execution logs
- `cancel_job` - Cancel running job
- `list_jobs` - List all jobs

### Synchronous Prediction (5 tools)
- `predict_peptide_binding` - Basic peptide MHC binding
- `predict_protein_epitopes` - Protein epitope scanning
- `predict_binding_affinity` - Enhanced IC50/EL prediction
- `predict_custom_mhc_binding` - Custom MHC sequences
- `export_predictions_to_excel` - Multi-allele Excel export

### Batch Processing (3 tools)
- `submit_batch_protein_analysis` - Multiple protein files
- `submit_multi_allele_screening` - Multiple HLA alleles
- `submit_large_peptide_screening` - Large peptide datasets

### Utilities (2 tools)
- `analyze_netmhcpan_output` - Parse existing results
- `get_server_info` - Server configuration

## Test Status: ✅ 100% PASSED

All 34 integration tests passed successfully:
- ✅ Server startup and tool discovery
- ✅ Claude Code registration and connectivity
- ✅ Sync tool functionality with demo data
- ✅ Submit API workflow (submit → status → result)
- ✅ Job management and background processing
- ✅ Error handling and parameter validation
- ✅ Real-world scenarios and batch processing

## Next Steps

1. Start using the MCP server in Claude Code with the example prompts above
2. Explore the demo data in `examples/data/` for testing
3. Check `reports/step7_integration.md` for detailed test results
4. Use `tests/test_prompts.md` for comprehensive testing scenarios

The server is production-ready and fully operational! 🎉