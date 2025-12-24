#!/usr/bin/env python3
"""
Script: peptide_prediction.py
Description: Predict MHC Class I binding for peptides using NetMHCpan-4.2

Original Use Case: examples/use_case_1_peptide_prediction.py
Dependencies Removed: loguru (replaced with standard logging)

Usage:
    python scripts/peptide_prediction.py --input <input_file> --output <output_file>

Example:
    python scripts/peptide_prediction.py --input examples/data/test.pep --output results/predictions.txt
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import json
import sys
from pathlib import Path
from typing import Union, Optional, Dict, Any

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
    "rank_threshold": None,
    "output_format": "text",
    "log_level": "INFO"
}

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_peptide_prediction(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Predict MHC Class I binding for peptides using NetMHCpan-4.2.

    Args:
        input_file: Path to input peptide file
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
        >>> result = run_peptide_prediction("test.pep", "output.txt", allele="HLA-B07:02")
        >>> print(f"Strong binders: {result['results']['strong_binders']}")
    """
    # Setup
    input_file = Path(input_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Setup logger
    logger = setup_logger("peptide_prediction", config.get("log_level", "INFO"))

    # Validate input
    if not validate_input_file(input_file):
        error_msg = f"Input file not found or not readable: {input_file}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Auto-generate output file if not provided
    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}_predictions.txt"
    else:
        output_file = Path(output_file)

    logger.info(f"Starting peptide prediction for: {input_file}")
    logger.info(f"Allele: {config['allele']}")
    logger.info(f"Output: {output_file}")

    try:
        # Setup NetMHCpan environment
        netmhcpan_script = setup_netmhcpan_env()

        # Build command
        cmd = [
            str(netmhcpan_script),
            "-p",  # Use peptide input
            "-a", config["allele"],  # Specify allele
            str(input_file)
        ]

        # Add rank threshold if specified
        if config.get("rank_threshold") is not None:
            cmd.extend(["-t", str(config["rank_threshold"])])

        # Run prediction
        success = run_netmhcpan_command(cmd, output_file, logger)

        # Parse results
        results = {}
        if success:
            results = parse_netmhcpan_results(output_file, logger)
            logger.info(f"Prediction completed successfully!")
        else:
            logger.error("Prediction failed")

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
        logger.error(f"Prediction failed: {str(e)}")
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
  # Basic peptide prediction
  python scripts/peptide_prediction.py --input examples/data/test.pep

  # Specify output file and allele
  python scripts/peptide_prediction.py --input test.pep --output results.txt --allele HLA-B07:02

  # Filter results by rank threshold
  python scripts/peptide_prediction.py --input test.pep --rank-threshold 2.0

  # Use custom config file
  python scripts/peptide_prediction.py --input test.pep --config configs/custom.json
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input peptide file path'
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
        '--rank-threshold', '-t',
        type=float,
        help='Rank threshold for output filtering (e.g., 2.0 for ≤2%% rank)'
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
    if args.rank_threshold is not None:
        cli_overrides["rank_threshold"] = args.rank_threshold
    if args.log_level != DEFAULT_CONFIG["log_level"]:
        cli_overrides["log_level"] = args.log_level

    # Run prediction
    try:
        result = run_peptide_prediction(
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
                print(f"   Total processed: {results.get('total_lines', 0)}")
            return 0
        else:
            print(f"❌ Failed: {result.get('metadata', {}).get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())