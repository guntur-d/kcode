"""Provider catalog: 80+ LLM providers ported from opencode's provider directory.

Original: https://github.com/anomalyco/opencode (packages/web/src/content/docs/providers.mdx)
plus https://opencode.ai/docs/providers/ and https://opencode.ai/zen.

Row format: (id, display name, base_url, api_key_env, protocol, note).
- protocol "openai": POST {base}/chat/completions with Bearer auth.
- protocol "anthropic": POST {base}/messages with x-api-key auth.
- protocol "azure": {base}/openai/deployments/{model}/chat/completions with api-key auth.
- protocol "custom": needs non-HTTP auth (AWS SigV4, OAuth, device flow...);
  kept in the catalog with a setup hint so --list-providers stays complete.
- base_url "" means the endpoint is account/deployment specific; the user
  must supply --base-url (validate() says so with the hint).
"""
from typing import Any, Dict, List, Optional

OPENAI = "openai"
ANTHROPIC = "anthropic"
AZURE = "azure"
CUSTOM = "custom"

PROTOCOLS = (OPENAI, ANTHROPIC, AZURE, CUSTOM)

# id, name, base_url, key_env, protocol, note
PROVIDERS = (
    ("opencode", "OpenCode Zen", "https://opencode.ai/zen/v1", "OPENCODE_API_KEY", OPENAI,
     "Curated pay-per-use gateway. Use models as opencode/<id>; catalog at opencode.ai/zen/v1/models."),
    ("opencode-go", "OpenCode Go", "https://opencode.ai/zen/go/v1", "OPENCODE_API_KEY", OPENAI,
     "Low-cost subscription plan models from the OpenCode team."),
    ("openai", "OpenAI", "https://api.openai.com/v1", "OPENAI_API_KEY", OPENAI, ""),
    ("anthropic", "Anthropic", "https://api.anthropic.com/v1", "ANTHROPIC_API_KEY", ANTHROPIC,
     "Native Messages API. Tool-calling is simplified to text on this protocol."),
    ("custom", "Custom endpoint", "", "", OPENAI,
     "Any OpenAI-compatible server. Set --base-url and --api-key explicitly."),
    ("302ai", "302.AI", "https://api.302.ai/v1", "AI302_API_KEY", OPENAI, ""),
    ("deepseek", "DeepSeek", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", OPENAI, ""),
    ("groq", "Groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", OPENAI, ""),
    ("together", "Together AI", "https://api.together.xyz/v1", "TOGETHER_API_KEY", OPENAI, ""),
    ("fireworks", "Fireworks AI", "https://api.fireworks.ai/inference/v1", "FIREWORKS_API_KEY", OPENAI, ""),
    ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", OPENAI, ""),
    ("llmgateway", "LLM Gateway", "https://api.llmgateway.io/v1", "LLM_GATEWAY_API_KEY", OPENAI, ""),
    ("xai", "xAI", "https://api.x.ai/v1", "XAI_API_KEY", OPENAI, ""),
    ("mistral", "Mistral", "https://api.mistral.ai/v1", "MISTRAL_API_KEY", OPENAI, ""),
    ("moonshot", "Moonshot AI (Kimi)", "https://api.moonshot.ai/v1", "MOONSHOT_API_KEY", OPENAI, ""),
    ("minimax", "MiniMax", "https://api.minimax.io/v1", "MINIMAX_API_KEY", OPENAI, ""),
    ("zai", "Z.AI (GLM)", "https://api.z.ai/api/paas/v4", "ZAI_API_KEY", OPENAI, ""),
    ("deepinfra", "Deep Infra", "https://api.deepinfra.com/v1/openai", "DEEPINFRA_API_KEY", OPENAI, ""),
    ("cerebras", "Cerebras", "https://api.cerebras.ai/v1", "CEREBRAS_API_KEY", OPENAI, ""),
    ("nvidia", "NVIDIA", "https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY", OPENAI,
     "Free tier at build.nvidia.com; local NIM via --base-url http://localhost:8000/v1."),
    ("nebius", "Nebius Token Factory", "https://api.tokenfactory.nebius.com/v1", "NEBIUS_API_KEY", OPENAI, ""),
    ("novita", "Novita", "https://api.novita.ai/openai/v1", "NOVITA_API_KEY", OPENAI, ""),
    ("siliconflow", "SiliconFlow", "https://api.siliconflow.cn/v1", "SILICONFLOW_API_KEY", OPENAI, ""),
    ("sambanova", "SambaNova", "https://api.sambanova.ai/v1", "SAMBANOVA_API_KEY", OPENAI, ""),
    ("hyperbolic", "Hyperbolic", "https://api.hyperbolic.xyz/v1", "HYPERBOLIC_API_KEY", OPENAI, ""),
    ("lepton", "Lepton AI", "https://api.lepton.ai/v1", "LEPTON_API_KEY", OPENAI, ""),
    ("perplexity", "Perplexity", "https://api.perplexity.ai", "PERPLEXITY_API_KEY", OPENAI, ""),
    ("cohere", "Cohere", "https://api.cohere.com/compatibility/v1", "CO_API_KEY", OPENAI,
     "OpenAI-compatibility endpoint."),
    ("ai21", "AI21", "https://api.ai21.com/studio/v1", "AI21_API_KEY", OPENAI, ""),
    ("writer", "Writer", "https://api.writer.com/v1", "WRITER_API_KEY", OPENAI, ""),
    ("upstage", "Upstage (Solar)", "https://api.upstage.ai/v1", "UPSTAGE_API_KEY", OPENAI, ""),
    ("alibaba", "Alibaba Qwen", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY", OPENAI, ""),
    ("volcengine", "Volcengine ARK (Doubao)", "https://ark.cn-beijing.volces.com/api/v3", "VOLCENGINE_API_KEY", OPENAI, ""),
    ("stepfun", "StepFun", "https://api.stepfun.com/v1", "STEPFUN_API_KEY", OPENAI, ""),
    ("baidu", "Baidu Qianfan", "https://qianfan.baidubce.com/v2", "BAIDU_API_KEY", OPENAI, ""),
    ("tencent", "Tencent Hunyuan", "https://api.hunyuan.cloud.tencent.com/v1", "TENCENT_API_KEY", OPENAI, ""),
    ("iflytek", "iFLYTEK Spark", "https://spark-api-open.xf-yun.com/v1", "IFLYTEK_API_KEY", OPENAI, ""),
    ("modelscope", "ModelScope", "https://api-inference.modelscope.cn/v1", "MODELSCOPE_API_KEY", OPENAI, ""),
    ("gmi", "GMI Cloud", "https://api.gmicloud.ai/v1", "GMI_API_KEY", OPENAI, ""),
    ("baseten", "Baseten", "https://inference.baseten.co/v1", "BASETEN_API_KEY", OPENAI, ""),
    ("cortecs", "Cortecs", "https://api.cortecs.ai/v1", "CORTECS_API_KEY", OPENAI, ""),
    ("frogbot", "FrogBot", "https://api.frogbot.ai/v1", "FROGBOT_API_KEY", OPENAI, ""),
    ("ionet", "IO.NET", "https://api.intelligence.io.solutions/api/v1", "IO_API_KEY", OPENAI, ""),
    ("edenai", "Eden AI", "https://api.edenai.run/v1", "EDENAI_API_KEY", OPENAI,
     "EU gateway via --base-url https://api.eu.edenai.run/v3."),
    ("zenmux", "ZenMux", "https://api.zenmux.ai/v1", "ZENMUX_API_KEY", OPENAI, ""),
    ("scx", "SCX.ai", "", "SCX_API_KEY", OPENAI,
     "OpenAI-compatible; set --base-url to your SCX.ai endpoint (platform.scx.ai)."),
    ("venice", "Venice AI", "https://api.venice.ai/api/v1", "VENICE_API_KEY", OPENAI, ""),
    ("vercel", "Vercel AI Gateway", "https://ai-gateway.vercel.sh/v1", "AI_GATEWAY_API_KEY", OPENAI, ""),
    ("helicone", "Helicone AI Gateway", "https://ai-gateway.helicone.ai", "HELICONE_API_KEY", OPENAI,
     "Observability gateway; routes to the provider matching your model."),
    ("github-models", "GitHub Models", "https://models.github.ai/inference", "GITHUB_TOKEN", OPENAI, ""),
    ("huggingface", "Hugging Face", "https://router.huggingface.co/v1", "HF_TOKEN", OPENAI,
     "Inference Providers router over 17+ providers."),
    ("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai/", "GEMINI_API_KEY", OPENAI,
     "Gemini OpenAI-compatibility endpoint."),
    ("requesty", "Requesty", "https://router.requesty.ai/v1", "REQUESTY_API_KEY", OPENAI, ""),
    ("aimlapi", "AI/ML API", "https://api.aimlapi.com/v1", "AIML_API_KEY", OPENAI, ""),
    ("chutes", "Chutes", "https://llm.chutes.ai/v1", "CHUTES_API_KEY", OPENAI, ""),
    ("kluster", "Kluster", "https://api.kluster.ai/v1", "KLUSTER_API_KEY", OPENAI, ""),
    ("featherless", "Featherless", "https://api.featherless.ai/v1", "FEATHERLESS_API_KEY", OPENAI, ""),
    ("infermatic", "Infermatic", "https://api.infermatic.ai/v1", "INFERMATIC_API_KEY", OPENAI, ""),
    ("targon", "Targon", "https://api.targon.com/v1", "TARGON_API_KEY", OPENAI, ""),
    ("nscale", "Nscale", "https://api.nscale.com/v1", "NSCALE_API_KEY", OPENAI, ""),
    ("friendli", "Friendli", "https://api.friendli.ai/serverless/v1", "FRIENDLI_API_KEY", OPENAI, ""),
    ("anyscale", "Anyscale", "https://api.endpoints.anyscale.com/v1", "ANYSCALE_API_KEY", OPENAI, ""),
    ("ollama-cloud", "Ollama Cloud", "https://ollama.com/v1", "OLLAMA_API_KEY", OPENAI,
     "Pull model info locally first: ollama pull <model>-cloud."),
    ("poolside", "Poolside", "", "POOLSIDE_API_KEY", OPENAI,
     "OpenAI-compatible; set --base-url to your deployment (platform.poolside.ai > API Keys)."),
    ("databricks", "Databricks", "", "DATABRICKS_TOKEN", OPENAI,
     "Set --base-url to https://<workspace>.cloud.databricks.com/serving-endpoints."),
    ("scaleway", "Scaleway", "", "SCW_SECRET_KEY", OPENAI,
     "Scaleway Generative APIs; set --base-url to your endpoint."),
    ("stackit", "STACKIT", "", "STACKIT_API_KEY", OPENAI,
     "STACKIT AI Model Serving; set --base-url and token from portal.stackit.cloud."),
    ("ovhcloud", "OVHcloud AI Endpoints", "", "OVH_AI_API_KEY", OPENAI,
     "Set --base-url to your region endpoint (AI & Machine Learning > AI Endpoints)."),
    ("snowflake", "Snowflake Cortex", "", "SNOWFLAKE_CORTEX_TOKEN", OPENAI,
     "Runs inside the Snowflake perimeter; set --base-url to https://<account>.snowflakecomputing.com."),
    ("ollama", "Ollama (local)", "http://localhost:11434/v1", "", OPENAI,
     "No key needed (local). Pick tool-capable models; raise num_ctx to 16k-32k if tools fail."),
    ("lmstudio", "LM Studio (local)", "http://127.0.0.1:1234/v1", "", OPENAI,
     "No key needed (local)."),
    ("llamacpp", "llama.cpp (local)", "http://127.0.0.1:8080/v1", "", OPENAI,
     "No key needed (local llama-server)."),
    ("atomic-chat", "Atomic Chat (local)", "http://127.0.0.1:1337/v1", "", OPENAI,
     "No key needed (local). Check GET /v1/models for loaded model ids."),
    ("azure", "Azure OpenAI", "", "AZURE_OPENAI_API_KEY", AZURE,
     "Set --base-url to https://<resource>.openai.azure.com and --model to your deployment name."),
    ("azure-cognitiveservices", "Azure Cognitive Services", "", "AZURE_OPENAI_API_KEY", AZURE,
     "Set --base-url to https://<resource>.cognitiveservices.azure.com and --model to your deployment name."),
    ("bedrock", "Amazon Bedrock", "", "AWS_BEARER_TOKEN_BEDROCK", CUSTOM,
     "Needs AWS SigV4 signing (access keys, profile, or bearer token); not HTTP-portable in this client."),
    ("vertex", "Google Vertex AI", "", "GOOGLE_APPLICATION_CREDENTIALS", CUSTOM,
     "Needs GCP OAuth (service account or gcloud ADC) plus GOOGLE_CLOUD_PROJECT."),
    ("github-copilot", "GitHub Copilot", "", "", CUSTOM,
     "Needs Copilot device flow (github.com/login/device); not API-key based."),
    ("gitlab-duo", "GitLab Duo", "", "GITLAB_TOKEN", CUSTOM,
     "Needs GitLab OAuth or PAT on Premium/Ultimate; Duo Agent Platform flow."),
    ("sap", "SAP AI Core", "", "AICORE_SERVICE_KEY", CUSTOM,
     "Needs SAP OAuth service key; not Bearer based."),
    ("modal", "Modal", "", "", CUSTOM,
     "Per-endpoint proxy token wk-<id>.ws-<secret>; set --base-url to your Modal endpoint."),
    ("digitalocean", "DigitalOcean Inference", "", "DIGITALOCEAN_ACCESS_TOKEN", CUSTOM,
     "OAuth login or Model Access Key; routers only via OAuth."),
    ("cloudflare-workers", "Cloudflare Workers AI", "", "CLOUDFLARE_API_KEY", CUSTOM,
     "Needs CLOUDFLARE_ACCOUNT_ID plus token; account-scoped REST API."),
    ("cloudflare-gateway", "Cloudflare AI Gateway", "", "CLOUDFLARE_API_TOKEN", CUSTOM,
     "Needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_GATEWAY_ID; unified billing target."),
)


def get_provider(pid):
    # type: (str) -> Optional[Dict[str, str]]
    for pid_, name, base, key, proto, note in PROVIDERS:
        if pid_ == (pid or "").strip().lower():
            return {"id": pid_, "name": name, "base": base, "key": key,
                    "proto": proto, "note": note}
    return None


def provider_ids():
    # type: () -> List[str]
    return [p[0] for p in PROVIDERS]


def count():
    # type: () -> int
    return len(PROVIDERS)


def resolve(cfg, fallback_base=""):
    # type: (Dict[str, Any], str) -> Dict[str, Any]
    """Fill base_url/api_key/protocol from the selected provider.

    Explicit values in cfg (from file/env/CLI) always win; provider values
    only fill blanks. Returns cfg for chaining.
    """
    pid = str(cfg.get("provider", "") or "openai").strip().lower()
    p = get_provider(pid)
    if p is None:
        cfg["protocol"] = OPENAI
        cfg["provider_note"] = ""
        return cfg
    if not str(cfg.get("base_url", "") or "").strip():
        cfg["base_url"] = p["base"] or fallback_base
    if not str(cfg.get("api_key", "") or "").strip() and p["key"]:
        import os as _os

        cfg["api_key"] = _os.environ.get(p["key"], "")
    cfg["protocol"] = p["proto"]
    cfg["provider_note"] = p["note"]
    return cfg
