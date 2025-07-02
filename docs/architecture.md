# Project Phoenix - Architecture Overview

## 1. High-Level Design
- Diagram of the layered architecture (UI -> Orchestration -> Engines -> Disk Access).
- Explanation of each layer's responsibility.

## 2. Engine A: The File System Parser
- Detailed explanation of the parsing logic.
- **NTFS:** How the MFT is located and parsed. How data runs are interpreted to reassemble fragmented files. How deleted files are identified.
- **FAT32/exFAT:** How the File Allocation Table is used as a linked list to find file clusters.

## 3. Engine B: The Raw Data Carver
- Explanation of the file signature database.
- The logic for scanning, identifying headers, and carving until a footer or max size is reached.
- How it handles overlapping files.

## 4. Low-Level Disk Access Layer
- How platform-specific handles are used to get raw, read-only access to a physical drive.
- Windows: `\\.\PhysicalDriveN`
- Linux/macOS: `/dev/sdX` or `/dev/diskN`
- The importance of read-only enforcement at this layer.