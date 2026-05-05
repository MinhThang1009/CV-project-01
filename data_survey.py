"""
P3.4.1 - Khảo sát dữ liệu (Data Survey)
=========================================
Khảo sát tập dữ liệu video nhằm xác định đặc điểm của đối tượng cần
theo dõi và các yếu tố có thể ảnh hưởng đến kết quả (plan.txt dòng 16).

Phần khảo sát làm rõ:
  - Số lượng đối tượng
  - Kích thước đối tượng trong ảnh
  - Hướng chuyển động
  - Mức độ che khuất
  - Thay đổi chiếu sáng
  - Độ phức tạp của cảnh nền

Cách dùng:
    python data_survey.py                      # Mặc định: kite-surf
    python data_survey.py --dataset soapbox    # Chọn dataset
    python data_survey.py --dataset all        # Xem tất cả dataset

Phím tắt khi xem:
    Space  : pause / resume
    Q / Esc: thoát
    N      : next dataset (khi --dataset all)
"""

import argparse
import glob
import os
import csv

import cv2
import numpy as np

# ─── Đường dẫn dữ liệu ────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

DATASETS = sorted([
    d for d in os.listdir(DATA_DIR)
    if os.path.isdir(os.path.join(DATA_DIR, d))
])


def load_frames(dataset_name: str) -> list:
    """Đọc tất cả ảnh .jpg từ thư mục dataset, sắp xếp theo tên."""
    folder = os.path.join(DATA_DIR, dataset_name)
    paths = sorted(glob.glob(os.path.join(folder, "*.jpg")))
    if not paths:
        print(f"[!] Không tìm thấy ảnh trong: {folder}")
        return []
    frames = [cv2.imread(p) for p in paths]
    return frames


def survey_dataset(dataset_name: str) -> dict:
    """Trả về thông tin thống kê cơ bản của một dataset."""
    folder = os.path.join(DATA_DIR, dataset_name)
    paths = sorted(glob.glob(os.path.join(folder, "*.jpg")))
    if not paths:
        return {}
    sample = cv2.imread(paths[0])
    h, w = sample.shape[:2]
    info = {
        "name": dataset_name,
        "num_frames": len(paths),
        "resolution": f"{w} x {h}",
        "width": w,
        "height": h,
    }
    return info


def analyze_dataset(dataset_name: str) -> dict:
    """
    Phân tích chi tiết một dataset theo yêu cầu P3.4.1:
      - Thay đổi chiếu sáng (brightness variation)
      - Tốc độ / hướng chuyển động (optical flow trung bình)
      - Độ phức tạp cảnh nền (edge density)
      - Biến đổi cường độ sáng theo frame
    """
    frames = load_frames(dataset_name)
    if not frames or len(frames) < 2:
        return {}

    h, w = frames[0].shape[:2]
    n = len(frames)

    # --- Phân tích chiếu sáng ---
    brightness_per_frame = []
    for f in frames:
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        brightness_per_frame.append(np.mean(gray))

    brightness_arr = np.array(brightness_per_frame)
    brightness_std = float(np.std(brightness_arr))
    brightness_range = float(brightness_arr.max() - brightness_arr.min())

    # --- Phân tích chuyển động (optical flow trung bình giữa các cặp frame) ---
    flow_magnitudes = []
    flow_angles = []
    for i in range(min(n - 1, 30)):  # Lấy mẫu tối đa 30 cặp
        g1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        g2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(g1, g2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        flow_magnitudes.append(float(np.mean(mag)))
        # Hướng chuyển động chủ đạo (góc trung bình, theo độ)
        flow_angles.append(float(np.degrees(np.mean(ang))))

    avg_flow_mag = float(np.mean(flow_magnitudes)) if flow_magnitudes else 0
    max_flow_mag = float(np.max(flow_magnitudes)) if flow_magnitudes else 0
    avg_flow_dir = float(np.mean(flow_angles)) if flow_angles else 0

    # --- Độ phức tạp cảnh nền (edge density trung bình) ---
    edge_densities = []
    for f in frames[::max(1, n // 5)]:  # Lấy mẫu 5 frame
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_densities.append(float(np.sum(edges > 0) / (h * w) * 100))

    avg_edge_density = float(np.mean(edge_densities))

    # --- Phân loại mức độ ---
    if avg_flow_mag < 1.0:
        motion_level = "Chậm"
    elif avg_flow_mag < 3.0:
        motion_level = "Trung bình"
    else:
        motion_level = "Nhanh"

    if brightness_std < 3.0:
        lighting_change = "Ổn định"
    elif brightness_std < 8.0:
        lighting_change = "Thay đổi nhẹ"
    else:
        lighting_change = "Thay đổi mạnh"

    if avg_edge_density < 5.0:
        scene_complexity = "Đơn giản"
    elif avg_edge_density < 12.0:
        scene_complexity = "Trung bình"
    else:
        scene_complexity = "Phức tạp"

    analysis = {
        "name": dataset_name,
        "num_frames": n,
        "resolution": f"{w}x{h}",
        "avg_brightness": float(np.mean(brightness_arr)),
        "brightness_std": brightness_std,
        "brightness_range": brightness_range,
        "lighting_change": lighting_change,
        "avg_flow_magnitude": avg_flow_mag,
        "max_flow_magnitude": max_flow_mag,
        "avg_flow_direction_deg": avg_flow_dir,
        "motion_level": motion_level,
        "avg_edge_density_pct": avg_edge_density,
        "scene_complexity": scene_complexity,
        "brightness_per_frame": brightness_per_frame,
        "flow_magnitudes": flow_magnitudes,
    }
    return analysis


def print_detailed_analysis(analysis: dict):
    """In phân tích chi tiết của một dataset theo yêu cầu P3.4.1."""
    if not analysis:
        return

    print(f"\n{'─'*60}")
    print(f"  PHÂN TÍCH: {analysis['name']}")
    print(f"{'─'*60}")
    print(f"  Số khung hình      : {analysis['num_frames']}")
    print(f"  Độ phân giải       : {analysis['resolution']}")
    print(f"  ")
    print(f"  ▸ Chiếu sáng:")
    print(f"    Độ sáng trung bình: {analysis['avg_brightness']:.1f}")
    print(f"    Biến thiên (std)  : {analysis['brightness_std']:.2f}")
    print(f"    Khoảng biến thiên : {analysis['brightness_range']:.1f}")
    print(f"    → Đánh giá        : {analysis['lighting_change']}")
    print(f"  ")
    print(f"  ▸ Chuyển động:")
    print(f"    Tốc độ TB (px/frame): {analysis['avg_flow_magnitude']:.2f}")
    print(f"    Tốc độ max          : {analysis['max_flow_magnitude']:.2f}")
    print(f"    Hướng TB (độ)       : {analysis['avg_flow_direction_deg']:.1f}")
    print(f"    → Đánh giá          : {analysis['motion_level']}")
    print(f"  ")
    print(f"  ▸ Cảnh nền:")
    print(f"    Mật độ cạnh TB (%) : {analysis['avg_edge_density_pct']:.2f}%")
    print(f"    → Đánh giá         : {analysis['scene_complexity']}")
    print(f"{'─'*60}")


def save_analysis_csv(all_analyses: list):
    """Lưu kết quả phân tích vào file CSV cho báo cáo."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    csv_path = os.path.join(REPORT_DIR, "data_survey_results.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Dataset", "Frames", "Resolution",
            "Brightness_Avg", "Brightness_Std", "Lighting_Change",
            "Flow_Avg_px", "Flow_Max_px", "Flow_Dir_deg", "Motion_Level",
            "Edge_Density_pct", "Scene_Complexity"
        ])
        for a in all_analyses:
            writer.writerow([
                a["name"], a["num_frames"], a["resolution"],
                f"{a['avg_brightness']:.1f}", f"{a['brightness_std']:.2f}",
                a["lighting_change"],
                f"{a['avg_flow_magnitude']:.2f}", f"{a['max_flow_magnitude']:.2f}",
                f"{a['avg_flow_direction_deg']:.1f}", a["motion_level"],
                f"{a['avg_edge_density_pct']:.2f}", a["scene_complexity"]
            ])

    print(f"\n  Kết quả phân tích lưu tại: {csv_path}")


def save_brightness_chart(all_analyses: list):
    """Tạo biểu đồ brightness theo frame cho mỗi dataset."""
    chart_w, chart_h = 800, 400
    margin = 60
    chart = np.ones((chart_h, chart_w, 3), dtype=np.uint8) * 255
    colors = [(0, 0, 255), (255, 0, 0), (0, 180, 0), (200, 0, 200), (0, 128, 255), (128, 128, 0)]

    max_frames = max(len(a["brightness_per_frame"]) for a in all_analyses)
    all_bright = [v for a in all_analyses for v in a["brightness_per_frame"]]
    min_b, max_b = min(all_bright), max(all_bright)
    b_range = max_b - min_b if max_b > min_b else 1.0

    for idx, a in enumerate(all_analyses):
        data = a["brightness_per_frame"]
        color = colors[idx % len(colors)]
        for i in range(1, len(data)):
            x1 = margin + int((i-1) / max_frames * (chart_w - 2*margin))
            y1 = chart_h - margin - int((data[i-1] - min_b) / b_range * (chart_h - 2*margin))
            x2 = margin + int(i / max_frames * (chart_w - 2*margin))
            y2 = chart_h - margin - int((data[i] - min_b) / b_range * (chart_h - 2*margin))
            cv2.line(chart, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

        ly = 15 + idx * 20
        cv2.line(chart, (chart_w - 200, ly), (chart_w - 175, ly), color, 2)
        cv2.putText(chart, a["name"], (chart_w - 170, ly + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)

    cv2.line(chart, (margin, margin), (margin, chart_h - margin), (0, 0, 0), 1)
    cv2.line(chart, (margin, chart_h - margin), (chart_w - margin, chart_h - margin), (0, 0, 0), 1)
    cv2.putText(chart, "Frame", (chart_w // 2, chart_h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    cv2.putText(chart, "Brightness", (2, chart_h // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.putText(chart, "Brightness over Time - All Datasets", (margin, margin - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, "survey_brightness.jpg")
    cv2.imwrite(path, chart)
    print(f"  Biểu đồ chiếu sáng lưu tại: {path}")


def play_frames(frames: list, dataset_name: str, fps: int = 15):
    """Phát chuỗi ảnh dưới dạng video, hỗ trợ pause/resume."""
    if not frames:
        return False

    h, w = frames[0].shape[:2]
    win_name = f"Data Survey - {dataset_name}"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, min(w, 960), min(h, 720))

    delay = max(1, int(1000 / fps))
    paused = False
    idx = 0

    while idx < len(frames):
        frame = frames[idx].copy()

        info_text = [
            f"Dataset: {dataset_name}",
            f"Frame: {idx + 1}/{len(frames)}",
            f"Resolution: {w}x{h}",
            f"FPS: {fps}",
        ]
        if paused:
            info_text.append("[PAUSED] Space to resume")

        y0 = 30
        for i, txt in enumerate(info_text):
            y = y0 + i * 28
            cv2.putText(frame, txt, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.65, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(frame, txt, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.65, (0, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(win_name, frame)

        key = cv2.waitKey(0 if paused else delay) & 0xFF
        if key == ord('q') or key == 27:
            cv2.destroyAllWindows()
            return True
        elif key == ord(' '):
            paused = not paused
        elif key == ord('n'):
            break

        if not paused:
            idx += 1

    cv2.destroyAllWindows()
    return False


def print_summary_table():
    """In bảng tổng hợp thông tin tất cả dataset ra console."""
    print("\n" + "=" * 60)
    print(f"{'Dataset':<15} {'Frames':>8} {'Resolution':>15}")
    print("-" * 60)
    for ds in DATASETS:
        info = survey_dataset(ds)
        if info:
            print(f"{info['name']:<15} {info['num_frames']:>8} {info['resolution']:>15}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="P3.4.1 - Khảo sát dữ liệu Lab3")
    parser.add_argument(
        "--dataset", type=str, default="all",
        help=f"Tên dataset ({', '.join(DATASETS)}) hoặc 'all'"
    )
    parser.add_argument("--fps", type=int, default=15, help="FPS phát lại (mặc định 15)")
    parser.add_argument("--no_display", action="store_true",
                        help="Không hiển thị video, chỉ phân tích")
    args = parser.parse_args()

    # ─── Phần 1: Bảng tổng hợp ─────────────────────────────────────────
    print_summary_table()

    # ─── Phần 2: Phân tích chi tiết từng dataset (P3.4.1 core) ─────────
    if args.dataset.lower() == "all":
        targets = DATASETS
    else:
        if args.dataset not in DATASETS:
            print(f"[!] Dataset '{args.dataset}' không tồn tại. Có: {DATASETS}")
            return
        targets = [args.dataset]

    print("\n" + "#" * 60)
    print("  P3.4.1 - PHÂN TÍCH CHI TIẾT DỮ LIỆU")
    print("#" * 60)

    all_analyses = []
    for ds in targets:
        print(f"\n  Đang phân tích {ds}...", end=" ", flush=True)
        analysis = analyze_dataset(ds)
        if analysis:
            all_analyses.append(analysis)
            print("xong.")
            print_detailed_analysis(analysis)

    # Lưu kết quả phân tích
    if all_analyses:
        save_analysis_csv(all_analyses)
        save_brightness_chart(all_analyses)

    # ─── Phần 3: Nhận xét tổng hợp ─────────────────────────────────────
    if len(all_analyses) > 1:
        print(f"\n{'='*60}")
        print("  NHẬN XÉT TỔNG HỢP (P3.4.1)")
        print(f"{'='*60}")

        fastest = max(all_analyses, key=lambda a: a["avg_flow_magnitude"])
        slowest = min(all_analyses, key=lambda a: a["avg_flow_magnitude"])
        most_complex = max(all_analyses, key=lambda a: a["avg_edge_density_pct"])

        print(f"  • Dataset chuyển động nhanh nhất: {fastest['name']} "
              f"({fastest['avg_flow_magnitude']:.2f} px/frame)")
        print(f"  • Dataset chuyển động chậm nhất : {slowest['name']} "
              f"({slowest['avg_flow_magnitude']:.2f} px/frame)")
        print(f"  • Dataset cảnh nền phức tạp nhất: {most_complex['name']} "
              f"({most_complex['avg_edge_density_pct']:.2f}% edge)")

        varying_light = [a for a in all_analyses if a["brightness_std"] > 5.0]
        if varying_light:
            names = ", ".join(a["name"] for a in varying_light)
            print(f"  • Dataset có chiếu sáng thay đổi: {names}")
        else:
            print(f"  • Tất cả dataset có chiếu sáng tương đối ổn định.")

        print(f"\n  → Dự kiến: dataset '{fastest['name']}' sẽ khó theo dõi nhất")
        print(f"    do chuyển động nhanh (có thể vi phạm giả định chuyển động ngắn")
        print(f"    của Lucas-Kanade, cần Pyramid LK với nhiều mức).")
        print(f"{'='*60}")

    # ─── Phần 4: Phát video (nếu không tắt display) ────────────────────
    if not args.no_display:
        for ds in targets:
            print(f"\n>>> Đang phát: {ds}")
            frames = load_frames(ds)
            quit_signal = play_frames(frames, ds, fps=args.fps)
            if quit_signal:
                print("Thoát.")
                break

    print("\nKhảo sát hoàn tất.")


if __name__ == "__main__":
    main()
