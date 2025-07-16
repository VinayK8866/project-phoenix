# Project Phoenix - Data Recovery Software
# Final Refactored Implementation using pytsk3

import os
import sys
import logging
from typing import List, Dict, Optional, BinaryIO
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# Dependency for Filesystem Forensics
try:
    import pytsk3
except ImportError:
    # Corrected, helpful error message
    messagebox.showerror("Dependency Missing", "The 'pytsk3' library is not installed.\nPlease activate your virtual environment and run:\n\npython -m pip install pytsk3")
    pytsk3 = None  # Set to None to handle failure gracefull

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phoenix_recovery.log', 'w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Phoenix')
logger.setLevel(logging.DEBUG)


class RecoveryMode(Enum):
    INTELLIGENT = "intelligent"
    DEEP_SCAN = "deep_scan"
    NORMAL = "normal"


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
    max_size: int = 100 * 1024 * 1024


@dataclass
class RecoveredFile:
    """Represents a file found during recovery"""
    name: str
    size: int
    offset: int
    file_type: str
    is_deleted: bool = False
    parent_path: str = ""
    timestamps: Optional[Dict[str, str]] = field(default_factory=dict)


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
            FileSignature("JPEG", [".jpg", ".jpeg"], b'\xFF\xD8\xFF', b'\xFF\xD9', 20 * 1024 * 1024),
            FileSignature("PNG", [".png"], b'\x89PNG\r\n\x1a\n', b'IEND\xaeB`\x82', 20 * 1024 * 1024),
            FileSignature("GIF", [".gif"], b'GIF8', b'\x00\x3B', 15 * 1024 * 1024),
            FileSignature("BMP", [".bmp"], b'BM', max_size=30 * 1024 * 1024),
            FileSignature("PDF", [".pdf"], b'%PDF-', b'%%EOF', 50 * 1024 * 1024),
            FileSignature("ZIP", [".zip", ".docx", ".xlsx", ".pptx"], b'PK\x03\x04', b'PK\x05\x06'),
            FileSignature("DOC", [".doc"], b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', max_size=50 * 1024 * 1024),
            FileSignature("MP4", [".mp4", ".mov"], b'\x00\x00\x00\x18ftyp', max_size=4 * 1024 * 1024 * 1024),
            FileSignature("AVI", [".avi"], b'RIFF', max_size=4 * 1024 * 1024 * 1024),
            FileSignature("MP3", [".mp3"], b'ID3', max_size=20 * 1024 * 1024),
            FileSignature("WAV", [".wav"], b'RIFF', max_size=1024 * 1024 * 1024),
        ]
        self.max_header_len = max(len(s.header) for s in self.signatures)

    def get_signature_by_header(self, data: bytes) -> Optional[FileSignature]:
        for sig in self.signatures:
            if data.startswith(sig.header):
                return sig
        return None


class DiskAccessLayer:
    """Low-level disk access with read-only safety"""
    @staticmethod
    def is_admin() -> bool:
        try:
            if sys.platform == "win32":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception as e:
            logger.error(f"Admin check failed: {e}")
            return False

    @staticmethod
    def get_available_drives() -> List[DriveInfo]:
        drives = []
        if sys.platform == "win32":
            try:
                import win32api, win32file
            except ImportError:
                return []

            drive_letters = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
            for drive in drive_letters:
                try:
                    drive_type = win32file.GetDriveType(drive)
                    if drive_type not in [win32file.DRIVE_FIXED, win32file.DRIVE_REMOVABLE]:
                        continue
                    _, total_bytes, _ = win32file.GetDiskFreeSpaceEx(drive)
                    vol_info = win32api.GetVolumeInformation(drive)
                    label = vol_info[0] or "Local Disk"
                    fs_type_str = vol_info[4]
                    file_system = FileSystemType(fs_type_str) if fs_type_str in [fs.value for fs in FileSystemType] else FileSystemType.UNKNOWN
                    device_path = drive.rstrip('\\')
                    drives.append(DriveInfo(device_path, label, total_bytes, file_system))
                except Exception as e:
                    logger.warning(f"Could not query drive {drive}: {e}")
        return drives

    @staticmethod
    def open_drive_readonly(device_path: str) -> Optional[BinaryIO]:
        try:
            if sys.platform == "win32":
                if not DiskAccessLayer.is_admin():
                    messagebox.showerror("Privilege Error", "Administrator privileges are required.\nPlease restart as an administrator.")
                    return None
                drive_path = f"\\\\.\\{device_path}"
                return open(drive_path, 'rb')
            else: # Linux/macOS
                if not DiskAccessLayer.is_admin():
                    messagebox.showerror("Privilege Error", "Root privileges (sudo) are required.")
                    return None
                return open(device_path, 'rb')
        except (PermissionError, FileNotFoundError, OSError) as e:
            logger.error(f"Failed to open drive {device_path}: {e}")
            messagebox.showerror("Drive Error", f"Could not open drive {device_path}:\n{e}")
            return None


class RawDataCarver:
    """Engine B: Raw data carving by searching for file signatures."""
    def __init__(self, signature_db: FileSignatureDatabase):
        self.signature_db = signature_db
        self.recovered_files = []
        self.sector_size = 512
        self.stop_requested = False

    def scan_drive(self, drive_handle: BinaryIO, drive_size: int, output_dir: Path, progress_callback=None) -> List[RecoveredFile]:
        self.recovered_files = []
        self.stop_requested = False
        file_counter = len(os.listdir(output_dir))

        drive_handle.seek(0)
        offset = 0
        logger.info(f"Starting raw data carving. Drive size: {drive_size} bytes.")

        while offset < drive_size and not self.stop_requested:
            if progress_callback and offset % (self.sector_size * 4096) == 0:  # Update progress every ~2MB
                progress = (offset / drive_size) * 100
                progress_callback(progress, f"Deep scanning at {offset / 1024**3:.2f} GB / {drive_size / 1024**3:.2f} GB")

            try:
                drive_handle.seek(offset)
                header_buffer = drive_handle.read(self.signature_db.max_header_len)
            except OSError:
                offset += self.sector_size
                continue

            if not header_buffer: break

            signature = self.signature_db.get_signature_by_header(header_buffer)
            if signature:
                carved_size = self._carve_file(signature, offset, drive_handle, output_dir, file_counter)
                if carved_size > 0:
                    file_counter += 1
                    offset += (carved_size // self.sector_size + 1) * self.sector_size
                else:
                    offset += self.sector_size
            else:
                offset += self.sector_size

        logger.info(f"Raw carving complete. Found {len(self.recovered_files)} files.")
        return self.recovered_files

    def _carve_file(self, signature: FileSignature, offset: int, drive_handle: BinaryIO, output_dir: Path, file_counter: int) -> int:
        try:
            drive_handle.seek(offset)
            ext = signature.extensions[0] if signature.extensions else ".bin"
            filename = f"carved_{offset:012d}_{signature.name.lower()}{ext}"
            output_path = output_dir / filename

            carved_size = 0
            chunk_size = 1048576  # 1MB
            with open(output_path, 'wb') as out_file:
                while carved_size < signature.max_size:
                    read_len = min(chunk_size, signature.max_size - carved_size)
                    chunk = drive_handle.read(read_len)
                    if not chunk: break

                    footer_pos = -1
                    if signature.footer:
                        footer_pos = chunk.find(signature.footer)

                    if footer_pos != -1:
                        out_file.write(chunk[:footer_pos + len(signature.footer)])
                        carved_size += footer_pos + len(signature.footer)
                        break
                    else:
                        out_file.write(chunk)
                        carved_size += len(chunk)

            self.recovered_files.append(RecoveredFile(filename, carved_size, offset, signature.name))
            return carved_size
        except Exception as e:
            logger.error(f"Error carving file {signature.name} at offset {offset}: {e}")
            return 0


class FileSystemParser:
    """Engine A: Intelligent file system parsing using the pytsk3 library."""
    def __init__(self):
        self.recovered_files = []
        self.stop_requested = False

    def detect_file_system(self, drive_handle: BinaryIO) -> FileSystemType:
        try:
            drive_handle.seek(0)
            boot_sector = drive_handle.read(512)
            if b'NTFS' in boot_sector[3:7]: return FileSystemType.NTFS
            if b'FAT32' in boot_sector[82:87]: return FileSystemType.FAT32
            if b'EXFAT' in boot_sector[3:8]: return FileSystemType.EXFAT
        except Exception:
            return FileSystemType.UNKNOWN
        return FileSystemType.UNKNOWN

    def parse_filesystem(self, drive_handle: BinaryIO, drive_size: int, output_dir: Path, progress_callback=None) -> List[RecoveredFile]:
        """Parses a filesystem using pytsk3, recovering files and directory structure."""
        logger.info("Starting intelligent filesystem parsing with pytsk3...")
        self.recovered_files = []

        if not pytsk3:
            logger.error("pytsk3 library is not available.")
            messagebox.showerror("Missing Library", "The pytsk3 library could not be imported. Intelligent Scan is not available.")
            return []
        
        try:
            img_info = pytsk3.Img_Info(stream=drive_handle)
            fs_info = pytsk3.FS_Info(img_info)
        except Exception as e:
            logger.error(f"Failed to open filesystem with pytsk3. Drive may be corrupt or unsupported. Error: {e}")
            messagebox.showerror("Filesystem Error", f"Could not open the filesystem. It may be damaged or not a supported format (e.g., NTFS, FAT, Ext).\n\nError: {e}")
            return []

        self._walk_directory(fs_info, fs_info.get_fs_info().root_inum, output_dir, progress_callback)
        
        logger.info(f"Intelligent parsing complete. Found {len(self.recovered_files)} files.")
        return self.recovered_files

    def _walk_directory(self, fs_info, dir_inum, current_path: Path, progress_callback):
        """Recursively walk a directory using its inode number and recover files."""
        if self.stop_requested:
            return

        try:
            directory = fs_info.open_dir(inode=dir_inum)
            # Simple progress update based on directory traversal
            if progress_callback:
                progress_callback(-1, f"Scanning folder: {current_path}") # Use -1 to indicate indeterminate progress
        except Exception as e:
            logger.warning(f"Could not open directory with inode {dir_inum}: {e}")
            return

        current_path.mkdir(parents=True, exist_ok=True)

        for f in directory:
            if self.stop_requested:
                break

            if not hasattr(f, "info") or not hasattr(f.info, "name") or not f.info.name:
                continue
            
            name_bytes = f.info.name.name
            if name_bytes in (b".", b".."):
                continue

            try:
                file_name = name_bytes.decode('utf-8')
            except UnicodeDecodeError:
                file_name = name_bytes.decode('latin-1', 'replace')

            # Sanitize filename for the host OS
            sanitized_name = "".join(c for c in file_name if c not in ('\\', '/', ':', '*', '?', '"', '<', '>', '|')).strip()
            if not sanitized_name:
                sanitized_name = f"unnamed_inode_{f.info.meta.addr}"
            
            output_path = current_path / sanitized_name

            if f.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                self._walk_directory(fs_info, f.info.meta.addr, output_path, progress_callback)
            
            elif f.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG and f.info.meta.size > 0:
                try:
                    file_size = f.info.meta.size
                    
                    with open(output_path, 'wb') as out_file:
                        out_file.write(f.read_random(0, file_size))
                    
                    recovered = RecoveredFile(
                        name=sanitized_name,
                        size=file_size,
                        offset=f.info.meta.addr,
                        file_type="File",
                        is_deleted=(f.info.meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC) != 0,
                        parent_path=str(current_path)
                    )
                    self.recovered_files.append(recovered)

                except Exception as e:
                    logger.warning(f"Failed to recover file '{file_name}': {e}")


class PhoenixGUI:
    """Main GUI application."""
    def __init__(self, master):
        self.master = master
        master.title("Project Phoenix - Data Recovery")
        self.root = master
        self.root.geometry("800x600")
        
        self.signature_db = FileSignatureDatabase()
        self.carver = RawDataCarver(self.signature_db)
        self.parser = FileSystemParser()
        
        self.source_drive = tk.StringVar()
        self.dest_dir = tk.StringVar()
        self.scan_mode = tk.StringVar(value=RecoveryMode.NORMAL.value)
        self.progress_var = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Ready to scan.")
        
        self.drive_map = {}
        self.recovery_thread = None
        
        self.create_widgets()
        self.refresh_drives()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Project Phoenix Data Recovery", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")
        
        ttk.Label(main_frame, text="1. Select Source Drive:").grid(row=1, column=0, sticky="w")
        self.source_combo = ttk.Combobox(main_frame, textvariable=self.source_drive, width=60, state="readonly")
        self.source_combo.grid(row=1, column=1, sticky="we", padx=(10, 0))
        ttk.Button(main_frame, text="Refresh", command=self.refresh_drives).grid(row=1, column=2, padx=(10, 0))
        
        ttk.Label(main_frame, text="2. Select Destination:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        dest_entry = ttk.Entry(main_frame, textvariable=self.dest_dir, width=60, state="readonly")
        dest_entry.grid(row=2, column=1, sticky="we", padx=(10, 0), pady=(10, 0))
        ttk.Button(main_frame, text="Browse...", command=self.browse_destination).grid(row=2, column=2, padx=(10, 0), pady=(10, 0))
        
        mode_frame = ttk.LabelFrame(main_frame, text="3. Choose Recovery Mode", padding="10")
        mode_frame.grid(row=3, column=0, columnspan=3, sticky="we", pady=(20, 0))
        
        ttk.Radiobutton(mode_frame, text="Intelligent Scan (Fast, recovers folder structure)", variable=self.scan_mode, value=RecoveryMode.INTELLIGENT.value).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="Deep Scan (Slow, finds files by signature)", variable=self.scan_mode, value=RecoveryMode.DEEP_SCAN.value).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="Normal Scan (Runs both, recommended)", variable=self.scan_mode, value=RecoveryMode.NORMAL.value).grid(row=2, column=0, sticky="w")
        
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky="we", pady=(20, 0))
        
        ttk.Label(main_frame, textvariable=self.status_text, wraplength=750).grid(row=5, column=0, columnspan=3, pady=(10, 0), sticky="w")
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(20, 0))
        
        self.start_btn = ttk.Button(button_frame, text="Start Recovery", command=self.start_recovery)
        self.start_btn.pack(side="left", padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_recovery, state="disabled")
        self.stop_btn.pack(side="left")

    def refresh_drives(self):
        self.status_text.set("Refreshing drive list...")
        self.root.update_idletasks()
        drives = DiskAccessLayer.get_available_drives()
        
        self.drive_map.clear()
        drive_list = [f"{d.label} ({d.device_path}) - {d.size / (1024**3):.2f} GB" for d in drives]
        for i, d in enumerate(drives):
            self.drive_map[drive_list[i]] = d

        self.source_combo['values'] = drive_list
        if drive_list:
            self.source_drive.set(drive_list[0])
            self.status_text.set("Ready to scan.")
        else:
            self.source_drive.set("")
            self.status_text.set("No drives found. Please restart as Administrator if on Windows.")
    
    def browse_destination(self):
        directory = filedialog.askdirectory(title="Select a Destination Folder")
        if directory:
            self.dest_dir.set(directory)
    
    def start_recovery(self):
        source_selection = self.source_drive.get()
        dest_path = self.dest_dir.get()

        if not source_selection or not dest_path:
            messagebox.showerror("Error", "Please select both a source drive and a destination.")
            return
        
        drive_info = self.drive_map.get(source_selection)
        if not drive_info:
            messagebox.showerror("Error", "Invalid drive selection. Please refresh the list.")
            return

        if Path(dest_path).resolve().drive == Path(drive_info.device_path).resolve().drive:
            if not messagebox.askyesno("Warning", "The destination is on the same drive as the source. This is NOT recommended. Continue anyway?"):
                return
        
        if not os.access(dest_path, os.W_OK):
            messagebox.showerror("Error", "The destination directory is not writable.")
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.source_combo.config(state="disabled")
        
        self.recovery_thread = threading.Thread(target=self._recovery_worker, daemon=True)
        self.recovery_thread.start()

    def stop_recovery(self):
        if self.recovery_thread and self.recovery_thread.is_alive():
            self.status_text.set("Stopping scan... Please wait.")
            self.carver.stop_requested = True
            self.parser.stop_requested = True
            self.stop_btn.config(state="disabled")

    def _recovery_worker(self):
        try:
            drive_info = self.drive_map[self.source_drive.get()]
            output_dir = Path(self.dest_dir.get())
            
            self._update_status(f"Opening drive {drive_info.device_path}...")
            drive_handle = DiskAccessLayer.open_drive_readonly(drive_info.device_path)
            
            if not drive_handle:
                self.root.after(0, self._reset_controls)
                return
            
            total_recovered_files = 0
            try:
                mode = self.scan_mode.get()
                
                if mode in (RecoveryMode.INTELLIGENT.value, RecoveryMode.NORMAL.value):
                    recovered = self.parser.parse_filesystem(drive_handle, drive_info.size, output_dir, self._update_progress)
                    total_recovered_files += len(recovered)

                if mode in (RecoveryMode.DEEP_SCAN.value, RecoveryMode.NORMAL.value):
                    recovered = self.carver.scan_drive(drive_handle, drive_info.size, output_dir, self._update_progress)
                    total_recovered_files += len(recovered)

                self.root.after(0, lambda: self._recovery_complete(total_recovered_files))
            finally:
                drive_handle.close()
                
        except Exception as e:
            logger.error(f"Critical error in recovery worker: {e}", exc_info=True)
            self.root.after(0, lambda error=e: messagebox.showerror("Recovery Failed", f"A critical error occurred: {error}"))
        finally:
            self.root.after(0, self._reset_controls)
    
    def _update_progress(self, progress, status_msg):
        def updater():
            if progress >= 0:
                self.progress_bar.config(mode='determinate')
                self.progress_var.set(progress)
            else:
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start(10)
            self.status_text.set(status_msg)
        self.root.after(0, updater)

    def _update_status(self, status_msg):
        def updater():
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.status_text.set(status_msg)
        self.root.after(0, updater)

    def _recovery_complete(self, file_count):
        if self.carver.stop_requested or self.parser.stop_requested:
            final_message = f"Scan stopped by user. Found {file_count} files so far."
        else:
            final_message = f"Scan complete! Found {file_count} potential files."
        
        self.status_text.set(final_message)
        messagebox.showinfo("Recovery Finished", f"{final_message}\nFiles have been saved to {self.dest_dir.get()}")
    
    def _reset_controls(self):
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_var.set(0)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.source_combo.config(state="readonly")
    
    def on_closing(self):
        if self.recovery_thread and self.recovery_thread.is_alive():
            if messagebox.askokcancel("Quit", "A scan is in progress. Are you sure you want to quit?"):
                self.stop_recovery()
                self.master.destroy()
        else:
            self.master.destroy()

    def run(self):
        self.root.mainloop()

def main():
    """Main entry point for the GUI application."""
    # Corrected check for pywin32
    if sys.platform == "win32":
        try:
            import win32api
        except ImportError:
            messagebox.showerror("Dependency Missing", "The 'pywin32' library is not installed.\nPlease activate your virtual environment and run:\n\npython -m pip install pywin32")
            return

    # Corrected check for pytsk3
    if not pytsk3:
        # The error is already shown by the import block at the top, so we just exit gracefully.
        logger.error("Exiting because pytsk3 library is missing.")
        return

    root = tk.Tk()
    app = PhoenixGUI(root)
    app.run()

if __name__ == "__main__":
    main()