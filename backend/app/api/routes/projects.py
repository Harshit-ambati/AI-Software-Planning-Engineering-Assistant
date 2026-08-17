from fastapi import APIRouter, HTTPException

from app.agents.supervisor.workflow import run_blueprint_workflow
from app.schemas.blueprint import BlueprintRequest, EngineeringBlueprint, ProjectListResponse
from app.services.project_store import project_store

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects() -> ProjectListResponse:
    return ProjectListResponse(projects=await project_store.list_projects())


@router.post("/blueprint", response_model=EngineeringBlueprint)
async def generate_blueprint(request: BlueprintRequest) -> EngineeringBlueprint:
    blueprint = run_blueprint_workflow(request.idea)
    return await project_store.save(blueprint)


@router.get("/{project_id}", response_model=EngineeringBlueprint)
async def get_project(project_id: str) -> EngineeringBlueprint:
    blueprint = await project_store.get(project_id)
    if blueprint is None:
        raise HTTPException(status_code=404, detail="Project blueprint not found.")
    return blueprint
