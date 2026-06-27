from django.conf import settings


SYSTEM_PROMPT = (
    'You are PetXpert AI, a careful veterinary assistant. Provide concise, practical '
    'education for pet owners, avoid definitive medical claims, and recommend a licensed '
    'veterinarian for urgent symptoms or worsening conditions. '
    'IMPORTANT: Keep ALL responses concise and to the point. Maximum 100-150 words per response. '
    'Use bullet points for recommendations. Avoid lengthy explanations. '
    'IMPORTANT: You must ONLY answer questions related to pets, animals, and veterinary care. '
    'If a user asks about ANY other topic (cars, technology, cooking, etc.) in ANY language, '
    'politely decline and explain that you are a veterinary assistant designed to help with pet-related questions only. '
    'Do not provide advice on non-pet topics regardless of the language used.'
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
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            temperature=temperature,
            max_tokens=900,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f'Unable to get an AI response right now: {exc}'


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
    ], temperature=0.4)


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

� PetXpert AI Assessment

🩺 Result
{disease}

📊 Confidence
{confidence_percentage}% ({confidence} Confidence)

� Summary
One short sentence explaining the result in simple language.

✅ Recommended Care
• 2-3 practical recommendations

{risk_emoji} Risk Level
{risk}

⚠️ Seek Veterinary Care If
{'' if is_healthy else '2-3 important warning signs (only if this is NOT a healthy condition)'}

AI assessments are image-based and should not replace professional veterinary advice.

Return the response in clean HTML format using:
- Cards with light gray backgrounds
- Icons/emojis
- Colored badges
- Modern responsive styling with padding and rounded corners"""
    
    return _chat_completion([
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': prompt},
    ], temperature=0.3)


def _generate_error_html(error_message):
    """Generate structured HTML error message."""
    return f"""<div style="background: #FEF2F2; border-left: 4px solid #EF4444; padding: 16px; border-radius: 8px; margin: 16px 0;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 24px;">⚠️</span>
        <div>
            <h3 style="color: #DC2626; margin: 0 0 8px 0; font-size: 16px;">Analysis Error</h3>
            <p style="color: #7F1D1D; margin: 0; font-size: 14px;">{error_message}</p>
        </div>
    </div>
    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #FECACA;">
        <p style="color: #991B1B; margin: 0; font-size: 13px;">💡 Please try again or consult a veterinarian if symptoms persist.</p>
    </div>
</div>"""


def assistant_reply(user_message, detection=None):
    """Single entry point for the chat assistant.

    When ``detection`` is provided (image was uploaded) the model's findings are
    woven into the prompt so the LLM responds with an image-aware answer.
    Otherwise it answers the owner's text directly.
    """
    user_message = (user_message or '').strip()
    owner_line = f"Owner's message: {user_message or '(no text provided)'}"

    if detection is None:
        return _chat_completion([
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_message},
        ], temperature=0.4)

    similarity = detection.get('similarity')
    similarity_text = f'{similarity:.3f}' if isinstance(similarity, (int, float)) else 'n/a'

    if detection.get('feature_unavailable'):
        error_msg = 'The image-based detector is currently unavailable on the server. Please try again later or describe your pet\'s symptoms in text.'
        html_response = _generate_error_html(error_msg)
        return html_response
    
    elif not detection.get('is_dog'):
        error_msg = 'The attached image does not appear to contain a dog. Our detector currently supports dogs only.'
        html_response = _generate_error_html(error_msg)
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
