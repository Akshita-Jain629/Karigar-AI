from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
import os
from services.user_service import get_or_create_user, update_user, complete_lesson, award_certificate
from services.lesson_data import get_lessons_for_skill, get_lesson_by_id, LANGUAGE_NAMES, SKILL_NAMES
from models.schemas import SkillCategory

router = APIRouter()

# Simulated WhatsApp message handler
# In production: integrate with Twilio/Meta WhatsApp Cloud API

def process_message(phone_number: str, message: str) -> str:
    """Core logic: process incoming WhatsApp message and return response"""
    user = get_or_create_user(phone_number)
    msg = message.strip().upper()
    state = user.get("state", "new")

    # New user - show welcome
    if state == "new":
        update_user(phone_number, {"state": "language_select"})
        return (
            "🙏 *Karigar AI में आपका स्वागत है!*\n"
            "Welcome to Karigar AI!\n\n"
            "अपनी भाषा चुनें / Choose your language:\n\n"
            "1️⃣ हिंदी\n2️⃣ தமிழ்\n3️⃣ తెలుగు\n"
            "4️⃣ বাংলা\n5️⃣ मराठी\n6️⃣ ગુજરાતી\n"
            "7️⃣ ಕನ್ನಡ\n8️⃣ മലയാളം\n9️⃣ English\n\n"
            "नंबर भेजें / Send the number"
        )

    # Language selection
    elif state == "language_select":
        lang_map = {"1": "hi", "2": "ta", "3": "te", "4": "bn", "5": "mr",
                    "6": "gu", "7": "kn", "8": "ml", "9": "en"}
        if msg in lang_map:
            lang = lang_map[msg]
            update_user(phone_number, {"language": lang, "state": "skill_select"})
            return (
                f"✅ भाषा चुनी: {LANGUAGE_NAMES[lang]}\n\n"
                "अब अपना कोर्स चुनें / Choose your course:\n\n"
                "1️⃣ ⚡ Electrician\n2️⃣ 🔧 Plumbing\n"
                "3️⃣ 🪚 Carpentry\n4️⃣ 🏗️ Construction\n"
                "5️⃣ 🔥 Welding\n6️⃣ 🖌️ Painting\n"
                "7️⃣ 🚗 Driving\n8️⃣ 📦 Delivery\n"
                "9️⃣ 🛡️ Security\n🔟 📱 Mobile Repair\n\n"
                "नंबर भेजें / Send the number"
            )
        else:
            return "कृपया 1-9 में से कोई नंबर भेजें\nPlease send a number from 1-9"

    # Skill selection
    elif state == "skill_select":
        skill_map = {"1": "electrician", "2": "plumbing", "3": "carpentry",
                     "4": "construction", "5": "welding", "6": "painting",
                     "7": "driving", "8": "delivery", "9": "security", "10": "mobile_repair"}
        if msg in skill_map:
            skill = skill_map[msg]
            update_user(phone_number, {"skill": skill, "state": "learning", "current_lesson": 1})
            return (
                f"🎉 बढ़िया! आपने चुना: {SKILL_NAMES[skill]}\n\n"
                f"आपका कोर्स शुरू हो रहा है!\n"
                f"Your course is starting!\n\n"
                f"📚 *पाठ 1 शुरू करने के लिए START भेजें*\n"
                f"Send START to begin Lesson 1\n\n"
                f"📊 Progress देखने के लिए: PROGRESS\n"
                f"❓ Help के लिए: HELP"
            )
        else:
            return "कृपया 1-10 में से कोई नंबर भेजें\nPlease send a number from 1-10"

    # Learning state
    elif state == "learning":
        skill_str = user.get("skill", "electrician")
        try:
            skill = SkillCategory(skill_str)
        except:
            skill = SkillCategory.ELECTRICIAN

        current_lesson_id = user.get("current_lesson", 1)
        lesson = get_lesson_by_id(skill, current_lesson_id)

        if msg == "START" or msg == "NEXT":
            if not lesson:
                return (
                    "🎊 *बधाई हो! आपने पूरा कोर्स पूरा किया!*\n"
                    "Congratulations! You completed the full course!\n\n"
                    "🏆 CERTIFICATE पाने के लिए: CERTIFICATE\n"
                    "नया कोर्स शुरू करने के लिए: NEW"
                )
            update_user(phone_number, {"state": "quiz"})
            return (
                f"📖 *पाठ {lesson['id']}: {lesson['title_hindi']}*\n"
                f"Lesson {lesson['id']}: {lesson['title']}\n\n"
                f"🎵 *[Audio Lesson - {lesson['duration_minutes']} min]*\n\n"
                f"📝 {lesson['audio_script_hindi']}\n\n"
                f"---\n"
                f"✅ पाठ सुनने के बाद QUIZ भेजें\n"
                f"After listening, send QUIZ"
            )

        elif msg == "QUIZ":
            if not lesson:
                return "पहले START भेजें / Send START first"
            quiz = lesson["quiz_questions"][0]
            update_user(phone_number, {"state": "quiz", "current_quiz": lesson["id"]})
            return (
                f"❓ *Quiz - पाठ {lesson['id']}*\n\n"
                f"{quiz['question']}\n\n"
                f"{chr(10).join(quiz['options'])}\n\n"
                f"A, B, C या D भेजें / Send A, B, C or D"
            )

        elif msg == "PROGRESS":
            completed = len(user.get("completed_lessons", []))
            xp = user.get("total_xp", 0)
            certs = len(user.get("certificates_earned", []))
            return (
                f"📊 *आपकी Progress / Your Progress*\n\n"
                f"✅ पूरे पाठ: {completed}/5\n"
                f"⭐ XP Points: {xp}\n"
                f"🏆 Certificates: {certs}\n"
                f"📚 Current Course: {SKILL_NAMES.get(skill_str, skill_str)}\n\n"
                f"अगला पाठ: NEXT\n"
                f"Quiz: QUIZ"
            )

        elif msg == "CERTIFICATE":
            completed = user.get("completed_lessons", [])
            if len(completed) >= 5:
                award_certificate(phone_number, skill_str)
                return (
                    f"🎓 *Certificate जारी हुआ!*\n\n"
                    f"*Karigar AI*\n"
                    f"यह प्रमाणित करता है कि\n"
                    f"*{user.get('name', 'Worker')}*\n"
                    f"ने {SKILL_NAMES.get(skill_str)} कोर्स\n"
                    f"सफलतापूर्वक पूरा किया है।\n\n"
                    f"🆔 Certificate ID: KRGR-{phone_number[-4:]}-{skill_str[:3].upper()}\n"
                    f"📅 Date: Today\n\n"
                    f"💼 नौकरी ढूंढें: JOB"
                )
            else:
                remaining = 5 - len(completed)
                return f"⚠️ Certificate के लिए {remaining} और पाठ पूरे करें!\nComplete {remaining} more lessons for certificate!"

        elif msg == "HELP":
            return (
                "📋 *Commands / कमांड्स*\n\n"
                "START - पाठ शुरू करें\n"
                "NEXT - अगला पाठ\n"
                "QUIZ - Quiz दें\n"
                "PROGRESS - प्रगति देखें\n"
                "CERTIFICATE - सर्टिफिकेट पाएं\n"
                "JOB - नौकरी ढूंढें\n"
                "NEW - नया कोर्स\n\n"
                "🆘 Support: support@karigar.ai"
            )

        else:
            return (
                "📱 Commands:\n"
                "START - पाठ शुरू करें\n"
                "QUIZ - Quiz दें\n"
                "PROGRESS - प्रगति\n"
                "HELP - सहायता"
            )

    # Quiz state
    elif state == "quiz":
        skill_str = user.get("skill", "electrician")
        try:
            skill = SkillCategory(skill_str)
        except:
            skill = SkillCategory.ELECTRICIAN

        current_lesson_id = user.get("current_lesson", 1)
        lesson = get_lesson_by_id(skill, current_lesson_id)

        if lesson and msg in ["A", "B", "C", "D"]:
            quiz = lesson["quiz_questions"][0]
            correct = quiz["correct"]
            if msg == correct:
                complete_lesson(phone_number, lesson["id"], 100, lesson["xp_reward"])
                update_user(phone_number, {"state": "learning"})
                return (
                    f"✅ *सही जवाब! Correct!* 🎉\n\n"
                    f"💡 {quiz['explanation']}\n\n"
                    f"⭐ +{lesson['xp_reward']} XP मिले!\n\n"
                    f"अगले पाठ के लिए NEXT भेजें\n"
                    f"Send NEXT for the next lesson"
                )
            else:
                complete_lesson(phone_number, lesson["id"], 0, lesson["xp_reward"] // 2)
                update_user(phone_number, {"state": "learning"})
                return (
                    f"❌ *गलत जवाब। Wrong answer.*\n\n"
                    f"✅ सही जवाब था: {correct}\n"
                    f"💡 {quiz['explanation']}\n\n"
                    f"⭐ +{lesson['xp_reward']//2} XP मिले!\n\n"
                    f"अगले पाठ के लिए NEXT भेजें\n"
                    f"Send NEXT for the next lesson"
                )
        else:
            return "A, B, C या D भेजें / Send A, B, C or D"

    return "HELP भेजें / Send HELP for commands"


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """WhatsApp webhook endpoint - receives messages from Twilio/Meta"""
    form_data = await request.form()
    phone = str(form_data.get("From", "")).replace("whatsapp:", "")
    message = str(form_data.get("Body", ""))

    if not phone or not message:
        raise HTTPException(status_code=400, detail="Missing phone or message")

    response = process_message(phone, message)
    return PlainTextResponse(content=f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{response}</Message></Response>",
                              media_type="text/xml")

@router.post("/simulate")
async def simulate_message(data: dict):
    """Simulate a WhatsApp message (for demo/testing)"""
    phone = data.get("phone", "919999999999")
    message = data.get("message", "")
    response = process_message(phone, message)
    return {"response": response, "phone": phone}

@router.get("/verify")
async def verify_webhook(request: Request):
    """Webhook verification for Meta WhatsApp API"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN", "karigar_verify_123"):
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")
