DỰ ÁN THỰC HÀNH
P3. Theo dõi đối tượng trong video
P3.1. Mục tiêu của dự án
Trong nhiều bài toán thị giác máy, việc xác định đối tượng trong từng ảnh riêng lẻ là chưa đủ. Hệ thống còn cần xác định được vị trí của đối tượng theo thời gian, duy trì sự liên tục giữa các khung hình và mô tả được quỹ đạo chuyển động của đối tượng trong chuỗi video. Đây là nội dung cốt lõi của bài toán theo dõi đối tượng.
Dự án này nhằm giúp người học xây dựng một quy trình theo dõi đối tượng trong video từ dữ liệu được cung cấp sẵn. Thông qua dự án, người học làm rõ được sự khác biệt giữa xử lý ảnh tĩnh và xử lý chuỗi ảnh theo thời gian, đồng thời hiểu được vai trò của thông tin chuyển động trong các bài toán thị giác máy.
P3.2. Dữ liệu
Dữ liệu sử dụng trong dự án là video hoặc chuỗi khung hình được cung cấp sẵn trong thư mục chứa tài nguyên của bài thực hành. Dữ liệu có chứa ít nhất một đối tượng cần theo dõi, chẳng hạn người, phương tiện hoặc một vật thể chuyển động rõ ràng trong cảnh quan sát.
Dữ liệu mẫu 3: Theo dõi đối tượng trong video hoặc chuỗi khung hình.
- Truy cập thư mục dữ liệu (Thư mục resources/lab3/)
- Các thư mục chứa chuỗi khung hình hoặc video
P3.3. Kiến thức nền tảng
Trước hết, người học cần nắm được nguyên lý ước lượng chuyển động trong chuỗi ảnh (xem Mục 6.2.1). Trên cơ sở đó, có thể hiểu các phương pháp nâng cao độ chính xác của vector chuyển động, tiêu biểu là thuật toán Lucas-Kanade (xem Mục 6.2.2) và thuật toán pyramid Lucas-Kanade (xem Mục 6.2.3).
Bên cạnh đó, nội dung theo dõi đối tượng trong chuỗi khung hình là cơ sở trực tiếp của dự án (xem Mục 6.2.4). Trong quá trình xử lý, người học cũng có thể vận dụng các kiến thức về làm mượt ảnh (xem Mục 4.1.2) hoặc khử nhiễu (xem Mục 4.3.1) để nâng cao độ ổn định của kết quả theo dõi trong một số trường hợp cụ thể.
P3.4. Yêu cầu thực hiện
P3.4.1. Khảo sát dữ liệu
Trước khi triển khai, cần khảo sát tập dữ liệu video được cung cấp sẵn nhằm xác định đặc điểm của đối tượng cần theo dõi và các yếu tố có thể ảnh hưởng đến kết quả. Phần khảo sát cần làm rõ số lượng đối tượng, kích thước đối tượng trong ảnh, hướng chuyển động, mức độ che khuất, thay đổi chiếu sáng và độ phức tạp của cảnh nền.
P3.4.2. Xây dựng quy trình theo dõi
Cần xây dựng một quy trình theo dõi đối tượng trong video gồm các bước chính: đọc video hoặc chuỗi khung hình, xác định đối tượng cần theo dõi ở khung hình đầu, lựa chọn phương pháp theo dõi phù hợp, cập nhật vị trí đối tượng theo thời gian và lưu kết quả theo dõi.
Tùy theo cách triển khai, có thể sử dụng một phương pháp kinh điển dựa trên chuyển động, đặc trưng hoặc vùng quan tâm. Cần giải thích rõ ý nghĩa của từng bước trong quy trình và lý do lựa chọn phương pháp.
P3.4.3. Triển khai và so sánh
Phần trọng tâm của dự án là triển khai thuật toán theo dõi trên tập dữ liệu đã cho và tổ chức thực nghiệm so sánh giữa các phương án khác nhau. Có thể lựa chọn so sánh các hướng như: hai cấu hình tham số khác nhau của cùng một phương pháp, hai phương pháp theo dõi khác nhau hoặc so sánh kết quả theo dõi trên các video có điều kiện chuyển động khác nhau.
Việc so sánh cần được thực hiện trên cùng tập dữ liệu và trong cùng điều kiện thí nghiệm. Cần lưu lại các khung hình kết quả, hộp bao đối tượng hoặc quỹ đạo chuyển động để phục vụ phân tích.
P3.4.4. Đánh giá kết quả
Kết quả của dự án cần được đánh giá chủ yếu thông qua quan sát trực quan quá trình bám bắt đối tượng qua các khung hình liên tiếp. Việc đánh giá cần làm rõ khả năng duy trì liên tục vị trí đối tượng, mức độ ổn định của kết quả theo thời gian, khả năng thích ứng với thay đổi chuyển động và mức độ ảnh hưởng của che khuất hoặc thay đổi chiếu sáng. Nếu điều kiện thực nghiệm cho phép, có thể sử dụng thêm một số chỉ số định lượng phù hợp để hỗ trợ so sánh giữa các phương án.
P3.5. Yêu cầu báo cáo
Báo cáo dự án cần được trình bày ngắn gọn, rõ ràng và có minh họa bằng hình ảnh ở các giai đoạn chính của quá trình theo dõi. Nội dung báo cáo tối thiểu gồm: phát biểu bài toán và mục tiêu của dự án, mô tả dữ liệu sử dụng, mô tả quy trình theo dõi, các phương án thực nghiệm; kết quả theo dõi và so sánh, nhận xét và kết luận.
P3.6. Sản phẩm nộp
Sản phẩm của dự án bao gồm: mã nguồn chương trình, báo cáo dự án, video đầu ra hoặc chuỗi ảnh kết quả sau theo dõi, dữ liệu ví dụ hoặc quỹ đạo của đối tượng nếu có, cùng slide tóm tắt nội dung thực hiện nếu có yêu cầu.
P3.7. Kết quả cần đạt
Sau khi hoàn thành dự án, kết quả đạt được cần thể hiện một quy trình theo dõi đối tượng cơ bản có khả năng đi từ dữ liệu video đến kết quả bám bắt đối tượng theo thời gian. Quan trọng hơn, dự án cần cho thấy được mối liên hệ giữa chuyển động ảnh, đặc trưng quan sát được và khả năng duy trì sự liên tục của đối tượng trong chuỗi khung hình.