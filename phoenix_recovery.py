# Project Phoenix - Data Recovery Software
# Starter Implementation with Core Architecture

import os
import sys
import struct
import hashlib
import logging
from typing import List, Dict, Optional, Tuple, BinaryIO
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phoenix_recovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Phoenix')

class RecoveryMode(Enum):
    INTELLIGENT = "intelligent"
    DEEP_SCAN = "deep_scan"

class FileSystemType(Enum):
    NTFS = "NTFS"
    FAT32 = "FAT32"
    EXFAT = "exFAT"
    UNKNOWN = "Unknown"

@dataclass
class FileSignature:
    """File signature definition for data carving"""
    name: str
    extensions: List[str]
    header: bytes
    footer: Optional[bytes] = None
    max_size: int = 100 * 1024 * 1024  # 100MB default
    
@dataclass
class RecoveredFile:
    """Represents a file found during recovery"""
    name: str
    size: int
    offset: int
    file_type: str
    is_deleted: bool = False
    parent_path: str = ""
    timestamps: Dict[str, str] = None

@dataclass
class DriveInfo:
    """Information about a storage drive"""
    device_path: str
    label: str
    size: int
    file_system: FileSystemType

class FileSignatureDatabase:
    """Database of known file signatures for data carving"""
    
    def __init__(self):
        self.signatures = [
            # Images
            FileSignature("JPEG", [".jpg", ".jpeg"], b'\xFF\xD8\xFF', b'\xFF\xD9'),
            FileSignature("PNG", [".png"], b'\x89PNG\r\n\x1a\n'),
            FileSignature("GIF", [".gif"], b'GIF8'),
            FileSignature("BMP", [".bmp"], b'BM'),
            
            # Documents
            FileSignature("PDF", [".pdf"], b'%PDF-', b'%%EOF'),
            FileSignature("ZIP", [".zip", ".docx", ".xlsx"], b'PK\x03\x04'),
            FileSignature("DOC", [".doc"], b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'),
            
            # RAW Images
            FileSignature("Canon RAW", [".cr2"], b'II*\x00\x10\x00\x00\x00CR'),
            FileSignature("Nikon RAW", [".nef"], b'II*\x00'),
            FileSignature("Sony RAW", [".arw"], b'II*\x00'),
            
            # Video
            FileSignature("MP4", [".mp4", ".mov"], b'\x00\x00\x00\x20ftypmp4'),
            FileSignature("AVI", [".avi"], b'RIFF'),
            
            # Audio
            FileSignature("MP3", [".mp3"], b'ID3'),
            FileSignature("WAV", [".wav"], b'RIFF'),
        ]
    
    def get_signature_by_header(self, data: bytes) -> Optional[FileSignature]:
        """Find file signature matching the given header data"""
        for sig in self.signatures:
            if data.startswith(sig.header):
                return sig
        return None

class DiskAccessLayer:
    """Low-level disk access with read-only safety"""
    
    @staticmethod
    def get_available_drives() -> List[DriveInfo]:
        """Get list of available drives for recovery"""
        drives = []
        
        if sys.platform == "win32":
            import win32api, win32file
            drive_list = win32api.GetLogicalDriveStrings()
            for drive in drive_list.split('\x00')[:-1]:
                try:
                    drive_type = win32file.GetDriveType(drive)
                    if drive_type in [win32file.DRIVE_FIXED, win32file.DRIVE_REMOVABLE]:
                        # Get drive info
                        free_bytes, total_bytes, _ = win32file.GetDiskFreeSpace(drive)
                        drives.append(DriveInfo(
                            device_path=drive,
                            label=f"Drive {drive}",
                            size=total_bytes,
                            file_system=FileSystemType.UNKNOWN
                        ))
                except:
                    continue
        
        elif sys.platform.startswith("linux"):
            # Linux implementation would go here
            # Use /proc/partitions and mount information
            pass
        
        elif sys.platform == "darwin":
            # macOS implementation would go here
            # Use diskutil or system_profiler
            pass
        
        return drives
    
    @staticmethod
    def open_drive_readonly(device_path: str) -> Optional[BinaryIO]:
        """Open drive in read-only mode with safety checks"""
        try:
            if sys.platform == "win32":
                # Windows: Open as raw device
                handle = open(f"\\\\.\\{device_path.rstrip('\\')}", 'rb')
                return handle
            else:
                # Unix-like: Open device file
                handle = open(device_path, 'rb')
                return handle
        except Exception as e:
            logger.error(f"Failed to open drive {device_path}: {e}")
            return None

class RawDataCarver:
    """Engine B: Raw data carving for deep scan recovery"""
    
    def __init__(self, signature_db: FileSignatureDatabase):
        self.signature_db = signature_db
        self.chunk_size = 512 * 1024  # 512KB chunks
        self.recovered_files = []
        
    def scan_drive(self, drive_handle: BinaryIO, output_dir: Path, 
                   progress_callback=None) -> List[RecoveredFile]:
        """Perform raw data carving on drive"""
        self.recovered_files = []
        drive_handle.seek(0, 2)  # Seek to end
        drive_size = drive_handle.tell()
        drive_handle.seek(0)  # Back to start
        
        offset = 0
        file_counter = 1
        
        logger.info(f"Starting raw data carving, drive size: {drive_size} bytes")
        
        while offset < drive_size:
            # Read chunk
            chunk = drive_handle.read(self.chunk_size)
            if not chunk:
                break
                
            # Search for file signatures
            self._search_signatures_in_chunk(chunk, offset, drive_handle, 
                                           output_dir, file_counter)
            
            # Update progress
            if progress_callback:
                progress = (offset / drive_size) * 100
                progress_callback(progress)
            
            offset += len(chunk)
            
        logger.info(f"Raw carving complete. Found {len(self.recovered_files)} files")
        return self.recovered_files
    
    def _search_signatures_in_chunk(self, chunk: bytes, chunk_offset: int,
                                   drive_handle: BinaryIO, output_dir: Path,
                                   file_counter: int):
        """Search for file signatures within a chunk"""
        for i in range(len(chunk) - 16):  # Leave room for signature
            signature = self.signature_db.get_signature_by_header(chunk[i:])
            if signature:
                file_offset = chunk_offset + i
                self._carve_file(signature, file_offset, drive_handle, 
                               output_dir, file_counter)
                file_counter += 1
    
    def _carve_file(self, signature: FileSignature, offset: int,
                   drive_handle: BinaryIO, output_dir: Path, file_counter: int):
        """Carve out a file starting at the given offset"""
        try:
            # Save current position
            current_pos = drive_handle.tell()
            drive_handle.seek(offset)
            
            # Generate output filename
            ext = signature.extensions[0] if signature.extensions else ".bin"
            filename = f"recovered_{file_counter:06d}{ext}"
            output_path = output_dir / filename
            
            # Carve file data
            carved_size = 0
            with open(output_path, 'wb') as output_file:
                while carved_size < signature.max_size:
                    chunk = drive_handle.read(min(8192, signature.max_size - carved_size))
                    if not chunk:
                        break
                    
                    # Check for footer if defined
                    if signature.footer and signature.footer in chunk:
                        footer_pos = chunk.find(signature.footer)
                        output_file.write(chunk[:footer_pos + len(signature.footer)])
                        carved_size += footer_pos + len(signature.footer)
                        break
                    
                    output_file.write(chunk)
                    carved_size += len(chunk)
            
            # Create recovery record
            recovered_file = RecoveredFile(
                name=filename,
                size=carved_size,
                offset=offset,
                file_type=signature.name
            )
            self.recovered_files.append(recovered_file)
            
            logger.info(f"Carved file: {filename} ({carved_size} bytes)")
            
            # Restore position
            drive_handle.seek(current_pos)
            
        except Exception as e:
            logger.error(f"Error carving file at offset {offset}: {e}")

class FileSystemParser:
    """Engine A: Intelligent file system parsing"""
    
    def __init__(self):
        self.recovered_files = []
    
    def detect_file_system(self, drive_handle: BinaryIO) -> FileSystemType:
        """Detect the file system type"""
        try:
            # Read boot sector
            drive_handle.seek(0)
            boot_sector = drive_handle.read(512)
            
            # Check for NTFS
            if b'NTFS' in boot_sector[3:11]:
                return FileSystemType.NTFS
            
            # Check for FAT32
            if b'FAT32' in boot_sector[82:87]:
                return FileSystemType.FAT32
            
            # Check for exFAT
            if b'EXFAT' in boot_sector[3:8]:
                return FileSystemType.EXFAT
                
        except Exception as e:
            logger.error(f"Error detecting file system: {e}")
        
        return FileSystemType.UNKNOWN
    
    def parse_ntfs(self, drive_handle: BinaryIO, output_dir: Path,
                   progress_callback=None) -> List[RecoveredFile]:
        """Parse NTFS file system (simplified implementation)"""
        logger.info("Starting NTFS parsing (basic implementation)")
        # This is a placeholder for the complex NTFS parsing logic
        # In a full implementation, this would:
        # 1. Locate and read the MFT
        # 2. Parse MFT records
        # 3. Rebuild directory structure
        # 4. Extract files using data runs
        
        # For now, return empty list with a note
        logger.warning("NTFS parsing not yet implemented in starter version")
        return []

class PhoenixGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Project Phoenix - Data Recovery")
        self.root.geometry("800x600")
        
        # Initialize components
        self.signature_db = FileSignatureDatabase()
        self.carver = RawDataCarver(self.signature_db)
        self.parser = FileSystemParser()
        
        # GUI variables
        self.source_drive = tk.StringVar()
        self.dest_dir = tk.StringVar()
        self.scan_mode = tk.StringVar(value=RecoveryMode.DEEP_SCAN.value)
        self.progress_var = tk.DoubleVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create the main GUI layout"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Project Phoenix Data Recovery",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Source drive selection
        ttk.Label(main_frame, text="Source Drive:").grid(row=1, column=0, sticky=tk.W)
        source_combo = ttk.Combobox(main_frame, textvariable=self.source_drive,
                                   width=40, state="readonly")
        source_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # Refresh drives button
        refresh_btn = ttk.Button(main_frame, text="Refresh Drives",
                                command=self.refresh_drives)
        refresh_btn.grid(row=1, column=2, padx=(10, 0))
        
        # Destination directory
        ttk.Label(main_frame, text="Destination:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        dest_entry = ttk.Entry(main_frame, textvariable=self.dest_dir, width=40)
        dest_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0))
        
        browse_btn = ttk.Button(main_frame, text="Browse",
                               command=self.browse_destination)
        browse_btn.grid(row=2, column=2, padx=(10, 0), pady=(10, 0))
        
        # Scan mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Recovery Mode", padding="10")
        mode_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0))
        
        intelligent_radio = ttk.Radiobutton(mode_frame, text="Intelligent Scan (Recovers names & structure)",
                                          variable=self.scan_mode, value=RecoveryMode.INTELLIGENT.value)
        intelligent_radio.grid(row=0, column=0, sticky=tk.W)
        
        deep_radio = ttk.Radiobutton(mode_frame, text="Deep Scan (Raw data carving)",
                                    variable=self.scan_mode, value=RecoveryMode.DEEP_SCAN.value)
        deep_radio.grid(row=1, column=0, sticky=tk.W)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                          maximum=100, length=400)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to scan")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(20, 0))
        
        self.start_btn = ttk.Button(button_frame, text="Start Recovery",
                                   command=self.start_recovery, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop",
                                  command=self.stop_recovery, state="disabled")
        self.stop_btn.pack(side=tk.LEFT)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Initialize drives list
        self.refresh_drives()
    
    def refresh_drives(self):
        """Refresh the list of available drives"""
        drives = DiskAccessLayer.get_available_drives()
        drive_list = [f"{drive.device_path} - {drive.label} ({drive.size // (1024**3)} GB)"
                     for drive in drives]
        
        # Update combobox
        source_combo = None
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Combobox):
                        source_combo = child
                        break
        
        if source_combo:
            source_combo['values'] = drive_list
    
    def browse_destination(self):
        """Browse for destination directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.dest_dir.set(directory)
    
    def start_recovery(self):
        """Start the recovery process"""
        if not self.source_drive.get():
            messagebox.showerror("Error", "Please select a source drive")
            return
        
        if not self.dest_dir.get():
            messagebox.showerror("Error", "Please select a destination directory")
            return
        
        # Confirm operation
        result = messagebox.askyesno("Confirm Recovery", 
                                   f"Start recovery from {self.source_drive.get()}?\n"
                                   f"Destination: {self.dest_dir.get()}\n"
                                   f"Mode: {self.scan_mode.get()}")
        if not result:
            return
        
        # Disable start button, enable stop button
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # Start recovery in separate thread
        self.recovery_thread = threading.Thread(target=self._recovery_worker)
        self.recovery_thread.daemon = True
        self.recovery_thread.start()
    
    def stop_recovery(self):
        """Stop the recovery process"""
        # In a full implementation, this would signal the recovery thread to stop
        self.status_label.config(text="Stopping recovery...")
        
    def _recovery_worker(self):
        """Recovery worker thread"""
        try:
            # Extract drive path from selection
            drive_path = self.source_drive.get().split(' - ')[0]
            output_dir = Path(self.dest_dir.get())
            
            # Open drive
            self.root.after(0, lambda: self.status_label.config(text="Opening drive..."))
            drive_handle = DiskAccessLayer.open_drive_readonly(drive_path)
            
            if not drive_handle:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to open drive"))
                return
            
            try:
                if self.scan_mode.get() == RecoveryMode.DEEP_SCAN.value:
                    # Raw data carving
                    self.root.after(0, lambda: self.status_label.config(text="Performing deep scan..."))
                    recovered = self.carver.scan_drive(drive_handle, output_dir,
                                                     self._update_progress)
                else:
                    # Intelligent parsing
                    self.root.after(0, lambda: self.status_label.config(text="Analyzing file system..."))
                    fs_type = self.parser.detect_file_system(drive_handle)
                    self.root.after(0, lambda: self.status_label.config(text=f"Found {fs_type.value} file system"))
                    
                    if fs_type == FileSystemType.NTFS:
                        recovered = self.parser.parse_ntfs(drive_handle, output_dir,
                                                         self._update_progress)
                    else:
                        self.root.after(0, lambda: messagebox.showwarning("Warning", 
                                       f"{fs_type.value} parsing not yet implemented. Using deep scan."))
                        recovered = self.carver.scan_drive(drive_handle, output_dir,
                                                         self._update_progress)
                
                # Recovery complete
                self.root.after(0, lambda: self._recovery_complete(len(recovered)))
                
            finally:
                drive_handle.close()
                
        except Exception as e:
            logger.error(f"Recovery error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Recovery failed: {e}"))
        finally:
            # Re-enable controls
            self.root.after(0, self._reset_controls)
    
    def _update_progress(self, progress):
        """Update progress bar from worker thread"""
        self.root.after(0, lambda: self.progress_var.set(progress))
    
    def _recovery_complete(self, file_count):
        """Handle recovery completion"""
        self.status_label.config(text=f"Recovery complete! Found {file_count} files")
        messagebox.showinfo("Recovery Complete", f"Successfully recovered {file_count} files!")
    
    def _reset_controls(self):
        """Reset control states after recovery"""
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress_var.set(0)
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    # Check for admin privileges
    if sys.platform == "win32":
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                messagebox.showerror("Error", "Please run as Administrator")
                return
        except:
            pass
    
    # Create and run application
    app = PhoenixGUI()
    app.run()

if __name__ == "__main__":
    main()