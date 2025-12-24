#!/usr/bin/env python3
"""
Script: excel_export.py
Description: Predict MHC Class I binding for multiple alleles with Excel export

Original Use Case: examples/use_case_5_excel_export.py
Dependencies Removed: loguru (replaced with standard logging)
Dependencies Added: pandas (for Excel export functionality)

Usage:
    python scripts/excel_export.py --input <peptide_file> --alleles <allele_list> --excel-file <output.xls>

Example:
    python scripts/excel_export.py --input examples/data/test.pep --alleles HLA-A01:01,HLA-A02:01 --excel-file predictions.xls
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import json
import sys
from pathlib import Path
from typing import Union, Optional, Dict, Any, List

# Optional pandas import for Excel functionality
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

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
    "alleles": ["HLA-A02:01"],
    "excel_format": "tab_delimited",  # "tab_delimited" or "xlsx" (requires openpyxl)
    "rank_threshold": None,
    "output_format": "text",
    "log_level": "INFO"
}

# ==============================================================================
# Excel Export Functions
# ==============================================================================
def create_excel_compatible_output(
    results_list: List[Dict[str, Any]],
    excel_file: Path,
    logger: Optional[object] = None
) -> bool:
    """
    Create Excel-compatible output from NetMHCpan results.

    Args:
        results_list: List of result dictionaries from multiple alleles
        excel_file: Path to output Excel file
        logger: Logger instance

    Returns:
        True if export successful, False otherwise
    """
    if logger is None:
        from lib.utils import setup_logger
        logger = setup_logger()

    try:
        # Collect all predictions from all alleles
        all_predictions = []
        for result in results_list:
            allele_name = result.get('allele', 'Unknown')
            predictions = result.get('results', {}).get('predictions', [])

            for pred in predictions:
                # Add allele info to each prediction
                pred_copy = pred.copy()
                pred_copy['allele'] = allele_name
                all_predictions.append(pred_copy)

        if not all_predictions:
            logger.warning("No predictions found for Excel export")
            return False

        # Create Excel-compatible format
        if PANDAS_AVAILABLE and excel_file.suffix.lower() in ['.xlsx', '.xls']:
            # Use pandas for true Excel format
            df = pd.DataFrame(all_predictions)

            # Reorder columns for better readability
            preferred_order = ['peptide', 'allele', 'score', 'rank']
            available_cols = [col for col in preferred_order if col in df.columns]
            other_cols = [col for col in df.columns if col not in preferred_order]
            df = df[available_cols + other_cols]

            # Save as Excel
            df.to_excel(str(excel_file), index=False, engine='openpyxl' if excel_file.suffix == '.xlsx' else None)
            logger.info(f"Excel file exported using pandas: {excel_file}")

        else:
            # Create tab-delimited format (Excel compatible)
            with open(excel_file, 'w') as f:
                if all_predictions:
                    # Write header
                    headers = list(all_predictions[0].keys())
                    f.write('\t'.join(headers) + '\n')

                    # Write data rows
                    for pred in all_predictions:
                        values = [str(pred.get(h, '')) for h in headers]
                        f.write('\t'.join(values) + '\n')

            logger.info(f"Tab-delimited Excel-compatible file created: {excel_file}")

        return True

    except Exception as e:
        logger.error(f"Excel export failed: {str(e)}")
        return False

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
def run_excel_export(
    input_file: Union[str, Path],
    alleles: Union[str, List[str]],
    excel_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Predict MHC Class I binding for multiple alleles with Excel export using NetMHCpan-4.2.

    Args:
        input_file: Path to input peptide file
        alleles: HLA alleles (string "A,B,C" or list ["A", "B", "C"])
        excel_file: Path to Excel output file
        output_file: Path to text output (optional, auto-generated if not provided)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - success: Boolean indicating if prediction succeeded
            - output_file: Path to text output file
            - excel_file: Path to Excel output file
            - results: Combined results from all alleles
            - metadata: Execution metadata

    Example:
        >>> result = run_excel_export("test.pep", ["HLA-A01:01", "HLA-A02:01"], "output.xls")
        >>> print(f"Excel file: {result['excel_file']}")
    """
    # Setup
    input_file = Path(input_file)
    excel_file = Path(excel_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Parse alleles
    if isinstance(alleles, str):
        alleles_list = [a.strip() for a in alleles.split(',')]
    else:
        alleles_list = list(alleles)

    # Setup logger
    logger = setup_logger("excel_export", config.get("log_level", "INFO"))

    # Validate input
    if not validate_input_file(input_file):
        error_msg = f"Input file not found or not readable: {input_file}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Check pandas availability for Excel features
    if not PANDAS_AVAILABLE and excel_file.suffix.lower() in ['.xlsx']:
        logger.warning("pandas not available - Excel export will use tab-delimited format")

    # Auto-generate text output file if not provided
    if output_file is None:
        alleles_suffix = "_".join([a.replace(':', '').replace('*', '') for a in alleles_list[:2]])
        output_file = input_file.parent / f"{input_file.stem}_multi_{alleles_suffix}.txt"
    else:
        output_file = Path(output_file)

    logger.info(f"Starting multi-allele prediction for: {input_file}")
    logger.info(f"Alleles: {', '.join(alleles_list)}")
    logger.info(f"Text output: {output_file}")
    logger.info(f"Excel output: {excel_file}")

    try:
        # Setup NetMHCpan environment
        netmhcpan_script = setup_netmhcpan_env()

        # Process each allele and collect results
        all_results = []
        combined_predictions = []
        success_count = 0

        # Create temporary directory for individual allele results
        temp_dir = output_file.parent / "temp_allele_results"
        temp_dir.mkdir(exist_ok=True)

        for i, allele in enumerate(alleles_list):
            logger.info(f"Processing allele {i+1}/{len(alleles_list)}: {allele}")

            # Create temporary output for this allele
            temp_output = temp_dir / f"allele_{allele.replace(':', '_').replace('*', '_')}.txt"

            # Build command for this allele
            cmd = [
                str(netmhcpan_script),
                "-p",  # Use peptide input
                "-a", allele,  # Specify allele
                str(input_file)
            ]

            # Add rank threshold if specified
            if config.get("rank_threshold") is not None:
                cmd.extend(["-t", str(config["rank_threshold"])])

            # Run prediction for this allele
            allele_success = run_netmhcpan_command(cmd, temp_output, logger)

            if allele_success:
                # Parse results for this allele
                allele_results = parse_netmhcpan_results(temp_output, logger)
                allele_results["allele"] = allele
                all_results.append({
                    "allele": allele,
                    "results": allele_results,
                    "success": True
                })

                # Add to combined predictions
                for pred in allele_results.get('predictions', []):
                    pred_copy = pred.copy()
                    pred_copy['source_allele'] = allele
                    combined_predictions.append(pred_copy)

                success_count += 1
                logger.info(f"  ✓ {allele}: {allele_results.get('strong_binders', 0)} strong, {allele_results.get('weak_binders', 0)} weak binders")
            else:
                logger.error(f"  ✗ {allele}: Prediction failed")
                all_results.append({
                    "allele": allele,
                    "results": {},
                    "success": False
                })

        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Create combined text output
        with open(output_file, 'w') as f:
            f.write(f"# Multi-allele NetMHCpan prediction results\n")
            f.write(f"# Input file: {input_file}\n")
            f.write(f"# Alleles: {', '.join(alleles_list)}\n")
            f.write(f"# Successful predictions: {success_count}/{len(alleles_list)}\n")
            f.write("# \n")

            for result in all_results:
                f.write(f"\n## Allele: {result['allele']}\n")
                if result['success']:
                    res = result['results']
                    f.write(f"Strong binders: {res.get('strong_binders', 0)}\n")
                    f.write(f"Weak binders: {res.get('weak_binders', 0)}\n")
                    f.write(f"Total processed: {res.get('total_lines', 0)}\n")
                else:
                    f.write("FAILED\n")

        # Create Excel export
        excel_success = create_excel_compatible_output(all_results, excel_file, logger)

        # Summary
        overall_success = success_count > 0 and excel_success

        if overall_success:
            logger.info(f"Multi-allele prediction completed successfully!")
            logger.info(f"Successful alleles: {success_count}/{len(alleles_list)}")
        else:
            logger.error("Multi-allele prediction had failures")

        return {
            "success": overall_success,
            "output_file": str(output_file),
            "excel_file": str(excel_file),
            "results": {
                "alleles_processed": len(alleles_list),
                "successful_alleles": success_count,
                "total_predictions": len(combined_predictions),
                "per_allele_results": all_results,
                "combined_predictions": combined_predictions
            },
            "metadata": {
                "input_file": str(input_file),
                "alleles": alleles_list,
                "config": config,
                "excel_success": excel_success
            }
        }

    except Exception as e:
        logger.error(f"Multi-allele prediction failed: {str(e)}")
        return {
            "success": False,
            "output_file": str(output_file) if output_file else None,
            "excel_file": str(excel_file),
            "results": {},
            "metadata": {
                "input_file": str(input_file),
                "alleles": alleles_list if 'alleles_list' in locals() else [],
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
  # Basic multi-allele prediction with Excel export
  python scripts/excel_export.py --input examples/data/test.pep --alleles HLA-A01:01,HLA-A02:01 --excel-file results.xls

  # Multiple alleles with custom output files
  python scripts/excel_export.py --input test.pep --alleles HLA-A01:01,HLA-A02:01,HLA-B07:02 --output summary.txt --excel-file detailed.xlsx

  # Filter by rank threshold
  python scripts/excel_export.py --input test.pep --alleles HLA-A02:01,HLA-B07:02 --excel-file filtered.xls --rank-threshold 2.0

  # Use config file
  python scripts/excel_export.py --input test.pep --alleles HLA-A02:01 --excel-file results.xls --config configs/multi.json

Note: For .xlsx files, install pandas and openpyxl: pip install pandas openpyxl
      Otherwise, tab-delimited Excel-compatible format will be used.
        """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input peptide file path'
    )
    parser.add_argument(
        '--alleles', '-a',
        required=True,
        help='Comma-separated list of HLA alleles (e.g., "HLA-A01:01,HLA-A02:01")'
    )
    parser.add_argument(
        '--excel-file', '--excel',
        required=True,
        help='Excel output file path (.xls or .xlsx)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Text output file path (auto-generated if not specified)'
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

    # Check pandas availability and warn user
    if not PANDAS_AVAILABLE:
        print("⚠️  Warning: pandas not available. Install with 'pip install pandas openpyxl' for full Excel support.")
        print("   Tab-delimited Excel-compatible format will be used instead.")

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with command line arguments
    cli_overrides = {}
    if args.rank_threshold is not None:
        cli_overrides["rank_threshold"] = args.rank_threshold
    if args.log_level != DEFAULT_CONFIG["log_level"]:
        cli_overrides["log_level"] = args.log_level

    # Run prediction
    try:
        result = run_excel_export(
            input_file=args.input,
            alleles=args.alleles,
            excel_file=args.excel_file,
            output_file=args.output,
            config=config,
            **cli_overrides
        )

        if result["success"]:
            print(f"✅ Success!")
            print(f"   Text output: {result['output_file']}")
            print(f"   Excel output: {result['excel_file']}")

            results = result.get("results", {})
            if results:
                print(f"   Alleles processed: {results.get('alleles_processed', 0)}")
                print(f"   Successful alleles: {results.get('successful_alleles', 0)}")
                print(f"   Total predictions: {results.get('total_predictions', 0)}")
            return 0
        else:
            print(f"❌ Failed: {result.get('metadata', {}).get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())