#!/usr/bin/env python3
"""
Script: protein_prediction.py
Description: Predict MHC Class I binding epitopes from protein FASTA sequences

Original Use Case: examples/use_case_2_protein_prediction.py
Dependencies Removed: loguru (replaced with standard logging)

Usage:
    python scripts/protein_prediction.py --input <fasta_file> --output <output_file>

Example:
    python scripts/protein_prediction.py --input examples/data/test.fsa --length 9 --allele HLA-A02:01
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import json
import sys
from pathlib import Path
from typing import Union, Optional, Dict, Any, List

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from lib.utils import (
    setup_logger, setup_netmhcpan_env, run_netmhcpan_command,
    parse_netmhcpan_results, validate_input_file, get_mcp_paths
)

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "allele": "HLA-A02:01",
    "peptide_length": "9",
    "rank_threshold": None,
    "sort_output": False,
    "output_format": "text",
    "log_level": "INFO"
}

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_protein_prediction(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Predict MHC Class I binding epitopes from protein FASTA sequences using NetMHCpan-4.2.

    Scans protein sequences for potential binding peptides of specified lengths.

    Args:
        input_file: Path to input FASTA file
        output_file: Path to save output (optional, auto-generated if not provided)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - success: Boolean indicating if prediction succeeded
            - output_file: Path to output file
            - results: Parsed results summary
            - metadata: Execution metadata

    Example:
        >>> result = run_protein_prediction("protein.fsa", "output.txt", peptide_length="8,9,10")
        >>> print(f"Total peptides: {result['results']['total_lines']}")
    """
    # Setup
    input_file = Path(input_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Setup logger
    logger = setup_logger("protein_prediction", config.get("log_level", "INFO"))

    # Validate input
    if not validate_input_file(input_file):
        error_msg = f"Input file not found or not readable: {input_file}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Auto-generate output file if not provided
    if output_file is None:
        length_suffix = config["peptide_length"].replace(",", "_")
        output_file = input_file.parent / f"{input_file.stem}_protein_pred_{length_suffix}mer.txt"
    else:
        output_file = Path(output_file)

    logger.info(f"Starting protein prediction for: {input_file}")
    logger.info(f"Allele: {config['allele']}")
    logger.info(f"Peptide lengths: {config['peptide_length']}")
    logger.info(f"Output: {output_file}")

    try:
        # Setup NetMHCpan environment
        netmhcpan_script = setup_netmhcpan_env()

        # Build command
        cmd = [
            str(netmhcpan_script),
            "-f", str(input_file),  # FASTA input
            "-a", config["allele"],  # Specify allele
            "-l", config["peptide_length"]  # Peptide lengths
        ]

        # Add optional parameters
        if config.get("rank_threshold") is not None:
            cmd.extend(["-t", str(config["rank_threshold"])])

        if config.get("sort_output"):
            cmd.append("-s")  # Sort by descending affinity

        # Run prediction
        success = run_netmhcpan_command(cmd, output_file, logger)

        # Parse results
        results = {}
        if success:
            results = parse_netmhcpan_results(output_file, logger)
            # Add protein-specific metadata
            results["peptide_lengths"] = config["peptide_length"]
            logger.info(f"Protein prediction completed successfully!")
        else:
            logger.error("Protein prediction failed")

        return {
            "success": success,
            "output_file": str(output_file),
            "results": results,
            "metadata": {
                "input_file": str(input_file),
                "config": config,
                "command": " ".join(cmd)
            }
        }

    except Exception as e:
        logger.error(f"Protein prediction failed: {str(e)}")
        return {
            "success": False,
            "output_file": str(output_file) if output_file else None,
            "results": {},
            "metadata": {
                "input_file": str(input_file),
                "config": config,
                "error": str(e)
            }
        }

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic protein prediction (9-mers)
  python scripts/protein_prediction.py --input examples/data/test.fsa

  # Multiple peptide lengths
  python scripts/protein_prediction.py --input protein.fsa --length 8,9,10

  # Different allele with sorted output
  python scripts/protein_prediction.py --input protein.fsa --allele HLA-B07:02 --sort

  # Filter by rank threshold
  python scripts/protein_prediction.py --input protein.fsa --rank-threshold 2.0

  # Use custom config
  python scripts/protein_prediction.py --input protein.fsa --config configs/protein.json
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input FASTA file path'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (auto-generated if not specified)'
    )
    parser.add_argument(
        '--allele', '-a',
        default=DEFAULT_CONFIG["allele"],
        help=f'HLA allele for prediction (default: {DEFAULT_CONFIG["allele"]})'
    )
    parser.add_argument(
        '--length', '-l',
        default=DEFAULT_CONFIG["peptide_length"],
        help=f'Peptide lengths (comma-separated, e.g., "8,9,10") (default: {DEFAULT_CONFIG["peptide_length"]})'
    )
    parser.add_argument(
        '--rank-threshold', '-t',
        type=float,
        help='Rank threshold for output filtering (e.g., 2.0 for ≤2%% rank)'
    )
    parser.add_argument(
        '--sort', '-s',
        action='store_true',
        help='Sort output by descending affinity'
    )
    parser.add_argument(
        '--config', '-c',
        help='Config file (JSON)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=DEFAULT_CONFIG["log_level"],
        help='Logging level'
    )

    args = parser.parse_args()

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with command line arguments
    cli_overrides = {}
    if args.allele != DEFAULT_CONFIG["allele"]:
        cli_overrides["allele"] = args.allele
    if args.length != DEFAULT_CONFIG["peptide_length"]:
        cli_overrides["peptide_length"] = args.length
    if args.rank_threshold is not None:
        cli_overrides["rank_threshold"] = args.rank_threshold
    if args.sort:
        cli_overrides["sort_output"] = True
    if args.log_level != DEFAULT_CONFIG["log_level"]:
        cli_overrides["log_level"] = args.log_level

    # Run prediction
    try:
        result = run_protein_prediction(
            input_file=args.input,
            output_file=args.output,
            config=config,
            **cli_overrides
        )

        if result["success"]:
            print(f"✅ Success: {result['output_file']}")
            results = result.get("results", {})
            if results:
                print(f"   Strong binders: {results.get('strong_binders', 0)}")
                print(f"   Weak binders: {results.get('weak_binders', 0)}")
                print(f"   Total peptides: {results.get('total_lines', 0)}")
                print(f"   Peptide lengths: {results.get('peptide_lengths', 'N/A')}")
            return 0
        else:
            print(f"❌ Failed: {result.get('metadata', {}).get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())