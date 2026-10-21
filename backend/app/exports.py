import json
import re


def json_schema(fields):
    properties = {}
    for field in fields:
        prop = {"type": field["type"], "description": field["description"]}
        if field["type"] == "array":
            prop["items"] = {}
        properties[field["name"]] = prop
    return dict(type="object", properties=properties, required=[f["name"] for f in fields if f["required"]])


def openapi(project, run):
    spec = dict(
        openapi="3.1.0",
        info={
            "title": project["name"],
            "version": str(run["version"]),
            "description": "Generated design proposal. Validate and implement before use.",
        },
        paths={},
        components={
            "securitySchemes": {
                "designAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": run["artifacts"]["apis"]["authentication"]
                    + " Mechanism is illustrative; reconcile with the chosen implementation.",
                }
            }
        },
    )
    for endpoint in run["artifacts"]["apis"]["endpoints"]:
        responses = {
            str(endpoint["success_status"]): {
                "description": "Success",
                "content": {"application/json": {"schema": json_schema(endpoint["response_fields"])}},
            }
        }
        responses["default"] = {"description": "; ".join(endpoint["errors"]) or "Unexpected error"}
        operation = dict(
            operationId=endpoint["id"],
            summary=endpoint["summary"],
            responses=responses,
            security=[{"designAuth": []}] if endpoint["authenticated"] else [],
            **{"x-requirement-ids": endpoint["requirement_ids"]},
        )
        params = re.findall(r"\{([^}]+)\}", endpoint["path"])
        if params:
            operation["parameters"] = [
                dict(name=p, **{"in": "path"}, required=True, schema={"type": "string"}) for p in params
            ]
        if endpoint["request_fields"]:
            operation["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": json_schema(endpoint["request_fields"])}},
            }
        spec["paths"].setdefault(endpoint["path"], {})[endpoint["method"].lower()] = operation
    return spec


def markdown(project, run):
    lines = [
        f"# {project['name']}",
        f"Revision {run['version']} · {run['provider']} / {run['model']}",
        "> Engineering design proposal. Generated plans require human review.",
        "## Brief",
        run["brief"],
    ]

    def render(value, depth=0):
        if isinstance(value, dict):
            for key, content in value.items():
                lines.append("  " * depth + "- **" + key.replace("_", " ").title() + "**")
                render(content, depth + 1)
        elif isinstance(value, list):
            for content in value:
                if isinstance(content, (dict, list)):
                    render(content, depth)
                else:
                    lines.append("  " * depth + "- " + str(content))
        else:
            lines.append("  " * depth + str(value))

    for stage, content in run["artifacts"].items():
        lines.append("\n## " + stage.replace("_", " ").title())
        render(content)
    return "\n\n".join(lines)


def compare(before, after):
    changes = []

    def walk(left, right, path):
        if left == right:
            return
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(left.keys() | right.keys()):
                walk(left.get(key), right.get(key), f"{path}/{key}")
        else:
            changes.append({"path": path, "before": left, "after": right})

    walk(before["artifacts"], after["artifacts"], "")
    return dict(
        before_version=before["version"],
        after_version=after["version"],
        changes=changes,
        brief_changed=before["brief"] != after["brief"],
    )


def json_export(project, run):
    return json.dumps(dict(project=project["name"], run=run), indent=2, ensure_ascii=False)
