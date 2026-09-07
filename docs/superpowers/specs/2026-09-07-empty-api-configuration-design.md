# Empty API configuration on first launch

## Goal

PaleoRigor must not imply that DeepSeek is the built-in or required provider. On a fresh installation, the API base URL, model name, and API key fields are visually empty.

## User-visible behavior

- A fresh profile returns an empty API base URL and an empty model name.
- The web form displays neutral grey examples through placeholders only; placeholder text is never submitted as configuration.
- The API key field is always empty when the page opens, including when a key is already stored securely.
- A previously saved API base URL and model name are restored on later launches.
- The interface may indicate that a stored API key exists, but it must never reveal or place that key in the input field.
- Saving or testing an incomplete configuration reports exactly which required field is missing: API URL, model name, or API key.

## Implementation boundary

- Remove the DeepSeek-specific defaults from runtime configuration.
- Keep the existing preferences and secure-secret stores so user-saved settings continue to persist.
- Use provider-neutral placeholders in both English and Chinese.
- Do not change planner behavior, supported API protocol, or packaging contents.

## Validation

- Unit tests cover fresh configuration, persisted configuration, API-key redaction, and required-field validation.
- Integration tests verify the configuration API returns empty values for a fresh profile.
- UI contract tests verify neutral placeholders and ensure no DeepSeek value is embedded in the initial form.
- Run the focused configuration/UI tests, then the full test suite relevant to the desktop application.

