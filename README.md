# P3: Object Tracking in Video

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5%2B-green?logo=opencv&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.20%2B-013243?logo=numpy&logoColor=white)

Feature-based object tracking using **Pyramid Lucas-Kanade** optical flow and **Shi-Tomasi** corner detection with forward-backward consistency checking.

## Demo

| Frame 0 (Init) | Frame 25 (Mid) | Frame 49 (End) |
|:---:|:---:|:---:|
| ![frame0](output/kite-surf_win21/frame_0000.jpg) | ![frame25](output/kite-surf_win21/frame_0025.jpg) | ![frame49](output/kite-surf_win21/frame_0049.jpg) |

> 🟢 Green box = bounding box &nbsp;|&nbsp; 🔴 Red dots = tracked features &nbsp;|&nbsp; 🔵 Cyan lines = trajectory trails

## Features

- **Pyramid Lucas-Kanade** (3-level) for large motion estimation
- **Shi-Tomasi** corner detection for trackable feature selection
- **Forward-Backward** consistency check for outlier rejection
- **Median displacement** for robust bounding box update
- **Auto re-detection** when tracked points drop below threshold
- Outputs: tracking video (`.mp4`), trajectory data (`.csv`), annotated frames (`.jpg`)

## Project Structure

```
├── data_survey.py             # Dataset analysis (lighting, motion, complexity)
├── tracker.py                 # Core tracking pipeline
├── experiment.py              # Automated experiments & evaluation
│
├── data/                      # Input image sequences (6 datasets)
├── output/                    # Tracking results (videos, frames, CSV)
├── reports/                   # Evaluation charts & metrics
└── docs/                      # Report & assignment spec
```

## Setup

**Prerequisites**: Python 3.8+

```bash
git clone https://github.com/MinhThang1009/CV-project-01.git
cd CV-project-01

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux/Mac

pip install -r requirements.txt
```

## Usage

```bash
# Dataset survey
python data_survey.py --dataset all --no_display

# Object tracking (interactive ROI selection)
python tracker.py --dataset kite-surf --win_size 21

# Headless tracking with predefined bbox
python tracker.py --dataset kite-surf --bbox 210 140 260 270 --no_display

# Run all experiments & generate evaluation reports
python experiment.py --no_display
```

## Results

### Window Size Comparison (`kite-surf`)

| WinSize | Stability (std↓) | Survival % ↑ | Avg Disp (px) | Jitter % ↓ |
|:-------:|:-----------------:|:------------:|:-------------:|:----------:|
| 15×15   | 7.20              | 11.5         | 11.18         | 0.0        |
| **21×21** | **7.14**        | 15.0         | 11.24         | **0.0**    |
| 31×31   | 7.16              | **20.5**     | 11.13         | 0.0        |

### Cross-Dataset Comparison (winSize=21)

| Dataset   | Stability (std↓) | Survival % ↑ | Avg Points | Jitter % ↓ |
|:---------:|:-----------------:|:------------:|:----------:|:----------:|
| kite-surf | 7.14              | 15.0         | 40         | 0.0        |
| **soapbox** | **4.38**        | 15.8         | **72**     | **0.0**    |

> **Key findings**: `winSize=21` provides the best stability. Slower-moving objects (`soapbox`) are easier to track. All configurations achieve 0% jitter rate.

## Method Overview

```
Frame₀ ──► Gaussian Blur ──► Shi-Tomasi Detection ──► Initial Points P₀
                                                           │
Frame_i ──► Gaussian Blur ──► Pyramid LK (3 levels) ◄─────┘
                                   │
                          Forward-Backward Check
                                   │
                          Median Displacement
                                   │
                          Update BBox + Trails
                                   │
                    Points < 10? ──► Re-detect Shi-Tomasi
```

## References

- **Lucas & Kanade** (1981). *An iterative image registration technique with an application to stereo vision.*
- **Shi & Tomasi** (1994). *Good features to track.*
- **Bouguet** (2000). *Pyramidal implementation of the Lucas-Kanade feature tracker.*

## Documentation

- 📄 [Project Report](docs/report.md) — Full analysis, methodology, and results
- 📋 [Assignment Specification](docs/assignment.md) — Original requirements
