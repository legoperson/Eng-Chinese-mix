from typing import List

import streamlit as st

from main import API_KEY_SHORTCUT, DEFAULT_API_KEY, DEFAULT_MODEL, run_workflow


SENTENCE_OPTIONS = {
    "Short: 4 sentences": {"sentence_count": 4, "article_length": "100 到 150 词"},
    "Medium: 5 sentences": {"sentence_count": 5, "article_length": "140 到 220 词"},
    "Long: 6-7 sentences": {"sentence_count": 6, "article_length": "200 到 320 词"},
}

DIFFICULTY_OPTIONS = {
    "Easy": "简单，偏常用字和高频短词，适合初学者",
    "Medium": "中等，适合中级中文学习者",
    "Advanced": "较高，允许更自然的短语和稍复杂表达，适合进阶学习者",
}


st.set_page_config(
    page_title="Mixed Writing Studio",
    page_icon="✍️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(232, 94, 39, 0.16), transparent 28%),
            radial-gradient(circle at top right, rgba(39, 91, 232, 0.14), transparent 26%),
            linear-gradient(180deg, #f8f1e7 0%, #f3eadf 42%, #efe3d3 100%);
        color: #1f1c19;
    }
    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(255,255,255,0.88), rgba(255,245,233,0.88));
        border: 1px solid rgba(91, 61, 44, 0.10);
        box-shadow: 0 16px 42px rgba(88, 58, 39, 0.10);
        margin-bottom: 1.2rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2.4rem;
        letter-spacing: -0.04em;
    }
    .hero p {
        margin: 0.6rem 0 0 0;
        color: #5e5147;
        font-size: 1.02rem;
    }
    .panel {
        padding: 1.1rem 1.2rem;
        border-radius: 22px;
        background: rgba(255,255,255,0.78);
        border: 1px solid rgba(91, 61, 44, 0.09);
        box-shadow: 0 12px 30px rgba(88, 58, 39, 0.08);
    }
    .result-card {
        padding: 1rem 1.15rem;
        border-radius: 20px;
        background: rgba(255,255,255,0.88);
        border: 1px solid rgba(91, 61, 44, 0.09);
        box-shadow: 0 10px 24px rgba(88, 58, 39, 0.07);
        min-height: 220px;
    }
    .section-label {
        font-size: 0.76rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #9a6d42;
        margin-bottom: 0.4rem;
    }
    .mixed-text {
        font-size: 1.14rem;
        line-height: 1.9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_logs(logs: List[str]) -> None:
    if logs:
        with st.expander("运行日志", expanded=False):
            st.code("\n".join(logs), language="text")


def app() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Mixed Writing Studio</h1>
            <p>
                输入英文或中文任意一边，另一边可以自动补全。再生成一篇更通顺、更像真实表达的中英混写文章。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.88, 1.12], gap="large")

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Generation Settings")
        api_key = st.text_input(
            "Gemini / Gemma API Key",
            value="",
            type="password",
            placeholder=f"Paste API key here, or enter {API_KEY_SHORTCUT} to use your default key",
        )
        model = st.text_input("Model", value=DEFAULT_MODEL)
        sentence_preset = st.select_slider(
            "Sentence Length",
            options=list(SENTENCE_OPTIONS.keys()),
            value="Medium: 5 sentences",
        )
        chinese_level = st.segmented_control(
            "Chinese Difficulty",
            options=list(DIFFICULTY_OPTIONS.keys()),
            default="Medium",
            selection_mode="single",
        )
        st.caption("英文或中文留空都可以，系统会只补缺失的那一部分。")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("Inputs")
        english_article = st.text_area(
            "English Article",
            height=220,
            placeholder="Leave blank to auto-generate an English article.",
        )
        chinese_text = st.text_area(
            "Chinese Words or Phrases",
            height=130,
            placeholder="例如：我 去 公园 早上 看 太阳 树 水 人 很多",
        )
        generate = st.button("Generate Mixed Article", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if not generate:
        return

    logs: List[str] = []

    def ui_log(message: str) -> None:
        logs.append(message)

    effective_api_key = DEFAULT_API_KEY if api_key == API_KEY_SHORTCUT else api_key
    if not effective_api_key:
        st.error(f"Missing API key. Enter your API key, or type {API_KEY_SHORTCUT} to use the default key.")
        return

    preset = SENTENCE_OPTIONS[sentence_preset]
    chinese_difficulty = DIFFICULTY_OPTIONS[chinese_level or "Medium"]

    try:
        with st.spinner("Generating..."):
            result = run_workflow(
                api_key=effective_api_key,
                model=model,
                english_article=english_article.strip() or None,
                chinese_text=chinese_text.strip() or None,
                sentence_count=preset["sentence_count"],
                article_length=preset["article_length"],
                chinese_difficulty=chinese_difficulty,
                logger=ui_log,
            )
    except Exception as exc:
        st.error(str(exc))
        render_logs(logs)
        return

    st.success("Generated")

    top_a, top_b = st.columns([1, 1], gap="large")

    with top_a:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">English Article</div>', unsafe_allow_html=True)
        st.write(result["english_article"])
        st.markdown('</div>', unsafe_allow_html=True)

    with top_b:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Chinese Word Bank</div>', unsafe_allow_html=True)
        st.write(result["chinese_text"])
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card" style="margin-top: 1rem;">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Mixed Article</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mixed-text">{result["mixed_article"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("Replacements")
    if result["replacements"]:
        st.dataframe(result["replacements"], use_container_width=True, hide_index=True)
    else:
        st.write("No replacements returned.")

    render_logs(logs)


if __name__ == "__main__":
    app()
