from fastapi import APIRouter, Depends, status
from app.db import AsyncSession, get_db
from app.models.admin import AdminDetails
from app.models.group import GroupCreate, GroupModify, GroupResponse, GroupsResponse
from .authentication import check_sudo_admin, get_current
from app.utils import responses
from app.operation.group import GroupOperation
from app.operation import OperatorType


router = APIRouter(prefix="/api/group", tags=["Groups"], responses={401: responses._401, 403: responses._403})
group_operator = GroupOperation(OperatorType.API)


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new group",
    description="Creates a new group in the system. Only sudo administrators can create groups.",
)
async def add_group(
    new_group: GroupCreate, db: AsyncSession = Depends(get_db), admin: AdminDetails = Depends(check_sudo_admin)
):
    """
    Create a new group in the system.

    The group model has the following properties:
    - **name**: String (3-64 chars) containing only a-z and 0-9
    - **inbound_tags**: List of inbound tags that this group can access
    - **is_disabled**: Boolean flag to disable/enable the group

    Returns:
        GroupResponse: The created group data with additional fields:
            - **id**: Unique identifier for the group
            - **total_users**: Number of users in this group

    Raises:
        401: Unauthorized - If not authenticated
        403: Forbidden - If not sudo admin
    """
    return await group_operator.add_group(db, new_group, admin)


@router.get(
    "s",
    response_model=GroupsResponse,
    summary="List all groups",
    description="Retrieves a paginated list of all groups in the system. Requires admin authentication.",
)
async def get_all_groups(
    offset: int = None, limit: int = None, db: AsyncSession = Depends(get_db), _: AdminDetails = Depends(get_current)
):
    """
    Retrieve a list of all groups with optional pagination.

    The response includes:
    - **groups**: List of GroupResponse objects containing:
        - **id**: Unique identifier
        - **name**: Group name
        - **inbound_tags**: List of allowed inbound tags
        - **is_disabled**: Group status
        - **total_users**: Number of users in group
    - **total**: Total count of groups

    Returns:
        GroupsResponse: List of groups and total count

    Raises:
        401: Unauthorized - If not authenticated
    """
    return await group_operator.get_all_groups(db, offset, limit)


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    summary="Get group details",
    description="Retrieves detailed information about a specific group by its ID.",
    responses={404: responses._404},
)
async def get_group(group_id: int, db: AsyncSession = Depends(get_db), _: AdminDetails = Depends(get_current)):
    """
    Get a specific group by its **ID**.

    The response includes:
    - **id**: Unique identifier
    - **name**: Group name (3-64 chars, a-z, 0-9)
    - **inbound_tags**: List of allowed inbound tags
    - **is_disabled**: Group status
    - **total_users**: Number of users in group

    Returns:
        GroupResponse: The requested group data

    Raises:
        404: Not Found - If group doesn't exist
    """
    return await group_operator.get_validated_group(db, group_id)


@router.put(
    "/{group_id}",
    response_model=GroupResponse,
    summary="Update group",
    description="Updates an existing group's information. Only sudo administrators can modify groups.",
    responses={404: responses._404},
)
async def modify_group(
    group_id: int,
    modified_group: GroupModify,
    db: AsyncSession = Depends(get_db),
    admin: AdminDetails = Depends(check_sudo_admin),
):
    """
    Update an existing group's information.

    The group model can be modified with:
    - **name**: String (3-64 chars) containing only a-z and 0-9
    - **inbound_tags**: List of inbound tags that this group can access
    - **is_disabled**: Boolean flag to disable/enable the group

    Returns:
        GroupResponse: The updated group data with additional fields:
            - **id**: Unique identifier for the group
            - **total_users**: Number of users in this group

    Raises:
        401: Unauthorized - If not authenticated
        403: Forbidden - If not sudo admin
        404: Not Found - If group doesn't exist
    """
    return await group_operator.modify_group(db, group_id, modified_group, admin)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete group",
    description="Deletes a group from the system. Only sudo administrators can delete groups.",
    responses={404: responses._404},
)
async def delete_group(
    group_id: int, db: AsyncSession = Depends(get_db), admin: AdminDetails = Depends(check_sudo_admin)
):
    """
    Delete a group by its **ID**.

    Returns:
        dict: Empty dictionary on successful deletion

    Raises:
        401: Unauthorized - If not authenticated
        403: Forbidden - If not sudo admin
        404: Not Found - If group doesn't exist
    """
    await group_operator.delete_group(db, group_id, admin)
    return {}
