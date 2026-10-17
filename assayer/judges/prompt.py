"""Prompts owned by Assayer, versioned and hashed so Judge results are auditable."""

import hashlib
from dataclasses import dataclass
from string import Template


@dataclass(frozen=True)
class Prompt:
    """A Judge prompt: a system and a user message with `$name` placeholders.

    Args:
        id: Stable name of the prompt, such as "criteria".
        version: Version of its wording; bump it when the text changes.
        system: System message.
        user: User message, filled with the values of the subject being judged.

    Raises:
        ValueError: If id or version is blank, or a template is malformed.
    """

    id: str
    version: str
    system: str
    user: str

    def __post_init__(self) -> None:
        """Validate the identity and the templates.

        Raises:
            ValueError: If id or version is blank, or a template is malformed.
        """
        if not self.id.strip() or not self.version.strip():
            raise ValueError("Prompt id and version cannot be blank")
        for template in (self.system, self.user):
            Template(template).get_identifiers()  # raises ValueError on a bad `$`

    @property
    def ref(self) -> str:
        """The `id@version` that names this prompt in results."""
        return f"{self.id}@{self.version}"

    @property
    def hash(self) -> str:
        """SHA-256 of the prompt text, so an edited prompt is told apart from its version."""
        text = f"{self.system}\n---\n{self.user}"
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def render(self, **values: str) -> list[dict[str, str]]:
        """Fill the templates into chat messages.

        Args:
            **values: Value of each placeholder.

        Returns:
            The system and user messages.

        Raises:
            KeyError: If a placeholder has no value.
        """
        return [
            {"role": "system", "content": Template(self.system).substitute(values)},
            {"role": "user", "content": Template(self.user).substitute(values)},
        ]
