from aidbox_python_sdk.aidboxpy import AsyncAidboxClient

from tests.conftest import SafeDBFixture


async def test_example(safe_db: SafeDBFixture, aidbox_client: AsyncAidboxClient) -> None:
    example_output = await aidbox_client.execute("$example", method="POST")

    assert example_output["status"] == "ok"
    assert example_output["patient"]["id"] == "example"
