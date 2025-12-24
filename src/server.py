"""NetMHCpan-4.2 MCP Server

Provides both synchronous and asynchronous APIs for NetMHCpan-4.2 tools.
Fast operations return results immediately, while batch processing uses the submit API.
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional, List, Union
import sys
import os

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = MCP_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from jobs.manager import job_manager
from loguru import logger

# Import script functions
try:
    from peptide_prediction import run_peptide_prediction
    from protein_prediction import run_protein_prediction
    from binding_affinity_prediction import run_binding_affinity_prediction
    from custom_mhc_prediction import run_custom_mhc_prediction
    from excel_export import run_excel_export
except ImportError as e:
    logger.warning(f"Could not import script modules: {e}")
    # We'll handle this gracefully in the tools

# Create MCP server
mcp = FastMCP("NetMHCpan-4.2")

# ==============================================================================
# Job Management Tools (for async operations)
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a submitted job.

    Args:
        job_id: The job ID returned from a submit_* function

    Returns:
        Dictionary with job status, timestamps, and any errors
    """
    return job_manager.get_job_status(job_id)

@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """
    Get the results of a completed job.

    Args:
        job_id: The job ID of a completed job

    Returns:
        Dictionary with the job results or error if not completed
    """
    return job_manager.get_job_result(job_id)

@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> dict:
    """
    Get log output from a running or completed job.

    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)

    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)

@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """
    Cancel a running job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)

@mcp.tool()
def list_jobs(status: Optional[str] = None) -> dict:
    """
    List all submitted jobs.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)

    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)

# ==============================================================================
# NetMHCpan Prediction Tools (Synchronous - Fast Operations)
# ==============================================================================

@mcp.tool()
def predict_peptide_binding(
    input_file: str,
    allele: str = "HLA-A02:01",
    rank_threshold: Optional[float] = None,
    output_file: Optional[str] = None
) -> dict:
    """
    Predict MHC Class I binding affinity for individual peptides.

    Fast operation (~1 second) for basic peptide binding prediction.

    Args:
        input_file: Path to file with peptides (one per line or space-separated with scores)
        allele: HLA allele (default: HLA-A02:01)
        rank_threshold: Optional rank threshold for filtering (e.g., 2.0 for weak binders)
        output_file: Optional path to save detailed output

    Returns:
        Dictionary with binding predictions, strong/weak binder counts, and output path
    """
    try:
        from peptide_prediction import run_peptide_prediction
        result = run_peptide_prediction(
            input_file=input_file,
            allele=allele,
            rank_threshold=rank_threshold,
            output_file=output_file
        )
        return {"status": "success", **result}
    except FileNotFoundError as e:
        return {"status": "error", "error": f"Input file not found: {e}"}
    except Exception as e:
        logger.error(f"Peptide prediction failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def predict_protein_epitopes(
    input_file: str,
    peptide_lengths: str = "9",
    allele: str = "HLA-A02:01",
    sort_output: bool = False,
    output_file: Optional[str] = None
) -> dict:
    """
    Scan protein sequence for potential MHC binding epitopes.

    Fast operation (~1 second) for epitope scanning from FASTA sequences.

    Args:
        input_file: Path to FASTA file with protein sequence(s)
        peptide_lengths: Comma-separated lengths to scan (e.g., "8,9,10")
        allele: HLA allele (default: HLA-A02:01)
        sort_output: Sort results by binding affinity
        output_file: Optional path to save detailed output

    Returns:
        Dictionary with epitope scan results and peptide statistics
    """
    try:
        from protein_prediction import run_protein_prediction
        result = run_protein_prediction(
            input_file=input_file,
            peptide_lengths=peptide_lengths,
            allele=allele,
            sort_output=sort_output,
            output_file=output_file
        )
        return {"status": "success", **result}
    except FileNotFoundError as e:
        return {"status": "error", "error": f"Input file not found: {e}"}
    except Exception as e:
        logger.error(f"Protein epitope prediction failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def predict_binding_affinity(
    input_file: str,
    allele: str = "HLA-A02:01",
    prediction_mode: str = "both",
    output_file: Optional[str] = None
) -> dict:
    """
    Enhanced binding prediction with both Eluted Ligand and Binding Affinity scores.

    Fast operation (~1 second) providing detailed IC50 and elution likelihood predictions.

    Args:
        input_file: Path to file with peptides
        allele: HLA allele (default: HLA-A02:01)
        prediction_mode: Prediction type - "EL" (elution), "BA" (binding), or "both"
        output_file: Optional path to save detailed output

    Returns:
        Dictionary with IC50 scores, EL predictions, and binding classifications
    """
    try:
        from binding_affinity_prediction import run_binding_affinity_prediction
        result = run_binding_affinity_prediction(
            input_file=input_file,
            allele=allele,
            prediction_mode=prediction_mode,
            output_file=output_file
        )
        return {"status": "success", **result}
    except FileNotFoundError as e:
        return {"status": "error", "error": f"Input file not found: {e}"}
    except ValueError as e:
        return {"status": "error", "error": f"Invalid prediction mode: {e}"}
    except Exception as e:
        logger.error(f"Binding affinity prediction failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def predict_custom_mhc_binding(
    input_file: str,
    mhc_sequence_file: str,
    mhc_name: str = "CUSTOM_MHC",
    output_file: Optional[str] = None
) -> dict:
    """
    Predict binding to custom or novel MHC allele sequences.

    Fast operation (~1 second) for research and personalized medicine applications.

    Args:
        input_file: Path to file with peptides
        mhc_sequence_file: Path to FASTA file with MHC sequence
        mhc_name: Identifier for the custom MHC (default: CUSTOM_MHC)
        output_file: Optional path to save detailed output

    Returns:
        Dictionary with custom MHC predictions and metadata
    """
    try:
        from custom_mhc_prediction import run_custom_mhc_prediction
        result = run_custom_mhc_prediction(
            input_file=input_file,
            mhc_sequence_file=mhc_sequence_file,
            mhc_name=mhc_name,
            output_file=output_file
        )
        return {"status": "success", **result}
    except FileNotFoundError as e:
        return {"status": "error", "error": f"File not found: {e}"}
    except Exception as e:
        logger.error(f"Custom MHC prediction failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def export_predictions_to_excel(
    input_file: str,
    alleles: Union[str, List[str]],
    excel_file: Optional[str] = None
) -> dict:
    """
    Export predictions for multiple alleles to Excel format.

    Fast operation (~1 second) for multi-allele comparison and analysis.

    Args:
        input_file: Path to file with peptides
        alleles: Single allele or list of alleles to compare (e.g., ["HLA-A02:01", "HLA-B07:02"])
        excel_file: Optional path for Excel output (auto-generated if not provided)

    Returns:
        Dictionary with Excel export results and comparison statistics
    """
    try:
        from excel_export import run_excel_export

        # Handle both string and list inputs for alleles
        if isinstance(alleles, str):
            alleles_list = [alleles]
        else:
            alleles_list = alleles

        result = run_excel_export(
            input_file=input_file,
            alleles=alleles_list,
            excel_file=excel_file
        )
        return {"status": "success", **result}
    except FileNotFoundError as e:
        return {"status": "error", "error": f"Input file not found: {e}"}
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        return {"status": "error", "error": str(e)}

# ==============================================================================
# Batch Processing Tools (Submit API for multiple inputs)
# ==============================================================================

@mcp.tool()
def submit_batch_protein_analysis(
    input_files: List[str],
    peptide_lengths: str = "9",
    allele: str = "HLA-A02:01",
    job_name: Optional[str] = None
) -> dict:
    """
    Submit batch protein epitope analysis for multiple FASTA files.

    Process multiple protein sequences in a single job. Use for:
    - Analyzing multiple proteins from a proteome
    - Batch screening of protein variants
    - Large-scale epitope discovery

    Args:
        input_files: List of FASTA file paths to analyze
        peptide_lengths: Comma-separated peptide lengths (e.g., "8,9,10")
        allele: HLA allele for all predictions
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id. Use get_job_status() to monitor progress.
    """
    script_path = str(SCRIPTS_DIR / "protein_prediction.py")

    return job_manager.submit_job(
        script_path=script_path,
        args={
            "input_files": input_files,  # Will be converted to comma-separated string
            "peptide_lengths": peptide_lengths,
            "allele": allele
        },
        job_name=job_name or f"batch_protein_analysis_{len(input_files)}_files"
    )

@mcp.tool()
def submit_multi_allele_screening(
    input_file: str,
    alleles: List[str],
    prediction_mode: str = "both",
    job_name: Optional[str] = None
) -> dict:
    """
    Submit multi-allele screening for comprehensive HLA coverage.

    Screen the same peptides against multiple HLA alleles. Use for:
    - Population coverage analysis
    - Vaccine design across HLA diversity
    - Comprehensive binding profile analysis

    Args:
        input_file: Path to file with peptides
        alleles: List of HLA alleles to screen against
        prediction_mode: "EL", "BA", or "both"
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id for monitoring the multi-allele analysis.
    """
    script_path = str(SCRIPTS_DIR / "binding_affinity_prediction.py")

    return job_manager.submit_job(
        script_path=script_path,
        args={
            "input": input_file,
            "alleles": ",".join(alleles),  # Multiple alleles
            "prediction_mode": prediction_mode
        },
        job_name=job_name or f"multi_allele_screening_{len(alleles)}_alleles"
    )

@mcp.tool()
def submit_large_peptide_screening(
    input_file: str,
    allele: str = "HLA-A02:01",
    prediction_mode: str = "both",
    chunk_size: int = 1000,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit large-scale peptide screening with progress tracking.

    Process large peptide libraries with batching for memory efficiency. Use for:
    - Proteome-wide epitope screening
    - Large peptide library analysis
    - High-throughput screening applications

    Args:
        input_file: Path to large peptide file
        allele: HLA allele for predictions
        prediction_mode: "EL", "BA", or "both"
        chunk_size: Number of peptides per processing chunk
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id for monitoring the large-scale screening.
    """
    script_path = str(SCRIPTS_DIR / "binding_affinity_prediction.py")

    return job_manager.submit_job(
        script_path=script_path,
        args={
            "input": input_file,
            "allele": allele,
            "prediction_mode": prediction_mode,
            "chunk_size": chunk_size
        },
        job_name=job_name or f"large_peptide_screening"
    )

# ==============================================================================
# Utility and Analysis Tools
# ==============================================================================

@mcp.tool()
def analyze_netmhcpan_output(
    netmhcpan_output_file: str,
    rank_threshold: float = 2.0
) -> dict:
    """
    Analyze raw NetMHCpan output file and extract binding statistics.

    Parse NetMHCpan results and provide summary statistics. Useful for:
    - Analyzing existing NetMHCpan outputs
    - Post-processing predictions with different thresholds
    - Quality control of prediction runs

    Args:
        netmhcpan_output_file: Path to NetMHCpan output file
        rank_threshold: Rank threshold for weak binder classification (default: 2.0)

    Returns:
        Dictionary with binding statistics and parsed predictions
    """
    try:
        from lib.utils import parse_netmhcpan_results, setup_logger

        logger = setup_logger("netmhcpan_analyzer")
        result = parse_netmhcpan_results(netmhcpan_output_file, logger)

        if result:
            return {"status": "success", **result}
        else:
            return {"status": "error", "error": "Failed to parse NetMHCpan output"}

    except FileNotFoundError as e:
        return {"status": "error", "error": f"Output file not found: {e}"}
    except Exception as e:
        logger.error(f"Output analysis failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def get_server_info() -> dict:
    """
    Get information about the NetMHCpan MCP server and available alleles.

    Returns:
        Dictionary with server version, supported alleles, and example usage
    """
    try:
        from lib.utils import setup_netmhcpan_env

        netmhcpan_path = setup_netmhcpan_env(MCP_ROOT)

        return {
            "status": "success",
            "server_name": "NetMHCpan-4.2 MCP Server",
            "version": "1.0.0",
            "netmhcpan_version": "4.2",
            "netmhcpan_path": str(netmhcpan_path),
            "supported_peptide_lengths": [8, 9, 10, 11, 12, 13, 14],
            "default_allele": "HLA-A02:01",
            "example_alleles": [
                "HLA-A01:01", "HLA-A02:01", "HLA-A03:01", "HLA-A24:02",
                "HLA-B07:02", "HLA-B08:01", "HLA-B27:05", "HLA-B35:01",
                "HLA-C07:02", "HLA-C08:02"
            ],
            "tools": {
                "synchronous": [
                    "predict_peptide_binding",
                    "predict_protein_epitopes",
                    "predict_binding_affinity",
                    "predict_custom_mhc_binding",
                    "export_predictions_to_excel"
                ],
                "batch_submit": [
                    "submit_batch_protein_analysis",
                    "submit_multi_allele_screening",
                    "submit_large_peptide_screening"
                ]
            },
            "example_usage": "Use predict_peptide_binding with input_file 'examples/data/test.pep'"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Could not get server info: {e}",
            "server_name": "NetMHCpan-4.2 MCP Server",
            "version": "1.0.0"
        }

# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    # Set up logging
    logger.info("Starting NetMHCpan-4.2 MCP Server")
    logger.info(f"Scripts directory: {SCRIPTS_DIR}")
    logger.info(f"MCP root: {MCP_ROOT}")

    # Run the server
    mcp.run()