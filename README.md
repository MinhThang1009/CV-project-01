# P3: Object Tracking in Video

Dự án thực hành Thị giác Máy — Theo dõi đối tượng bằng **Pyramid Lucas-Kanade** + **Shi-Tomasi** feature detection.

## Project Structure

```
├── README.md                  # Project overview
├── requirements.txt           # Python dependencies
├── .gitignore
│
├── data_survey.py             # P3.4.1 - Dataset analysis (lighting, motion, scene)
├── tracker.py                 # P3.4.2 - Object tracker (Pyramid LK + Shi-Tomasi)
├── experiment.py              # P3.4.3 & P3.4.4 - Experiments & evaluation
│
├── data/                      # Input: image sequences (6 datasets)
│   ├── kite-surf/             #   50 frames - kite surfer
│   ├── lab-coat/              #   47 frames - person in lab coat
│   ├── libby/                 #   49 frames - fast motion
│   ├── pigs/                  #   79 frames - complex background
│   ├── shooting/              #   40 frames - lighting change
│   └── soapbox/               #   99 frames - soapbox car
│
├── output/                    # Output: tracking results
│   ├── kite-surf_win15/       #   tracking_*.mp4 + frame_*.jpg + trajectory_*.csv
│   ├── kite-surf_win21/
│   ├── kite-surf_win31/
│   └── soapbox_win21/
│
├── reports/                   # Evaluation reports & charts
│   ├── data_survey_results.csv
│   ├── survey_brightness.jpg
│   ├── compare_winsize_kite-surf.jpg
│   ├── compare_datasets_win21.jpg
│   ├── points_winsize_kite-surf.jpg
│   ├── points_datasets_win21.jpg
│   ├── eval_winsize_kite-surf.txt
│   └── eval_datasets_win21.txt
│
└── docs/                      # Documentation
    ├── report.md              #   Project report (báo cáo)
    └── assignment.md          #   Assignment specification (đề bài)
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
```

## Usage

```bash
# 1. Dataset survey (P3.4.1)
python data_survey.py --dataset all --no_display

# 2. Object tracking (P3.4.2) - select ROI with mouse
python tracker.py --dataset kite-surf --win_size 21

# 3. Tracking with predefined bbox (headless)
python tracker.py --dataset kite-surf --bbox 210 140 260 270 --no_display

# 4. Experiments & evaluation (P3.4.3 + P3.4.4)
python experiment.py --no_display
```

## Results

| Dataset   | WinSize | Stability (std) | Survival % | Jitter % |
|-----------|---------|-----------------|-----------|----------|
| kite-surf | 15      | 7.20            | 11.5      | 0.0      |
| kite-surf | 21      | **7.14**        | 15.0      | 0.0      |
| kite-surf | 31      | 7.16            | 20.5      | 0.0      |
| soapbox   | 21      | **4.38**        | 15.8      | 0.0      |

See [docs/report.md](docs/report.md) for the full report.
