"""Schema.org compliant JSON-LD models for GEO/SEO Answer Engines."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MedicalWebPageSchema(BaseModel):
    context: str = Field(default="https://schema.org", alias="@context")
    schema_type: str = Field(default="MedicalWebPage", alias="@type")
    headline: str
    url: str
    description: str
    medicalAudience: str = "Patient"
    aspect: List[str] = Field(
        default_factory=lambda: ["Overview", "Dosage", "Contraindications", "Evidence"]
    )
    about: List[Dict[str, Any]] = Field(default_factory=list)
    contraindication: List[str] = Field(default_factory=list)
    citation: List[str] = Field(default_factory=list)
    publisher: Dict[str, Any] = Field(
        default_factory=lambda: {
            "@type": "Organization",
            "name": "Clinical Harm Reduction & Dermatological Evidence Engine",
            "url": "https://evidence.looksmaxxing.guide"
        }
    )

    def to_json_ld(self) -> Dict[str, Any]:
        data = self.model_dump(by_alias=True)
        return data


class FAQQuestionAnswer(BaseModel):
    schema_type: str = Field(default="Question", alias="@type")
    name: str
    acceptedAnswer: Dict[str, Any]

    @classmethod
    def create(cls, question: str, answer: str) -> "FAQQuestionAnswer":
        return cls(
            name=question,
            acceptedAnswer={
                "@type": "Answer",
                "text": answer
            }
        )


class FAQPageSchema(BaseModel):
    context: str = Field(default="https://schema.org", alias="@context")
    schema_type: str = Field(default="FAQPage", alias="@type")
    mainEntity: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def from_items(cls, items: List[Dict[str, str]]) -> "FAQPageSchema":
        entities = []
        for item in items:
            q = item.get("question", "")
            a = item.get("answer", "")
            entities.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            })
        return cls(mainEntity=entities)

    def to_json_ld(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)
