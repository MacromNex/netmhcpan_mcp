#!/usr/bin/env python3
"""
Script: binding_affinity_prediction.py
Description: Predict MHC Class I binding affinities with both EL and BA scores

Original Use Case: examples/use_case_4_binding_affinity_prediction.py
Dependencies Removed: loguru (replaced with standard logging)

Usage:
    python scripts/binding_affinity_prediction.py --input <peptide_file> --output <output_file>

Example:
    python scripts/binding_affinity_prediction.py --input examples/data/test.pep --allele HLA-A02:01
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
    "prediction_mode": "both",  # "EL", "BA", or "both"
    "rank_threshold": None,
    "output_format": "text",
    "log_level": "INFO"
}

# ==============================================================================
# Enhanced Parsing Function for Binding Affinity Results
# ==============================================================================
def parse_binding_affinity_results(
    output_file: Union[str, Path],
    logger: Optional[object] = None
) -> Dict[str, Any]:
    """
    Parse NetMHCpan output specifically for binding affinity predictions.

    Enhanced version that handles both EL and BA prediction columns.

    Args:
        output_file: Path to NetMHCpan output file
        logger: Logger instance

    Returns:
        Dictionary with detailed binding affinity results
    """
    if logger is None:
        from lib.utils import setup_logger
        logger = setup_logger()

    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()

        results_started = False
        strong_binders = 0
        weak_binders = 0
        total_lines = 0
        predictions = []

        for line in lines:
            line = line.strip()

            # Skip comment lines
            if line.startswith('#'):
                continue

            # Look for separator line
            if line.startswith("-----"):
                results_started = True
                continue

            # Process result lines
            if results_started and line:
                parts = line.split()
                if len(parts) >= 11:  # Standard output with EL+BA has 11+ columns
                    try:
                        total_lines += 1

                        # Extract key values (adjust indices based on NetMHCpan output format)
                        peptide = parts[2] if len(parts) > 2 else ''
                        allele = parts[1] if len(parts) > 1 else ''
                        el_score = float(parts[6]) if len(parts) > 6 else 0.0
                        el_rank = float(parts[7]) if len(parts) > 7 else 100.0
                        ba_score = float(parts[8]) if len(parts) > 8 else 0.0
                        ba_rank = float(parts[9]) if len(parts) > 9 else 100.0

                        # Use EL rank for classification (more commonly used)
                        if el_rank <= 0.5:
                            strong_binders += 1
                        elif el_rank <= 2.0:
                            weak_binders += 1

                        # Store detailed prediction
                        predictions.append({
                            'peptide': peptide,
                            'allele': allele,
                            'el_score': el_score,
                            'el_rank': el_rank,
                            'ba_score': ba_score,  # IC50 binding affinity
                            'ba_rank': ba_rank,
                            'strong_binder': el_rank <= 0.5,
                            'weak_binder': 0.5 < el_rank <= 2.0
                        })

                    except (ValueError, IndexError):
                        # Skip malformed lines
                        continue

        result = {
            'strong_binders': strong_binders,
            'weak_binders': weak_binders,
            'total_lines': total_lines,
            'predictions': predictions,
            'has_binding_affinities': True
        }

        # Enhanced summary logging for binding affinities
        logger.info("=== Binding Affinity Prediction Summary ===")
        logger.info(f"Strong binders (≤0.5% EL rank): {strong_binders}")
        logger.info(f"Weak binders (≤2.0% EL rank): {weak_binders}")
        logger.info(f"Total peptides analyzed: {total_lines}")

        # Show top binding affinities if available
        if predictions:
            sorted_preds = sorted(predictions, key=lambda x: x['ba_score'])[:3]
            logger.info("Top binding affinities (IC50 nM):")
            for i, pred in enumerate(sorted_preds, 1):
                logger.info(f"  {i}. {pred['peptide']}: {pred['ba_score']:.2f} nM (EL: {pred['el_rank']:.3f}%)")

        return result

    except Exception as e:
        logger.warning(f"Could not parse binding affinity results: {str(e)}")
        return {
            'strong_binders': 0,
            'weak_binders': 0,
            'total_lines': 0,
            'predictions': [],
            'has_binding_affinities': False
        }

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_binding_affinity_prediction(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Predict MHC Class I binding affinities with both EL and BA scores using NetMHCpan-4.2.

    Args:
        input_file: Path to input peptide file
        output_file: Path to save output (optional, auto-generated if not provided)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - success: Boolean indicating if prediction succeeded
            - output_file: Path to output file
            - results: Parsed results summary with binding affinities
            - metadata: Execution metadata

    Example:
        >>> result = run_binding_affinity_prediction("test.pep", "output.txt", allele="HLA-B07:02")
        >>> print(f"Best IC50: {min(p['ba_score'] for p in result['results']['predictions'])}")
    """
    # Setup
    input_file = Path(input_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Setup logger
    logger = setup_logger("binding_affinity", config.get("log_level", "INFO"))

    # Validate input
    if not validate_input_file(input_file):
        error_msg = f"Input file not found or not readable: {input_file}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Auto-generate output file if not provided
    if output_file is None:
        mode_suffix = config["prediction_mode"].lower()
        output_file = input_file.parent / f"{input_file.stem}_binding_{mode_suffix}.txt"
    else:
        output_file = Path(output_file)

    logger.info(f"Starting binding affinity prediction for: {input_file}")
    logger.info(f"Allele: {config['allele']}")
    logger.info(f"Prediction mode: {config['prediction_mode']}")
    logger.info(f"Output: {output_file}")

    try:
        # Setup NetMHCpan environment
        netmhcpan_script = setup_netmhcpan_env()

        # Build command - enable both EL and BA predictions
        cmd = [
            str(netmhcpan_script),
            "-p",  # Use peptide input
            "-a", config["allele"],  # Specify allele
            str(input_file)
        ]

        # Add prediction mode (EL+BA gives most comprehensive results)
        if config["prediction_mode"].lower() == "both":
            cmd.extend(["-BA", "-EL"])  # Both binding affinity and eluted ligand
        elif config["prediction_mode"].upper() == "BA":
            cmd.append("-BA")  # Binding affinity only
        elif config["prediction_mode"].upper() == "EL":
            cmd.append("-EL")  # Eluted ligand only

        # Add rank threshold if specified
        if config.get("rank_threshold") is not None:
            cmd.extend(["-t", str(config["rank_threshold"])])

        # Run prediction
        success = run_netmhcpan_command(cmd, output_file, logger)

        # Parse results with enhanced binding affinity parsing
        results = {}
        if success:
            results = parse_binding_affinity_results(output_file, logger)
            results["prediction_mode"] = config["prediction_mode"]
            logger.info(f"Binding affinity prediction completed successfully!")
        else:
            logger.error("Binding affinity prediction failed")

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
        logger.error(f"Binding affinity prediction failed: {str(e)}")
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
  # Basic binding affinity prediction (both EL and BA)
  python scripts/binding_affinity_prediction.py --input examples/data/test.pep

  # Binding affinity only
  python scripts/binding_affinity_prediction.py --input test.pep --mode BA

  # Different allele with rank filtering
  python scripts/binding_affinity_prediction.py --input test.pep --allele HLA-B07:02 --rank-threshold 2.0

  # Use custom config file
  python scripts/binding_affinity_prediction.py --input test.pep --config configs/affinity.json
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
        '--mode', '-m',
        choices=['EL', 'BA', 'both'],
        default=DEFAULT_CONFIG["prediction_mode"],
        help=f'Prediction mode: EL (eluted ligand), BA (binding affinity), or both (default: {DEFAULT_CONFIG["prediction_mode"]})'
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
    if args.mode != DEFAULT_CONFIG["prediction_mode"]:
        cli_overrides["prediction_mode"] = args.mode
    if args.rank_threshold is not None:
        cli_overrides["rank_threshold"] = args.rank_threshold
    if args.log_level != DEFAULT_CONFIG["log_level"]:
        cli_overrides["log_level"] = args.log_level

    # Run prediction
    try:
        result = run_binding_affinity_prediction(
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
                print(f"   Prediction mode: {results.get('prediction_mode', 'N/A')}")

                # Show best binding affinity if available
                predictions = results.get('predictions', [])
                if predictions:
                    best_ic50 = min(p['ba_score'] for p in predictions)
                    print(f"   Best IC50: {best_ic50:.2f} nM")
            return 0
        else:
            print(f"❌ Failed: {result.get('metadata', {}).get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())