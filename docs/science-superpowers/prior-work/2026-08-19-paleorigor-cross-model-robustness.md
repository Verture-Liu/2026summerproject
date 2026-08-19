# Prior-work note: PaleoRigor cross-model robustness

The matched-arm design and strict-success endpoint are inherited unchanged from the approved PaleoRigor benchmark question, plan, and v5 pre-registration. This avoids introducing a new endpoint after seeing the Flash outcome.

DeepSeek's official API documentation states that V4-Pro and V4-Flash are available through the same Chat Completions interface and base URL, with model identifiers `deepseek-v4-pro` and `deepseek-v4-flash`. This permits a second-model robustness check while keeping provider, API protocol, prompt format, response format, and local execution environment fixed.

The main validity threat is model-configuration confounding: Pro and Flash differ in capacity and potentially latency/cost. Therefore the primary estimand is the within-Pro PaleoRigor-versus-raw difference. Absolute Pro-versus-Flash ranking is explicitly excluded. The previously observed Flash outcomes cannot serve as a new confirmatory sample and will be shown only as context.

Source: DeepSeek API documentation, “DeepSeek V4 Preview Release,” 24 April 2026, https://api-docs.deepseek.com/news/news260424/ (accessed 19 August 2026).
