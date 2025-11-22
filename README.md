# YOLOv11 Object Detection Web Application

A real-time object detection web application powered by YOLOv11, featuring a modern React frontend and Flask backend.

## 📋 Overview

This project implements YOLOv11 (You Only Look Once version 11) for real-time object detection through an intuitive web interface. Users can upload images or use their webcam to detect and identify objects with bounding boxes and confidence scores.

## ✨ Features

- 🖼️ **Image Upload Detection** - Upload images and get instant object detection results
- 🎨 **Modern UI** - Clean and responsive interface built with React

## 🛠️ Tech Stack

### Frontend
- React.js
- Vite
- Axios for API calls
- Modern CSS/Tailwind 

### Backend
- Python 3.x
- Flask
- YOLOv11 (Ultralytics)
- OpenCV
- PyTorch

## 📦 Prerequisites

Before running this project, make sure you have:

- **Node.js** (v16 or higher)
- **npm**
- **Python** (v3.8 or higher)
- **pip** (Python package manager)
- **Git** (for cloning the repository)

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
# Using Git
git clone https://github.com/josephsbtn/Project_Deep_Learning.git
cd Project_Deep_Learning

# Or download the ZIP file and extract it
```

### 2. Setup Frontend

```bash
# Navigate to frontend directory
cd yolov11-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will run on `http://localhost:5173` (or the port shown in terminal). Click the localhost link to open it in your browser.

### 3. Setup Backend

Open a new terminal window and:

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run the Flask server
python app.py
```

The backend API will run on `http://localhost:5000` (default Flask port).

## 💡 Usage

1. Make sure both frontend and backend servers are running
2. Open your browser and navigate to the frontend URL (usually `http://localhost:5173`)
3. Choose one of the detection options:
   - **Upload Image**: Click to upload an image from your device
   - **Use Webcam**: Enable webcam for real-time detection
4. View the detection results with bounding boxes and labels

## 📁 Project Structure

```
Project_Deep_Learning/
├── yolov11-frontend/          # React frontend application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── backend/                    # Flask backend API
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   └── models/                # YOLOv11 model files
└── README.md
```

## 👤👤👤👤 Contributor

**Joseph Sebastian**
- GitHub: [@josephsbtn](https://github.com/josephsbtn)

**William Prasetyo Utomo**
- GitHub: [@WyVern28](https://github.com/WyVern28)

  **Ferdinand Putra Nugroho**
- GitHub: [@dinandputra](https://github.com/dinandputra)

  **Zaidaan Faros Noland**
- GitHub: [@NolandDotU](https://github.com/NolandDotU)

---
