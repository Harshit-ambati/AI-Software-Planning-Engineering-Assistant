from app.schemas.blueprint import EngineeringBlueprint, ProjectSummary


class ProjectStore:
    def __init__(self) -> None:
        self._blueprints: dict[str, EngineeringBlueprint] = {}

    def save(self, blueprint: EngineeringBlueprint) -> EngineeringBlueprint:
        self._blueprints[blueprint.project_id] = blueprint
        return blueprint

    def list_projects(self) -> list[ProjectSummary]:
        projects = [
            ProjectSummary(
                project_id=blueprint.project_id,
                idea=blueprint.idea,
                status="complete",
                validation_status=blueprint.validation.status,
                created_at=blueprint.created_at,
            )
            for blueprint in self._blueprints.values()
        ]
        return sorted(projects, key=lambda project: project.created_at, reverse=True)

    def get(self, project_id: str) -> EngineeringBlueprint | None:
        return self._blueprints.get(project_id)


project_store = ProjectStore()
