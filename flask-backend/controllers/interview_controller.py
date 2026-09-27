import os
import json
from flask import request, jsonify
from bson import ObjectId

from db import users_collection, interviews_collection
from services.openRouter_service import ask_ai


# =========================================================
# 1. ANALYZE RESUME
# =========================================================

def analyze_resume():
    filepath = None

    try:
        filepath = getattr(request, "uploaded_file", None)

        if not filepath:
            return jsonify({
                "message": "Resume required"
            }), 400

        # Read PDF
        import PyPDF2

        resume_text = ""

        with open(filepath, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                resume_text += page_text + "\n"

        # Clean text
        resume_text = " ".join(resume_text.split())

        messages = [
            {
                "role": "system",
                "content": """
Extract structured data from resumeText.

Return strictly JSON:

{
    "role": "string",
    "experience": "string",
    "projects": ["project1", "project2"],
    "skills": ["skill1", "skill2"]
}
"""
            },
            {
                "role": "user",
                "content": resume_text
            }
        ]

        # Ask AI
        ai_response = ask_ai(messages)

        if not ai_response:
            return jsonify({
                "message": "AI returned empty response"
            }), 500

        # Remove markdown JSON wrapper
        cleaned = (
            ai_response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        parsed = json.loads(cleaned)

        # Delete uploaded file
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({
            "role": parsed.get("role", ""),
            "experience": parsed.get("experience", ""),
            "projects": parsed.get("projects", []),
            "skills": parsed.get("skills", []),
            "resumeText": resume_text
        }), 200

    except Exception as error:

        print("Analyze Resume Error:", error)

        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({
            "message": str(error)
        }), 500


# =========================================================
# 2. GENERATE QUESTIONS
# =========================================================

def generate_question():

    try:
        data = request.get_json() or {}

        role = (data.get("role") or "").strip()
        experience = (data.get("experience") or "").strip()
        mode = (data.get("mode") or "").strip()

        resume_text = data.get("resumeText")
        projects = data.get("projects")
        skills = data.get("skills")

        if not role or not experience or not mode:
            return jsonify({
                "message": "Role, Experience and mode are required."
            }), 400

        # Get current user
        user_id = request.user_id

        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            return jsonify({
                "message": "Invalid user ID"
            }), 401

        user = users_collection.find_one({
            "_id": user_object_id
        })

        if not user:
            return jsonify({
                "message": "user not found."
            }), 404

        # Check credits
        credits = user.get("credits", 0)

        if credits < 50:
            return jsonify({
                "message": "Not enough credits. Minium 50 required."
            }), 404

        # Projects
        if isinstance(projects, list) and len(projects) > 0:
            project_text = ",".join(str(project) for project in projects)
        else:
            project_text = "None"

        # Skills
        if isinstance(skills, list) and len(skills) > 0:
            skills_text = ",".join(str(skill) for skill in skills)
        else:
            skills_text = "None"

        safe_resume = (resume_text or "").strip() or "None"

        # User prompt
        user_prompt = f"""
Role:{role}
Experience:{experience}
InterviewMode:{mode}
Projects:{project_text}
Skills:{skills_text}
Resume:{safe_resume}
"""

        if not user_prompt.strip():
            return jsonify({
                "message": "Prompt content is empty."
            }), 400

        # AI prompt
        messages = [
            {
                "role": "system",
                "content": """
You are a real human interviewer conducting a professional interview.

Speak in simple, natural English as if you are directly talking to the candidate.

Generate exactly 5 interview questions.

Strict Rules:
- Each question must contain between 15 and 25 words.
- Each question must be a single complete sentence.
- Do NOT number them.
- Do NOT add explanations.
- Do NOT add extra text before or after.
- One question per line only.
- Keep language simple and conversational.
- Questions must feel practical and realistic.

Difficulty progression:
Question 1 → easy
Question 2 → easy
Question 3 → medium
Question 4 → medium
Question 5 → hard

Make questions based on the candidate’s role, experience, interviewMode,
projects, skills, and resume details.
"""
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        ai_response = ask_ai(messages)

        if not ai_response or not ai_response.strip():
            print("AI returned empty response.")

            return jsonify({
                "message": "AI returned empty response."
            }), 500

        # Convert AI response to list
        questions_array = [
            q.strip()
            for q in ai_response.split("\n")
            if q.strip()
        ][:5]

        if len(questions_array) == 0:
            print("AI failed to generate questions")

            return jsonify({
                "message": "AI failed to generate questions"
            }), 500

        # Deduct credits
        new_credits = credits - 50

        users_collection.update_one(
            {"_id": user_object_id},
            {
                "$set": {
                    "credits": new_credits
                }
            }
        )

        # Create questions
        difficulties = [
            "easy",
            "easy",
            "medium",
            "medium",
            "hard"
        ]

        time_limits = [
            60,
            60,
            90,
            120,
            120
        ]

        questions = []

        for index, question in enumerate(questions_array):

            questions.append({
                "question": question,
                "difficulty": difficulties[index],
                "timeLimit": time_limits[index],
                "answer": None,
                "feedback": None,
                "score": 0,
                "confidence": 0,
                "communication": 0,
                "correctness": 0
            })

        # Create interview document
        interview_document = {
            "userId": user_object_id,
            "role": role,
            "experience": experience,
            "mode": mode,
            "resumeText": safe_resume,
            "questions": questions,
            "finalScore": 0,
            "status": "Incompleted"
        }

        result = interviews_collection.insert_one(
            interview_document
        )

        interview_id = result.inserted_id

        print("Interview Created:", interview_id)

        return jsonify({
            "interviewId": str(interview_id),
            "creditsLeft": new_credits,
            "userName": user.get("name", ""),
            "questions": [
                {
                    **question,
                    "_id": None
                }
                for question in questions
            ]
        }), 200

    except Exception as error:

        print("Generate Question Error:", error)

        return jsonify({
            "message": f"failed to create interview {error}"
        }), 500


# =========================================================
# 3. SUBMIT ANSWER
# =========================================================

def submit_answer():

    try:
        data = request.get_json() or {}

        interview_id = data.get("interviewId")
        question_index = data.get("questionIndex")
        answer = data.get("answer")
        time_taken = data.get("timeTaken", 0)

        if not interview_id or question_index is None:
            return jsonify({
                "message": "Interview ID and question index are required."
            }), 400

        try:
            interview_object_id = ObjectId(interview_id)
        except Exception:
            return jsonify({
                "message": "Invalid interview ID"
            }), 400

        interview = interviews_collection.find_one({
            "_id": interview_object_id
        })

        if not interview:
            return jsonify({
                "message": "Interview not found"
            }), 404

        questions = interview.get("questions", [])

        if question_index < 0 or question_index >= len(questions):
            return jsonify({
                "message": "Invalid question index"
            }), 400

        question = questions[question_index]

        # ============================================
        # No answer
        # ============================================

        if not answer:

            question["score"] = 0
            question["feedback"] = "You did not submit an answer."
            question["answer"] = ""

            interviews_collection.update_one(
                {"_id": interview_object_id},
                {
                    "$set": {
                        f"questions.{question_index}": question
                    }
                }
            )

            return jsonify({
                "feedback": question["feedback"]
            }), 200

        # ============================================
        # Time exceeded
        # ============================================

        if time_taken > question.get("timeLimit", 0):

            question["score"] = 0
            question["feedback"] = "Time limit exceeded."
            question["answer"] = answer

            interviews_collection.update_one(
                {"_id": interview_object_id},
                {
                    "$set": {
                        f"questions.{question_index}": question
                    }
                }
            )

            return jsonify({
                "feedback": question["feedback"]
            }), 200

        # ============================================
        # AI Evaluation
        # ============================================

        messages = [
            {
                "role": "system",
                "content": """
You are a professional human interviewer evaluating a candidate's answer in a real interview.

Evaluate naturally and fairly, like a real person would.

Score the answer in these areas (0 to 10):

1. Confidence – Does the answer sound clear, confident, and well-presented?
2. Communication – Is the language simple, clear, and easy to understand?
3. Correctness – Is the answer accurate, relevant, and complete?

Rules:
- Be realistic and unbiased.
- Do not give random high scores.
- If the answer is weak, score low.
- If the answer is strong and detailed, score high.
- Consider clarity, structure, and relevance.

Calculate:
finalScore = average of confidence, communication, and correctness
rounded to nearest whole number.

Feedback Rules:
- Write natural human feedback.
- 10 to 15 words only.
- Sound like real interview feedback.
- Can suggest improvement if needed.
- Do NOT repeat the question.
- Do NOT explain scoring.
- Keep tone professional and honest.

Return ONLY valid JSON in this format:

{
    "confidence": number,
    "communication": number,
    "correctness": number,
    "finalScore": number,
    "feedback": "short human feedback"
}
"""
            },
            {
                "role": "user",
                "content": f"""
Question: {question.get("question")}

Answer: {answer}
"""
            }
        ]

        ai_response = ask_ai(messages)

        cleaned = (
            ai_response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        parsed = json.loads(cleaned)

        # Update question
        question["answer"] = answer
        question["confidence"] = parsed.get("confidence", 0)
        question["communication"] = parsed.get("communication", 0)
        question["correctness"] = parsed.get("correctness", 0)
        question["score"] = parsed.get("finalScore", 0)
        question["feedback"] = parsed.get("feedback", "")

        interviews_collection.update_one(
            {"_id": interview_object_id},
            {
                "$set": {
                    f"questions.{question_index}": question
                }
            }
        )

        return jsonify({
            "feedback": parsed.get("feedback", "")
        }), 200

    except Exception as error:

        print("Submit Answer Error:", error)

        return jsonify({
            "message": f"failed to submit answer {error}"
        }), 500


# =========================================================
# 4. FINISH INTERVIEW
# =========================================================

def finish_interview():

    try:
        data = request.get_json() or {}

        interview_id = data.get("interviewId")

        if not interview_id:
            return jsonify({
                "message": "Interview ID is required"
            }), 400

        try:
            interview_object_id = ObjectId(interview_id)
        except Exception:
            return jsonify({
                "message": "Invalid interview ID"
            }), 400

        interview = interviews_collection.find_one({
            "_id": interview_object_id
        })

        if not interview:
            return jsonify({
                "message": "failed to find Interview"
            }), 400

        questions = interview.get("questions", [])

        total_questions = len(questions)

        total_score = 0
        total_confidence = 0
        total_communication = 0
        total_correctness = 0

        for question in questions:

            total_score += question.get("score") or 0
            total_confidence += question.get("confidence") or 0
            total_communication += question.get("communication") or 0
            total_correctness += question.get("correctness") or 0

        if total_questions:
            final_score = total_score / total_questions
            avg_confidence = total_confidence / total_questions
            avg_communication = total_communication / total_questions
            avg_correctness = total_correctness / total_questions
        else:
            final_score = 0
            avg_confidence = 0
            avg_communication = 0
            avg_correctness = 0

        # Update interview
        interviews_collection.update_one(
            {"_id": interview_object_id},
            {
                "$set": {
                    "finalScore": final_score,
                    "status": "completed"
                }
            }
        )

        question_wise_score = []

        for question in questions:

            question_wise_score.append({
                "question": question.get("question"),
                "score": question.get("score") or 0,
                "feedback": question.get("feedback") or 0,
                "confidence": question.get("confidence") or 0,
                "communication": question.get("communication") or 0,
                "correctness": question.get("correctness") or 0
            })

        return jsonify({
            "finalScore": round(final_score, 1),
            "confidence": round(avg_confidence, 1),
            "communication": round(avg_communication, 1),
            "correctness": round(avg_correctness, 1),
            "questionWiseScore": question_wise_score
        }), 200

    except Exception as error:

        print("Finish Interview Error:", error)

        return jsonify({
            "message": f"failed to finish interview {error}"
        }), 500


# =========================================================
# 5. GET MY INTERVIEWS
# =========================================================

def get_my_interviews():

    try:
        user_id = request.user_id

        try:
            user_object_id = ObjectId(user_id)
        except Exception:
            return jsonify({
                "message": "Invalid user ID"
            }), 401

        interviews = list(
            interviews_collection.find(
                {
                    "userId": user_object_id
                },
                {
                    "role": 1,
                    "experience": 1,
                    "mode": 1,
                    "finalScore": 1,
                    "status": 1,
                    "createdAt": 1
                }
            ).sort(
                "createdAt",
                -1
            )
        )

        # Convert ObjectId and datetime
        for interview in interviews:

            interview["_id"] = str(interview["_id"])

            if interview.get("createdAt"):
                interview["createdAt"] = interview[
                    "createdAt"
                ].isoformat()

        return jsonify(interviews), 200

    except Exception as error:

        print("Get My Interviews Error:", error)

        return jsonify({
            "message": f"failed to find currentUser Interview {error}"
        }), 500


# =========================================================
# 6. GET INTERVIEW REPORT
# =========================================================

def get_interview_report(interview_id):

    try:

        try:
            interview_object_id = ObjectId(interview_id)
        except Exception:
            return jsonify({
                "message": "Invalid interview ID"
            }), 400

        interview = interviews_collection.find_one({
            "_id": interview_object_id
        })

        if not interview:
            return jsonify({
                "message": "Interview not found"
            }), 404

        questions = interview.get("questions", [])

        total_questions = len(questions)

        total_score = 0
        total_confidence = 0
        total_communication = 0
        total_correctness = 0

        for question in questions:

            total_score += question.get("score") or 0
            total_confidence += question.get("confidence") or 0
            total_communication += question.get("communication") or 0
            total_correctness += question.get("correctness") or 0

        if total_questions:

            final_score = total_score / total_questions
            avg_confidence = total_confidence / total_questions
            avg_communication = total_communication / total_questions
            avg_correctness = total_correctness / total_questions

        else:

            final_score = 0
            avg_confidence = 0
            avg_communication = 0
            avg_correctness = 0

        return jsonify({
            "finalScore": interview.get("finalScore", 0),
            "confidence": round(avg_confidence, 1),
            "communication": round(avg_communication, 1),
            "correctness": round(avg_correctness, 1),
            "questionWiseScore": questions
        }), 200

    except Exception as error:

        print("Get Interview Report Error:", error)

        return jsonify({
            "message": f"failed to find currentUser Interview {error}"
        }), 500