from pydantic import BaseModel, Field, field_validator


class Scores(BaseModel):
    content: int = Field(ge=1, le=10)
    style: int = Field(ge=1, le=10)
    strategy: int = Field(ge=1, le=10)
    @field_validator("content", "style", "strategy", mode="before")
    @classmethod
    def _round(cls, v):
        return round(v) if isinstance(v, float) else v


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