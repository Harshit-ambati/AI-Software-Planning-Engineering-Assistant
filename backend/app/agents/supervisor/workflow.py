from uuid import uuid4

from app.agents.api_design.agent import design_api
from app.agents.architecture.agent import design_architecture
from app.agents.database_design.agent import design_database
from app.agents.documentation.agent import plan_implementation, write_documentation
from app.agents.requirement.agent import analyze_requirements
from app.agents.validation.agent import validate_blueprint
from app.schemas.blueprint import EngineeringBlueprint


def run_blueprint_workflow(idea: str) -> EngineeringBlueprint:
    requirements = analyze_requirements(idea)
    architecture = design_architecture(requirements)
    database = design_database(requirements)
    api = design_api(requirements, database)
    implementation = plan_implementation(requirements, architecture, database, api)
    documentation = write_documentation(idea, requirements, architecture, database, api)
    validation = validate_blueprint(requirements, architecture, database, api)

    return EngineeringBlueprint(
        project_id=str(uuid4()),
        idea=idea.strip(),
        requirements=requirements,
        architecture=architecture,
        database=database,
        api=api,
        implementation=implementation,
        documentation=documentation,
        validation=validation,
    )
