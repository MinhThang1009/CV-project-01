"""
P3.4.2 - Theo dõi đối tượng (Object Tracker)
==============================================
Module cốt lõi: Feature-based Tracker dùng Pyramid Lucas-Kanade.

Quy trình (theo Mục 6.2.4 trong tài liệu):
  1. Khởi tạo tại I₀:
     - Làm mượt Gaussian (Mục 4.1.2) để giảm nhiễu
     - Chọn ROI bằng chuột (cv2.selectROI)
     - Phát hiện điểm đặc trưng Shi-Tomasi trong ROI
       (đảm bảo điều kiện theo dõi được: 2 giá trị riêng của ma trận
        cấu trúc M đều đủ lớn - Mục 6.2.1)
  2. Theo dõi qua từng khung hình I_i:
     - Pyramid LK (Mục 6.2.3) → vector chuyển động
     - Lọc outlier (status + forward-backward check)
     - Cập nhật bbox bằng median displacement
     - Bổ sung điểm mới nếu cần (Mục 6.2.4 - Bước 2)
  3. Lưu kết quả:
     - Video đầu ra (.mp4) — yêu cầu P3.6
     - Quỹ đạo đối tượng (.csv) — yêu cầu P3.6
     - Chuỗi ảnh kết quả — yêu cầu P3.6

Cách dùng:
    python tracker.py                                       # Mặc định: kite-surf
    python tracker.py --dataset soapbox --win_size 31       # Tùy chọn
    python tracker.py --dataset kite-surf --no_display      # Không hiển thị

Kiến thức nền tảng:
    - Ước lượng chuyển động (Mục 6.2.1): v = M⁻¹ Fᵀ b
    - Thuật toán LK lặp (Mục 6.2.2): tăng độ chính xác qua nhiều vòng lặp
    - Pyramid LK (Mục 6.2.3): xử lý chuyển động dài bằng kim tự tháp ảnh
    - Theo dõi đối tượng (Mục 6.2.4): khung thuật toán tổng quát
    - Làm mượt Gaussian (Mục 4.1.2): tiền xử lý giảm nhiễu
"""

import argparse
import csv
import glob
import os
import time

import cv2
import numpy as np


# ─── Đường dẫn ─────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# ─── Hàm tiện ích ──────────────────────────────────────────────────────────

def load_frames(dataset_name: str) -> list:
    """Đọc chuỗi ảnh .jpg từ thư mục dataset."""
    folder = os.path.join(DATA_DIR, dataset_name)
    paths = sorted(glob.glob(os.path.join(folder, "*.jpg")))
    if not paths:
        raise FileNotFoundError(f"Không tìm thấy ảnh trong: {folder}")
    return [cv2.imread(p) for p in paths]


def detect_features(gray, roi_bbox, max_corners=200, quality=0.01, min_dist=7):
    """
    Phát hiện điểm đặc trưng Shi-Tomasi trong vùng ROI.

    Lý do chọn Shi-Tomasi (Mục 6.2.1, 6.2.4 Bước 1):
      - goodFeaturesToTrack sử dụng tiêu chí min(λ₁, λ₂) > threshold
      - Đảm bảo cả 2 giá trị riêng của ma trận cấu trúc M đều đủ lớn
      - Điều này là điều kiện cần để thuật toán LK ước lượng được vector
        chuyển động (M phải khả nghịch - công thức 6.20)
    """
    x, y, w, h = roi_bbox
    mask = np.zeros_like(gray)
    mask[y:y+h, x:x+w] = 255

    points = cv2.goodFeaturesToTrack(
        gray, maxCorners=max_corners, qualityLevel=quality,
        minDistance=min_dist, mask=mask, blockSize=7
    )
    return points


def track_points(prev_gray, curr_gray, prev_pts, win_size=21, max_level=3):
    """
    Theo dõi điểm bằng Pyramid Lucas-Kanade (Mục 6.2.3).

    Thuật toán Pyramid LK:
      - Xây dựng kim tự tháp ảnh L mức cho cả prev_gray và curr_gray
        + Mức 0: ảnh gốc (M × N)
        + Mức l: ảnh I^l (M/2^l × N/2^l), thu được bằng lọc Gaussian + downsample
      - Tại mỗi mức l (từ L-1 xuống 0):
          + Tính điểm neo p^l = (xB/2^l + vx^l, yB/2^l + vy^l)
          + Áp dụng LK lặp (Mục 6.2.2) trong cửa sổ W:
              Khởi tạo (vx,vy) = (0,0)
              Lặp: tính (cx,cy) theo công thức 6.20, cập nhật (vx,vy) += (cx,cy)
              Dừng khi đủ số lần lặp hoặc (cx,cy) quá nhỏ
          + Cập nhật: (vx^l, vy^l) ← (vx^l + vx, vy^l + vy)
      - Kết quả cuối: vector chuyển động tại mức 0

    Forward-backward check (ràng buộc R - Mục 6.2.4):
      - Theo dõi ngược từ curr → prev
      - Nếu |điểm gốc - điểm quay ngược| > threshold → loại bỏ
      - Giúp phát hiện: điểm bị che khuất, drift sang nền, lỗi tracking
    """
    lk_params = dict(
        winSize=(win_size, win_size),    # Kích thước cửa sổ W (Mục 6.2.1)
        maxLevel=max_level,               # Số mức kim tự tháp (Mục 6.2.3)
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        # 30 vòng lặp LK (Mục 6.2.2) hoặc dừng khi sai số < 0.01
    )

    # Forward: prev → curr
    next_pts, status_fwd, _ = cv2.calcOpticalFlowPyrLK(
        prev_gray, curr_gray, prev_pts, None, **lk_params
    )

    # Backward: curr → prev (forward-backward consistency check)
    back_pts, status_bwd, _ = cv2.calcOpticalFlowPyrLK(
        curr_gray, prev_gray, next_pts, None, **lk_params
    )

    # Tính sai lệch forward-backward
    fb_error = np.linalg.norm(prev_pts - back_pts, axis=2).flatten()

    # Điểm hợp lệ: status OK + sai lệch FB nhỏ (ràng buộc R)
    fb_threshold = 1.0  # pixel
    good_mask = (status_fwd.flatten() == 1) & (fb_error < fb_threshold)

    return next_pts, good_mask


def update_bbox(prev_pts, curr_pts, good_mask, bbox):
    """
    Cập nhật bounding box dựa trên trung vị (median) của vector dịch chuyển.

    Lý do dùng median:
      - Robust hơn mean với outlier (điểm bị drift sang nền)
      - Phù hợp với bài toán theo dõi khi có nhiễu và che khuất
    """
    if good_mask.sum() < 2:
        return bbox  # Không đủ điểm → giữ nguyên

    prev_good = prev_pts[good_mask].reshape(-1, 2)
    curr_good = curr_pts[good_mask].reshape(-1, 2)
    displacement = curr_good - prev_good

    dx = np.median(displacement[:, 0])
    dy = np.median(displacement[:, 1])

    x, y, w, h = bbox
    x_new = int(x + dx)
    y_new = int(y + dy)

    return (x_new, y_new, w, h)


def draw_results(frame, bbox, curr_pts, good_mask, trails, frame_idx):
    """Vẽ kết quả lên khung hình: bbox, điểm đặc trưng, quỹ đạo."""
    vis = frame.copy()
    x, y, w, h = bbox

    # Vẽ bounding box (hộp bao đối tượng)
    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Vẽ tâm bbox
    cx, cy = x + w // 2, y + h // 2
    cv2.circle(vis, (cx, cy), 5, (0, 255, 0), -1)

    # Vẽ điểm đặc trưng hiện tại
    if curr_pts is not None:
        for i, pt in enumerate(curr_pts):
            if good_mask[i]:
                px, py = pt.ravel()
                cv2.circle(vis, (int(px), int(py)), 3, (0, 0, 255), -1)

    # Vẽ quỹ đạo (trails) - Mục 6.2.4 Bước 3: mô hình hóa quỹ đạo chuyển động
    for trail in trails:
        if len(trail) > 1:
            for j in range(1, len(trail)):
                p1 = (int(trail[j-1][0]), int(trail[j-1][1]))
                p2 = (int(trail[j][0]), int(trail[j][1]))
                cv2.line(vis, p1, p2, (255, 255, 0), 1, cv2.LINE_AA)

    # Thông tin text
    num_pts = int(good_mask.sum()) if good_mask is not None else 0
    info = f"Frame {frame_idx} | Points: {num_pts} | BBox: ({x},{y},{w},{h})"
    cv2.putText(vis, info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(vis, info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (0, 255, 255), 1, cv2.LINE_AA)

    return vis


def save_trajectory_csv(bbox_history, point_counts, dataset_name, win_size, out_dir):
    """
    Lưu quỹ đạo đối tượng ra file CSV (yêu cầu P3.6:
    "dữ liệu ví dụ hoặc quỹ đạo của đối tượng nếu có").

    Cột: frame, center_x, center_y, bbox_x, bbox_y, bbox_w, bbox_h, num_points
    """
    csv_path = os.path.join(out_dir, f"trajectory_{dataset_name}_win{win_size}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "frame", "center_x", "center_y",
            "bbox_x", "bbox_y", "bbox_w", "bbox_h", "num_points"
        ])
        for i, bbox in enumerate(bbox_history):
            x, y, w, h = bbox
            cx = x + w // 2
            cy = y + h // 2
            n_pts = point_counts[i] if i < len(point_counts) else 0
            writer.writerow([i, cx, cy, x, y, w, h, n_pts])

    print(f"  Quỹ đạo lưu tại: {csv_path}")
    return csv_path


# ─── Tracker chính ─────────────────────────────────────────────────────────

def run_tracker(dataset_name: str, win_size: int = 21, max_level: int = 3,
                display: bool = True, gaussian_blur: bool = True,
                init_bbox: tuple = None):
    """
    Quy trình theo dõi đối tượng đầy đủ (Mục 6.2.4).

    Lý do chọn phương pháp (P3.4.2 - cần giải thích):
      - Phương pháp: Feature-based tracking dùng Optical Flow
      - Lý do: Phù hợp với dữ liệu chuỗi ảnh liên tiếp, tận dụng được
        thông tin chuyển động giữa các khung hình (giả định brightness
        constancy). Pyramid LK cho phép xử lý cả chuyển động dài.
      - Shi-Tomasi đảm bảo chọn được điểm dễ theo dõi (ma trận M khả nghịch).

    Args:
        dataset_name: Tên thư mục dataset trong lab3/
        win_size: Kích thước cửa sổ W cho LK (Mục 6.2.1)
        max_level: Số mức kim tự tháp (Mục 6.2.3, tối đa 5)
        display: Hiển thị cửa sổ kết quả real-time
        gaussian_blur: Áp dụng Gaussian blur (Mục 4.1.2) để giảm nhiễu

    Returns:
        dict chứa thông tin kết quả
    """
    print(f"\n{'='*60}")
    print(f"  TRACKER: {dataset_name} | winSize={win_size} | maxLevel={max_level}")
    print(f"{'='*60}")

    # Đọc dữ liệu
    frames = load_frames(dataset_name)
    print(f"  Đã tải {len(frames)} khung hình.")

    # ─── Bước 1: Khởi tạo tại I₀ (Mục 6.2.4 - Bước 1) ────────────────────
    first_frame = frames[0].copy()

    # Làm mượt ảnh bằng Gaussian (Mục 4.1.2)
    # h_G(x,y;σ) = 1/(2πσ²) exp(-(x²+y²)/(2σ²))
    # Kernel 5×5, σ=1.0 → giảm nhiễu cộng mà không làm mất chi tiết quan trọng
    if gaussian_blur:
        first_frame_processed = cv2.GaussianBlur(first_frame, (5, 5), 1.0)
    else:
        first_frame_processed = first_frame

    # Chọn ROI
    if init_bbox is not None:
        bbox = tuple(init_bbox)
        print(f"  Sử dụng bbox được cung cấp sẵn: {bbox}")
    else:
        print("  >>> Hãy chọn vùng đối tượng cần theo dõi (kéo chuột), rồi nhấn ENTER/Space.")
        bbox = cv2.selectROI("Chọn đối tượng - Nhấn ENTER khi xong",
                             first_frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow("Chọn đối tượng - Nhấn ENTER khi xong")

    if bbox[2] == 0 or bbox[3] == 0:
        print("[!] Không chọn được ROI. Thoát.")
        return None

    print(f"  ROI ban đầu: x={bbox[0]}, y={bbox[1]}, w={bbox[2]}, h={bbox[3]}")

    # Chuyển sang grayscale
    prev_gray = cv2.cvtColor(first_frame_processed, cv2.COLOR_BGR2GRAY)

    # Phát hiện điểm đặc trưng Shi-Tomasi trong ROI (Mục 6.2.4 Bước 1)
    prev_pts = detect_features(prev_gray, bbox)
    if prev_pts is None or len(prev_pts) == 0:
        print("[!] Không phát hiện được điểm đặc trưng. Thoát.")
        return None
    print(f"  Phát hiện {len(prev_pts)} điểm đặc trưng ban đầu.")

    # Khởi tạo quỹ đạo (Mục 6.2.4 - Bước 3)
    trails = [[pt.ravel().tolist()] for pt in prev_pts]

    # Tạo thư mục output
    out_dir = os.path.join(OUTPUT_DIR, f"{dataset_name}_win{win_size}")
    os.makedirs(out_dir, exist_ok=True)

    # Lưu kết quả
    bbox_history = [bbox]
    point_counts = [len(prev_pts)]
    MIN_POINTS = 10  # Ngưỡng tối thiểu để bổ sung điểm mới

    # ─── Khởi tạo VideoWriter (yêu cầu P3.6: "video đầu ra") ─────────────
    h_img, w_img = first_frame.shape[:2]
    video_path = os.path.join(out_dir, f"tracking_{dataset_name}_win{win_size}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(video_path, fourcc, 15.0, (w_img, h_img))

    # Lưu frame đầu
    good_mask_init = np.ones(len(prev_pts), dtype=bool)
    vis0 = draw_results(first_frame, bbox, prev_pts, good_mask_init, trails, 0)
    cv2.imwrite(os.path.join(out_dir, "frame_0000.jpg"), vis0)
    video_writer.write(vis0)

    if display:
        cv2.namedWindow("Tracking", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Tracking", min(w_img, 960), min(h_img, 720))

    # ─── Bước 2: Theo dõi qua từng khung hình (Mục 6.2.4 - Bước 2) ───────
    t_start = time.time()

    for i in range(1, len(frames)):
        frame = frames[i]
        if gaussian_blur:
            frame_processed = cv2.GaussianBlur(frame, (5, 5), 1.0)
        else:
            frame_processed = frame
        curr_gray = cv2.cvtColor(frame_processed, cv2.COLOR_BGR2GRAY)

        # Pyramid LK: ước lượng vector chuyển động (Mục 6.2.3)
        next_pts, good_mask = track_points(prev_gray, curr_gray, prev_pts,
                                           win_size=win_size, max_level=max_level)

        # Cập nhật bbox bằng median displacement
        bbox = update_bbox(prev_pts, next_pts, good_mask, bbox)
        bbox_history.append(bbox)

        # Giới hạn bbox trong ảnh
        bx, by, bw, bh = bbox
        bx = max(0, min(bx, w_img - bw))
        by = max(0, min(by, h_img - bh))
        bbox = (bx, by, bw, bh)

        # Cập nhật quỹ đạo cho các điểm còn tốt (Mục 6.2.4 Bước 3)
        new_trails = []
        for j in range(len(prev_pts)):
            if good_mask[j]:
                trail = trails[j] + [next_pts[j].ravel().tolist()]
                if len(trail) > 30:
                    trail = trail[-30:]
                new_trails.append(trail)
        trails = new_trails

        # Lọc lấy chỉ các điểm tốt
        curr_good_pts = next_pts[good_mask].reshape(-1, 1, 2)
        curr_good_mask = np.ones(len(curr_good_pts), dtype=bool)
        point_counts.append(len(curr_good_pts))

        # Bổ sung điểm đặc trưng mới nếu cần (Mục 6.2.4 - Bước 2)
        # "Sử dụng phát hiện điểm đặc trưng Shi-Tomasi để phát hiện
        #  những điểm có thể theo dõi mới, và bổ sung vào P_i nếu
        #  thỏa mãn điều kiện R"
        if len(curr_good_pts) < MIN_POINTS:
            new_pts = detect_features(curr_gray, bbox, max_corners=100)
            if new_pts is not None and len(new_pts) > 0:
                curr_good_pts = np.vstack([curr_good_pts, new_pts])
                curr_good_mask = np.ones(len(curr_good_pts), dtype=bool)
                for pt in new_pts:
                    trails.append([pt.ravel().tolist()])
                print(f"  Frame {i}: Bổ sung {len(new_pts)} điểm mới "
                      f"(tổng: {len(curr_good_pts)})")

        # Vẽ kết quả
        vis = draw_results(frame, bbox, curr_good_pts, curr_good_mask, trails, i)

        # Ghi vào video (.mp4)
        video_writer.write(vis)

        # Lưu ảnh kết quả (mỗi 5 frame + frame cuối)
        if i % 5 == 0 or i == len(frames) - 1:
            cv2.imwrite(os.path.join(out_dir, f"frame_{i:04d}.jpg"), vis)

        # Hiển thị
        if display:
            cv2.imshow("Tracking", vis)
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q') or key == 27:
                break

        # Chuẩn bị cho frame tiếp theo
        prev_gray = curr_gray
        prev_pts = curr_good_pts.astype(np.float32)

    elapsed = time.time() - t_start
    avg_fps = (len(frames) - 1) / elapsed if elapsed > 0 else 0

    # Đóng video writer
    video_writer.release()
    print(f"  Video đầu ra: {video_path}")

    if display:
        cv2.destroyAllWindows()

    # ─── Lưu quỹ đạo ra CSV (P3.6) ───────────────────────────────────────
    traj_path = save_trajectory_csv(bbox_history, point_counts,
                                     dataset_name, win_size, out_dir)

    # ─── Kết quả ──────────────────────────────────────────────────────────
    result = {
        "dataset": dataset_name,
        "win_size": win_size,
        "max_level": max_level,
        "num_frames": len(frames),
        "avg_fps": avg_fps,
        "elapsed_sec": elapsed,
        "output_dir": out_dir,
        "video_path": video_path,
        "trajectory_csv": traj_path,
        "bbox_history": bbox_history,
        "point_counts": point_counts,
    }

    print(f"\n  Hoàn tất: {len(frames)} frames trong {elapsed:.2f}s "
          f"(~{avg_fps:.1f} FPS)")
    print(f"  Output lưu tại: {out_dir}")

    return result


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="P3 - Theo dõi đối tượng bằng Pyramid Lucas-Kanade"
    )
    parser.add_argument("--dataset", type=str, default="kite-surf",
                        help="Tên dataset trong lab3/")
    parser.add_argument("--win_size", type=int, default=21,
                        help="Kích thước cửa sổ LK (mặc định 21)")
    parser.add_argument("--max_level", type=int, default=3,
                        help="Số mức kim tự tháp (mặc định 3)")
    parser.add_argument("--bbox", type=int, nargs=4, default=None,
                        metavar=("X","Y","W","H"),
                        help="Bbox ban đầu (x y w h). Nếu không có, dùng chuột.")
    parser.add_argument("--no_display", action="store_true",
                        help="Không hiển thị GUI, chỉ lưu output")
    parser.add_argument("--no_blur", action="store_true",
                        help="Tắt Gaussian blur tiền xử lý")
    args = parser.parse_args()

    result = run_tracker(
        dataset_name=args.dataset,
        win_size=args.win_size,
        max_level=args.max_level,
        display=not args.no_display,
        gaussian_blur=not args.no_blur,
        init_bbox=tuple(args.bbox) if args.bbox else None,
    )

    if result:
        print(f"\n  Tóm tắt: Dataset={result['dataset']}, "
              f"FPS={result['avg_fps']:.1f}, "
              f"Frames={result['num_frames']}")
        print(f"  Video: {result['video_path']}")
        print(f"  Quỹ đạo: {result['trajectory_csv']}")


if __name__ == "__main__":
    main()
