# Project Phoenix - File System-Aware Data Recovery Utility

![Project Phoenix Logo](https://img.shields.io/badge/Project-Phoenix-orange.svg)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)

## 🔥 Overview

Project Phoenix is a powerful, file system-aware data recovery utility designed to overcome the limitations of traditional data carvers. Unlike tools that only recover file data, Phoenix prioritizes the complete restoration of user data including original filenames, timestamps, and folder hierarchies.

## ✨ Key Features

- **🧠 Intelligent Recovery**: Parses file system metadata to rebuild directory structures
- **🔍 Deep Scan Mode**: Raw data carving for severely damaged drives
- **📁 Structure Preservation**: Maintains original filenames and folder hierarchies
- **🛡️ Safety First**: Read-only access to source drives with multiple safeguards
- **🎯 Multi-Format Support**: Handles NTFS, FAT32, exFAT file systems
- **📊 Progress Tracking**: Real-time progress monitoring and detailed logging

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Administrator/root privileges
- Windows: `pywin32` package

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/project-phoenix.git
cd project-phoenix

# Install dependencies
pip install -r requirements.txt

# Run as administrator
python phoenix_recovery.py

