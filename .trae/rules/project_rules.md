# Project Phoenix: File System-Aware Data Recovery Utility
## Complete Development & User Documentation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Design](#architecture-design)
3. [Core Principles](#core-principles)
4. [Technical Specifications](#technical-specifications)
5. [Development Methodology](#development-methodology)
6. [User Guide](#user-guide)
7. [Implementation Roadmap](#implementation-roadmap)
8. [System Requirements](#system-requirements)
9. [Safety Protocols](#safety-protocols)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

### Vision Statement
Project Phoenix is designed to be a comprehensive, file system-aware data recovery utility that prioritizes complete and structured restoration of user data, going beyond simple file carving to recover original filenames, timestamps, and folder hierarchies.

### Primary Objectives
- **Structure-First Recovery**: Parse file system metadata to rebuild original directory trees
- **Intelligent File Reassembly**: Correctly reassemble fragmented files using file system pointers
- **Hybrid Recovery Engine**: Provide both intelligent and deep scan recovery methods
- **Non-Destructive Operation**: Maintain strict read-only access to source drives

### Key Differentiators
Unlike traditional data carvers (such as PhotoRec), Project Phoenix employs a dual-engine approach that prioritizes intelligent recovery while maintaining fallback capabilities for severely damaged media.

---

## Architecture Design

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
├─────────────────────────────────────────────────────────────┤
│                  Orchestration Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Engine A               │              Engine B             │
│  File System Parser     │         Raw Data Carver          │
│  (Intelligent Recovery) │        (Deep Scan Recovery)      │
├─────────────────────────────────────────────────────────────┤
│                Low-Level Disk Access Layer                  │
└─────────────────────────────────────────────────────────────┘
```

### Engine A: File System Parser (Intelligent Recovery)

**Purpose**: Primary recovery engine that reads and interprets file system metadata

**Capabilities**:
- Recovers files with original names and attributes
- Maintains folder structure and hierarchy
- Handles fragmented files correctly
- Recovers deleted files with intact metadata

**Supported File Systems**:
- NTFS (Windows)
- FAT32/exFAT (Universal)
- APFS (macOS) - Future implementation
- ext4 (Linux) - Future implementation

### Engine B: Raw Data Carver (Deep Scan Recovery)

**Purpose**: Fallback recovery engine for severely damaged or formatted drives

**Capabilities**:
- Sector-by-sector analysis
- File signature recognition
- Recovery without file system dependency
- Generic file naming with sequential numbering

**File Type Support**:
- Images: JPEG, PNG, TIFF, BMP, GIF
- Documents: PDF, DOC, DOCX, TXT, RTF
- RAW Photos: CR2, NEF, ARW, DNG, RAF
- Video: MP4, AVI, MOV, MKV
- Audio: MP3, WAV, FLAC, AAC

---

## Core Principles

### 1. Non-Destructive Operation (Golden Rule)
- **Strict Read-Only Access**: Source drives are never written to
- **Source Protection**: Multiple safeguards prevent accidental writes
- **Data Integrity**: Original data remains untouched throughout process

### 2. User Safety Protocols
- **Explicit Confirmation**: Users must confirm source and destination drives
- **Clear Warnings**: Interface provides prominent safety warnings
- **Operation Logging**: All actions are logged for transparency

### 3. Transparency and Clarity
- **Detailed Reporting**: Comprehensive logs of recovery operations
- **Progress Tracking**: Real-time status updates during scanning
- **Result Explanation**: Clear explanations of what was and wasn't recoverable

---

## Technical Specifications

### File System Parser Implementation

#### NTFS Recovery Process

1. **Partition Discovery**
   - Read Master Boot Record (MBR) or GUID Partition Table (GPT)
   - Identify partition locations, sizes, and types
   - Validate partition integrity

2. **File System Identification**
   - Read Partition Boot Record (PBR)
   - Verify NTFS signature
   - Extract Master File Table (MFT) location

3. **MFT Processing**
   - Parse MFT records sequentially
   - Extract file attributes:
     - Filename and extension
     - Parent directory references
     - Timestamps (created, modified, accessed)
     - File size and attributes
     - Data run locations

4. **Directory Tree Reconstruction**
   - Build in-memory directory structure
   - Resolve parent-child relationships
   - Flag deleted but recoverable entries

5. **File Data Recovery**
   - Follow data runs to physical sectors
   - Reassemble fragmented files in correct order
   - Restore original filenames and folder structure

#### FAT32/exFAT Recovery Process

1. **Boot Sector Analysis**
   - Validate FAT signature
   - Extract File Allocation Table location
   - Determine cluster size and root directory location

2. **FAT Parsing**
   - Read File Allocation Table entries
   - Map cluster chains for each file
   - Identify free and bad clusters

3. **Directory Structure Recovery**
   - Parse directory entries
   - Extract long filename entries (VFAT)
   - Reconstruct folder hierarchy

### Raw Data Carver Implementation

#### File Signature Database Structure

```
File Type: JPEG
Header: FF D8 FF
Footer: FF D9
Max Size: 50MB
Extensions: .jpg, .jpeg

File Type: PDF
Header: %PDF-
Footer: %%EOF
Max Size: 100MB
Extensions: .pdf
```

#### Carving Algorithm

1. **Sequential Scan**
   - Read drive in 512KB chunks
   - Maintain overlap buffer for signature detection
   - Track current position and progress

2. **Signature Detection**
   - Search for known file headers in each chunk
   - Validate header integrity
   - Queue potential file starts

3. **Data Extraction**
   - Copy data from header to footer (if known)
   - Apply maximum file size limits
   - Handle incomplete files gracefully

---

## Development Methodology

### Phase 1: Foundation (Weeks 1-4)
**Objectives**:
- Core application framework
- Cross-platform disk access implementation
- Basic UI/UX design
- Engine B (Raw Data Carver) development

**Deliverables**:
- Functional data carver with 15+ file types
- Basic user interface
- Read-only disk access layer
- Initial safety protocols

### Phase 2: Intelligent Engine - NTFS (Weeks 5-10)
**Objectives**:
- Complete NTFS parser implementation
- MFT analysis and directory tree reconstruction
- Integration with main application
- Comprehensive testing with NTFS volumes

**Deliverables**:
- Fully functional NTFS recovery engine
- Directory tree visualization
- File preview capabilities
- Deleted file recovery

### Phase 3: Extended File System Support (Weeks 11-14)
**Objectives**:
- FAT32 and exFAT parser implementation
- Cross-file system compatibility
- Enhanced error handling
- Performance optimization

**Deliverables**:
- Multi-file system support
- Improved recovery speed
- Enhanced error reporting
- Automated file system detection

### Phase 4: Polish and Advanced Features (Weeks 15-18)
**Objectives**:
- UI/UX improvements
- Advanced filtering and search
- Custom signature support
- Performance benchmarking

**Deliverables**:
- Production-ready application
- Comprehensive documentation
- User manual and tutorials
- Performance optimization

---

## User Guide

### Getting Started

#### System Requirements
- **Windows**: Windows 10/11, Administrator privileges
- **macOS**: macOS 10.15+, root access
- **Linux**: Ubuntu 18.04+, sudo privileges
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Adequate space on destination drive

#### Installation
1. Download Project Phoenix installer
2. Run with administrative privileges
3. Follow installation wizard
4. Launch application as administrator

### Recovery Workflow

#### Step 1: Drive Selection
1. Launch Project Phoenix with administrator privileges
2. Review connected drives list
3. Select source drive (drive to recover from)
4. **Warning**: Ensure correct drive selection

#### Step 2: Destination Configuration
1. Select destination drive (different from source)
2. Choose recovery folder location
3. Verify adequate free space
4. Confirm write permissions

#### Step 3: Scan Mode Selection

**Intelligent Scan (Recommended)**
- Use for: Accidental deletion, minor corruption
- Benefits: Original names, folder structure, timestamps
- Time: Faster scan, depends on file system size

**Deep Scan (Advanced)**
- Use for: Formatted drives, severe corruption, unknown file systems
- Benefits: Maximum file recovery potential
- Time: Slower scan, depends on drive size

#### Step 4: Recovery Process
1. Review scan results in tree view
2. Select files and folders to recover
3. Apply filters if needed (file type, date, size)
4. Click "Recover Selected Items"
5. Monitor progress and wait for completion

#### Step 5: Verification
1. Review recovery report
2. Verify recovered files integrity
3. Check folder structure restoration
4. Document any issues for support

### Best Practices

#### Pre-Recovery
- Stop using the affected drive immediately
- Avoid installing software on the source drive
- Ensure destination drive has sufficient space
- Create drive image for critical recovery scenarios

#### During Recovery
- Do not interrupt the recovery process
- Monitor system resources
- Avoid running other disk-intensive applications
- Keep recovery logs for troubleshooting

#### Post-Recovery
- Verify file integrity before deleting originals
- Organize recovered files systematically
- Document recovery success rate
- Update backup procedures to prevent future loss

---

## Safety Protocols

### Data Protection Measures

#### Source Drive Protection
- **Read-Only Mount**: Source drives mounted in read-only mode
- **Write Prevention**: Multiple software locks prevent accidental writes
- **Hardware Protection**: Recommend write-blocking hardware when available

#### Operation Safety
- **Confirmation Dialogs**: Multiple confirmations for critical operations
- **Drive Validation**: Verify drive selection before proceeding
- **Process Monitoring**: Real-time monitoring of all disk operations

#### Error Handling
- **Graceful Degradation**: Continue operation despite minor errors
- **Comprehensive Logging**: Detailed error logs for troubleshooting
- **Safe Termination**: Clean shutdown procedures for all scenarios

### Warning Systems

#### Critical Warnings
- Source and destination drive selection
- Insufficient destination space
- Potential data overwrite scenarios
- System resource limitations

#### Informational Alerts
- Scan progress and estimated completion
- File system type detection results
- Recovery success statistics
- Performance optimization suggestions

---

## Troubleshooting

### Common Issues and Solutions

#### "Drive Not Detected"
**Symptoms**: Source drive not appearing in drive list
**Solutions**:
- Verify drive connection and power
- Check if drive appears in system disk management
- Try different USB port or cable
- Run application with elevated privileges

#### "Insufficient Permissions"
**Symptoms**: Cannot access drive or create recovery files
**Solutions**:
- Run application as administrator/root
- Check destination drive permissions
- Verify antivirus is not blocking access
- Ensure destination drive is not full

#### "Scan Interrupted"
**Symptoms**: Recovery process stops unexpectedly
**Solutions**:
- Check available system memory
- Verify destination drive has adequate space
- Disable power management for USB drives
- Close other applications to free resources

#### "No Files Found"
**Symptoms**: Scan completes but finds no recoverable files
**Solutions**:
- Try Deep Scan mode if using Intelligent Scan
- Verify correct source drive selection
- Check if drive is severely corrupted
- Consider professional data recovery services

### Performance Optimization

#### Scan Speed Improvement
- Close unnecessary applications
- Increase virtual memory allocation
- Use SSD for destination drive
- Scan specific folders instead of entire drive

#### Memory Management
- Monitor RAM usage during scan
- Adjust scan chunk size for available memory
- Use 64-bit version for large drives
- Consider drive imaging for repeated recovery attempts

---

## Technical Support

### Log Files and Diagnostics
- **Location**: `%APPDATA%/ProjectPhoenix/Logs/`
- **Content**: Detailed operation logs, error messages, performance metrics
- **Retention**: 30 days automatic retention

### Support Channels
- **Documentation**: Comprehensive online help system
- **Community**: User forums and knowledge base
- **Professional**: Premium support for enterprise users

### Reporting Issues
When reporting issues, please include:
- Project Phoenix version number
- Operating system and version
- Drive types and capacities
- Error messages and log files
- Steps to reproduce the issue

---

## Appendices

### Appendix A: Supported File Signatures
[Detailed list of supported file types and their signatures]

### Appendix B: File System Technical Details
[In-depth technical specifications for supported file systems]

### Appendix C: Performance Benchmarks
[Performance data and optimization guidelines]

### Appendix D: Legal and Compliance
[Software licensing, data protection compliance, and legal considerations]

---

*Document Version: 1.0*  
*Last Updated: [Current Date]*  
*Classification: Technical Documentation*