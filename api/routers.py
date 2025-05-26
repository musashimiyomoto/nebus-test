from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db_session, validate_api_key
from api.schemas import Organization, OrganizationDetail, RadiusQuery, RectangleQuery
from db.queries import (
    get_organization_detail,
    get_organizations_by_activity_id,
    get_organizations_by_building_id,
    get_organizations_by_name,
    get_organizations_by_radius,
    get_organizations_by_rectangle,
)

router = APIRouter(prefix="/organizations", dependencies=[Depends(validate_api_key)])


@router.get(
    path="/",
    description="Get organizations with optional name filter",
)
async def get_organizations(
    skip: int = 0,
    limit: int = 100,
    name: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    """Get organizations with optional name filter

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        name: Optional name to filter organizations
        session: Database session

    Returns:
        List of organizations

    """
    return map(
        Organization.model_validate,
        await get_organizations_by_name(
            session=session,
            name=name,
            skip=skip,
            limit=limit,
        ),
    )


@router.get(
    path="/building/{building_id}",
    description="Get organizations in a specific building",
)
async def get_organizations_by_building(
    building_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    """Get organizations in a specific building

    Args:
        building_id: ID of the building to filter by
        session: Database session

    Returns:
        List of organizations in the building

    """
    return map(
        Organization.model_validate,
        await get_organizations_by_building_id(
            session=session,
            building_id=building_id,
            skip=skip,
            limit=limit,
        ),
    )


@router.get(
    path="/activity/{activity_id}",
    description="Get organizations with a specific activity",
)
async def get_organizations_by_activity(
    activity_id: int,
    skip: int = 0,
    limit: int = 100,
    include_children: bool = True,
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    """Get organizations with a specific activity

    Args:
        activity_id: ID of the activity to filter by
        include_children: Whether to include child activities
        session: Database session

    Returns:
        List of organizations with the activity

    """
    return map(
        Organization.model_validate,
        await get_organizations_by_activity_id(
            session=session,
            activity_id=activity_id,
            include_children=include_children,
            skip=skip,
            limit=limit,
        ),
    )


@router.post(
    path="/search/radius",
    description="Search organizations within a radius from a center point",
)
async def search_organizations_by_radius(
    query: RadiusQuery,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    """Search organizations within a radius from a center point

    Args:
        query: Radius search parameters
        session: Database session

    Returns:
        List of organizations within the radius

    """
    return map(
        Organization.model_validate,
        await get_organizations_by_radius(
            session=session,
            center_latitude=query.center.latitude,
            center_longitude=query.center.longitude,
            radius=query.radius,
            skip=skip,
            limit=limit,
        ),
    )


@router.post(
    path="/search/rectangle",
    description="Search organizations within a rectangular area",
)
async def search_organizations_by_rectangle(
    query: RectangleQuery,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    """Search organizations within a rectangular area

    Args:
        query: Rectangle search parameters
        session: Database session

    Returns:
        List of organizations within the rectangle

    """
    return map(
        Organization.model_validate,
        await get_organizations_by_rectangle(
            session=session,
            min_latitude=query.min_latitude,
            max_latitude=query.max_latitude,
            min_longitude=query.min_longitude,
            max_longitude=query.max_longitude,
            skip=skip,
            limit=limit,
        ),
    )


@router.get(
    path="/{organization_id}",
    description="Get detailed information about a specific organization",
)
async def get_organization(
    organization_id: int, session: AsyncSession = Depends(get_db_session)
) -> OrganizationDetail:
    """Get detailed information about a specific organization

    Args:
        organization_id: ID of the organization to retrieve
        session: Database session

    Returns:
        Detailed organization information

    Raises:
        HTTPException: If organization not found

    """
    organization = await get_organization_detail(
        session=session, organization_id=organization_id
    )
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return OrganizationDetail(
        id=organization.id,
        name=organization.name,
        building_id=organization.building_id,
        building=organization.building,
        phone_numbers=organization.phone_numbers,
        activities=[activity.activity for activity in organization.activities],
    )
