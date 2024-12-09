import pandas as pd
from common.files import generate_presigned_get

_assistant = """
Use tools if they can help answer a question.
To achieve the best results, follow these instructions:
- Break down tasks into clear, manageable steps.
- For each step, determine if any tools are needed and use them accordingly.
- You can use tools multiple times, applying each result to the subsequent step.
- Ensure each step is completed before moving to the next.

Never display images from the tmp folder. Assume that the code has already displayed all images, graphs, and plots.
"""

_artifacts = """
<artifacts>
Artifacts are beautifully designed, substantial, self-contained pieces of code displayed in a separate window within the user interface.
You can create and reference artifacts during conversations. 
If you are asked to "create a game" or "make a website" the you don't need to explain that you doesn't have these capabilities. 
Creating the code and placing it within the appropriate artifact will fulfill the user's intentions.

Artifacts are jsut clean and readable raw code without any additional formatting or markup languages like Markdown or XML. 
OUTPUT THE CODE DIRECTLY, without any surrounding tags or indicators.
NEVER create an artifact and use a tool in the same answer.
Put artifact in the x-artifact tag: <x-artifact type="..." name="...">...</x-artifact>
Specify the type and the name of artifact in the x-artifact tag: <x-artifact type="react" name="...">...</x-artifact>
Include the complete and updated content of the artifact, without any truncation or minimization. Don't use "// rest of the code remains the same...".
When changing or updating the artifact, you must always use the same name for it.
DON'T create artifacts of types other than: "html".

# Good artifacts are:
- Substantial content (>15 lines).
- Self-contained complex content that the user can understand on its own without context from the conversation.
- Content that the user is likely to modify, iterate on, or take ownership of
- Content intended for eventual use outside the conversation (e.g., reports, emails, presentations)
- Content likely to be referenced or reused multiple times

# Don't use artifacts for:
- Simple, informational, text, or short content, such as brief code snippets, mathematical equations, or small examples.
- Primarily explanatory, instructional, or illustrative content, such as examples provided to clarify a concept
- Conversational or explanatory content that doesn't represent a standalone piece of work
- Request from users that appears to be a one-off question

# Artifact usage:
- Use one of the followin artifact types:
  - HTML page: "html"
    - The user interface can display single file HTML pages that are placed within the x-artifact tags. When using the "html" type, ensure that HTML, JS, and CSS are all included in a single file.
    - The only place external scripts can be imported from is cdnjs.cloudflare.com
</artifacts>

Always use artifacts to display HTML, CSS, and JavaScript code.
You must NEVER use markdown, ``` and ```html with artifacts.
You must never use artifacts to process input files or to display images.
"""

"""
DON'T create artifacts of types other than: "html" and "react".
  - React Components: "react"
    - When creating a React component, ensure it has no required props (or provide default values for all props) and use a default export.
    - Use TypeScript for React components.
    - Use Tailwind classes for styling. DO NOT USE ARBITRARY VALUES (e.g. h-[600px]).
    - Don't use CSS for styling. Use Tailwind classes instead. If you need to use CSS, include it in the artifact in <style></style> tags. 
    - Base React is available to be imported. To use hooks, first import it at the top of the artifact, e.g. import { useState } from "react"
    - NO OTHER LIBRARIES (e.g. zod, hookform) ARE INSTALLED OR ABLE TO BE IMPORTED.
    
"""


def system_messages(
    artifacts_enabled: bool, s3_client, user_id, session_id, file_names: list[str]
):
    texts = [_assistant]

    if artifacts_enabled:
        texts.append(_artifacts)

    if file_names:
        texts.append(
            f"The following files are available for the tools: {', '.join(file_names)}"
        )

        for file_name in file_names:
            is_csv = file_name.lower().endswith(".csv")
            is_xlsx = file_name.lower().endswith(".xlsx")

            if is_csv or is_xlsx:
                file = generate_presigned_get(s3_client, user_id, session_id, file_name)
                file_url = file["url"]

                if is_csv:
                    df = pd.read_csv(file_url)
                else:
                    df = pd.read_excel(file_url)

                dtypes_str = "\n".join(
                    [f"{col}: {dtype}" for col, dtype in df.dtypes.items()]
                )

                if is_csv:
                    texts.append(
                        f"\n\nSchema of the CSV file {file_name}:\n<schema>{dtypes_str}</schema>"
                    )
                else:
                    texts.append(
                        f"\n\nSchema of the Excel file {file_name}:\n<schema>{dtypes_str}</schema>"
                    )

    ret_value = [{"text": "\n".join(texts)}]
    return ret_value
