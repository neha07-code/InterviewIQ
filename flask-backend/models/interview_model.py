from datetime import datetime


def create_interview(
    user_id,
    role,
    experience,
    mode,
    resume_text=None
):
    if mode not in ["HR", "Technical"]:
        raise ValueError("Mode must be HR or Technical")

    return {
        "userId": user_id,
        "role": role,
        "experience": experience,
        "mode": mode,
        "resumeText": resume_text,
        "questions": [],
        "finalScore": 0,
        "status": "Incompleted",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }


def create_question(
    question,
    difficulty,
    time_limit,
    answer=None,
    feedback=None,
    score=0,
    confidence=0,
    communication=0,
    correctness=0
):
    return {
        "question": question,
        "difficulty": difficulty,
        "timeLimit": time_limit,
        "answer": answer,
        "feedback": feedback,
        "score": score,
        "confidence": confidence,
        "communication": communication,
        "correctness": correctness
    }