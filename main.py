#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional


DEFAULT_MODEL = "gemma-3-27b-it"
DEFAULT_API_KEY = "AIzaSyB2itfNfPRSwtNCYg97YqnRIq0glIQS9mo"
API_KEY_SHORTCUT = "abc321"
MIN_REQUEST_INTERVAL_SECONDS = 4.2
MAX_RETRIES = 3

Logger = Optional[Callable[[str], None]]


def log(message: str) -> None:
    print(f"[INFO] {message}", file=sys.stderr, flush=True)


def sleep_with_progress(seconds: float, reason: str, logger: Logger = None) -> None:
    remaining = max(0, int(seconds + 0.999))
    if remaining <= 0:
        return
    if logger is not None:
        logger(f"{reason}，预计等待 {remaining} 秒")
    else:
        log(f"{reason}，预计等待 {remaining} 秒")
    while remaining > 0:
        print(f"\r[WAIT] {reason}，剩余 {remaining:>2} 秒", end="", file=sys.stderr, flush=True)
        time.sleep(1)
        remaining -= 1
    print("\r" + " " * 80 + "\r", end="", file=sys.stderr, flush=True)


def extract_text(response_json: Dict[str, Any]) -> str:
    parts: List[str] = []
    for candidate in response_json.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def extract_json_block(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


class GeminiClient:
    def __init__(self, api_key: str, model: str, min_interval: float, logger: Logger = None) -> None:
        self.api_key = api_key
        self.model = model
        self.min_interval = min_interval
        self.logger = logger or log
        self._last_request_time = 0.0

    def _respect_rate_limit(self) -> None:
        now = time.time()
        wait_seconds = self.min_interval - (now - self._last_request_time)
        if wait_seconds > 0:
            sleep_with_progress(wait_seconds, "遵守每分钟 15 次请求限制", self.logger)

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            self.logger(f"开始请求 Gemini，第 {attempt}/{MAX_RETRIES} 次尝试")
            try:
                return self._generate_json_once(prompt)
            except RuntimeError as exc:
                last_error = exc
                retry_seconds = self._extract_retry_seconds(str(exc))
                if attempt >= MAX_RETRIES or retry_seconds is None:
                    break
                sleep_with_progress(retry_seconds, "Gemini 返回限流，等待后重试", self.logger)
        raise last_error if last_error else RuntimeError("Unknown Gemini API error.")

    def _generate_json_once(self, prompt: str) -> Dict[str, Any]:
        self._respect_rate_limit()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        generation_config: Dict[str, Any] = {
            "temperature": 0.7,
        }
        if self._supports_json_mode():
            generation_config["responseMimeType"] = "application/json"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": generation_config,
        }
        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            self.logger(f"正在调用模型 {self.model}")
            with urllib.request.urlopen(request, timeout=60) as response:
                response_json = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gemini API connection error: {exc}") from exc

        self._last_request_time = time.time()
        self.logger("Gemini 已返回结果，正在解析 JSON")
        text = extract_text(response_json)
        if not text:
            raise RuntimeError(f"Gemini API returned no text: {json.dumps(response_json, ensure_ascii=False)}")
        return extract_json_block(text)

    @staticmethod
    def _extract_retry_seconds(error_text: str) -> Optional[float]:
        match = re.search(r'"retryDelay":\s*"(\d+)s"', error_text)
        if match:
            return float(match.group(1)) + 1.0
        if "HTTP 429" in error_text:
            return 60.0
        return None

    def _supports_json_mode(self) -> bool:
        return not self.model.startswith("gemma-")


def build_generation_prompt(sentence_count: int, article_length: str, chinese_difficulty: str) -> str:
    return f"""
你要生成测试用材料，并且只返回 JSON。

任务：
1. 生成一段自然英文短文，内容轻松、具体、适合做替换实验。
2. 再生成一组中文字符或短词，数量 10 到 20 个，适合替换英文里的部分含义。

严格要求：
- 只输出 JSON，不要 markdown，不要解释。
- JSON 结构必须是：
{{
  "english_article": "...",
  "chinese_text": "..."
}}
- chinese_text 用空格分隔中文字符或短词。
- english_article 的长度要求：{article_length}。
- english_article 必须至少有 {sentence_count} 句。
- chinese_text 的难度要求：{chinese_difficulty}。
- 英文文章里要包含尽量多的可被这些中文字符或短词表达的意思。
""".strip()


def build_english_only_prompt(chinese_text: str, sentence_count: int, article_length: str) -> str:
    return f"""
你要根据给定的中文词，生成一段适合做中英混写的英文文章，并且只返回 JSON。

可用中文字符或短词：
{chinese_text}

任务：
1. 生成一段自然、连贯、好读的英文短文。
2. 英文内容要尽量包含可以被这些中文词自然替换的单词或短语。

严格要求：
- 只输出 JSON，不要 markdown，不要解释。
- JSON 结构必须是：
{{
  "english_article": "..."
}}
- 文章长度要求：{article_length}。
- 句子数量要求：至少 {sentence_count} 句。
- 语气自然，不要像词表拼接出来的句子。
""".strip()


def build_chinese_only_prompt(english_article: str, difficulty: str) -> str:
    return f"""
你要根据给定的英文文章，生成一组适合替换其中部分内容的中文词，并且只返回 JSON。

英文文章：
{english_article}

任务：
1. 挑选文章里适合被中文替换的核心词或短语。
2. 生成一组中文字符或短词，方便后续做中英混写。

严格要求：
- 只输出 JSON，不要 markdown，不要解释。
- JSON 结构必须是：
{{
  "chinese_text": "..."
}}
- 中文难度要求：{difficulty}。
- 输出 10 到 20 个中文字符或短词。
- 用空格分隔。
- 优先选择能让最终文章读起来比较自然的词，不要只挑生硬、零碎的词。
""".strip()


def build_mix_prompt(english_article: str, chinese_text: str) -> str:
    return f"""
你要把英文文章改造成“英文里混着中文”的文章，并且只返回 JSON。

英文文章：
{english_article}

可用中文字符或短词：
{chinese_text}

任务：
1. 找出英文文章中，哪些单词或短语的含义可以直接用上面提供的中文字符或短词表达。
2. 只替换那些自然、明显、不会严重破坏可读性的部分。
3. 生成一篇混合后的文章，优先保证整段读起来通顺自然，而不是机械地多替换。
4. 可以对个别词位做轻微调整，让句子更像真实的人写的中英混合表达，但不要改变原文主要意思。

严格要求：
- 只能使用“可用中文字符或短词”里已经给出的中文，不要发明新的中文。
- 如果某个中文短词更适合替换短语，可以直接替换整个短语。
- 替换不要过度，保持文章仍然主要是英文。
- 最终 mixed_article 要比“逐词硬替换”更自然，避免明显别扭的表达。
- 只输出 JSON，不要 markdown，不要解释。
- JSON 结构必须是：
{{
  "replacements": [
    {{
      "original": "英文原文中的单词或短语",
      "replacement": "替换后的中文"
    }}
  ],
  "mixed_article": "最终混合文章"
}}
""".strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把英文文章的一部分替换成指定中文，生成中英混写文章。"
    )
    parser.add_argument("--english", help="输入英文文章。不传则自动生成测试文章。")
    parser.add_argument("--chinese", help="输入可用于替换的中文字符或短词。不传则自动生成测试内容。")
    parser.add_argument("--api-key", default=os.getenv("GEMINI_API_KEY", DEFAULT_API_KEY), help="Gemini API key。")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini 模型名。默认: gemma-3-27b-it")
    parser.add_argument(
        "--save-json",
        default="result.json",
        help="把完整结果保存到哪个 JSON 文件。默认: result.json",
    )
    return parser.parse_args()


def run_workflow(
    api_key: str,
    model: str,
    english_article: Optional[str] = None,
    chinese_text: Optional[str] = None,
    sentence_count: int = 5,
    article_length: str = "140 到 220 词",
    chinese_difficulty: str = "中等，适合中级中文学习者",
    logger: Logger = None,
) -> Dict[str, Any]:
    active_logger = logger or log
    client = GeminiClient(
        api_key=api_key,
        model=model,
        min_interval=MIN_REQUEST_INTERVAL_SECONDS,
        logger=active_logger,
    )

    generated_inputs: Dict[str, Any] = {}

    if not english_article and not chinese_text:
        active_logger("未提供英文和中文，先自动生成整套测试素材")
        generated_inputs = client.generate_json(
            build_generation_prompt(sentence_count, article_length, chinese_difficulty)
        )
        english_article = generated_inputs["english_article"]
        chinese_text = generated_inputs["chinese_text"]
    elif not english_article:
        active_logger("未提供英文，正在根据你给的中文生成英文文章")
        generated_english = client.generate_json(
            build_english_only_prompt(chinese_text or "", sentence_count, article_length)
        )
        english_article = generated_english["english_article"]
        generated_inputs["english_article"] = english_article
    elif not chinese_text:
        active_logger("未提供中文，正在根据你给的英文生成中文词")
        generated_chinese = client.generate_json(
            build_chinese_only_prompt(english_article, chinese_difficulty)
        )
        chinese_text = generated_chinese["chinese_text"]
        generated_inputs["chinese_text"] = chinese_text
    else:
        active_logger("检测到你已提供英文和中文素材，跳过自动生成步骤")

    active_logger("开始生成中英混写文章")
    mix_result = client.generate_json(build_mix_prompt(english_article, chinese_text))

    return {
        "model": model,
        "rate_limit_note": "Script enforces at least 4.2 seconds between Gemini requests to stay under 15 requests per minute.",
        "english_article": english_article,
        "chinese_text": chinese_text,
        "replacements": mix_result.get("replacements", []),
        "mixed_article": mix_result.get("mixed_article", ""),
        "auto_generated_inputs": bool(generated_inputs),
    }


def main() -> int:
    args = parse_args()
    log("脚本启动")
    if not args.api_key:
        raise RuntimeError("Missing API key. Set GEMINI_API_KEY or pass --api-key.")
    final_result = run_workflow(
        api_key=args.api_key,
        model=args.model,
        english_article=args.english,
        chinese_text=args.chinese,
        logger=log,
    )

    with open(args.save_json, "w", encoding="utf-8") as file:
        json.dump(final_result, file, ensure_ascii=False, indent=2)
    log(f"结果已保存到 {args.save_json}")

    print("=== English Article ===")
    print(final_result["english_article"])
    print()
    print("=== Chinese Text ===")
    print(final_result["chinese_text"])
    print()
    print("=== Replacements ===")
    for item in final_result["replacements"]:
        original = item.get("original", "")
        replacement = item.get("replacement", "")
        print(f"- {original} -> {replacement}")
    print()
    print("=== Mixed Article ===")
    print(final_result["mixed_article"])
    print()
    print(f"Saved JSON result to: {args.save_json}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
