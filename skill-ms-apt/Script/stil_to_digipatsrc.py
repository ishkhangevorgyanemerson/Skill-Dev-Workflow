#!/usr/bin/env python3
"""
STIL to Digipatsrc Converter

A command-line tool to convert Standard Test Interface Language (STIL) files
to digipatsrc format compatible with NI Semiconductor Test System (STS).

Usage:
    python stil_to_digipatsrc.py input.stil output.digipatsrc [options]

Author: AI Assistant
Created: November 2024
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from stil_parser import STILParser, STILData
from digipatsrc_generator import DigipatsrcGenerator


def validate_input_file(filepath: str) -> bool:
    """Validate that the input STIL file exists and is readable."""
    if not os.path.exists(filepath):
        print(f"Error: Input file '{filepath}' does not exist.")
        return False
    
    if not os.path.isfile(filepath):
        print(f"Error: '{filepath}' is not a file.")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first line to check if it's a STIL file
            first_lines = f.read(1000)
            if 'STIL' not in first_lines:
                print(f"Warning: '{filepath}' may not be a valid STIL file (no STIL header found).")
    except Exception as e:
        print(f"Error: Cannot read input file '{filepath}': {e}")
        return False
    
    return True


def create_output_directory(filepath: str) -> bool:
    """Create output directory if it doesn't exist."""
    output_dir = os.path.dirname(filepath)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
            return True
        except Exception as e:
            print(f"Error: Cannot create output directory '{output_dir}': {e}")
            return False
    return True


def convert_stil_to_digipatsrc(input_file: str, output_file: str, 
                              target_tester: str = "NiSTS-6570",
                              pinmap_file: Optional[str] = None,
                              verbose: bool = False) -> bool:
    """
    Convert a STIL file to digipatsrc format.
    
    Args:
        input_file: Path to the input STIL file
        output_file: Path to the output digipatsrc file
        target_tester: Target tester name
        pinmap_file: Path to pinmap CSV file for signal mapping (required)
        verbose: Enable verbose output
        
    Returns:
        True if conversion was successful, False otherwise
    """
    try:
        if not pinmap_file:
            raise ValueError("Pinmap file is required for signal mapping. "
                           "Please provide a pinmap CSV file using --pinmap option.")
        
        if verbose:
            print(f"Parsing STIL file: {input_file}")
        
        # Parse the STIL file
        parser = STILParser()
        stil_data = parser.parse_file(input_file)
        
        if verbose:
            print(f"Found {len(stil_data.signals)} signals")
            print(f"Found {len(stil_data.signal_groups)} signal groups")
            print(f"Found {len(stil_data.waveform_tables)} waveform tables")
            print(f"Found {len(stil_data.scan_chains)} scan chains")
            print(f"Found {len(stil_data.patterns)} patterns")
            print(f"Using pinmap file: {pinmap_file}")
        
        if verbose:
            print(f"Generating digipatsrc file: {output_file}")
        
        # Generate the digipatsrc file
        generator = DigipatsrcGenerator(pinmap_file=pinmap_file)
        generator.generate_file(
            stil_data, 
            output_file,
            source_file=input_file,
            target_tester=target_tester
        )
        
        if verbose:
            print("Conversion completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main entry point for the converter."""
    parser = argparse.ArgumentParser(
        description="Convert STIL files to digipatsrc format for NI STS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic conversion
    python stil_to_digipatsrc.py input.stil output.digipatsrc
    
    # Use pinmap file for signal mapping
    python stil_to_digipatsrc.py input.stil output.digipatsrc --pinmap Pinmap.csv
    
    # Specify target tester
    python stil_to_digipatsrc.py input.stil output.digipatsrc --tester "NiSTS-6571"
    
    # Enable verbose output
    python stil_to_digipatsrc.py input.stil output.digipatsrc -v
    
    # Auto-generate output filename
    python stil_to_digipatsrc.py input.stil --auto-output
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Path to the input STIL file'
    )
    
    parser.add_argument(
        'output_file',
        nargs='?',
        help='Path to the output digipatsrc file (optional if --auto-output is used)'
    )
    
    parser.add_argument(
        '--pinmap', '-p',
        required=True,
        help='Path to pinmap CSV file for signal mapping (required)'
    )
    
    parser.add_argument(
        '--tester', '-t',
        default='NiSTS-6570',
        help='Target tester name (default: NiSTS-6570)'
    )
    
    parser.add_argument(
        '--auto-output', '-a',
        action='store_true',
        help='Automatically generate output filename based on input filename'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Overwrite output file if it exists'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='STIL to Digipatsrc Converter v1.0'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.output_file and not args.auto_output:
        print("Error: Either provide output_file or use --auto-output")
        sys.exit(1)
    
    # Generate output filename if auto-output is requested
    if args.auto_output:
        input_path = Path(args.input_file)
        output_path = input_path.with_suffix('.digipatsrc')
        args.output_file = str(output_path)
        if args.verbose:
            print(f"Auto-generated output filename: {args.output_file}")
    
    # Validate input file
    if not validate_input_file(args.input_file):
        sys.exit(1)
    
    # Validate pinmap file - now required
    if not os.path.exists(args.pinmap):
        print(f"Error: Required pinmap file '{args.pinmap}' does not exist.")
        sys.exit(1)
    
    # Check if output file exists
    if os.path.exists(args.output_file) and not args.force:
        response = input(f"Output file '{args.output_file}' already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Conversion cancelled.")
            sys.exit(0)
    
    # Create output directory if needed
    if not create_output_directory(args.output_file):
        sys.exit(1)
    
    if args.verbose:
        print(f"Converting '{args.input_file}' to '{args.output_file}'")
        print(f"Target tester: {args.tester}")
        print(f"Using pinmap: {args.pinmap}")
    
    success = convert_stil_to_digipatsrc(
        args.input_file,
        args.output_file,
        args.tester,
        args.pinmap,
        args.verbose
    )
    
    if success:
        file_size = os.path.getsize(args.output_file)
        print(f"Conversion completed successfully!")
        print(f"Output file: {args.output_file} ({file_size:,} bytes)")
        sys.exit(0)
    else:
        print("Conversion failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()