# Individual contribution report

- Họ và tên: Chử Trần Phương Nam
- Mã học viên: K4-L3A-01
- Nhóm: Nhóm 1 - RAG Pipeline ĐHQGHN-UET
- Repository/branch: https://github.com/Chutranphuongnam624/K4-L3A-RAG-Pipeline / main

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Thu thập & Kiểm định dữ liệu (Task 1 & 2) | Khảo sát, phát hiện lỗi scanned PDF của QĐ 3626 (0 text char) và thay thế bằng digital PDF chuẩn; crawl 6 bài tin tức UET có metadata | `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, commit `0c44996` | Done |
| Chuẩn hóa văn bản Markdown (Task 3) | Viết pipeline chuyển đổi 3 PDF pháp lý sang Markdown sạch kèm page comment; làm sạch HTML news | `src/task3_convert_markdown.py`, `data/standardized/` | Done |
| Chunking, Indexing & ChromaDB (Task 4) | Thiết kế chunking 500 ký tự (overlap 50), xây dựng embedding pipeline với bge-m3 / vector hashing fallback, index 472 chunks vào ChromaDB | `src/task4_chunking_indexing.py`, `chroma_db/` | Done |
| Hybrid Retrieval & Reranking (Tasks 5, 6, 7, 8, 9) | Xây dựng Dense Cosine Search, BM25Okapi Lexical Search, Reciprocal Rank Fusion ($k=60$) và Vectorless Fallback threshold 0.35 | `src/task5_semantic_search.py` đến `src/task9_retrieval_pipeline.py` | Done |
| Generation, Citation & Prompt Engineering (Task 10) | Tối ưu Lost-in-the-middle context, thiết kế prompt phân tầng thẩm quyền ĐHQGHN - UET tránh sai lệch ngữ cảnh, safe refusal | `src/task10_generation.py` | Done |
| Golden Dataset & Evaluation A/B | Xây dựng 16 grounded Q&A pairs (10 legal + 6 news); benchmark so sánh Config A (Dense) vs Config B (Hybrid RRF) trên 4 metrics | `group_project/evaluation/golden_dataset.json`, `group_project/evaluation/RESULT.md` | Done |
| Chatbot UI Streamlit | Xây dựng UI Streamlit hoàn chỉnh kết nối pipeline, hiển thị expandable citation, metadata nguồn và điều chỉnh top_k | `app.py` | Done |

---

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Kết hợp mô hình dữ liệu 2 cấp: Quy chế khung ĐHQGHN (Legal) + Thông báo thực thi của Trường ĐH Công nghệ UET (News).
   - **Lý do/evidence:** Trường ĐH Công nghệ thuộc ĐHQGHN và không ban hành quy chế đào tạo đại học độc lập mà áp dụng trực tiếp QĐ 3626/QĐ-ĐHQGHN. Các thông báo trên UET chỉ rõ mốc thời gian (tốt nghiệp tháng 01/2026), phòng ban tiếp nhận (P.107-G2, P.210-G2).
   - **Trade-off:** Cần kiểm soát chặt chẽ vai trò của từng nguồn bằng System Prompt để LLM không nhầm lẫn giữa thẩm quyền ban hành cấp ĐHQGHN và trách nhiệm giải quyết thủ tục tại Trường thành viên UET.

2. **Quyết định:** Triển khai Hybrid Search kết hợp Reciprocal Rank Fusion (RRF) thay vì dùng Dense-only hoặc nối chuỗi thô.
   - **Lý do/evidence:** Kết quả benchmark trên 16 câu hỏi Golden Dataset chứng minh Context Recall tăng từ 0.69 (Dense) lên 0.88 (Hybrid RRF) (+19%), Context Precision tăng từ 0.65 lên 0.85 (+20%). BM25 bắt chính xác các thực thể số hiệu văn bản ("QĐ 3626"), mốc thời gian và phòng ban thực tế mà dense embedding dễ bỏ sót.
   - **Trade-off:** Latency trung bình mỗi truy vấn tăng từ 66.9ms lên 108.1ms (+41.2ms) do phải tính toán thêm BM25 và rank fusion, tuy nhiên vẫn hoàn toàn dưới ngưỡng thời gian thực tương tác (<200ms).

---

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng:
  - Bộ kiểm thử hợp đồng: `pytest tests/test_contracts.py` (15 tests).
  - Bộ kiểm thử nghiệm thu: `pytest tests/test_acceptance.py` (5 tests).
  - Benchmark 16 câu hỏi trong Golden Dataset đối đầu Config A vs Config B.
- Kết quả trước/sau:
  - Ban đầu: 3/5 acceptance tests passed (do thiếu Golden Dataset và RESULT.md).
  - Sau khi hoàn thiện: **20/20 tests passed (100%)**, toàn bộ 5/5 tiêu chí nghiệm thu đạt chuẩn.
- Lỗi đã phát hiện và cách xử lý:
  - File PDF tải về ban đầu của QĐ 3626 là bản scan ảnh không có text layer (0 ký tự trích xuất được) $\rightarrow$ đã tìm và thay thế bằng bản Digital PDF chính thức của ĐHQGHN (52 trang, >96.000 ký tự text sạch).
  - Lỗi truy vấn *"học bổng uet bao nhiêu tiền"* bị Safe Refusal: Do BM25 băm từ bằng `split()` giữ nguyên dấu ngoặc `"(uet)"` và dấu hai chấm `"uet:"`, không match được token `"uet"` của người dùng; đồng thời thiếu Query Expansion giữa từ khẩu ngữ *"tiền"* với thuật ngữ văn bản (*"mức học bổng"*, *"kinh phí"*), và ChromaDB tồn đọng chunk rác cũ. Đã xử lý triệt để bằng regex tokenizer `re.findall(r"\w+", ...)`, Query Expansion, dọn dẹp vectorstore tự động và tối ưu hóa context citation (Commit `e1b63d4`).
  - Các câu hỏi liên quan đến bảng điểm số học ("A+", "B+", "3.7") bị loãng ngữ nghĩa khi chỉ dùng Dense retrieval $\rightarrow$ BM25 kết hợp RRF đã đưa chunk quy đổi điểm lên rank top đầu.

---

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Chunking cố định 500 ký tự đôi khi cắt ngang các bảng biểu quy chế phức tạp nhiều cột (như Bảng quy đổi điểm Điều 41), khiến cấu trúc bảng bị phân mảnh nhỏ.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Triển khai Markdown Table-aware Chunking để gom nguyên vẹn bảng biểu quy chế vào cùng một chunk chuyên biệt, kết hợp thêm bộ mở rộng từ đồng nghĩa tiếng Việt (Query Expansion cho từ viết tắt: "ĐRL", "CTSV", "GPA").

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Chử Trần Phương Nam
