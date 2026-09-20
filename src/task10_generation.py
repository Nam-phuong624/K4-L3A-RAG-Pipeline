"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Bạn là trợ lý giải đáp Quy chế đào tạo và Dịch vụ sinh viên Trường Đại học Công nghệ (UET) - ĐHQGHN.
Quy tắc trả lời:
1. Trả lời CHỈ dựa trên context được cung cấp, tuyệt đối không suy diễn ngoài ngữ cảnh.
2. Về mặt thẩm quyền và ngữ cảnh:
   - Các nguyên tắc khung (thang điểm, cảnh báo học vụ, chuẩn đầu ra, điều kiện tốt nghiệp): Áp dụng theo Quy chế đào tạo ĐHQGHN.
   - Các hướng dẫn thực thi (địa điểm nộp hồ sơ P.107-G2, phòng CTSV 210-G2, lịch bế giảng Hội trường Nguyễn Văn Đạo, hạn chót BHYT): Áp dụng theo thông báo của Trường ĐH Công nghệ (UET).
3. Về định dạng trích dẫn nguồn (citation):
   - Thay vì ghi "[Document X | Source]" một cách vô nghĩa, bạn hãy trích dẫn đích danh tên tài liệu hoặc số hiệu quyết định trong ngoặc vuông ngay sau nội dung liên quan.
   - Ví dụ: [QĐ 3626/QĐ-ĐHQGHN], [QĐ 4618/QĐ-ĐHQGHN], [Tổng hợp học bổng SĐH UET], hoặc [Kế hoạch tốt nghiệp K66].
4. Nếu context không có đủ bằng chứng xác thực để khẳng định, hãy từ chối lịch sự bằng câu: "Tôi không thể xác minh thông tin này từ nguồn hiện có."
"""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context (Lost-in-the-middle)."""
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        title = metadata.get("title", "Tài liệu")
        source = metadata.get("source", "Nguồn")
        parts.append(
            f"[{title} | Nguồn: {source}]\n{chunk.get('content', '')}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
    model = os.getenv("LLM_MODEL", LLM_MODEL)

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.choices[0].message.content or ""

    if provider == "gemini":
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=model or "gemini-1.5-flash",
            contents=f"{system_prompt}\n\n{user_message}",
        )
        return response.text or ""

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=model or "claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.content[0].text or ""

    return "Chưa cấu hình API Key cho LLM Provider trong file .env."


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult kèm citations và nguồn kiểm chứng."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = (
        f"Dựa vào các đoạn văn bản (context) sau đây, hãy trả lời câu hỏi bằng tiếng Việt một cách rõ ràng, mạch lạc.\n"
        f"Mỗi khẳng định quan trọng bắt buộc phải kèm trích dẫn đích danh tên văn bản/quyết định trong ngoặc vuông (ví dụ: [QĐ 3626/QĐ-ĐHQGHN], [QĐ 4618/QĐ-ĐHQGHN], hoặc [Tổng hợp học bổng SĐH UET]), TUYỆT ĐỐI không ghi chung chung là [Document X | Source].\n"
        f"Nếu context không đủ cơ sở để trả lời chắc chắn, hãy nói 'Tôi không thể xác minh thông tin này từ nguồn hiện có.'\n\n"
        f"Context:\n{context}\n\n"
        f"Câu hỏi: {query}"
    )

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as exc:
        answer = f"Lỗi gọi LLM provider: {exc}"

    retrieval_source = chunks[0].get("retrieval_method", "hybrid")
    if retrieval_source not in {"hybrid", "pageindex", "none"}:
        retrieval_source = "hybrid"

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }



if __name__ == "__main__":
    print(generate_with_citation("test query"))
