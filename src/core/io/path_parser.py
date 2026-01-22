import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class PathParser:
    def __init__(self, source_root: str, pattern: Optional[str] = None):
        self.source_root = Path(source_root)
        self.pattern = re.compile(pattern) if pattern else None
        
    def parse(self, file_path: str) -> Dict[str, str]:
        """
        Parse metadata from file path.
        Returns dict with keys: 'captured_date', 'location_tag', 'source_structure'
        """
        abs_path = Path(file_path)
        try:
            rel_path = abs_path.relative_to(self.source_root)
        except ValueError:
            # Should not happen if fs_manager works correctly
            rel_path = abs_path
            
        result = {
            'captured_date': datetime.now().strftime("%Y%m%d"),
            'location_tag': 'Unknown',
            'source_structure': str(rel_path.parent).replace('\\', '/')
        }
        
        # 1. Regex Match (High Priority)
        if self.pattern:
            # Match against the relative path string (normalized to unix style for consistency)
            path_str = str(rel_path).replace('\\', '/')
            match = self.pattern.search(path_str)
            if match:
                groups = match.groupdict()
                if 'date' in groups:
                    result['captured_date'] = groups['date']
                if 'location' in groups:
                    loc = groups['location']
                    # STRICT SAFETY: Location should never contain the filename
                    # If regex was greedy (e.g. .*), it captures the whole path including filename.
                    filename = abs_path.name
                    
                    if loc.endswith(filename):
                        loc = loc[:-len(filename)]
                    
                    # Clean up trailing separators
                    loc = loc.rstrip('/\\_ ')
                    
                    result['location_tag'] = loc
                return result

        # 2. Default Guessing Logic (Fallback)
        # Assumes relative path folders contain location/date info.
        # We iterate through all folder levels to build the location tag.
        parts = rel_path.parts
        if len(parts) <= 1:
            # File is in root
            return result
            
        folder_parts = parts[:-1] # Exclude filename
        locations = []
        found_date = None
        
        for folder in folder_parts:
            # Check for patterns
            
            # Pattern 1: Range yyyyMMdd-yyyyMMdd{location}
            # e.g. 20231001-20231007Japan
            match_range_full = re.match(r'^(\d{8})-(\d{8})[_\s-]*(.+)$', folder)
            if match_range_full:
                found_date = match_range_full.group(1)
                locations.append(match_range_full.group(3))
                continue
                
            # Pattern 2: Range yyyyMMdd-dd{location}
            # e.g. 20231001-07_USA
            match_range_short = re.match(r'^(\d{8})-(\d{2})[_\s-]*(.+)$', folder)
            if match_range_short:
                found_date = match_range_short.group(1)
                locations.append(match_range_short.group(3))
                continue
                
            # Pattern 3: Standard Single Date yyyyMMdd_Location
            # e.g. 20231020_OlympicPark or 20241230东京
            match_single = re.match(r'^(\d{8})[_\s-]*(.+)$', folder)
            if match_single:
                found_date = match_single.group(1)
                locations.append(match_single.group(2))
                continue
            
            # Pattern 4: Date only (Folder is just date)
            if folder.isdigit() and len(folder) == 8:
                 found_date = folder
                 continue

            # Fallback: Treat entire folder name as location
            locations.append(folder)
            
        if found_date:
            result['captured_date'] = found_date
            
        if locations:
            # Clean up and join
            clean_locs = [loc.strip('_ ') for loc in locations if loc]
            result['location_tag'] = '_'.join(clean_locs)
                
        return result
