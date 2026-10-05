from pydantic import BaseModel, Field


class Scores(BaseModel):
    content: int = Field(ge=0, le=10)
    style: int = Field(ge=0, le=10)
    strategy: int = Field(ge=0, le=10)


class Quote(BaseModel):
    from_student: str
    comment: str


class Feedback(BaseModel):
    scores: Scores
    overall_comment: str
    strengths: list[str]
    weaknesses: list[str]
    quotes: list[Quote]
    next_drill: str



# feedback = Feedback.model_validate(data)
# print(feedback.scores.content)