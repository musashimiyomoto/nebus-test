from fastapi import APIRouter, Depends, HTTPException, status
from geopy.distance import geodesic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import get_db_session, validate_api_key
from api.schemas import Organization, OrganizationDetail, RadiusQuery, RectangleQuery
from db import models

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
    query = select(models.Organization)

    if name:
        query = query.where(models.Organization.name.ilike(f"%{name}%"))

    result = await session.execute(query.offset(skip).limit(limit))

    return map(Organization.model_validate, result.scalars().all())


@router.get(
    path="/building/{building_id}",
    description="Get organizations in a specific building",
)
async def get_organizations_by_building(
    building_id: int, session: AsyncSession = Depends(get_db_session)
) -> list[Organization]:
    """Get organizations in a specific building

    Args:
        building_id: ID of the building to filter by
        session: Database session

    Returns:
        List of organizations in the building

    """
    result = await session.execute(
        statement=select(models.Organization).where(
            models.Organization.building_id == building_id
        )
    )
    return map(Organization.model_validate, result.scalars().all())


@router.get(
    path="/activity/{activity_id}",
    description="Get organizations with a specific activity",
)
async def get_organizations_by_activity(
    activity_id: int,
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
    if include_children:
        activity_ids = [activity_id]

        activity_result = await session.execute(
            select(models.Activity).where(models.Activity.id == activity_id)
        )
        activity = activity_result.scalar_one_or_none()

        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
            )

        if activity.level < 3:
            children_result = await session.execute(
                select(models.Activity).where(models.Activity.parent_id == activity_id)
            )
            children = children_result.scalars().all()
            activity_ids.extend([child.id for child in children])

            if activity.level == 1:
                for child in children:
                    grandchildren_result = await session.execute(
                        select(models.Activity).where(
                            models.Activity.parent_id == child.id
                        )
                    )

                    activity_ids.extend(
                        [
                            grandchild.id
                            for grandchild in grandchildren_result.scalars().all()
                        ]
                    )

        query = (
            select(models.Organization)
            .join(
                models.OrganizationActivity,
                models.Organization.id == models.OrganizationActivity.organization_id,
            )
            .where(models.OrganizationActivity.activity_id.in_(activity_ids))
            .distinct()
        )
    else:
        query = (
            select(models.Organization)
            .join(
                models.OrganizationActivity,
                models.Organization.id == models.OrganizationActivity.organization_id,
            )
            .where(models.OrganizationActivity.activity_id == activity_id)
        )

    result = await session.execute(query)

    return map(Organization.model_validate, result.scalars().all())


@router.post(
    path="/search/radius",
    description="Search organizations within a radius from a center point",
)
async def search_organizations_by_radius(
    query: RadiusQuery, session: AsyncSession = Depends(get_db_session)
) -> list[Organization]:
    """Search organizations within a radius from a center point

    Args:
        query: Radius search parameters
        session: Database session

    Returns:
        List of organizations within the radius

    """
    buildings_result = await session.execute(select(models.Building))

    building_ids = []
    for building in buildings_result.scalars().all():
        distance = geodesic(
            (query.center.latitude, query.center.longitude),
            (building.latitude, building.longitude),
        ).kilometers

        if distance <= query.radius:
            building_ids.append(building.id)

    if not building_ids:
        return []

    result = await session.execute(
        select(models.Organization).where(
            models.Organization.building_id.in_(building_ids)
        )
    )

    return map(Organization.model_validate, result.scalars().all())


@router.post(
    path="/search/rectangle",
    description="Search organizations within a rectangular area",
)
async def search_organizations_by_rectangle(
    query: RectangleQuery, session: AsyncSession = Depends(get_db_session)
) -> list[Organization]:
    """Search organizations within a rectangular area

    Args:
        query: Rectangle search parameters
        session: Database session

    Returns:
        List of organizations within the rectangle

    """
    buildings_result = await session.execute(
        select(models.Building.id).where(
            (models.Building.latitude >= query.min_latitude)
            & (models.Building.latitude <= query.max_latitude)
            & (models.Building.longitude >= query.min_longitude)
            & (models.Building.longitude <= query.max_longitude)
        )
    )
    building_ids = buildings_result.scalars().all()

    if not building_ids:
        return []

    result = await session.execute(
        select(models.Organization).where(
            models.Organization.building_id.in_(building_ids)
        )
    )

    return map(Organization.model_validate, result.scalars().all())


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
    result = await session.execute(
        (
            select(models.Organization)
            .options(
                selectinload(models.Organization.building),
                selectinload(models.Organization.phone_numbers),
                selectinload(models.Organization.activities).selectinload(
                    models.OrganizationActivity.activity
                ),
            )
            .where(models.Organization.id == organization_id)
        )
    )
    result = result.scalar_one_or_none()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return OrganizationDetail(
        id=result.id,
        name=result.name,
        building_id=result.building_id,
        building=result.building,
        phone_numbers=result.phone_numbers,
        activities=[activity.activity for activity in result.activities],
    )
