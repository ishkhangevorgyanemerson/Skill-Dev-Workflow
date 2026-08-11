"""
STIL Parser - Parse STIL files and extract test pattern information.

This module provides functionality to parse Standard Test Interface Language (STIL) files
and extract relevant information for test pattern conversion.
"""

import re
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class SignalDirection(Enum):
    """Signal direction enumeration."""
    INPUT = "In"
    OUTPUT = "Out"
    BIDIRECTIONAL = "InOut"


@dataclass
class Signal:
    """Represents a signal definition from STIL file."""
    name: str
    direction: SignalDirection
    is_scan_in: bool = False
    is_scan_out: bool = False


@dataclass
class SignalGroup:
    """Represents a signal group definition."""
    name: str
    signals: List[str]
    comment: str = ""


@dataclass
class WaveformTable:
    """Represents a waveform table definition."""
    name: str
    period: str
    waveforms: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)


@dataclass
class ScanChain:
    """Represents a scan chain definition."""
    name: str
    length: int
    scan_in: str
    scan_out: str
    inversion: int
    scan_cells: List[str] = field(default_factory=list)


@dataclass
class Pattern:
    """Represents a test pattern."""
    name: str
    calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class STILData:
    """Container for all parsed STIL data."""
    header: Dict[str, str] = field(default_factory=dict)
    signals: List[Signal] = field(default_factory=list)
    signal_groups: List[SignalGroup] = field(default_factory=list)
    waveform_tables: List[WaveformTable] = field(default_factory=list)
    scan_chains: List[ScanChain] = field(default_factory=list)
    patterns: List[Pattern] = field(default_factory=list)


class STILParser:
    """Parser for STIL files."""
    
    def __init__(self):
        self.data = STILData()
        self.current_section = None
        
    def parse_file(self, filepath: str) -> STILData:
        """Parse a STIL file and return extracted data."""
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> STILData:
        """Parse STIL content and return extracted data."""
        self.data = STILData()
        
        # Parse each section
        self._parse_header(content)
        self._parse_signals(content)
        self._parse_signal_groups(content)
        self._parse_timing(content)
        self._parse_scan_structures(content)
        self._parse_patterns(content)
        
        return self.data
    
    def _parse_header(self, content: str) -> None:
        """Parse the header section."""
        # Extract STIL version
        stil_match = re.search(r'STIL\s+([\d.]+)', content)
        if stil_match:
            self.data.header['stil_version'] = stil_match.group(1)
        
        # Extract header block
        header_match = re.search(r'Header\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)}', content, re.DOTALL)
        if header_match:
            header_content = header_match.group(1)
            
            # Extract title
            title_match = re.search(r'Title\s+"([^"]+)"', header_content)
            if title_match:
                self.data.header['title'] = title_match.group(1)
            
            # Extract date
            date_match = re.search(r'Date\s+"([^"]+)"', header_content)
            if date_match:
                self.data.header['date'] = date_match.group(1)
            
            # Extract source
            source_match = re.search(r'Source\s+"([^"]+)"', header_content)
            if source_match:
                self.data.header['source'] = source_match.group(1)
    
    def _parse_signals(self, content: str) -> None:
        """Parse the signals section."""
        # Find the start of Signals block
        signals_start = re.search(r'Signals\s*\{', content, re.DOTALL)
        if not signals_start:
            return
        
        # Find matching closing brace using brace counting
        start_pos = signals_start.end()
        brace_count = 1
        pos = start_pos
        
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count != 0:
            return  # Unmatched braces
        
        signals_content = content[start_pos:pos-1]
        
        # Find all signal definitions - pattern matches signal with optional attributes
        # Format: "signal_name" Direction { attributes; }
        signal_pattern = r'"([^"]+)"\s+(In|Out|InOut)\s*(?:\{\s*([^}]*)\s*\})?'
        for match in re.finditer(signal_pattern, signals_content):
            signal_name = match.group(1)
            direction_str = match.group(2)
            attributes = match.group(3) if match.group(3) else ""
            
            direction = SignalDirection(direction_str)
            is_scan_in = 'ScanIn' in attributes
            is_scan_out = 'ScanOut' in attributes
            
            signal = Signal(signal_name, direction, is_scan_in, is_scan_out)
            self.data.signals.append(signal)
    
    def _parse_signal_groups(self, content: str) -> None:
        """Parse the signal groups section."""
        # Find the start of SignalGroups block
        groups_start = re.search(r'SignalGroups\s*\{', content, re.DOTALL)
        if not groups_start:
            return
        
        # Find matching closing brace using brace counting
        start_pos = groups_start.end()
        brace_count = 1
        pos = start_pos
        
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count != 0:
            return  # Unmatched braces
        
        groups_content = content[start_pos:pos-1]
        
        # Find all signal group definitions - handle multi-line definitions
        # Pattern: "group_name" = 'signal expression' [{ attributes }] ; // optional comment
        # The signal expression uses single quotes and contains double-quoted signal names or group references
        # Match until we find the closing single quote followed by optional whitespace and semicolon
        group_pattern = r'"([^"]+)"\s*=\s*\'([^\']+)\'\s*(?:\{[^}]*\})?\s*;'
        for match in re.finditer(group_pattern, groups_content, re.DOTALL):
            group_name = match.group(1)
            signals_str = match.group(2)
            
            # Extract comment if present (after the semicolon)
            comment = ""
            rest_of_line = groups_content[match.end():match.end()+100]
            comment_match = re.search(r'//\s*([^\n]*)', rest_of_line)
            if comment_match:
                comment = comment_match.group(1).strip()
            
            # Parse signal list - handle + separated signals and multi-line
            signals = []
            
            # Remove newlines and extra spaces
            signals_str = ' '.join(signals_str.split())
            
            # Extract signal names from the expression (e.g., "SIG1" + "SIG2" + "SIG3")
            signal_refs = re.findall(r'"([^"]+)"', signals_str)
            signals.extend(signal_refs)
            
            signal_group = SignalGroup(group_name, signals, comment)
            self.data.signal_groups.append(signal_group)
    
    def _parse_timing(self, content: str) -> None:
        """Parse the timing section with waveform tables using brace counting."""
        # Find the Timing section using brace counting
        timing_start = content.find('Timing')
        if timing_start == -1:
            return
        
        # Find the opening brace after "Timing"
        brace_start = content.find('{', timing_start)
        if brace_start == -1:
            return
        
        # Count braces to find the complete Timing block
        brace_count = 1
        pos = brace_start + 1
        timing_end = -1
        
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    timing_end = pos
                    break
            pos += 1
        
        if timing_end == -1:
            return
        
        timing_content = content[brace_start + 1:timing_end]
        
        # Find all waveform tables using brace counting
        pos = 0
        while pos < len(timing_content):
            # Find next WaveformTable
            wft_start = timing_content.find('WaveformTable', pos)
            if wft_start == -1:
                break
            
            # Extract table name
            name_start = timing_content.find('"', wft_start)
            if name_start == -1:
                pos = wft_start + 1
                continue
            
            name_end = timing_content.find('"', name_start + 1)
            if name_end == -1:
                pos = wft_start + 1
                continue
            
            table_name = timing_content[name_start + 1:name_end]
            
            # Find the opening brace for this WaveformTable
            table_brace_start = timing_content.find('{', name_end)
            if table_brace_start == -1:
                pos = wft_start + 1
                continue
            
            # Count braces to find the complete WaveformTable block
            brace_count = 1
            table_pos = table_brace_start + 1
            table_brace_end = -1
            
            while table_pos < len(timing_content) and brace_count > 0:
                if timing_content[table_pos] == '{':
                    brace_count += 1
                elif timing_content[table_pos] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        table_brace_end = table_pos
                        break
                table_pos += 1
            
            if table_brace_end == -1:
                pos = wft_start + 1
                continue
            
            table_content = timing_content[table_brace_start + 1:table_brace_end]
            
            # Create waveform table object
            waveform_table = WaveformTable(name=table_name, period='', waveforms={})
            
            # Extract period
            period_match = re.search(r"Period\s+'([^']+)'", table_content)
            if period_match:
                waveform_table.period = period_match.group(1)
            
            # Extract waveforms section using brace counting
            waveforms_start = table_content.find('Waveforms')
            if waveforms_start != -1:
                waveforms_brace_start = table_content.find('{', waveforms_start)
                if waveforms_brace_start != -1:
                    # Count braces for Waveforms block
                    brace_count = 1
                    wf_pos = waveforms_brace_start + 1
                    waveforms_brace_end = -1
                    
                    while wf_pos < len(table_content) and brace_count > 0:
                        if table_content[wf_pos] == '{':
                            brace_count += 1
                        elif table_content[wf_pos] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                waveforms_brace_end = wf_pos
                                break
                        wf_pos += 1
                    
                    if waveforms_brace_end != -1:
                        waveforms_content = table_content[waveforms_brace_start + 1:waveforms_brace_end]
                        
                        # Parse individual waveform definitions
                        waveform_pattern = r'"([^"]+)"\s*{([^{}]*(?:{[^{}]*}[^{}]*)*?)}'
                        for wf_match in re.finditer(waveform_pattern, waveforms_content, re.DOTALL):
                            signal_pattern = wf_match.group(1)
                            waveform_def = wf_match.group(2)
                            
                            if signal_pattern not in waveform_table.waveforms:
                                waveform_table.waveforms[signal_pattern] = {}
                            
                            # Parse state definitions
                            state_pattern = r'([HLTX01ZNP])\s*{([^}]+)}'
                            for state_match in re.finditer(state_pattern, waveform_def):
                                state = state_match.group(1)
                                timing = state_match.group(2)
                                
                                # Parse timing events
                                timing_events = re.findall(r"'([^']+)'\s+([DUTLHZX])", timing)
                                waveform_table.waveforms[signal_pattern][state] = timing_events
            
            self.data.waveform_tables.append(waveform_table)
            
            # Move position to end of this WaveformTable
            pos = table_brace_end + 1
    
    def _parse_scan_structures(self, content: str) -> None:
        """Parse the scan structures section."""
        scan_match = re.search(r'ScanStructures\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)}', content, re.DOTALL)
        if not scan_match:
            return
        
        scan_content = scan_match.group(1)
        
        # Find scan chain definitions
        chain_pattern = r'ScanChain\s+"([^"]+)"\s*{([^{}]*(?:{[^{}]*}[^{}]*)*?)}'
        for match in re.finditer(chain_pattern, scan_content, re.DOTALL):
            chain_name = match.group(1)
            chain_content = match.group(2)
            
            scan_chain = ScanChain(chain_name, 0, "", "", 0)
            
            # Parse chain properties
            length_match = re.search(r'ScanLength\s+(\d+)', chain_content)
            if length_match:
                scan_chain.length = int(length_match.group(1))
            
            scan_in_match = re.search(r'ScanIn\s+"([^"]+)"', chain_content)
            if scan_in_match:
                scan_chain.scan_in = scan_in_match.group(1)
            
            scan_out_match = re.search(r'ScanOut\s+"([^"]+)"', chain_content)
            if scan_out_match:
                scan_chain.scan_out = scan_out_match.group(1)
            
            inversion_match = re.search(r'ScanInversion\s+(\d+)', chain_content)
            if inversion_match:
                scan_chain.inversion = int(inversion_match.group(1))
            
            # Parse scan cells
            cells_match = re.search(r'ScanCells\s+(.*?)(?=\n\s*}|\n\s*\w+|\Z)', chain_content, re.DOTALL)
            if cells_match:
                cells_content = cells_match.group(1)
                cell_names = re.findall(r'"([^"]+)"', cells_content)
                scan_chain.scan_cells = cell_names
            
            self.data.scan_chains.append(scan_chain)
    
    def _parse_patterns(self, content: str) -> None:
        """Parse pattern sections."""
        # Find Pattern block(s) using brace counting
        pattern_start = re.search(r'Pattern\s+"([^"]+)"\s*\{', content, re.DOTALL)
        if not pattern_start:
            return
        
        pattern_name = pattern_start.group(1)
        start_pos = pattern_start.end()
        brace_count = 1
        pos = start_pos
        
        # Find matching closing brace
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        if brace_count != 0:
            return  # Unmatched braces
        
        pattern_content = content[start_pos:pos-1]
        
        # Parse all pattern calls within this Pattern block
        self._parse_pattern_calls(pattern_content)
    
    def _parse_pattern_calls(self, content: str) -> None:
        """Parse individual pattern calls within a patterns section."""
        # Strategy: Find all "pattern N": labels and their associated Call blocks
        # Each pattern can have multiple Call blocks (load_unload, multiclock_capture, etc.)
        
        # Find all pattern labels with their positions
        pattern_labels = []
        for match in re.finditer(r'"pattern\s+(\d+)":', content):
            pattern_num = match.group(1)
            pattern_labels.append((int(pattern_num), match.start()))
        
        # Sort by position to process in order
        pattern_labels.sort(key=lambda x: x[1])
        
        # For each pattern, find all Call blocks until the next pattern or end
        for i, (pattern_num, start_pos) in enumerate(pattern_labels):
            pattern_name = f"pattern_{pattern_num}"
            
            # Determine the end position (start of next pattern or end of content)
            if i < len(pattern_labels) - 1:
                end_pos = pattern_labels[i + 1][1]
            else:
                end_pos = len(content)
            
            # Extract content for this pattern
            pattern_content = content[start_pos:end_pos]
            
            # Find all Call blocks within this pattern
            pattern = Pattern(pattern_name)
            
            # Find all Call statements using brace counting
            call_matches = list(re.finditer(r'Call\s+"([^"]+)"\s*\{', pattern_content))
            
            for call_match in call_matches:
                call_type = call_match.group(1)
                call_start = call_match.end()
                
                # Use brace counting to find the matching closing brace
                brace_count = 1
                pos = call_start
                while pos < len(pattern_content) and brace_count > 0:
                    if pattern_content[pos] == '{':
                        brace_count += 1
                    elif pattern_content[pos] == '}':
                        brace_count -= 1
                    pos += 1
                
                call_content = pattern_content[call_start:pos-1]
                
                call_data = {
                    'type': call_type,
                    'content': call_content.strip()
                }
                
                # Parse signal data if present
                if call_type == "load_unload":
                    signal_data = {}
                    # Handle very long signal values that span multiple lines
                    signal_pattern = r'"([^"]+)"\s*=\s*([HLXTLZ01\n\r\s]+?)(?=;|\Z)'
                    for sig_match in re.finditer(signal_pattern, call_content):
                        signal_name = sig_match.group(1)
                        signal_values = sig_match.group(2)
                        # Remove all whitespace and newlines from signal values
                        signal_values = ''.join(signal_values.split())
                        signal_data[signal_name] = signal_values
                    call_data['signals'] = signal_data
                
                elif call_type == "multiclock_capture":
                    signal_data = {}
                    signal_pattern = r'"([^"]+)"\s*=\s*([HLXTLZ01P\\rn\s]+?)(?=;|\Z)'
                    for sig_match in re.finditer(signal_pattern, call_content):
                        signal_name = sig_match.group(1)
                        signal_values = sig_match.group(2)
                        # Remove whitespace, newlines, and escape sequences
                        signal_values = re.sub(r'[\s\\rn]+', '', signal_values)
                        signal_data[signal_name] = signal_values
                    call_data['signals'] = signal_data
                
                pattern.calls.append(call_data)
            
            # Only add pattern if it has calls
            if pattern.calls:
                self.data.patterns.append(pattern)


# Usage example
if __name__ == "__main__":
    parser = STILParser()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    stil_file_path = os.path.join(base_dir, "stil_files", "tpc2201_pr.stil")
    stil_data = parser.parse_file(stil_file_path)
    print(f"Parsed {len(stil_data.signals)} signals")
    print(f"Found {len(stil_data.patterns)} patterns")
    print(f"Found {len(stil_data.waveform_tables)} waveform tables")