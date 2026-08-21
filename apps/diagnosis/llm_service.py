from django.conf import settings
from .utils import markdown_to_html


SYSTEM_PROMPT = (
    "You are PetXpert AI, a friendly and careful veterinary assistant. "

    "Provide concise, practical, easy-to-understand general guidance "
    "about pets, animals, and veterinary care. "

    "Do not make definitive diagnoses or prescribe prescription medication "
    "or dosages. Recommend veterinary care when symptoms are serious, "
    "persistent, or worsening. "

    "Respond naturally like a helpful ChatGPT-style assistant. "
    "Do not unnecessarily repeat the user's question. "
    "Do not introduce yourself unless specifically asked. "

    "Keep responses between 60 and 150 words. "

    "FORMAT: "
    "Use Markdown formatting. "
    "Use ### headings when multiple sections are useful. "
    "Use bullet points with -. "
    "Use **bold** for important information. "
    "Leave blank lines between sections. "
    "Do not generate HTML. "
    "Do not use code blocks. "

    "Only answer questions related to pets, animals, "
    "and veterinary care. "
    "For unrelated questions, politely explain that you "
    "only help with pet-related topics."
)


def _client():
    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        return None, 'GROQ_API_KEY is not configured.'
    try:
        from groq import Groq
    except ImportError as exc:
        return None, f'Groq dependency is not installed: {exc}'
    return Groq(api_key=api_key), ''


def _chat_completion(messages, temperature=0.3):
    client, error = _client()
    if error:
        return error

    try:
        result = client.chat.completions.with_raw_response.create(
            model='openai/gpt-oss-120b',
            messages=messages,
            temperature=temperature,
            max_tokens=400,
        )
        # Get HTTP headers
        headers = result.headers
        print("\n=== Groq API Rate Limits ===")
        print(
            "Requests limit:",
            headers.get("x-ratelimit-limit-requests", "N/A")
        )
        print(
            "Requests remaining:",
            headers.get("x-ratelimit-remaining-requests", "N/A")
        )
        print(
            "Tokens limit:",
            headers.get("x-ratelimit-limit-tokens", "N/A")
        )
        print(
            "Tokens remaining:",
            headers.get("x-ratelimit-remaining-tokens", "N/A")
        )
        print(
            "Request reset:",
            headers.get("x-ratelimit-reset-requests", "N/A")
        )
        print(
            "Token reset:",
            headers.get("x-ratelimit-reset-tokens", "N/A")
        )
        print("=============================\n")
        # Convert raw response into normal ChatCompletion object
        response = result.parse()
        # Show token usage for this request
        if response.usage:
            print("=== Token Usage ===")
            print("Prompt tokens:", response.usage.prompt_tokens)
            print("Completion tokens:", response.usage.completion_tokens)
            print("Total tokens:", response.usage.total_tokens)
            print("===================\n")
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"Groq API Error: {exc}")
        import traceback
        traceback.print_exc()
        return (
            'The AI assistant is temporarily unavailable. '
            'Please try again later or describe your pet\'s symptoms '
            'for general guidance.'
        )


def explain_disease(disease_name, severity='', similarity=None):
    if not disease_name or disease_name == 'Unknown':
        return 'The model could not confidently identify a known disease. Please consult a veterinarian if symptoms are visible or persistent.'
    similarity_text = f' Cosine similarity: {similarity:.3f}.' if similarity is not None else ''
    prompt = (
        f'Explain the dog condition "{disease_name}" for a pet owner. Severity: {severity or "unspecified"}.'
        f'{similarity_text} Use clear sections: Disease Overview, Causes, Symptoms, Treatments, '
        'Vet Recommendation, and Prevention Tips.'
    )
    return _chat_completion([
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': prompt},
    ])


def pet_chat(question):
    return _chat_completion([
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': question},
    ], temperature=0.5)


def _generate_diagnosis_html(disease, similarity, user_message=''):
    """Generate structured HTML diagnosis report."""
    similarity_value = float(similarity) if similarity else 0.0

    # Determine confidence level
    if similarity_value >= 0.8:
        confidence = "High"
        confidence_color = "#10B981"
    elif similarity_value >= 0.5:
        confidence = "Medium"
        confidence_color = "#F59E0B"
    else:
        confidence = "Low"
        confidence_color = "#EF4444"

    # Check if this is a healthy condition
    healthy_keywords = ['healthy', 'normal', 'no issues', 'clear', 'good', 'fine']
    is_healthy = any(keyword in disease.lower() for keyword in healthy_keywords)

    # Determine risk level - always Low for healthy conditions
    if is_healthy:
        risk = "Low"
        risk_emoji = "🟢"
    elif similarity_value >= 0.7:
        risk = "High"
        risk_emoji = "🔴"
    elif similarity_value >= 0.4:
        risk = "Moderate"
        risk_emoji = "🟡"
    else:
        risk = "Low"
        risk_emoji = "🟢"

    confidence_percentage = int(similarity_value * 100)

    prompt = f"""You are PetXpert AI, a professional veterinary assistant.

Generate a concise, modern, and user-friendly diagnosis response.

Rules:
- Keep the entire response between 80–150 words.
- Use emojis and clear section headings.
- Sound professional but friendly.
- Do not output raw model predictions.
- Explain the result in simple language.
- Include confidence percentage.
- Include a risk level badge: 🟢 Low, 🟡 Moderate, 🔴 High
- Provide 2–3 practical recommendations.
- Mention when a vet visit may be needed.
- Avoid lengthy explanations.
- Format the response like a premium AI assistant.
- IMPORTANT: If the condition is healthy/normal, do NOT include scary warning signs. Instead, mention general wellness tips.

Disease Prediction: {disease}
Owner Message: {user_message or '(none)'}
Is Healthy Condition: {is_healthy}
Similarity Score: {similarity_value:.3f}
Confidence: {confidence_percentage}% ({confidence} Confidence)
Risk Level: {risk}

Output Structure:

🩺 PetXpert AI Assessment

🩺 Result
{disease}

📊 Confidence
{confidence_percentage}% ({confidence} Confidence)

📝 Summary
One short sentence explaining the result in simple language.

✅ Recommended Care
• 2-3 practical recommendations

{risk_emoji} Risk Level
{risk}

⚠️ Seek Veterinary Care If
{'' if is_healthy else '2-3 important warning signs (only if this is NOT a healthy condition)'}

Return the response in clean HTML format using:
- Cards with light gray backgrounds
- Icons/emojis
- Colored badges
- Modern responsive styling with padding and rounded corners"""

    return _chat_completion([
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': prompt},
    ], temperature=0.3)


def _generate_error_html(error_message, include_tip=True):
    """Generate structured HTML error message."""
    tip_block = ''
    if include_tip:
        tip_block = """
    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #FECACA;">
        <p style="color: #991B1B; margin: 0; font-size: 13px;">💡 Please try again or consult a veterinarian if symptoms persist.</p>
    </div>"""
    return f"""<div style="background: #FEF2F2; border-left: 4px solid #EF4444; padding: 16px; border-radius: 8px; margin: 16px 0;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 24px;">⚠️</span>
        <div>
            <h3 style="color: #DC2626; margin: 0 0 8px 0; font-size: 16px;">Analysis Error</h3>
            <p style="color: #7F1D1D; margin: 0; font-size: 14px;">{error_message}</p>
        </div>
    </div>{tip_block}
</div>"""


def _strip_html(value):
    if not value:
        return ''
    import re
    text = re.sub(r'<[^>]+>', ' ', str(value))
    return re.sub(r'\s+', ' ', text).strip()


def assistant_reply(user_message, detection=None, history=None):
    """Single entry point for the chat assistant.

    When ``detection`` is provided (image was uploaded) the model's findings are
    woven into the prompt so the LLM responds with an image-aware answer.
    Otherwise it answers the owner's text directly.
    """
    user_message = (user_message or '').strip()
    owner_line = f"Owner's message: {user_message or '(no text provided)'}"

    if detection is None:
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        recent_history = (history or [])[-10:]
        for item in recent_history:
            role = item.get('role')
            content = _strip_html(item.get('content') or item.get('text') or '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content})
        messages.append({'role': 'user', 'content': user_message})
        response = _chat_completion(messages, temperature=0.5)
        return markdown_to_html(response)

    similarity = detection.get('similarity')
    similarity_text = f'{similarity:.3f}' if isinstance(similarity, (int, float)) else 'n/a'

    if detection.get('feature_unavailable'):
        error_msg = 'The image-based detector is currently unavailable on the server. Please try again later or describe your pet\'s symptoms in text.'
        html_response = _generate_error_html(error_msg)
        return html_response

    elif not detection.get('is_dog'):
        error_msg = 'The attached image does not appear to contain a dog. Our detector currently supports dogs only.'
        html_response = _generate_error_html(error_msg, include_tip=False)
        return html_response

    else:
        disease = detection.get('disease', 'Unknown')
        if disease == 'Unknown':
            error_msg = f'A dog was detected, but we couldn\'t confidently identify a specific condition (similarity: {similarity_text}). This might be due to image quality or an uncommon condition.'
            if user_message:
                return _chat_completion([
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': (
                        f'{owner_line}\n\nImage analysis: {error_msg} '
                        'Answer the owner\'s question using this context.'
                    )},
                ], temperature=0.4)
            html_response = _generate_error_html(error_msg)
            return html_response
        else:
            html_response = _generate_diagnosis_html(disease, similarity, user_message)
            return html_response