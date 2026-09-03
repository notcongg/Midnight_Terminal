from __future__ import annotations

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.status import Status

from src.cmd.rootfs.ai.ai_log import write_ai_log
from src.cmd.rootfs.ai.models import (
    get_api_key,
    get_base_url,
    get_model,
)
from src.cmd.rootfs.ai.options import (
    AIOptions,
    parse_args,
)
from src.shell.context.context import ShellContext


load_dotenv()

console = Console()


def _build_messages(
    question: str,
    piped_input: str,
    system_prompt: str | None,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    if piped_input:
        content = (
            f"{question}\n\n"
            "The following content was provided "
            "through the Midnight Terminal pipeline:\n\n"
            "```\n"
            f"{piped_input}"
            "```\n"
        )
    else:
        content = question

    messages.append(
        {
            "role": "user",
            "content": content,
        }
    )

    return messages


def _complete(
    client: OpenAI,
    model: str,
    messages: list[dict[str, str]],
    options: AIOptions,
):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=options.temperature,
        top_p=options.top_p,
        max_tokens=options.max_tokens,
        seed=options.seed,
        stream=options.stream,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": options.thinking,
            }
        },
    )


def _stream_response(completion) -> str:
    response_parts: list[str] = []

    for chunk in completion:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        content = getattr(
            delta,
            "content",
            None,
        )

        if content:
            print(
                content,
                end="",
                flush=True,
            )

            response_parts.append(content)

    print()

    return "".join(response_parts)


def _thinking_status() -> Status:
    return Status(
        "Thinking...",
        spinner="dots",
    )


def cmd_ai(
    args: list[str],
    context: ShellContext,
) -> str:
    # ---------------------------------------------------------
    # Parse arguments
    # ---------------------------------------------------------

    try:
        options, question_parts = parse_args(args)

    except ValueError as exc:
        return f"ai: {exc}\n"

    if not question_parts:
        return "ai: missing question\n"

    question = " ".join(question_parts)

    # ---------------------------------------------------------
    # Resolve model / API
    # ---------------------------------------------------------

    try:
        config = get_model(options.model)
        api_key = get_api_key(config)
        base_url = get_base_url()

    except (ValueError, RuntimeError) as exc:
        return f"ai: {exc}\n"

    # ---------------------------------------------------------
    # Read pipeline/input-redirection data only when present
    # ---------------------------------------------------------

    piped_input = ""

    if getattr(
        context,
        "has_pipeline_input",
        False,
    ):
        piped_input = context.stdin.read()

    # ---------------------------------------------------------
    # Build messages
    # ---------------------------------------------------------

    messages = _build_messages(
        question=question,
        piped_input=piped_input,
        system_prompt=options.system,
    )

    # ---------------------------------------------------------
    # Create client
    # ---------------------------------------------------------

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    # ---------------------------------------------------------
    # Thinking spinner
    # ---------------------------------------------------------

    status: Status | None = None

    if options.thinking:
        status = _thinking_status()
        status.start()

    try:
        completion = _complete(
            client=client,
            model=config.model,
            messages=messages,
            options=options,
        )

    except Exception as exc:
        if status is not None:
            status.stop()

        return f"ai: {exc}\n"

    finally:
        if status is not None:
            status.stop()

    # ---------------------------------------------------------
    # Get response
    # ---------------------------------------------------------

    if options.stream:
        response = _stream_response(
            completion
        )

    else:
        try:
            response = (
                completion
                .choices[0]
                .message
                .content
                or ""
            )

        except (AttributeError, IndexError):
            return "ai: invalid response from model\n"

    # ---------------------------------------------------------
    # Save request / response log
    # ---------------------------------------------------------

    try:
        write_ai_log(
            model=config.name,
            engine=config.model,
            thinking=options.thinking,
            stream=options.stream,
            question=question,
            response=response,
        )

    except OSError:
        # Logging must never break the AI command.
        pass

    # ---------------------------------------------------------
    # Streaming already printed the response
    # ---------------------------------------------------------

    if options.stream:
        return ""

    return response
