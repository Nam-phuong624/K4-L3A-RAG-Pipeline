import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="VNU-UET RAG Assistant",
    page_icon="🎓",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🎓 VNU-UET Assistant")
    st.markdown(
        "Trợ lý hỏi đáp **Quy chế đào tạo & Dịch vụ sinh viên** "
        "Trường Đại học Công nghệ - ĐHQGHN."
    )
    st.markdown("---")
    st.subheader("Cấu hình Retrieval")
    top_k = st.slider("Số lượng Chunks (top_k)", min_value=3, max_value=10, value=5)
    
    st.markdown("---")
    st.markdown("### Tài liệu trong hệ thống:")
    st.markdown("- **Legal:** QĐ 3626 (Đào tạo), QĐ 4618 (Học bổng), QĐ 2244 (Học vụ)")
    st.markdown("- **News/Notices:** Kế hoạch tốt nghiệp K66, BHYT, Học bổng Vingroup, Học bổng SĐH UET...")
    
    if st.button("Xóa lịch sử hội thoại"):
        st.session_state.messages = []
        st.rerun()

st.title("🎓 Trợ lý Quy chế & Dịch vụ Sinh viên VNU-UET")
st.caption("Tra cứu quy chế đào tạo, chuẩn tốt nghiệp, học bổng và thông báo học vụ chính thức.")

# Render message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            retrieval_method = message.get("retrieval_source", "hybrid")
            num_chunks = len(message["sources"])
            with st.expander(f"📚 Xem nguồn trích dẫn & Retrieval ({retrieval_method.upper()} - {num_chunks} chunks)"):
                for idx, src in enumerate(message["sources"], 1):
                    meta = src.get("metadata", {})
                    title = meta.get("title", "Tài liệu")
                    source_name = meta.get("source", "Tài liệu gốc")
                    doc_type = meta.get("doc_type", "Chung")
                    score = src.get("score", 0.0)
                    chunk_id = src.get("id", "N/A")
                    content_snippet = src.get("content", "")
                    st.markdown(f"**[{idx}] {title}** `({doc_type.upper()})` — *Score/Rank:* `{score:.4f}`")
                    st.caption(f"Nguồn: `{source_name}` | Chunk ID: `{chunk_id}`")
                    st.markdown(f"> {content_snippet}")
                    st.divider()

query = st.chat_input("Nhập câu hỏi về quy chế hoặc thông báo sinh viên UET...")

if query:
    # 1. Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 2. Xử lý câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và sinh câu trả lời..."):
            result = generate_with_citation(query, top_k=top_k)
            answer = result.get("answer", "Tôi không thể xác minh thông tin này từ nguồn hiện có.")
            sources = result.get("sources", [])
            retrieval_source = result.get("retrieval_source", "hybrid")

            st.markdown(answer)

            if sources:
                num_chunks = len(sources)
                with st.expander(f"📚 Xem nguồn trích dẫn & Retrieval ({retrieval_source.upper()} - {num_chunks} chunks)"):
                    for idx, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        title = meta.get("title", "Tài liệu")
                        source_name = meta.get("source", "Tài liệu gốc")
                        doc_type = meta.get("doc_type", "Chung")
                        score = src.get("score", 0.0)
                        chunk_id = src.get("id", "N/A")
                        content_snippet = src.get("content", "")
                        st.markdown(f"**[{idx}] {title}** `({doc_type.upper()})` — *Score/Rank:* `{score:.4f}`")
                        st.caption(f"Nguồn: `{source_name}` | Chunk ID: `{chunk_id}`")
                        st.markdown(f"> {content_snippet}")
                        st.divider()

    # 3. Lưu vào lịch sử phiên làm việc
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
