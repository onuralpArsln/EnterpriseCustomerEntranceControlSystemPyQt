# User Photo Capture Application

## Overview
This is a PyQt-based desktop application for capturing and managing user photos with timestamp tracking.

## Features
- Real-time camera feed
- Photo capture functionality
- User photo storage
- Metadata tracking with registration timestamps
- User list view
- Photo preview and details

## Prerequisites
- Python 3.7+
- PyQt5
- OpenCV
- Required libraries:
  ```
  pip install PyQt5 opencv-python
  ```

## Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/user-photo-capture.git
   cd user-photo-capture
   ```

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

## Running the Application
```
python user_photo_capture.py
```

## Usage Guide

### Capturing a Photo
1. Launch the application
2. Click 'Snap Photo'
3. Enter user name
4. Click 'Save User'

### Viewing Users
- Click on a username in the left panel
- View photo and registration details
- Return to capture screen with 'Back to Capture'

## Project Structure
```
project_root/
│
├── users/
│   ├── user_metadata.json  # User registration metadata
│   └── *.jpg               # User photos
│
├── user_photo_capture.py   # Main application script
└── README.md               # This documentation
```

## Metadata Storage
- Users are stored in `users/` directory
- Metadata tracked in `user_metadata.json`
- Includes:
  - Photo path
  - Registration timestamp

## Troubleshooting
- Ensure camera is connected
- Check Python and library versions
- Verify camera permissions

## Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create pull request

## License
[Specify your license here]

## Contact
[Your contact information]