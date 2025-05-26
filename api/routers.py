from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db_session, validate_api_key
from api.schemas import (
    Organization,
    OrganizationByActivityQuery,
    OrganizationByBuildingQuery,
    OrganizationByNameQuery,
    OrganizationByRadiusQuery,
    OrganizationByRectangleQuery,
    OrganizationDetail,
)
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
async def get_organizations_by_name(
    params: OrganizationByNameQuery = Query(),
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    return map(
        Organization.model_validate,
        await get_organizations_by_name(session=session, **params.model_dump()),
    )


@router.get(
    path="/building/{building_id}",
    description="Get organizations in a specific building",
)
async def get_organizations_by_building(
    params: OrganizationByBuildingQuery = Query(),
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    return map(
        Organization.model_validate,
        await get_organizations_by_building_id(session=session, **params.model_dump()),
    )


@router.get(
    path="/activity/{activity_id}",
    description="Get organizations with a specific activity",
)
async def get_organizations_by_activity(
    params: OrganizationByActivityQuery = Query(),
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    return map(
        Organization.model_validate,
        await get_organizations_by_activity_id(session=session, **params.model_dump()),
    )


@router.post(
    path="/search/radius",
    description="Search organizations within a radius from a center point",
)
async def search_organizations_by_radius(
    params: OrganizationByRadiusQuery = Query(),
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    return map(
        Organization.model_validate,
        await get_organizations_by_radius(session=session, **params.model_dump()),
    )


@router.post(
    path="/search/rectangle",
    description="Search organizations within a rectangular area",
)
async def search_organizations_by_rectangle(
    params: OrganizationByRectangleQuery = Query(),
    session: AsyncSession = Depends(get_db_session),
) -> list[Organization]:
    return map(
        Organization.model_validate,
        await get_organizations_by_rectangle(session=session, **params.model_dump()),
    )


@router.get(
    path="/{organization_id}",
    description="Get detailed information about a specific organization",
)
async def get_organization(
    organization_id: int, session: AsyncSession = Depends(get_db_session)
) -> OrganizationDetail:
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
