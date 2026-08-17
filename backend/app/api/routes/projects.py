from fastapi import APIRouter

from app.agents.supervisor.workflow import run_blueprint_workflow
from app.schemas.blueprint import BlueprintRequest, EngineeringBlueprint

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/blueprint", response_model=EngineeringBlueprint)
async def generate_blueprint(request: BlueprintRequest) -> EngineeringBlueprint:
    return run_blueprint_workflow(request.idea)
