"""
Digipatsrc Generator - Generate digipatsrc files from parsed STIL data.

This module provides functionality to generate digipatsrc format files
compatible with NI Semiconductor Test System (STS) from STIL data.
"""

from typing import Dict, List, TextIO, Optional
from datetime import datetime
import re
import csv
from pathlib import Path
from stil_parser import STILData, Signal, Pattern, SignalDirection, STILParser
import os


class DigipatsrcGenerator:
    """Generator for digipatsrc format files."""
    
    def __init__(self, pinmap_file: Optional[str] = None):
        self.signal_mapping = {}  # Maps STIL signals to tester pins
        self.timeset_mapping = {}  # Maps STIL timing to digipatsrc timesets
        self.pinmap_file = pinmap_file
        self.pinmap_data = {}  # Will store pinmap information
        
        if pinmap_file:
            self._load_pinmap(pinmap_file)
            
    def _load_pinmap(self, pinmap_file: str) -> None:
        """Load pinmap file and create signal mappings. Supports both .csv and plain text formats."""
        try:
            with open(pinmap_file, 'r', encoding='utf-8') as file:
                all_lines = file.readlines()
                
                # Find the header line (starts with # and contains column names)
                header_line = None
                data_lines = []
                
                for line in all_lines:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    
                    # Check if this is the header line (starts with # and contains "Group" or "Order")
                    if stripped.startswith('#') and ('Group' in stripped or 'Order' in stripped):
                        # Remove the leading # and use as header
                        header_line = stripped[1:].strip()
                    elif not stripped.startswith('#'):
                        # This is a data line
                        data_lines.append(line)
                
                if not header_line:
                    raise ValueError("Pinmap file does not contain a valid header line")
                
                if not data_lines:
                    raise ValueError("Pinmap file contains no data after removing comments and empty lines")
                
                # Try to determine if it's CSV format or plain text
                is_csv_format = ',' in header_line
                
                if is_csv_format:
                    # Parse as CSV data - prepend header to data lines
                    all_csv_lines = [header_line] + data_lines
                    csv_reader = csv.DictReader(all_csv_lines)
                    for row in csv_reader:
                        # Strip spaces from keys and values for clean matching
                        cleaned_row = {k.strip(): v.strip() if v else v for k, v in row.items()}
                        self._process_pinmap_row(cleaned_row)
                else:
                    # Parse as plain text format
                    headers = header_line.strip().split()
                    for line in data_lines:
                        if line.strip():
                            values = line.strip().split()
                            # Create a dictionary mapping headers to values
                            row = {}
                            for i, header in enumerate(headers):
                                if i < len(values):
                                    row[header] = values[i]
                                else:
                                    row[header] = ''
                            self._process_pinmap_row(row)
                        
        except Exception as e:
            print(f"Warning: Could not load pinmap file '{pinmap_file}': {e}")
            print("Pinmap file is required for signal mapping. Cannot proceed without it.")
            raise ValueError(f"Failed to load required pinmap file '{pinmap_file}': {e}")

    def _process_pinmap_row(self, row: dict) -> None:
        """Process a single row from the pinmap data."""
        # Handle different possible column names for flexibility
        group_name_keys = ['Group/Alias Name', 'Group_Alias_Name', 'GroupName', 'Group', 'TesterPin', 'Pin']
        signal_name_keys = ['Signal Name', 'Signal_Name', 'SignalName', 'Signal']
        original_signal_keys = ['Original Signal Name (without bus index values)', 'Original_Signal_Name', 'OriginalSignal', 'STILSignal', 'Original']
        direction_keys = ['Direction', 'Dir', 'Type']
        is_scan_keys = ['Is Scan?', 'Is_Scan', 'IsScan', 'Scan']
        remove_keys = ['Remove?', 'Remove', 'Skip', 'Exclude']
        
        # Extract values using flexible key matching
        group_name = self._get_value_by_keys(row, group_name_keys, '').strip()
        signal_name = self._get_value_by_keys(row, signal_name_keys, '').strip()
        original_signal = self._get_value_by_keys(row, original_signal_keys, '').strip()
        direction = self._get_value_by_keys(row, direction_keys, '').strip()
        is_scan = self._get_value_by_keys(row, is_scan_keys, '').strip().lower() == 'true'
        remove = self._get_value_by_keys(row, remove_keys, '').strip().lower() == 'true'
        
        # Use original signal name as key, fallback to group name if not available
        signal_key = original_signal if original_signal else group_name
        
        # Only include signals that are not marked for removal and have a valid key
        if not remove and signal_key:
            if "LATCH" not in signal_key:
                self.pinmap_data[signal_key] = {
                    'tester_pin': group_name,
                    'signal_name': signal_name,
                    'direction': direction,
                    'is_scan': is_scan
                }
            
                # Create the mapping
                self.signal_mapping[signal_key] = group_name

    def _get_value_by_keys(self, row: dict, possible_keys: list, default: str = '') -> str:
        """Get value from row using the first matching key from possible_keys."""
        for key in possible_keys:
            if key in row and row[key] is not None:
                return str(row[key])
        return default
       
    def generate_file(self, stil_data: STILData, output_path: str, 
                     source_file: str = "", target_tester: str = "NiSTS-6570") -> None:
        """Generate a digipatsrc file from STIL data."""
        with open(output_path, 'w', encoding='utf-8') as file:
            self._write_header(file, source_file, target_tester)
            self._write_file_format_version(file)
            self._write_timeset_declaration(file, stil_data)
            self._write_pattern_declaration(file, stil_data)
            self._write_patterns(file, stil_data)
    
    def _write_header(self, file: TextIO, source_file: str, target_tester: str) -> None:
        """Write the file header."""
        current_time = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
        
        file.write(f"""
// --------------------------------------------------------------------------------------------------------
// VectorPort v2022.11.17
// Created by Test Spectrum, Inc.
// http://vectorport.testspectrum.com
// Source file {source_file}
// Target tester {target_tester}
// Converted on {current_time}
// --------------------------------------------------------------------------------------------------------

""")
    
    def _write_file_format_version(self, file: TextIO) -> None:
        """Write the file format version."""
        file.write("file_format_version 1.1;\n")
    
    def _write_timeset_declaration(self, file: TextIO, stil_data: STILData) -> None:
        """Write the timeset declaration."""
        # Extract timeset names from waveform tables
        timeset_names = []
        for wft in stil_data.waveform_tables:
            timeset_names.append(wft.name)
        
        if timeset_names:
            timeset_str = ", ".join(timeset_names)
            file.write(f"timeset {timeset_str};\n\n")
        else:
            # No timesets found - write empty timeset declaration or skip
            file.write("// No timesets found in STIL data\n\n")
    
    def _write_pattern_declaration(self, file: TextIO, stil_data: STILData) -> None:
        """Write the pattern declaration with signal mappings."""
        mapped_signals = []
        
        if self.pinmap_data:
            # Use pinmap for signal mapping - all signals must come from pinmap
            for signal in stil_data.signals:
                if signal.name in self.pinmap_data:
                    pinmap_entry = self.pinmap_data[signal.name]
                    tester_pin = pinmap_entry['tester_pin']
                    mapped_signals.append(tester_pin)
                    self.signal_mapping[signal.name] = tester_pin
        else:
            # No pinmap provided - cannot proceed without explicit signal mapping
            raise ValueError("No pinmap file provided. Signal mapping is required to convert STIL to digipatsrc. "
                           "Please provide a pinmap file using --pinmap option.")
        
        # Write pattern declaration
        if mapped_signals:
            signal_list = ", ".join(mapped_signals)
            file.write(f"pattern _pattern_ ({signal_list})\n{{\n")
        else:
            raise ValueError("No signals were mapped from pinmap. Check that pinmap file contains valid signal mappings.")
    
    def _write_patterns(self, file: TextIO, stil_data: STILData) -> None:
        """Write the pattern data."""
        # Write precondition signals
        file.write("preconditionallSignals:\n")
        file.write("                         _default_WFT_                   X 1 0 X X; \n")
        file.write("                         -                               X 1 0 X X; \n")
        file.write("// Ann {* chain_test *}\n")
        
        # Process patterns
        total_patterns = len(stil_data.patterns)
        for i, pattern in enumerate(stil_data.patterns):
            is_last_pattern = (i == total_patterns - 1)
            self._write_single_pattern(file, pattern, i, stil_data, is_last_pattern)
        
        # Close pattern block
        file.write("}\n")
    
    def _generate_default_line(self) -> str:
        """Generate the default WFT line based on signal names."""
        signal_order = list(self.signal_mapping.keys())
        default_values = []
        
        for signal_name in signal_order:
            if "CLEAR" in signal_name:
                default_values.append("1")
            elif "CLK" in signal_name:
                default_values.append("0")
            else:
                default_values.append("X")
        
        return " ".join(default_values)
    
    def _write_single_pattern(self, file: TextIO, pattern: Pattern, 
                            pattern_index: int, stil_data: STILData, is_last_pattern: bool = False) -> None:
        """Write a single pattern section."""
        file.write(f"pattern{pattern_index}:\n")
        
        # Write default WFT line for this pattern
        default_values = self._generate_default_line()
        file.write(f"                         _default_WFT_                   {default_values}; \n")
        
        # Process each call in the pattern
        total_calls = len(pattern.calls)
        for call_index, call in enumerate(pattern.calls):
            is_last_call = (call_index == total_calls - 1)
            is_first_call = (call_index == 0)
            if call['type'] == 'load_unload':
                self._write_load_unload_vectors(file, call, stil_data, is_last_pattern and is_last_call, is_first_call, is_last_call)
            elif call['type'] == 'multiclock_capture':
                self._write_capture_vector(file, call, is_last_pattern and is_last_call)
    
    def _write_load_unload_vectors(self, file: TextIO, call: Dict, stil_data: STILData, is_last_line: bool = False, is_first_call: bool = False, is_last_call: bool = False) -> None:
        """Write load/unload vector sequence."""
        if 'signals' not in call:
            return
        
        signals = call['signals']
        
        # Get scan data length
        scan_data_length = 0
        for signal_name, data in signals.items():
            if len(data) > scan_data_length:
                scan_data_length = len(data)
        
        # Get signal order from pinmap - must be defined
        if not self.signal_mapping:
            raise ValueError("No signal mapping available. Cannot generate load/unload vectors without proper signal mapping.")
        
        signal_order = list(self.signal_mapping.keys())
        
        # Generate vectors for each bit
        for bit_index in range(scan_data_length):
            # Check if this is the last vector line in the last pattern
            is_last_vector = is_last_line and (bit_index == scan_data_length - 1)
            # Check if this is the first vector line of the pattern
            is_first_vector = is_first_call and (bit_index == 0)
            # Check if this is the last vector line of the pattern (any pattern)
            is_pattern_last_vector = is_last_call and (bit_index == scan_data_length - 1)
            
            # Initialize signal states - no defaults, must be explicitly set
            signal_states = {}
            
            # Extract actual values from signals - all must come from input data
            for signal_name, data in signals.items():
                if signal_name in self.signal_mapping and bit_index < len(data):
                    # Map STIL values directly without assumptions
                    value = data[bit_index]
                    signal_states[signal_name] = map_stil_value_to_digipat(value)
                elif signal_name in self.signal_mapping:
                    # Signal is mapped but no data available for this bit
                    raise ValueError(f"Signal '{signal_name}' is mapped but no data available for bit {bit_index}. "
                                   f"All signal data must be provided in STIL patterns.")
            
            # Check if all mapped signals have values
            for signal_name in signal_order:
                if signal_name not in signal_states:
                    # Signal is in mapping but not in pattern data
                    # Check if it's in the pattern signals at all
                    if signal_name not in signals:
                        # Set CLK signals to 0 on first and last lines of each pattern
                        if "CLK" in signal_name:
                            if is_last_vector:
                                signal_states[signal_name] = "0"
                            else:
                                signal_states[signal_name] = "1"
                        elif "CLEAR" in signal_name:
                            signal_states[signal_name] = "1"
                        elif "SDI" in signal_name:
                            signal_states[signal_name] = "0"
                        else:
                            signal_states[signal_name] = "X"
                    else:
                        # Signal exists but no value for this bit position
                        signal_states[signal_name] = "X"  # Only allowed default
            
            # Write vector line in the correct signal order
            vector_values = []
            for signal_name in signal_order:
                if signal_name in signal_states:
                    vector_values.append(signal_states[signal_name])
                else:
                    raise ValueError(f"No value available for signal '{signal_name}' at bit position {bit_index}")
            
            vector_line = " ".join(vector_values)
            
            # Add "halt" at the beginning of the last line
            if is_last_vector:
                file.write(f"halt                     -                               {vector_line}; \n")
            else:
                file.write(f"                         -                               {vector_line}; \n")
    
    def _write_capture_vector(self, file: TextIO, call: Dict, is_last_line: bool = False) -> None:
        """Write capture vector."""
        if 'signals' not in call:
            raise ValueError("No signals found in capture pattern call. Capture vectors require signal data.")
        
        signals = call['signals']
        
        if not self.signal_mapping:
            raise ValueError("No signal mapping available. Cannot generate capture vectors without proper signal mapping.")
        
        signal_order = list(self.signal_mapping.keys())
        signal_states = {}
        
        # Extract signal values from patterns - must come from input data
        pattern_signals_found = False
        
        for signal_name, data in signals.items():
            if signal_name == "_pi" and len(data) >= 1:
                pattern_signals_found = True
                # Parse primary input signals - map based on signal order and pinmap
                input_signals = [sig for sig in signal_order 
                               if self.pinmap_data.get(sig, {}).get('direction', '').lower() == 'input']
                
                for i, input_signal in enumerate(input_signals):
                    if i < len(data):
                        value = data[i]
                        signal_states[input_signal] = map_stil_value_to_digipat(value)
                    else:
                        raise ValueError(f"Not enough input data in '_pi' pattern for signal '{input_signal}'. "
                                       f"Pattern data length: {len(data)}, expected at least: {i+1}")
                                
            elif signal_name == "_po" and len(data) >= 1:
                pattern_signals_found = True
                # Parse primary output signals - map based on signal order and pinmap
                output_signals = [sig for sig in signal_order 
                                if self.pinmap_data.get(sig, {}).get('direction', '').lower() == 'output']
                
                for i, output_signal in enumerate(output_signals):
                    if i < len(data):
                        value = data[i]
                        signal_states[output_signal] = map_stil_value_to_digipat(value)
                    else:
                        raise ValueError(f"Not enough output data in '_po' pattern for signal '{output_signal}'. "
                                       f"Pattern data length: {len(data)}, expected at least: {i+1}")
            
            # Handle direct signal mapping
            elif signal_name in self.signal_mapping:
                pattern_signals_found = True
                if len(data) >= 1:
                    signal_states[signal_name] = map_stil_value_to_digipat(data[0])
                else:
                    raise ValueError(f"No data available for signal '{signal_name}' in capture pattern.")
        
        if not pattern_signals_found:
            raise ValueError("No recognizable signal patterns found in capture call. "
                           "Expected '_pi', '_po', or direct signal names.")
        
        # Verify all mapped signals have values
        for signal_name in signal_order:
            if signal_name not in signal_states:
                raise ValueError(f"No value available for mapped signal '{signal_name}' in capture pattern. "
                               f"All mapped signals must have values in STIL pattern data.")
        
        # Write capture vector with appropriate timeset
        timeset = "_multiclock_capture_WFT_"
        vector_values = []
        for signal_name in signal_order:
            vector_values.append(signal_states[signal_name])
        
        vector_line = " ".join(vector_values)
        
        # Add "halt" at the beginning of the last line
        if is_last_line:
            file.write(f"halt                     {timeset:<30} {vector_line}; \n")
        else:
            file.write(f"                         {timeset:<30} {vector_line}; \n")
        
    def _get_signal_order(self, stil_data: STILData) -> List[str]:
        """Get the signal order for vector generation."""
        if not self.signal_mapping:
            raise ValueError("No signal mapping available. Cannot determine signal order without pinmap.")
        return list(self.signal_mapping.keys())
            
    def _get_signal_order_from_mapping(self) -> List[str]:
        """Get signal order from the current mapping."""
        if not self.signal_mapping:
            raise ValueError("No signal mapping available. Cannot determine signal order without pinmap.")
        return list(self.signal_mapping.keys())


# Helper functions
# Only these five values are valid in .digipatsrc files.
# Any STIL value outside this set must be mapped to 'X'.
VALID_DIGIPATSRC_VALUES = {'0', '1', 'L', 'H', 'X'}


def map_stil_value_to_digipat(value: str) -> str:
    """Map STIL signal values to digipatsrc format.

    Valid digipatsrc values: 0, 1, L, H, X.
    STIL values Z, T, P and any other unsupported values are mapped to X.
    """
    upper = value.upper()
    if upper in VALID_DIGIPATSRC_VALUES:
        return upper
    return 'X'


def extract_signal_order(stil_data: STILData) -> List[str]:
    """Extract the correct signal order from STIL data."""
    # Look for signal groups that define the signal order
    for group in stil_data.signal_groups:
        if group.name in ['_pi', 'all_inputs', '_in']:
            return group.signals
    
    # Raise error instead of fallback - no assumptions
    raise ValueError("Cannot determine signal order from STIL data. "
                   "No recognized signal groups ('_pi', 'all_inputs', '_in') found. "
                   "Signal order must be explicitly defined in STIL file or pinmap.")


class DigitimingGenerator:
    """Generator for digitiming XML files from STIL timing data."""
    
    def __init__(self, pinmap_file: Optional[str] = None):
        self.pinmap_data = {}
        self.signal_mapping = {}
        
        if pinmap_file:
            self._load_pinmap(pinmap_file)
    
    def _load_pinmap(self, pinmap_file: str) -> None:
        """Load pinmap file to get signal to pin mapping."""
        try:
            with open(pinmap_file, 'r', encoding='utf-8') as file:
                all_lines = file.readlines()
                
                header_line = None
                data_lines = []
                
                for line in all_lines:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    
                    if stripped.startswith('#') and ('Group' in stripped or 'Order' in stripped):
                        header_line = stripped[1:].strip()
                    elif not stripped.startswith('#'):
                        data_lines.append(line)
                
                if not header_line or not data_lines:
                    raise ValueError("Invalid pinmap file format")
                
                is_csv_format = ',' in header_line
                
                if is_csv_format:
                    all_csv_lines = [header_line] + data_lines
                    csv_reader = csv.DictReader(all_csv_lines)
                    for row in csv_reader:
                        cleaned_row = {k.strip(): v.strip() if v else v for k, v in row.items()}
                        self._process_pinmap_row(cleaned_row)
                        
        except Exception as e:
            print(f"Warning: Could not load pinmap file: {e}")
    
    def _process_pinmap_row(self, row: dict) -> None:
        """Process a single row from pinmap."""
        group_name_keys = ['Group/Alias Name', 'Group_Alias_Name', 'GroupName', 'Group', 'TesterPin', 'Pin']
        original_signal_keys = ['Original Signal Name (without bus index values)', 'Original_Signal_Name', 'OriginalSignal', 'STILSignal', 'Original']
        remove_keys = ['Remove?', 'Remove', 'Skip', 'Exclude']
        
        group_name = self._get_value_by_keys(row, group_name_keys, '').strip()
        original_signal = self._get_value_by_keys(row, original_signal_keys, '').strip()
        remove = self._get_value_by_keys(row, remove_keys, '').strip().lower() == 'true'
        
        signal_key = original_signal if original_signal else group_name
        
        if not remove and signal_key and "LATCH" not in signal_key:
            self.pinmap_data[signal_key] = group_name
            self.signal_mapping[signal_key] = group_name
    
    def _get_value_by_keys(self, row: dict, possible_keys: list, default: str = '') -> str:
        """Get value from row using first matching key."""
        for key in possible_keys:
            if key in row and row[key] is not None:
                return str(row[key])
        return default
    
    def generate_file(self, stil_data: STILData, output_path: str) -> None:
        """Generate a digitiming XML file from STIL timing data."""
        with open(output_path, 'w', encoding='utf-8') as file:
            self._write_xml_header(file)
            self._write_timing_sheet(file, stil_data)
            self._write_xml_footer(file)
    
    def _write_xml_header(self, file: TextIO) -> None:
        """Write XML header."""
        file.write('<?xml version="1.0" encoding="utf-8"?>\n')
        file.write('<TimingFile xmlns:xsd="http://www.w3.org/2001/XMLSchema" ')
        file.write('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
        file.write('schemaVersion="1.0" xmlns="http://www.ni.com/Semiconductor/Timing">\n')
        file.write('\t<TimingSheet>\n\n')
        file.write('\t\t<TimeSets>\n')
    
    def _write_xml_footer(self, file: TextIO) -> None:
        """Write XML footer."""
        file.write('\t\t</TimeSets>\n\n')
        file.write('\t</TimingSheet>\n')
        file.write('</TimingFile>\n')
    
    def _write_timing_sheet(self, file: TextIO, stil_data: STILData) -> None:
        """Write the timing sheet with all timesets."""
        for waveform_table in stil_data.waveform_tables:
            self._write_timeset(file, waveform_table, stil_data)
    
    def _write_timeset(self, file: TextIO, waveform_table, stil_data: STILData) -> None:
        """Write a single timeset."""
        file.write(f'\t\t\t<TimeSet name="{waveform_table.name}">\n')
        
        # Write period
        period_value = self._convert_period_to_seconds(waveform_table.period)
        file.write(f'\t\t\t\t<Period>{period_value}</Period>\n')
        
        # Write pin edges
        file.write('\t\t\t\t<PinEdges>\n')
        
        # Get all signals from pinmap
        for signal_name, tester_pin in self.signal_mapping.items():
            self._write_pin_edge(file, signal_name, tester_pin, waveform_table, stil_data)
        
        file.write('\t\t\t\t</PinEdges>\n')
        file.write('\t\t\t</TimeSet>\n')
    
    def _write_pin_edge(self, file: TextIO, signal_name: str, tester_pin: str, 
                       waveform_table, stil_data: STILData) -> None:
        """Write pin edge configuration for a signal."""
        file.write(f'\t\t\t\t\t<PinEdge pin="{tester_pin}">\n')
        
        # Determine drive format based on signal name and waveform data
        is_output = self._is_output_signal(signal_name, stil_data)
        
        # Check if signal has pulse waveform (P state)
        has_pulse = self._has_pulse_waveform(signal_name, waveform_table)
        
        if has_pulse:
            # Use Return format for clock signals with pulse
            if "SCLK" in signal_name:
                # ReturnToLow for SCLK
                file.write('\t\t\t\t\t\t<ReturnToLow>\n')
                file.write('\t\t\t\t\t\t\t<On>0</On>\n')
                file.write('\t\t\t\t\t\t\t<Data>50E-9</Data>\n')
                file.write('\t\t\t\t\t\t\t<Return>100E-9</Return>\n')
                file.write('\t\t\t\t\t\t\t<Off>100E-9</Off>\n')
                file.write('\t\t\t\t\t\t</ReturnToLow>\n')
            elif "CLEAR_SELECT" in signal_name:
                # ReturnToHigh for CLEAR_SELECT
                file.write('\t\t\t\t\t\t<ReturnToHigh>\n')
                file.write('\t\t\t\t\t\t\t<On>0</On>\n')
                file.write('\t\t\t\t\t\t\t<Data>50E-9</Data>\n')
                file.write('\t\t\t\t\t\t\t<Return>100E-9</Return>\n')
                file.write('\t\t\t\t\t\t\t<Off>100E-9</Off>\n')
                file.write('\t\t\t\t\t\t</ReturnToHigh>\n')
            else:
                # Default to DriveNonReturn for other signals with pulse
                file.write('\t\t\t\t\t\t<DriveNonReturn>\n')
                file.write('\t\t\t\t\t\t\t<On>0</On>\n')
                file.write('\t\t\t\t\t\t\t<Data>0</Data>\n')
                if is_output:
                    file.write('\t\t\t\t\t\t\t<Off>0</Off>\n')
                else:
                    file.write('\t\t\t\t\t\t\t<Off>100E-9</Off>\n')
                file.write('\t\t\t\t\t\t</DriveNonReturn>\n')
        else:
            # DriveNonReturn for non-clock signals
            file.write('\t\t\t\t\t\t<DriveNonReturn>\n')
            file.write('\t\t\t\t\t\t\t<On>0</On>\n')
            file.write('\t\t\t\t\t\t\t<Data>0</Data>\n')
            if is_output:
                file.write('\t\t\t\t\t\t\t<Off>0</Off>\n')
            else:
                file.write('\t\t\t\t\t\t\t<Off>100E-9</Off>\n')
            file.write('\t\t\t\t\t\t</DriveNonReturn>\n')
        
        # CompareStrobe
        file.write('\t\t\t\t\t\t<CompareStrobe>\n')
        if is_output:
            file.write('\t\t\t\t\t\t\t<Strobe>40E-9</Strobe>\n')
        else:
            file.write('\t\t\t\t\t\t\t<Strobe>0</Strobe>\n')
        file.write('\t\t\t\t\t\t</CompareStrobe>\n')
        
        # DataSource
        file.write('\t\t\t\t\t\t<DataSource>Pattern</DataSource>\n')
        
        file.write('\t\t\t\t\t</PinEdge>\n')
    
    def _has_pulse_waveform(self, signal_name: str, waveform_table) -> bool:
        """Check if signal has pulse (P) waveform definition."""
        # Check in waveform table for this specific signal
        for pattern_name, states in waveform_table.waveforms.items():
            if signal_name in pattern_name:
                if 'P' in states:
                    return True
        
        # Also check for signal name directly
        if signal_name in waveform_table.waveforms:
            if 'P' in waveform_table.waveforms[signal_name]:
                return True
        
        return False
    
    def _is_output_signal(self, signal_name: str, stil_data: STILData) -> bool:
        """Determine if signal is an output."""
        for signal in stil_data.signals:
            if signal.name == signal_name:
                return signal.direction == SignalDirection.OUTPUT or signal.is_scan_out
        return False
    
    def _convert_period_to_seconds(self, period_str: str) -> str:
        """Convert STIL period format to seconds notation."""
        # Examples: '100ns' -> '100E-9', '1us' -> '1E-6'
        if not period_str:
            return '100E-9'  # Default
        
        period_str = period_str.lower().strip().replace("'", "")
        
        # Extract number and unit
        import re
        match = re.match(r'([\d.]+)\s*([a-z]+)', period_str)
        if not match:
            return '100E-9'
        
        value = match.group(1)
        unit = match.group(2)
        
        # Convert to scientific notation
        unit_map = {
            's': 'E+0',
            'ms': 'E-3',
            'us': 'E-6',
            'ns': 'E-9',
            'ps': 'E-12'
        }
        
        exponent = unit_map.get(unit, 'E-9')
        return f'{value}{exponent}'


class PinmapGenerator:
    """Generator for pinmap XML files from STIL signal data and pinmap CSV."""
    
    def __init__(self, pinmap_file: Optional[str] = None):
        self.pinmap_data = {}
        self.signal_mapping = {}
        
        if pinmap_file:
            self._load_pinmap(pinmap_file)
    
    def _load_pinmap(self, pinmap_file: str) -> None:
        """Load pinmap file to get signal to pin mapping."""
        try:
            with open(pinmap_file, 'r', encoding='utf-8') as file:
                all_lines = file.readlines()
                
                header_line = None
                data_lines = []
                
                for line in all_lines:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    
                    if stripped.startswith('#') and ('Group' in stripped or 'Order' in stripped):
                        header_line = stripped[1:].strip()
                    elif not stripped.startswith('#'):
                        data_lines.append(line)
                
                if not header_line or not data_lines:
                    raise ValueError("Invalid pinmap file format")
                
                is_csv_format = ',' in header_line
                
                if is_csv_format:
                    all_csv_lines = [header_line] + data_lines
                    csv_reader = csv.DictReader(all_csv_lines)
                    for row in csv_reader:
                        cleaned_row = {k.strip(): v.strip() if v else v for k, v in row.items()}
                        self._process_pinmap_row(cleaned_row)
                        
        except Exception as e:
            print(f"Warning: Could not load pinmap file: {e}")
    
    def _process_pinmap_row(self, row: dict) -> None:
        """Process a single row from pinmap."""
        group_name_keys = ['Group/Alias Name', 'Group_Alias_Name', 'GroupName', 'Group', 'TesterPin', 'Pin']
        original_signal_keys = ['Original Signal Name (without bus index values)', 'Original_Signal_Name', 'OriginalSignal', 'STILSignal', 'Original']
        direction_keys = ['Direction', 'Dir', 'Type']
        remove_keys = ['Remove?', 'Remove', 'Skip', 'Exclude']
        
        group_name = self._get_value_by_keys(row, group_name_keys, '').strip()
        original_signal = self._get_value_by_keys(row, original_signal_keys, '').strip()
        direction = self._get_value_by_keys(row, direction_keys, '').strip()
        remove = self._get_value_by_keys(row, remove_keys, '').strip().lower() == 'true'
        
        signal_key = original_signal if original_signal else group_name
        
        if not remove and signal_key and "LATCH" not in signal_key:
            self.pinmap_data[signal_key] = {
                'tester_pin': group_name,
                'direction': direction
            }
            self.signal_mapping[signal_key] = group_name
    
    def _get_value_by_keys(self, row: dict, possible_keys: list, default: str = '') -> str:
        """Get value from row using first matching key."""
        for key in possible_keys:
            if key in row and row[key] is not None:
                return str(row[key])
        return default
    
    def generate_file(self, stil_data: STILData, output_path: str) -> None:
        """Generate a pinmap XML file from STIL signal data."""
        with open(output_path, 'w', encoding='utf-8') as file:
            self._write_xml_header(file)
            self._write_instruments(file)
            self._write_pins(file, stil_data)
            self._write_pin_groups(file, stil_data)
            self._write_xml_footer(file)
    
    def _write_xml_header(self, file: TextIO) -> None:
        """Write XML header."""
        file.write('<?xml version="1.0" encoding="utf-8"?>\n')
        file.write('<PinMap xmlns="http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd" ')
        file.write('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" schemaVersion="1.0">\n')
    
    def _write_xml_footer(self, file: TextIO) -> None:
        """Write XML footer."""
        file.write('\n</PinMap>\n')
    
    def _write_instruments(self, file: TextIO) -> None:
        """Write instruments section."""
        file.write('\t<Instruments>\n')
        file.write('\t\t<NIDigitalPatternInstrument name="Digital Pattern1" numberOfChannels="32" />\n')
        file.write('\t\t<NIDigitalPatternInstrument name="Digital Pattern2" numberOfChannels="32" />\n')
        file.write('\t\t<NIDigitalPatternInstrument name="Digital Pattern3" numberOfChannels="32" />\n')
        file.write('\t\t<NIDCPowerInstrument name="PSU1" numberOfChannels="4"/>\n')
        file.write('\t\t<NIDCPowerInstrument name="PSU2" numberOfChannels="4"/>\n')
        file.write('\t</Instruments>\n\n')
    
    def _write_pins(self, file: TextIO, stil_data: STILData) -> None:
        """Write pins section."""
        file.write('\t<Pins>\n')
        
        # Get all mapped signals
        for signal_name, tester_pin in self.signal_mapping.items():
            file.write(f'\t\t<DUTPin name="{tester_pin}"/>\n')
        
        file.write('\t</Pins>\n\n')
    
    def _write_pin_groups(self, file: TextIO, stil_data: STILData) -> None:
        """Write pin groups section."""
        file.write('\t<PinGroups>\n')
        
        # Find output signals to create pin groups
        output_signals = []
        for signal in stil_data.signals:
            if signal.direction == SignalDirection.OUTPUT or signal.is_scan_out:
                if signal.name in self.signal_mapping:
                    output_signals.append(signal.name)
        
        # Create pin groups for output signals
        for signal_name in output_signals:
            tester_pin = self.signal_mapping[signal_name]
            # Create a simplified group name (remove suffix like _6571)
            group_name = signal_name
            
            file.write(f'\t\t<PinGroup name="{group_name}">\n')
            file.write(f'\t\t\t<PinReference pin="{tester_pin}"/>\n')
            file.write('\t\t</PinGroup>\n')
        
        file.write('\t</PinGroups>\n\n')


def generate_pattern_source(stil_folder, output_folder):
    """Generate digipatsrc, digitiming, and pinmap files for all STIL files in the specified folder."""
    stil_folder_path = Path(stil_folder)
    output_folder_path = Path(output_folder)
    output_folder_path.mkdir(parents=True, exist_ok=True)
    
    stil_files = list(stil_folder_path.glob("*.stil"))
    
    for stil_file in stil_files:
        try:
            output_folder = output_folder_path / stil_file.stem
            os.makedirs(output_folder, exist_ok=True)
            # Parse STIL file
            parser = STILParser()
            stil_data = parser.parse_file(str(stil_file))
            
            # Get pinmap file path
            pin_file_path = stil_folder_path / "Pinmap"
            
            # Generate digipatsrc file
            generator = DigipatsrcGenerator(pinmap_file=str(pin_file_path))
            output_file_path = output_folder / (stil_file.stem + ".digipatsrc")
            generator.generate_file(stil_data, str(output_file_path), 
                                  source_file=str(stil_file))
            print(f"Generated digipatsrc file: {output_file_path}")
            
            # Generate digitiming file
            timing_generator = DigitimingGenerator(pinmap_file=str(pin_file_path))
            timing_output_path = output_folder / (stil_file.stem + ".digitiming")
            timing_generator.generate_file(stil_data, str(timing_output_path))
            print(f"Generated digitiming file: {timing_output_path}")
            
            # Generate pinmap file
            pinmap_generator = PinmapGenerator(pinmap_file=str(pin_file_path))
            pinmap_output_path = output_folder / (stil_file.stem + ".pinmap")
            pinmap_generator.generate_file(stil_data, str(pinmap_output_path))
            print(f"Generated pinmap file: {pinmap_output_path}")
            
        except Exception as e:
            print(f"Error processing STIL file '{stil_file}': {e}")
            import traceback
            traceback.print_exc()

# Usage example
if __name__ == "__main__":

    base_dir = os.path.dirname(os.path.abspath(__file__))
    stil_folder = os.path.join(base_dir, "stil_files")
    output_folder = os.path.join(base_dir, "digipatsrc_output")
    generate_pattern_source(stil_folder, output_folder)
    # stil_file_path = os.path.join(base_dir, "tpc2201_pr.stil")
    # pin_file_path = os.path.join(base_dir, "Pinmap")
    # # Parse STIL file
    # parser = STILParser()
    # stil_data = parser.parse_file(stil_file_path)
    
    # # Generate digipatsrc file with pinmap
    # generator = DigipatsrcGenerator(pinmap_file=pin_file_path)
    # generator.generate_file(stil_data, "output.digipatsrc", 
    #                       source_file=stil_file_path)