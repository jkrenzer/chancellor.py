"""A consumer-supplied root model for the tests (0.1.0:D0030)."""

from pydantic import BaseModel, ConfigDict

from chancellor.builtin.jkrenzer import models


class DecisionSection(BaseModel):
    core: models.DecisionCore
    records: list[models.Decision] = []


class RequirementSection(BaseModel):
    core: models.RequirementCore
    records: list[models.Requirement] = []


class SpecificationSection(BaseModel):
    core: models.SpecificationCore
    records: list[models.Specification] = []


class Catalogue(BaseModel):
    """Exposes its sections through `chancellor_sections`, as the protocol describes."""

    model_config = ConfigDict(extra="forbid")

    decisions: DecisionSection
    requirements: RequirementSection
    specifications: SpecificationSection

    def chancellor_sections(self):
        return {
            name: (section.core, section.records)
            for name, section in (
                ("decisions", self.decisions),
                ("requirements", self.requirements),
                ("specifications", self.specifications),
            )
        }
