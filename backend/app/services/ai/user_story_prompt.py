
"""Build structured prompts for AI-assisted user story generation."""


SYSTEM_PROMPT = """
You are a senior business analyst specializing in Agile software development.

Your task is to generate a professional user story draft from a business
requirement.

Follow these rules:
1. Use only the information provided in the requirement.
2. Do not invent business rules, integrations, or technical capabilities.
3. Write the user story from the perspective of a relevant user role.
4. Use the format: As a [role], I want [goal], so that [benefit].
5. Generate clear, measurable, and testable acceptance criteria.
6. If information is missing, do not assume facts.
7. Return a JSON object containing exactly:
   - title
   - description
   - acceptance_criteria
8. Keep the title within 160 characters.
9. Keep the description within 5000 characters.
10. Generate between 1 and 10 acceptance criteria.
11. Keep each acceptance criterion within 1000 characters.
12. Do not include Markdown formatting or explanations outside the JSON.
""".strip()


def build_user_story_prompt(
    requirement_title: str,
    requirement_description: str,
    requirement_priority: str,
) -> str:
    """Build a user prompt using the source requirement."""

    # Gereksinim bilgilerini AI modeline yapılandırılmış biçimde iletiyorum.
    # Kaynak gereksinimde bulunmayan bilgilerin uydurulmamasını istiyorum.
    return f"""
Generate a user story draft based on the following requirement.

Requirement title:
{requirement_title}

Requirement description:
{requirement_description}

Requirement priority:
{requirement_priority}

Return only the requested JSON object.
""".strip()
