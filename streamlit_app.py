import json
import os
from typing import List

import streamlit as st

from main import DEFAULT_API_KEY, DEFAULT_MODEL, run_workflow


st.set_page_config(
    page_title="Chinese English Mixed Writing",
    page_icon="🈶",
    layout="wide",
)


def render_logs(logs: List[str]) -> None:
    if logs:
        st.caption("运行日志")
        st.code("\n".join(logs), language="text")


def app() -> None:
    st.title("Chinese English Mixed Writing")
    st.write("输入英文文章和中文词，或直接让模型自动生成测试内容，再生成一篇英文里混着中文的文章。")

    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input(
            "Gemini / Gemma API Key",
            value=os.getenv("GEMINI_API_KEY", DEFAULT_API_KEY),
            type="password",
        )
        model = st.text_input("Model", value=DEFAULT_MODEL)
        mode = st.radio("Input Mode", ["Auto generate", "Manual input"], index=0)

    english_article = ""
    chinese_text = ""

    if mode == "Manual input":
        english_article = st.text_area(
            "English article",
            height=220,
            placeholder="Paste your English article here.",
        )
        chinese_text = st.text_area(
            "Chinese words or phrases",
            height=120,
            placeholder="例如：我 去 公园 早上 看 太阳 树 水 人 很多",
        )
    else:
        st.info("Auto generate 模式下，不输入内容也可以直接测试。模型会先生成至少 4 到 5 句英文，再生成可替换的中文词。")

    if st.button("Generate Mixed Article", type="primary", use_container_width=True):
        logs: List[str] = []

        def ui_log(message: str) -> None:
            logs.append(message)

        try:
            with st.spinner("Calling model..."):
                result = run_workflow(
                    api_key=api_key,
                    model=model,
                    english_article=english_article or None,
                    chinese_text=chinese_text or None,
                    logger=ui_log,
                )
        except Exception as exc:
            st.error(str(exc))
            render_logs(logs)
            return

        st.success("Done")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("English Article")
            st.write(result["english_article"])
            st.subheader("Chinese Text")
            st.write(result["chinese_text"])

        with col2:
            st.subheader("Mixed Article")
            st.write(result["mixed_article"])

        st.subheader("Replacements")
        if result["replacements"]:
            st.table(result["replacements"])
        else:
            st.write("No replacements returned.")

        st.subheader("JSON Result")
        st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")
        render_logs(logs)


if __name__ == "__main__":
    app()
