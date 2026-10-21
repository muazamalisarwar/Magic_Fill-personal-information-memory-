import sys
sys.path.insert(0, '.')
import asyncio
import json
from app.database.database import SessionLocal
from app.services.user_service import get_user_profile
from app.services.groq_service import query_groq_llm, _extract_all_memory_tokens, _is_grounded_in_memory

async def test_full():
    db = SessionLocal()
    profile = get_user_profile(db, 1)
    p = profile['personal_info']
    user_mem = {
        'personal_info': {
            'full_name': p.full_name,
            'email': p.email,
            'phone': p.phone,
            'gender': p.gender,
            'date_of_birth': p.date_of_birth.isoformat() if p.date_of_birth else None,
            'degree': p.degree,
            'university': p.university,
        },
        'experiences': [
            {'company': e.company, 'job_title': e.job_title, 'description': e.description, 'skills': e.skills}
            for e in (profile.get('experiences') or [])
        ],
        'custom_fields': [
            {'field_key': cf.field_key, 'field_label': cf.field_label, 'field_value': cf.field_value}
            for cf in (profile.get('custom_fields') or [])
        ]
    }
    fields = [
        {'field_id': 'f_exp', 'label': 'Years of Professional Experience', 'input_type': 'range', 'min': 0, 'max': 20},
        {'field_id': 'f_bio', 'label': 'Professional Summary / Bio', 'input_type': 'textarea'},
        {'field_id': 'f_reloc', 'label': 'Willing to Relocate?', 'input_type': 'checkbox'},
        {'field_id': 'f_deg', 'label': 'Education Level', 'input_type': 'select', 'options': ['High School', 'Associate', 'Bachelor of Science', 'Master of Science', 'Doctorate']},
        {'field_id': 'f_work_auth', 'label': 'Work Authorization', 'input_type': 'radio', 'options': ['Authorized to work in country', 'Need visa sponsorship']},
    ]

    system_prompt = (
        "You are Magic Fill's Core AI Form Matching Engine. Your mission is to analyze "
        "ALL detected input fields on a web page and decide which value from User Memory "
        "should be written into each field.\n\n"
        "Return a valid JSON object matching this schema:\n"
        "{\n"
        '  "mappings": [\n'
        "    {\n"
        '      "field_id": "field id",\n'
        '      "memory_key": "path in user_memory",\n'
        '      "value": "exact grounded value",\n'
        '      "confidence": 0.95,\n'
        '      "reason": "explanation"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    user_prompt = {
        'form_context': 'Test Form',
        'user_memory': user_mem,
        'fields_to_match': fields,
    }
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': json.dumps(user_prompt)},
    ]
    raw_res = await query_groq_llm(messages)
    print('Raw LLM Response:')
    print(json.dumps(raw_res, indent=2))

    if raw_res and 'mappings' in raw_res:
        valid_memory_values, raw_memory_strings = _extract_all_memory_tokens(user_mem)
        for item in raw_res['mappings']:
            val = str(item.get('value', ''))
            key = str(item.get('memory_key', ''))
            grounded = _is_grounded_in_memory(val, key, valid_memory_values, raw_memory_strings)
            print(f'Item: {item.get("field_id")} -> val="{val}", grounded={grounded}')

asyncio.run(test_full())
