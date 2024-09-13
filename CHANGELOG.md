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
