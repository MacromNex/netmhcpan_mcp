"""
Shared utility functions for NetMHCpan MCP scripts.

These functions are extracted and simplified from the original use case scripts
to minimize dependencies and provide reusable functionality.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Union, Optional, Dict, Any, Tuple


def setup_logger(name: str = "netmhcpan", level: str = "INFO") -> logging.Logger:
    """
    Setup a simple logger to replace loguru dependency.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:  # Avoid duplicate handlers
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper()))
    return logger


def setup_netmhcpan_env(mcp_root: Optional[Path] = None) -> Path:
    """
    Setup NetMHCpan environment variables and paths.

    Args:
        mcp_root: Root directory of MCP project (auto-detected if None)

    Returns:
        Path to netMHCpan executable script

    Raises:
        FileNotFoundError: If NetMHCpan directory or script not found
    """
    if mcp_root is None:
        # Auto-detect MCP root from script location
        mcp_root = Path(__file__).parent.parent.parent.absolute()

    netmhcpan_dir = mcp_root / "repo" / "netMHCpan-4.2"

    if not netmhcpan_dir.exists():
        raise FileNotFoundError(f"NetMHCpan directory not found: {netmhcpan_dir}")

    netmhcpan_script = netmhcpan_dir / "netMHCpan"
    if not netmhcpan_script.exists():
        raise FileNotFoundError(f"NetMHCpan script not found: {netmhcpan_script}")

    # Set environment variables
    os.environ['NMHOME'] = str(netmhcpan_dir)
    os.environ['TMPDIR'] = '/tmp'

    return netmhcpan_script


def run_netmhcpan_command(
    cmd: list,
    output_file: Union[str, Path],
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Run a NetMHCpan command and capture output.

    Args:
        cmd: Command list to execute
        output_file: File to write output to
        logger: Logger instance (creates new one if None)

    Returns:
        True if successful, False otherwise
    """
    if logger is None:
        logger = setup_logger()

    logger.info(f"Running NetMHCpan with command: {' '.join(map(str, cmd))}")
    logger.info(f"Output will be saved to: {output_file}")

    try:
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        # Run the command and capture output
        with open(output_file, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

        logger.info(f"Prediction completed successfully!")
        logger.info(f"Results saved to: {output_file}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"NetMHCpan failed with error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False


def parse_netmhcpan_results(
    output_file: Union[str, Path],
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Parse NetMHCpan output and return summary statistics.

    Args:
        output_file: Path to NetMHCpan output file
        logger: Logger instance (creates new one if None)

    Returns:
        Dictionary with parsing results:
        {
            'strong_binders': int,  # count with ≤0.5% rank
            'weak_binders': int,    # count with ≤2.0% rank
            'total_lines': int,     # total result lines processed
            'predictions': list     # list of prediction dicts (optional)
        }
    """
    if logger is None:
        logger = setup_logger()

    try:
        with open(output_file, 'r') as f:
            lines = f.readlines()

        # Find results section (after the header)
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

            # Look for the separator line that indicates results start
            if line.startswith("-----"):
                results_started = True
                continue

            # Process result lines
            if results_started and line:
                parts = line.split()
                if len(parts) >= 11:  # Standard NetMHCpan output has 11+ columns
                    try:
                        total_lines += 1
                        rank = float(parts[9])  # %Rank column (0-based index)

                        # Classification based on rank
                        if rank <= 0.5:
                            strong_binders += 1
                        elif rank <= 2.0:
                            weak_binders += 1

                        # Store prediction details (optional)
                        if len(parts) >= 11:
                            predictions.append({
                                'peptide': parts[2] if len(parts) > 2 else '',
                                'allele': parts[1] if len(parts) > 1 else '',
                                'score': float(parts[6]) if len(parts) > 6 else 0.0,
                                'rank': rank
                            })
                    except (ValueError, IndexError):
                        # Skip malformed lines
                        continue

        result = {
            'strong_binders': strong_binders,
            'weak_binders': weak_binders,
            'total_lines': total_lines,
            'predictions': predictions
        }

        logger.info("=== Prediction Summary ===")
        logger.info(f"Strong binders (≤0.5% rank): {strong_binders}")
        logger.info(f"Weak binders (≤2.0% rank): {weak_binders}")
        logger.info(f"Total lines processed: {total_lines}")

        return result

    except Exception as e:
        logger.warning(f"Could not parse results: {str(e)}")
        return {
            'strong_binders': 0,
            'weak_binders': 0,
            'total_lines': 0,
            'predictions': []
        }


def validate_input_file(file_path: Union[str, Path]) -> bool:
    """
    Validate that input file exists and is readable.

    Args:
        file_path: Path to input file

    Returns:
        True if file is valid, False otherwise
    """
    file_path = Path(file_path)
    return file_path.exists() and file_path.is_file()


def get_mcp_paths(script_path: Optional[Path] = None) -> Dict[str, Path]:
    """
    Get standard MCP project paths.

    Args:
        script_path: Path to current script (auto-detected if None)

    Returns:
        Dictionary with standard paths:
        {
            'mcp_root': Path,
            'scripts': Path,
            'configs': Path,
            'examples': Path,
            'data': Path
        }
    """
    if script_path is None:
        script_path = Path(__file__)

    # Assume script is in scripts/ or scripts/lib/
    if script_path.parent.name == 'lib':
        mcp_root = script_path.parent.parent.parent
    else:
        mcp_root = script_path.parent.parent

    return {
        'mcp_root': mcp_root.absolute(),
        'scripts': mcp_root / 'scripts',
        'configs': mcp_root / 'configs',
        'examples': mcp_root / 'examples',
        'data': mcp_root / 'examples' / 'data'
    }