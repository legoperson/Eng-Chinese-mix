import os
from typing import List

import streamlit as st

from main import DEFAULT_API_KEY, DEFAULT_MODEL, run_workflow


SENTENCE_OPTIONS = {
    "Short: 4 sentences": {"sentence_count": 4, "article_length": "100 to 150 words"},
    "Medium: 5 sentences": {"sentence_count": 5, "article_length": "140 to 220 words"},
    "Long: 6-7 sentences": {"sentence_count": 6, "article_length": "200 to 320 words"},
}

DIFFICULTY_OPTIONS = {
    "Easy": "Easy Chinese, focused on common characters and high-frequency short words for beginners",
    "Medium": "Medium difficulty Chinese, suitable for intermediate learners",
    "Advanced": "More advanced Chinese, allowing more natural phrases and slightly richer expressions",
}


st.set_page_config(
    page_title="Mixed Reading Studio",
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
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(91, 61, 44, 0.09);
        border-radius: 22px;
        box-shadow: 0 12px 30px rgba(88, 58, 39, 0.08);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0.35rem 0.45rem;
    }
    .result-shell {
        position: relative;
    }
    .result-shell::after {
        content: "";
        position: absolute;
        width: 180px;
        height: 180px;
        right: -48px;
        top: -52px;
        background: radial-gradient(circle, rgba(230, 143, 88, 0.16), rgba(230, 143, 88, 0.00) 72%);
        pointer-events: none;
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
    .note-card {
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: rgba(255, 250, 244, 0.92);
        border: 1px solid rgba(154, 109, 66, 0.14);
        margin-top: 1rem;
    }
    .story-card {
        padding: 1.1rem 1.2rem;
        border-radius: 22px;
        background: linear-gradient(160deg, rgba(255,255,255,0.92), rgba(251, 244, 232, 0.95));
        border: 1px solid rgba(154, 109, 66, 0.12);
        box-shadow: 0 12px 28px rgba(88, 58, 39, 0.08);
        margin: 1rem 0;
    }
    .story-card h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.18rem;
        color: #6b4930;
    }
    .story-card p {
        margin: 0.45rem 0;
        color: #5c5046;
        line-height: 1.72;
    }
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.9rem;
        margin-top: 1rem;
    }
    .feature-card {
        padding: 1rem 1.05rem;
        border-radius: 20px;
        background: rgba(255,255,255,0.88);
        border: 1px solid rgba(154, 109, 66, 0.12);
        min-height: 160px;
        position: relative;
        overflow: hidden;
    }
    .feature-card h4 {
        margin: 0 0 0.45rem 0;
        color: #6a4a33;
        font-size: 1rem;
    }
    .feature-card p {
        margin: 0;
        color: #60554b;
        line-height: 1.66;
        font-size: 0.96rem;
    }
    .feature-icon {
        position: absolute;
        right: 0.9rem;
        bottom: 0.4rem;
        font-size: 2.4rem;
        opacity: 0.18;
    }
    .levels-row {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin-top: 1rem;
    }
    .level-pill {
        padding: 0.95rem 1rem;
        border-radius: 18px;
        background: rgba(255, 247, 239, 0.96);
        border: 1px solid rgba(154, 109, 66, 0.14);
    }
    .level-pill strong {
        display: block;
        color: #754f34;
        margin-bottom: 0.28rem;
    }
    .level-pill span {
        color: #61564d;
        font-size: 0.92rem;
        line-height: 1.55;
    }
    .art-band {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.9rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .art-tile {
        padding: 1rem;
        min-height: 150px;
        border-radius: 20px;
        background: linear-gradient(160deg, rgba(255,255,255,0.84), rgba(248,236,221,0.92));
        border: 1px solid rgba(154, 109, 66, 0.12);
        box-shadow: 0 10px 22px rgba(88, 58, 39, 0.07);
        position: relative;
        overflow: hidden;
    }
    .art-tile h4 {
        margin: 0;
        font-size: 0.95rem;
        letter-spacing: 0.04em;
        color: #6f4d34;
    }
    .art-tile p {
        margin: 0.55rem 0 0 0;
        color: #65574b;
        line-height: 1.65;
        font-size: 0.95rem;
    }
    .art-glyph {
        position: absolute;
        right: 0.85rem;
        bottom: 0.45rem;
        font-size: 2.6rem;
        opacity: 0.18;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


DEFAULT_EXAMPLE_ENGLISH = (
    "On Saturday morning, Mia walked to a small park near her apartment. "
    "She bought a warm coffee, sat beside the water, and watched a father teach his son how to ride a bike. "
    "A light wind moved through the trees, and the whole place felt quiet and bright. "
    "Before going home, she took a few photos of the sun on the lake and sent them to her friend."
)

DEFAULT_EXAMPLE_CHINESE = "早上 公园 水 树 风 安静 太阳 回家 朋友 照片"

DEFAULT_EXAMPLE_MIXED = (
    "On Saturday 早上, Mia walked to a small 公园 near her apartment. "
    "She bought a warm coffee, sat beside the 水, and watched a father teach his son how to ride a bike. "
    "A light 风 moved through the 树, and the whole place felt 安静 and bright. "
    "Before 回家, she took a few 照片 of the 太阳 on the lake and sent them to her 朋友."
)


def render_logs(logs: List[str]) -> None:
    if logs:
        with st.expander("Run Log", expanded=False):
            st.code("\n".join(logs), language="text")


def app() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Mixed Reading Studio</h1>
            <p>
                A gentle reading helper for Chinese beginners. It keeps English as a support frame and introduces Chinese little by little, so learners can understand the story and still grow their Chinese reading ability.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="story-card">
            <h3>What This Tool Does</h3>
            <p>
                Mixed Reading Studio is a beginner-friendly reading tool. Instead of asking learners to jump straight into full Chinese texts,
                it uses English as a scaffold and carefully blends in Chinese words and short phrases.
            </p>
            <p>
                That means the passage still feels readable, but the learner keeps meeting useful Chinese inside a story they can already follow.
                It turns reading into understandable input: not too easy, not too hard, and much less scary than a page full of unfamiliar characters.
            </p>
            <p>
                The goal is not to stay dependent on English forever. The goal is to help learners move from English-supported reading
                toward reading more and more Chinese with confidence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card">
                <h4>Why It Helps</h4>
                <p>Pure Chinese can feel too hard, while pure English teaches very little Chinese. This tool creates the missing middle step.</p>
                <div class="feature-icon">桥</div>
            </div>
            <div class="feature-card">
                <h4>Vocabulary In Context</h4>
                <p>Chinese words appear inside a real passage, so learners see meaning, sentence position, and usage together instead of memorizing isolated lists.</p>
                <div class="feature-icon">词</div>
            </div>
            <div class="feature-card">
                <h4>Lower Character Anxiety</h4>
                <p>Beginners are not thrown into a wall of Hanzi. They meet characters inside a familiar English frame, which feels calmer and more approachable.</p>
                <div class="feature-icon">字</div>
            </div>
            <div class="feature-card">
                <h4>From Knowing To Reading</h4>
                <p>It helps learners move beyond “I know a few words” toward “I can read a short passage and infer meaning from context.”</p>
                <div class="feature-icon">读</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="story-card">
            <h3>Good For</h3>
            <p>Chinese beginners, bilingual children, overseas Chinese classes, tutors, parents, and graded reading practice.</p>
            <div class="levels-row">
                <div class="level-pill">
                    <strong>Level 1</strong>
                    <span>Mostly easy nouns</span>
                </div>
                <div class="level-pill">
                    <strong>Level 2</strong>
                    <span>Common verbs and adjectives</span>
                </div>
                <div class="level-pill">
                    <strong>Level 3</strong>
                    <span>Useful short phrases</span>
                </div>
                <div class="level-pill">
                    <strong>Level 4</strong>
                    <span>More Chinese, less English support</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.88, 1.12], gap="large")

    with left:
        with st.container(border=True):
            st.subheader("Generation Settings")
            st.caption("A gradual reading tool that helps beginners meet Chinese while still understanding the passage.")
            api_key = st.text_input(
                "Gemini / Gemma API Key",
                value="",
                type="password",
                placeholder="Paste API key here, or use Streamlit secrets / GEMINI_API_KEY",
            )
            st.caption("Get an API key from your Gemini account. A free API key is enough. Paste it here and you can start.")
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
            st.caption("You can leave either English or Chinese blank. The app will generate only the missing part.")

        st.markdown('<div class="note-card">', unsafe_allow_html=True)
        st.markdown("**How To Use The API Key**")
        st.write(
            "Go to your Google Gemini account and create an API key. A free-tier key works for this app."
            " Once you have it, paste the key into the input field above and start generating."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        with st.container(border=True):
            st.subheader("Inputs")
            english_article = st.text_area(
                "English Article",
                height=220,
                placeholder="Leave blank to auto-generate an English article.",
            )
            chinese_text = st.text_area(
                "Chinese Words or Phrases",
                height=130,
                placeholder="Example: 早上 公园 水 树 风 安静 太阳 回家 朋友 照片",
            )
            generate = st.button("Generate Mixed Article", type="primary", use_container_width=True)

    st.markdown(
        """
        <div class="art-band">
            <div class="art-tile">
                <h4>Read In Layers</h4>
                <p>Keep the sentence mostly English, then let a few Chinese words carry the image, mood, and key meaning.</p>
                <div class="art-glyph">文</div>
            </div>
            <div class="art-tile">
                <h4>Vocabulary In Context</h4>
                <p>Instead of memorizing isolated words, you see them sitting inside a living paragraph with rhythm and scene.</p>
                <div class="art-glyph">字</div>
            </div>
            <div class="art-tile">
                <h4>Gentle Mixing</h4>
                <p>The app aims for smoother mixed reading, not a harsh word-by-word swap that breaks the flow.</p>
                <div class="art-glyph">读</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not generate:
        with st.container(border=True):
            st.markdown('<div class="result-shell">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Example Preview</div>', unsafe_allow_html=True)
            st.write("English Example")
            st.write(DEFAULT_EXAMPLE_ENGLISH)
            st.write("Chinese Word Bank Example")
            st.write(DEFAULT_EXAMPLE_CHINESE)
            st.write("Mixed Reading Example")
            st.markdown(f'<div class="mixed-text">{DEFAULT_EXAMPLE_MIXED}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        return

    logs: List[str] = []

    def ui_log(message: str) -> None:
        logs.append(message)

    secret_api_key = st.secrets.get("GEMINI_API_KEY", "")
    env_api_key = os.getenv("GEMINI_API_KEY", DEFAULT_API_KEY)
    effective_api_key = api_key or secret_api_key or env_api_key
    if not effective_api_key:
        st.error("Missing API key. Enter it manually, or set Streamlit secrets / GEMINI_API_KEY.")
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
        with st.container(border=True):
            st.markdown('<div class="result-shell">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">English Article</div>', unsafe_allow_html=True)
            st.write(result["english_article"])
            st.markdown('</div>', unsafe_allow_html=True)

    with top_b:
        with st.container(border=True):
            st.markdown('<div class="result-shell">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">Chinese Word Bank</div>', unsafe_allow_html=True)
            st.write(result["chinese_text"])
            st.markdown('</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="result-shell">', unsafe_allow_html=True)
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
