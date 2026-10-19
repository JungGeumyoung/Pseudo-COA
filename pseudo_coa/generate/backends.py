"""생성 모델 백엔드.

기본은 로컬에 설치된 Claude Code CLI(`claude -p`)를 비대화식으로 호출한다. API 키 없이 로그인된 구독으로 동작하고,
`--json-schema`로 구조화 출력을 강제할 수 있어 파이프라인에 적합하다. 다른 모델로 바꾸려면 `Backend.generate`를
같은 서명으로 구현하면 된다(예: vLLM OpenAI 호환 서버).

generate(system, user, schema) -> (obj: dict, meta: dict)
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time


class BackendError(RuntimeError):
    pass


class UsageLimitError(BackendError):
    """구독 사용 한도 도달. 재시도해도 소용없으므로 호출자가 배치를 멈춰야 한다."""


def _extract_json(text):
    """모델이 스키마 밖 텍스트를 섞어 보냈을 때 첫 번째 JSON 객체를 복구한다."""
    if not text:
        raise BackendError("empty result")
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise BackendError("no JSON object in result: %r" % text[:200])
    return json.loads(m.group(0))


class ClaudeCLIBackend(object):
    name = "claude-cli"

    def __init__(self, model=None, effort=None, max_budget_usd=3.0, timeout=900, cwd=None, retries=2, max_output_tokens=64000):
        self.model = model
        self.effort = effort
        self.max_budget_usd = max_budget_usd
        self.timeout = timeout
        self.cwd = cwd or tempfile.mkdtemp(prefix="coa_gen_")
        self.retries = retries
        # 생각 토큰과 큰 JSON이 한 응답의 출력 한도(기본 32000)에 걸려 구조화 출력이 잘리는 일을 막는다
        self.env = dict(os.environ, CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(max_output_tokens)) if max_output_tokens else None

    def _cmd(self, system, schema):
        cmd = ["claude", "-p", "--tools", "", "--no-session-persistence",
               "--output-format", "json", "--max-budget-usd", str(self.max_budget_usd),
               "--system-prompt", system]
        if schema is not None:
            cmd += ["--json-schema", json.dumps(schema, ensure_ascii=False)]
        if self.model:
            cmd += ["--model", self.model]
        if self.effort:
            cmd += ["--effort", self.effort]
        return cmd

    def generate(self, system, user, schema=None):
        last = None
        for attempt in range(self.retries + 1):
            if last is not None:  # 앞 시도가 실패했으면 이유를 남긴다
                print("  [retry %d] %s" % (attempt, str(last)[:300]), file=sys.stderr, flush=True)
            t0 = time.time()
            try:
                proc = subprocess.run(self._cmd(system, schema), input=user, capture_output=True, text=True,
                                      timeout=self.timeout, cwd=self.cwd, env=self.env)
            except subprocess.TimeoutExpired:
                last = BackendError("timeout after %ds" % self.timeout)
                continue
            raw = proc.stdout.strip()
            try:
                env = json.loads(raw)
            except Exception:
                last = BackendError("non-JSON CLI envelope: %r / stderr=%r" % (raw[:300], proc.stderr[-300:]))
                continue
            if env.get("is_error"):
                msg = str(env.get("result"))
                dbg = os.environ.get("COA_DEBUG_DIR")   # 실패한 응답 전체를 남겨 원인을 본다
                if dbg:
                    try:
                        os.makedirs(dbg, exist_ok=True)
                        with open(os.path.join(dbg, "cli_error_%d_%d.json" % (int(time.time()), os.getpid())), "w", encoding="utf-8") as fh:
                            json.dump(env, fh, ensure_ascii=False, indent=1)
                    except OSError:
                        pass
                errs = json.dumps(env.get("errors"), ensure_ascii=False)[:300] if env.get("errors") else ""
                last = BackendError("CLI error: subtype=%s cost=$%s turns=%s | %s %s" % (env.get("subtype"), env.get("total_cost_usd"), env.get("num_turns"),
                                                                                    msg[:200], errs))
                if "Not logged in" in msg:
                    raise last
                if any(k in msg.lower() for k in ("session limit", "usage limit", "rate limit", "limit reached", "hit your")):
                    raise UsageLimitError(msg[:300])
                continue
            try:
                obj = env.get("structured_output") or _extract_json(env.get("result", ""))
            except Exception as e:
                last = BackendError(str(e))
                continue
            meta = {
                "backend": self.name,
                "model": self.model or sorted((env.get("modelUsage") or {}).keys()),
                "cost_usd": env.get("total_cost_usd"),
                "duration_s": round(time.time() - t0, 1),
                "usage": {k: (env.get("usage") or {}).get(k) for k in
                          ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")},
                "attempt": attempt,
                "num_turns": env.get("num_turns"),
            }
            return obj, meta
        raise last or BackendError("unknown failure")


class OpenAICompatBackend(object):
    """vLLM / Ollama 등 OpenAI 호환 서버용 (국방망 내부 모델로 교체할 때). openai 패키지 필요."""
    name = "openai-compat"

    def __init__(self, base_url, model, api_key="EMPTY", timeout=900, retries=2, temperature=0.7):
        from openai import OpenAI  # noqa: F401  (지연 import)
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self.model = model
        self.retries = retries
        self.temperature = temperature

    def generate(self, system, user, schema=None):
        last = None
        for attempt in range(self.retries + 1):
            t0 = time.time()
            try:
                kw = {}
                if schema is not None:
                    kw["response_format"] = {"type": "json_schema",
                                             "json_schema": {"name": "coa_case", "schema": schema}}
                r = self._client.chat.completions.create(
                    model=self.model, temperature=self.temperature,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], **kw)
                obj = _extract_json(r.choices[0].message.content)
                meta = {"backend": self.name, "model": self.model, "duration_s": round(time.time() - t0, 1),
                        "usage": dict(r.usage) if r.usage else None, "attempt": attempt}
                return obj, meta
            except Exception as e:
                last = BackendError(str(e))
        raise last


def make_backend(spec):
    """'claude' | 'claude:<model>[:<effort>]' | 'openai:<base_url>|<model>'"""
    if spec.startswith("openai:"):
        base, model = spec[len("openai:"):].split("|", 1)
        return OpenAICompatBackend(base, model)
    parts = spec.split(":")
    model = parts[1] if len(parts) > 1 and parts[1] else None
    effort = parts[2] if len(parts) > 2 and parts[2] else None
    return ClaudeCLIBackend(model=model, effort=effort)
