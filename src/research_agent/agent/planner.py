import json
from typing import Any

import httpx
from pydantic import ValidationError

from research_agent.agent.models import BlockedDecision, Workflow
from research_agent.agent.prompts import build_planner_prompt
from research_agent.runtime.secret_guard import assert_no_secret_contamination


class Planner:
    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
    ):
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def _complete(self, messages: list[dict[str, str]]) -> str:
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": 0,
                "messages": messages,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @staticmethod
    def _parse(content: str) -> Workflow | BlockedDecision:
        try:
            decoded = json.loads(content)
        except (TypeError, ValueError):
            decoded = None
        if isinstance(decoded, dict) and decoded.get("status") == "blocked":
            return BlockedDecision.model_validate(decoded)
        return Workflow.model_validate_json(content)

    async def plan(
        self, instruction: str, file_summaries: list[dict[str, Any]], skill_descriptors
    ) -> Workflow | BlockedDecision:
        """Return a workflow to review, or the control layer's refusal."""
        if not self.model:
            raise ValueError("Model name is required")
        system_prompt = build_planner_prompt(file_summaries, skill_descriptors)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
        ]
        content = await self._complete(messages)
        assert_no_secret_contamination(content, self.api_key)
        try:
            result = self._parse(content)
        except ValidationError as error:
            repair_messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Repair the following invalid workflow JSON. Return only the corrected JSON. "
                        "Do not change the user's intended task. If the task crosses a boundary "
                        "stated in the control layer, return the blocked decision JSON instead.\n"
                        f"VALIDATION_ERRORS={error.errors(include_url=False)}\n"
                        f"INVALID_WORKFLOW={content}"
                    ),
                },
            ]
            repaired = await self._complete(repair_messages)
            assert_no_secret_contamination(repaired, self.api_key)
            result = self._parse(repaired)
        assert_no_secret_contamination(result.model_dump(mode="json"), self.api_key)
        return result
