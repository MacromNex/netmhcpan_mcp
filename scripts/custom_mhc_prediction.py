#!/usr/bin/env python3
"""
Script: custom_mhc_prediction.py
Description: Predict MHC Class I binding using custom MHC sequences

Original Use Case: examples/use_case_3_custom_mhc_prediction.py
Dependencies Removed: loguru (replaced with standard logging)

Usage:
    python scripts/custom_mhc_prediction.py --input <peptide_file> --mhc-seq <mhc_fasta> --output <output_file>

Example:
    python scripts/custom_mhc_prediction.py --input examples/data/test.pep --mhc-seq examples/data/B0702.fsa
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
    "mhc_name": "USER_DEF",
    "rank_threshold": None,
    "output_format": "text",
    "log_level": "INFO"
}

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_custom_mhc_prediction(
    input_file: Union[str, Path],
    mhc_sequence_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Predict MHC Class I binding using custom MHC sequences with NetMHCpan-4.2.

    Args:
        input_file: Path to input peptide file
        mhc_sequence_file: Path to custom MHC sequence FASTA file
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
        >>> result = run_custom_mhc_prediction("test.pep", "custom_mhc.fsa", "output.txt")
        >>> print(f"Custom MHC predictions: {result['results']['total_lines']}")
    """
    # Setup
    input_file = Path(input_file)
    mhc_sequence_file = Path(mhc_sequence_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Setup logger
    logger = setup_logger("custom_mhc_prediction", config.get("log_level", "INFO"))

    # Validate inputs
    if not validate_input_file(input_file):
        error_msg = f"Input file not found or not readable: {input_file}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if not validate_input_file(mhc_sequence_file):
        error_msg = f"MHC sequence file not found or not readable: {mhc_sequence_file}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Auto-generate output file if not provided
    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}_custom_mhc_pred.txt"
    else:
        output_file = Path(output_file)

    logger.info(f"Starting custom MHC prediction for: {input_file}")
    logger.info(f"Custom MHC sequence: {mhc_sequence_file}")
    logger.info(f"MHC name: {config['mhc_name']}")
    logger.info(f"Output: {output_file}")

    try:
        # Setup NetMHCpan environment
        netmhcpan_script = setup_netmhcpan_env()

        # Build command
        cmd = [
            str(netmhcpan_script),
            "-p",  # Use peptide input
            "-hlaseq", str(mhc_sequence_file),  # Custom MHC sequence file
            "-hlaid", config["mhc_name"],  # Custom MHC identifier
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
            # Add custom MHC metadata
            results["mhc_name"] = config["mhc_name"]
            results["mhc_sequence_file"] = str(mhc_sequence_file)
            logger.info(f"Custom MHC prediction completed successfully!")
        else:
            logger.error("Custom MHC prediction failed")

        return {
            "success": success,
            "output_file": str(output_file),
            "results": results,
            "metadata": {
                "input_file": str(input_file),
                "mhc_sequence_file": str(mhc_sequence_file),
                "config": config,
                "command": " ".join(cmd)
            }
        }

    except Exception as e:
        logger.error(f"Custom MHC prediction failed: {str(e)}")
        return {
            "success": False,
            "output_file": str(output_file) if output_file else None,
            "results": {},
            "metadata": {
                "input_file": str(input_file),
                "mhc_sequence_file": str(mhc_sequence_file),
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
  # Basic custom MHC prediction
  python scripts/custom_mhc_prediction.py --input examples/data/test.pep --mhc-seq examples/data/B0702.fsa

  # Specify output file and custom MHC name
  python scripts/custom_mhc_prediction.py --input test.pep --mhc-seq custom.fsa --output results.txt --mhc-name MY_HLA

  # Filter results by rank threshold
  python scripts/custom_mhc_prediction.py --input test.pep --mhc-seq custom.fsa --rank-threshold 2.0

  # Use custom config file
  python scripts/custom_mhc_prediction.py --input test.pep --mhc-seq custom.fsa --config configs/custom.json
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input peptide file path'
    )
    parser.add_argument(
        '--mhc-seq', '--mhc',
        required=True,
        help='Custom MHC sequence FASTA file path'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (auto-generated if not specified)'
    )
    parser.add_argument(
        '--mhc-name',
        default=DEFAULT_CONFIG["mhc_name"],
        help=f'Custom MHC identifier name (default: {DEFAULT_CONFIG["mhc_name"]})'
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
    if args.mhc_name != DEFAULT_CONFIG["mhc_name"]:
        cli_overrides["mhc_name"] = args.mhc_name
    if args.rank_threshold is not None:
        cli_overrides["rank_threshold"] = args.rank_threshold
    if args.log_level != DEFAULT_CONFIG["log_level"]:
        cli_overrides["log_level"] = args.log_level

    # Run prediction
    try:
        result = run_custom_mhc_prediction(
            input_file=args.input,
            mhc_sequence_file=getattr(args, 'mhc_seq'),
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
                print(f"   MHC name: {results.get('mhc_name', 'N/A')}")
            return 0
        else:
            print(f"❌ Failed: {result.get('metadata', {}).get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())