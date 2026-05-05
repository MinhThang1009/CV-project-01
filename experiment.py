"""
P3.4.3 & P3.4.4 - Triển khai, So sánh và Đánh giá
====================================================
Kịch bản thử nghiệm:
  1. So sánh winSize: 15 vs 21 vs 31 trên cùng dataset
  2. So sánh dataset: kite-surf vs soapbox

Đánh giá (P3.4.4): bbox stability, point survival, trajectory smoothness,
tự động in nhận xét/kết luận.

Cách dùng:
    python experiment.py
    python experiment.py --exp winsize --no_display
    python experiment.py --exp dataset --no_display
"""
import argparse, os, csv
import cv2
import numpy as np
from tracker import run_tracker, load_frames, OUTPUT_DIR

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

# Bbox mặc định cho các dataset (x, y, w, h) - xác định từ frame đầu tiên
# Người dùng có thể thay đổi hoặc dùng selectROI khi chạy tracker.py trực tiếp
DEFAULT_BBOXES = {
    "kite-surf": (210, 140, 260, 270),   # người lướt ván
    "soapbox":   (140, 100, 220, 220),   # xe soapbox
    "lab-coat":  (300, 80, 200, 350),    # người mặc áo lab
    "libby":     (280, 60, 200, 340),    # người
    "pigs":      (300, 150, 200, 200),   # con heo
    "shooting":  (450, 100, 200, 300),   # người
}


# ─── Đánh giá định lượng (P3.4.4) ─────────────────────────────────────────
def evaluate_result(result: dict) -> dict:
    """Tính các chỉ số định lượng từ kết quả tracking."""
    bh = result["bbox_history"]
    pc = result["point_counts"]
    centers = [(x + w//2, y + h//2) for x, y, w, h in bh]

    # Displacement giữa các frame liên tiếp
    displacements = [np.sqrt((centers[i][0]-centers[i-1][0])**2 +
                             (centers[i][1]-centers[i-1][1])**2)
                     for i in range(1, len(centers))]

    # 1) Bbox stability: std of displacement (nhỏ = ổn định)
    bbox_stability = float(np.std(displacements)) if displacements else 0

    # 2) Point survival rate: pts cuối / pts đầu
    survival = pc[-1] / pc[0] * 100 if pc[0] > 0 else 0

    # 3) Avg displacement per frame
    avg_disp = float(np.mean(displacements)) if displacements else 0

    # 4) Max displacement (phát hiện nhảy đột ngột)
    max_disp = float(np.max(displacements)) if displacements else 0

    # 5) Smoothness: tỷ lệ frame có displacement đột biến (>3*mean)
    if avg_disp > 0 and displacements:
        jitter_frames = sum(1 for d in displacements if d > 3 * avg_disp)
        jitter_rate = jitter_frames / len(displacements) * 100
    else:
        jitter_rate = 0

    # 6) Avg points
    avg_pts = float(np.mean(pc))

    return {
        "bbox_stability_std": round(bbox_stability, 3),
        "point_survival_pct": round(survival, 1),
        "avg_displacement_px": round(avg_disp, 3),
        "max_displacement_px": round(max_disp, 3),
        "jitter_rate_pct": round(jitter_rate, 1),
        "avg_points": round(avg_pts, 1),
        "initial_points": pc[0],
        "final_points": pc[-1],
    }


def generate_commentary(result: dict, metrics: dict) -> str:
    """Tự động sinh nhận xét cho một kết quả tracking (P3.4.4)."""
    lines = []
    ds = result["dataset"]
    ws = result["win_size"]

    lines.append(f"--- Nhận xét: {ds} (winSize={ws}) ---")

    # Ổn định
    if metrics["bbox_stability_std"] < 1.0:
        lines.append("  • Bbox rất ổn định (std < 1px).")
    elif metrics["bbox_stability_std"] < 3.0:
        lines.append("  • Bbox tương đối ổn định.")
    else:
        lines.append(f"  • Bbox không ổn định (std={metrics['bbox_stability_std']:.2f}px).")

    # Duy trì điểm
    if metrics["point_survival_pct"] > 50:
        lines.append(f"  • Duy trì tốt điểm đặc trưng ({metrics['point_survival_pct']:.0f}% còn lại).")
    elif metrics["point_survival_pct"] > 20:
        lines.append(f"  • Mất một phần điểm ({metrics['point_survival_pct']:.0f}% còn lại), "
                     "có thể do che khuất hoặc biến dạng.")
    else:
        lines.append(f"  • Mất nhiều điểm ({metrics['point_survival_pct']:.0f}% còn lại), "
                     "tracking có thể bị drift.")

    # Jitter
    if metrics["jitter_rate_pct"] > 10:
        lines.append(f"  • Có {metrics['jitter_rate_pct']:.0f}% frame bị nhảy đột ngột "
                     "→ đối tượng chuyển động không đều hoặc bị che khuất.")
    else:
        lines.append("  • Quỹ đạo mượt, không có nhảy đột ngột.")

    return "\n".join(lines)


# ─── Visualization helpers ─────────────────────────────────────────────────
def save_comparison_image(results, title, filename):
    images, labels = [], []
    for res in results:
        saved = sorted([f for f in os.listdir(res["output_dir"]) if f.endswith(".jpg")])
        if saved:
            img = cv2.imread(os.path.join(res["output_dir"], saved[-1]))
            if img is not None:
                images.append(img)
                labels.append(f"{res['dataset']} win={res['win_size']} FPS={res['avg_fps']:.1f}")
    if len(images) < 2:
        return
    th = min(i.shape[0] for i in images)
    tw = min(i.shape[1] for i in images)
    resized = [cv2.resize(i, (tw, th)) for i in images]
    for i, img in enumerate(resized):
        cv2.putText(img, labels[i], (10, th-15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0,0,0), 3, cv2.LINE_AA)
        cv2.putText(img, labels[i], (10, th-15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0,255,255), 1, cv2.LINE_AA)
    comp = np.hstack(resized)
    bar = np.zeros((40, comp.shape[1], 3), dtype=np.uint8)
    cv2.putText(bar, title, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1)
    comp = np.vstack([bar, comp])
    os.makedirs(REPORT_DIR, exist_ok=True)
    cv2.imwrite(os.path.join(REPORT_DIR, filename), comp)
    print(f"  Ảnh so sánh: {os.path.join(REPORT_DIR, filename)}")


def save_point_chart(results, filename):
    cw, ch, m = 800, 400, 60
    chart = np.ones((ch, cw, 3), dtype=np.uint8) * 255
    colors = [(0,0,255),(255,0,0),(0,180,0),(255,128,0)]
    mf = max(len(r["point_counts"]) for r in results)
    mp = max(max(r["point_counts"]) for r in results)
    for idx, res in enumerate(results):
        c = colors[idx % len(colors)]
        d = res["point_counts"]
        for i in range(1, len(d)):
            x1 = m + int((i-1)/mf*(cw-2*m)); x2 = m + int(i/mf*(cw-2*m))
            y1 = ch-m-int(d[i-1]/mp*(ch-2*m)); y2 = ch-m-int(d[i]/mp*(ch-2*m))
            cv2.line(chart,(x1,y1),(x2,y2),c,2,cv2.LINE_AA)
        ly = 20+idx*22
        cv2.line(chart,(cw-250,ly),(cw-220,ly),c,2)
        cv2.putText(chart,f"{res['dataset']} win={res['win_size']}",(cw-215,ly+5),
                    cv2.FONT_HERSHEY_SIMPLEX,0.4,c,1,cv2.LINE_AA)
    cv2.line(chart,(m,m),(m,ch-m),(0,0,0),1)
    cv2.line(chart,(m,ch-m),(cw-m,ch-m),(0,0,0),1)
    cv2.putText(chart,"Frame",(cw//2,ch-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,0),1)
    cv2.putText(chart,"Points",(5,ch//2),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,0),1)
    os.makedirs(REPORT_DIR, exist_ok=True)
    cv2.imwrite(os.path.join(REPORT_DIR, filename), chart)
    print(f"  Biểu đồ: {os.path.join(REPORT_DIR, filename)}")


def print_eval_table(results, evals, title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")
    print(f"  {'Dataset':<12} {'Win':>4} {'FPS':>6} {'Stab':>6} {'Surv%':>6} "
          f"{'AvgD':>6} {'Jit%':>5} {'Pts':>5}")
    print(f"  {'-'*72}")
    for r, e in zip(results, evals):
        print(f"  {r['dataset']:<12} {r['win_size']:>4} {r['avg_fps']:>6.1f} "
              f"{e['bbox_stability_std']:>6.2f} {e['point_survival_pct']:>6.1f} "
              f"{e['avg_displacement_px']:>6.2f} {e['jitter_rate_pct']:>5.1f} "
              f"{e['avg_points']:>5.0f}")
    print(f"{'='*80}")


def save_eval_report(results, evals, commentaries, filename):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("  BÁO CÁO ĐÁNH GIÁ KẾT QUẢ (P3.4.4)\n")
        f.write("=" * 70 + "\n\n")
        for r, e, c in zip(results, evals, commentaries):
            f.write(f"Dataset: {r['dataset']} | winSize={r['win_size']}\n")
            f.write(f"  Frames: {r['num_frames']}, FPS: {r['avg_fps']:.1f}\n")
            f.write(f"  Video: {r.get('video_path','N/A')}\n")
            f.write(f"  Trajectory: {r.get('trajectory_csv','N/A')}\n")
            f.write(f"  Metrics:\n")
            for k, v in e.items():
                f.write(f"    {k}: {v}\n")
            f.write(f"\n{c}\n\n")
            f.write("-" * 70 + "\n\n")
    print(f"  Báo cáo đánh giá: {path}")


# ─── Experiments ───────────────────────────────────────────────────────────
def experiment_winsize(dataset="kite-surf", display=True):
    print("\n" + "#"*70)
    print("  THỬ NGHIỆM 1: So sánh kích thước cửa sổ (winSize)")
    print("#"*70)
    results, evals, comments = [], [], []
    for ws in [15, 21, 31]:
        bbox = DEFAULT_BBOXES.get(dataset)
        res = run_tracker(dataset, win_size=ws, display=display, init_bbox=bbox)
        if res:
            results.append(res)
            e = evaluate_result(res)
            evals.append(e)
            c = generate_commentary(res, e)
            comments.append(c)
            print(c)
    if len(results) >= 2:
        print_eval_table(results, evals, f"So sánh winSize trên {dataset}")
        save_comparison_image(results, f"WinSize comparison - {dataset}",
                              f"compare_winsize_{dataset}.jpg")
        save_point_chart(results, f"points_winsize_{dataset}.jpg")
        save_eval_report(results, evals, comments, f"eval_winsize_{dataset}.txt")

        # Kết luận tự động
        best = min(zip(results, evals), key=lambda x: x[1]["bbox_stability_std"])
        print(f"\n  → KẾT LUẬN: winSize={best[0]['win_size']} cho kết quả ổn định nhất "
              f"trên {dataset} (stability_std={best[1]['bbox_stability_std']:.3f})")
    return results


def experiment_dataset(datasets=None, win_size=21, display=True):
    if datasets is None:
        datasets = ["kite-surf", "soapbox"]
    print("\n" + "#"*70)
    print("  THỬ NGHIỆM 2: So sánh giữa các dataset")
    print("#"*70)
    results, evals, comments = [], [], []
    for ds in datasets:
        bbox = DEFAULT_BBOXES.get(ds)
        res = run_tracker(ds, win_size=win_size, display=display, init_bbox=bbox)
        if res:
            results.append(res)
            e = evaluate_result(res)
            evals.append(e)
            c = generate_commentary(res, e)
            comments.append(c)
            print(c)
    if len(results) >= 2:
        print_eval_table(results, evals, f"So sánh dataset (winSize={win_size})")
        save_comparison_image(results, f"Dataset comparison (win={win_size})",
                              f"compare_datasets_win{win_size}.jpg")
        save_point_chart(results, f"points_datasets_win{win_size}.jpg")
        save_eval_report(results, evals, comments, f"eval_datasets_win{win_size}.txt")

        best = min(zip(results, evals), key=lambda x: x[1]["bbox_stability_std"])
        worst = max(zip(results, evals), key=lambda x: x[1]["bbox_stability_std"])
        print(f"\n  → KẾT LUẬN: '{best[0]['dataset']}' dễ theo dõi hơn "
              f"'{worst[0]['dataset']}' (stability: {best[1]['bbox_stability_std']:.3f} "
              f"vs {worst[1]['bbox_stability_std']:.3f})")
    return results


def main():
    parser = argparse.ArgumentParser(description="P3.4.3 & P3.4.4 - Thử nghiệm & Đánh giá")
    parser.add_argument("--exp", type=str, default="all", choices=["all","winsize","dataset"])
    parser.add_argument("--dataset", type=str, default="kite-surf")
    parser.add_argument("--no_display", action="store_true")
    args = parser.parse_args()
    display = not args.no_display
    all_r = []

    if args.exp in ("all", "winsize"):
        all_r.extend(experiment_winsize(args.dataset, display))
    if args.exp in ("all", "dataset"):
        all_r.extend(experiment_dataset(display=display))

    if all_r:
        print(f"\n  Ảnh/báo cáo: {REPORT_DIR}")
        print(f"  Output frames/video: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
