import pytest

from backend.tests.conftest import auth_header


@pytest.mark.asyncio
async def test_list_pipelines_returns_current_organization_stages(async_client, seeded_org, pipeline, stages):
    response = await async_client.get("/api/v1/pipelines/", headers=auth_header(seeded_org["alpha-rep"]))

    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == str(pipeline.id)
    assert [stage["id"] for stage in data[0]["stages"]] == [str(stage.id) for stage in stages]
