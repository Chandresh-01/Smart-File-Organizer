# Smart File Organizer

A Python-based desktop application that organizes files into structured folders based on type, date, or size. The application ensures data safety by creating a copy of the selected folder before performing any operations.

---

## Overview

Smart File Organizer is designed to simplify file management by automatically categorizing files while preserving the original data. It provides a user-friendly graphical interface along with features like preview, undo functionality, and customizable rules.

---

## Features

* Safe copy mechanism to prevent data loss
* File organization by:
* Type (Images, Videos, Documents, etc.)
* Date (Year and Month)
* Size (Small, Medium, Large)
* Preview functionality before execution
* Undo last operation
* Custom rule management (add, edit, delete categories and extensions)
* Progress tracking with file count
* Activity logging
* Dark and light theme support

---

## Tech Stack

* Python
* Tkinter (GUI)
* Pathlib
* Shutil
* JSON (for configuration)
* Logging

---

## Project Structure

```id="projstruct01"
├── main.py                # GUI application
├── organizer_core.py      # Core logic for file organization
├── rules_manager.py       # Rule management system
├── config/
│   └── rules.json         # File categorization rules
├── logs/
│   ├── activity.log       # Operation logs
│   └── last_actions.json  # Undo tracking
```

---

## Requirements

* Python 3.8 or higher

This project uses only standard Python libraries. No external dependencies are required.

---

## How to Run

```bash id="runproj01"
python main.py
```

---

## Usage

1. Launch the application
2. Select a folder
3. Choose an organization mode (Type, Date, or Size)
4. (Optional) Modify rules using the Manage Rules option
5. Use Preview to review planned changes
6. Start the process using the safe copy option
7. Use Undo Last to revert changes if needed

---

## Important Notes

* The original folder is never modified

* A new folder is created in the same directory with the name:

  <original_folder>_Organized_Copy

* All operations are performed on the copied folder

---

## Future Enhancements

* Recursive folder organization
* Duplicate file detection
* Command-line interface version
* Packaging as a standalone executable

---

## Author

Chandresh (CJ)

---
