from typing import Any

import httpx
from pydantic import ValidationError

from research_agent.agent.models import Workflow
from research_agent.agent.prompts import build_system_prompt


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

    async def plan(self, instruction: str, file_summaries: list[dict[str, Any]], skill_descriptors) -> Workflow:
        if not self.model:
            raise ValueError("Model name is required")
        system_prompt = build_system_prompt(file_summaries, skill_descriptors)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
        ]
        content = await self._complete(messages)
        try:
            return Workflow.model_validate_json(content)
        except ValidationError as error:
            repair_messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Repair the following invalid workflow JSON. Return only the corrected JSON. "
                        "Do not change the user's intended task.\n"
                        f"VALIDATION_ERRORS={error.errors(include_url=False)}\n"
                        f"INVALID_WORKFLOW={content}"
                    ),
                },
            ]
            repaired = await self._complete(repair_messages)
            return Workflow.model_validate_json(repaired)
