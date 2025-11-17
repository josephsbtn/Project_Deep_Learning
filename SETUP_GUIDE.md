# YOLOv11 Project - Setup Guide

## Prerequisites
- Python 3.8+ (tested with Python 3.13)
- Node.js 16+ and npm
- Git

## Project Structure
```
Project_Deep_Learning/
├── backend/              # Flask API Backend
│   ├── app.py           # Main Flask application
│   ├── requirements.txt # Python dependencies
│   ├── model/           # YOLO model
│   └── utils/           # Utility functions
│
└── yolov11-frontend/    # React TypeScript Frontend
    ├── src/
    │   ├── App.tsx      # Main application component
    │   ├── services/    # API service layer
    │   └── types/       # TypeScript type definitions
    └── package.json
```

## Backend Setup

### 1. Navigate to backend directory
```bash
cd backend
```

### 2. Create virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the backend server
```bash
python app.py
```

The backend will run on `http://localhost:5000`

## Frontend Setup

### 1. Navigate to frontend directory
```bash
cd yolov11-frontend
```

### 2. Install dependencies
```bash
npm install
```

### 3. Run the development server
```bash
npm run dev
```

The frontend will run on `http://localhost:5173` (default Vite port)

## Available Features

### 1. Enhancement
- Upload an image or video
- Select "Enhancement" mode
- Choose enhancement type: CLAHE, Histogram, Gamma, or Bilateral
- Adjust brightness (-100 to 100)
- Adjust contrast (-100 to 100)

### 2. Detect
- Upload an image
- Select "Detect" mode
- View detected objects with bounding boxes and labels
- See confidence scores for each detection

### 3. Tracking
- Upload an image or video
- Select "Tracking" mode
- Objects will be tracked with unique IDs

### 4. Counter (Line)
- Upload an image or video
- Select "Counter (Line)" mode
- View count of objects crossing the line
- See "Count In" and "Count Out" statistics

## API Endpoints

### Image Processing
- `POST /enhance-image` - Enhance image quality
- `POST /detect` - Detect objects in image
- `POST /track` - Track objects in image
- `POST /count-line` - Count objects crossing a line

### Polygon Zone
- `POST /create-polygon` - Create a polygon zone for counting
- `POST /count-polygon/<polygon_id>` - Count objects in polygon zone

### Video Processing
- `POST /process-video` - Process video with various options

### Utilities
- `GET /outputs` - List all output files
- `GET /download?filename=<name>` - Download a specific output file

## Troubleshooting

### Backend Issues

**Port 5000 already in use:**
```python
# In app.py, change the port:
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
```

**CORS errors:**
- Make sure `flask-cors` is installed
- Check that `CORS(app)` is called in app.py

### Frontend Issues

**API connection failed:**
- Make sure backend is running on port 5000
- Check the `API_BASE_URL` in `src/services/api.ts`
- Verify CORS is enabled in backend

**Port 5173 already in use:**
```bash
# Kill the process or change port in vite.config.ts
```

## Development Tips

### Hot Reload
- Backend: Flask debug mode is enabled by default
- Frontend: Vite provides hot module replacement (HMR)

### Testing API Endpoints
You can test endpoints using tools like:
- Postman
- cURL
- Thunder Client (VS Code extension)

Example cURL command:
```bash
curl -X POST http://localhost:5000/detect \
  -F "file=@path/to/image.jpg"
```

## Production Deployment

### Backend
1. Set `debug=False` in app.py
2. Use production WSGI server like Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend
1. Build the production bundle:
```bash
npm run build
```

2. Serve the `dist` folder using a web server (nginx, Apache, etc.)

## Notes
- Make sure both backend and frontend are running simultaneously
- The backend processes files and returns base64-encoded results
- Large video files may take time to process
- GPU acceleration is available if CUDA is properly configured
