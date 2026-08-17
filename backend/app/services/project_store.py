from app.schemas.blueprint import EngineeringBlueprint, ProjectSummary
from app.database.mongodb import get_database_or_none


class ProjectStore:
    def __init__(self) -> None:
        self._blueprints: dict[str, EngineeringBlueprint] = {}

    async def save(self, blueprint: EngineeringBlueprint) -> EngineeringBlueprint:
        self._blueprints[blueprint.project_id] = blueprint
        database = get_database_or_none()
        if database is not None:
            await database.projects.replace_one(
                {"project_id": blueprint.project_id},
                blueprint.model_dump(mode="json"),
                upsert=True,
            )
        return blueprint

    async def list_projects(self) -> list[ProjectSummary]:
        database = get_database_or_none()
        if database is not None:
            cursor = database.projects.find({}, {"_id": 0}).sort("created_at", -1)
            blueprints = [EngineeringBlueprint.model_validate(document) async for document in cursor]
            return [self._to_summary(blueprint) for blueprint in blueprints]

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

    async def get(self, project_id: str) -> EngineeringBlueprint | None:
        database = get_database_or_none()
        if database is not None:
            document = await database.projects.find_one({"project_id": project_id}, {"_id": 0})
            if document is not None:
                return EngineeringBlueprint.model_validate(document)

        return self._blueprints.get(project_id)

    def _to_summary(self, blueprint: EngineeringBlueprint) -> ProjectSummary:
        return ProjectSummary(
            project_id=blueprint.project_id,
            idea=blueprint.idea,
            status="complete",
            validation_status=blueprint.validation.status,
            created_at=blueprint.created_at,
        )


project_store = ProjectStore()
