from sqlalchemy import select

from app.extensions import db
from app.models.issue import Issue
from app.services.organization_service import OrganizationError
from app.services.project_service import get_project


STATUSES = ("backlog", "todo", "in_progress", "done")
PRIORITIES = ("low", "medium", "high", "urgent")

EDITABLE_FIELDS = {"title", "description", "status", "priority"}


def validate_issue_payload(
    payload: dict,
    *,
    partial: bool = False,
) -> dict:
    unknown_fields = set(payload) - EDITABLE_FIELDS

    if unknown_fields:
        raise OrganizationError(
            "Unknown fields: " + ", ".join(sorted(unknown_fields)),
            "VALIDATION_ERROR",
            400,
        )

    if partial and not payload:
        raise OrganizationError(
            "Provide at least one field to update.",
            "VALIDATION_ERROR",
            400,
        )

    values = {}

    if not partial or "title" in payload:
        title = payload.get("title")

        if not isinstance(title, str) or not title.strip():
            raise OrganizationError(
                "title is required and must be a non-empty string.",
                "VALIDATION_ERROR",
                400,
            )

        title = title.strip()

        if len(title) > 200:
            raise OrganizationError(
                "title must be 200 characters or fewer.",
                "VALIDATION_ERROR",
                400,
            )

        values["title"] = title

    if not partial or "description" in payload:
        description = payload.get("description", "")

        if not isinstance(description, str):
            raise OrganizationError(
                "description must be a string.",
                "VALIDATION_ERROR",
                400,
            )

        description = description.strip()

        if len(description) > 10000:
            raise OrganizationError(
                "description must be 10000 characters or fewer.",
                "VALIDATION_ERROR",
                400,
            )

        values["description"] = description

    for field, allowed, default in (
        ("status", STATUSES, "backlog"),
        ("priority", PRIORITIES, "medium"),
    ):
        if partial and field not in payload:
            continue

        value = payload.get(field, default)

        if not isinstance(value, str) or value not in allowed:
            raise OrganizationError(
                f"{field} must be one of: {', '.join(allowed)}.",
                "VALIDATION_ERROR",
                400,
            )

        values[field] = value

    return values


def save_issue(issue: Issue) -> Issue:
    try:
        db.session.add(issue)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return issue


def list_issues(
    actor_id: int,
    organization_id: int,
    project_id: int,
):
    get_project(actor_id, organization_id, project_id)

    statement = (
        select(Issue)
        .where(Issue.project_id == project_id)
        .order_by(Issue.id.desc())
    )

    return list(db.session.scalars(statement))


def create_issue(
    actor_id: int,
    organization_id: int,
    project_id: int,
    payload: dict,
) -> Issue:
    get_project(actor_id, organization_id, project_id)

    values = validate_issue_payload(payload)

    issue = Issue(
        project_id=project_id,
        **values,
    )

    return save_issue(issue)


def get_issue(
    actor_id: int,
    organization_id: int,
    project_id: int,
    issue_id: int,
) -> Issue:
    get_project(actor_id, organization_id, project_id)

    statement = select(Issue).where(
        Issue.id == issue_id,
        Issue.project_id == project_id,
    )

    issue = db.session.scalar(statement)

    if issue is None:
        raise OrganizationError(
            "Issue not found.",
            "NOT_FOUND",
            404,
        )

    return issue


def update_issue(
    actor_id: int,
    organization_id: int,
    project_id: int,
    issue_id: int,
    payload: dict,
) -> Issue:
    issue = get_issue(
        actor_id,
        organization_id,
        project_id,
        issue_id,
    )

    values = validate_issue_payload(payload, partial=True)

    for field, value in values.items():
        setattr(issue, field, value)

    return save_issue(issue)