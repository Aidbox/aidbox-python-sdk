## 0.1.21

- Fix drop_before_all test fixture for resources with suffix history

## 0.1.20

- Fix deprecation warnings of fhirpy

## 0.1.19

- Use $resource-types over Entity for db

## 0.1.18

- Add fhir-schema support to DB Proxy

## 0.1.17

- update dependencies
- get rid of deprecated event_loop asyncio fixture

## 0.1.16

- Don't raise 404 error for aidbox configured with FHIR Schema

## 0.1.15

- Add compliance_params (fhirCore, fhirUrl, fhirResource) as operation parameter

## 0.1.14

- Fix db innitialization crash for fhirschema
- Update aiohttp = "~=3.10.2"

## 0.1.13

- Add py.typed marker

## 0.1.12

- Update drop_before_all to support fhir-schema and old approach #68

## 0.1.11

- Add `headers` to SDKOperationRequest

## 0.1.10

- Improve exposed types.py
- Use web.AppKey for client/db/sdk/settings app keys (backward compatible with str key)

## 0.1.9

- Drop support of python3.8
- Lint project source code

## 0.1.8

- Move db proxy initialization after app registration

## 0.1.7

- Fix sqlalchemy tables recreation (useful in tests)

## 0.1.6

- Revert subscriptions `request` arg changes that made in 0.1.5

## 0.1.5

- Add aidbox_db fixture
- Adjust subscriptions to have `app` key in `request` dict

## 0.1.4

- Optimize app registration (get rid of manifest conversion)

## 0.1.3

- Initial pypi release
