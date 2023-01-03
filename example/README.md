# example Backend

## Black autoformater
```
pip install autohooks autohooks-plugin-black autohooks-plugin-isort
pre-commit install
```

## Tests
To run tests locally, copy `.env.tpl` to `.env` and specify `TESTS_AIDBOX_LICENSE`[https://license-ui.aidbox.app/](https://license-ui.aidbox.app/).


Build images using `docker compose -f docker-compose.tests.yaml build`.


After that, just start `./run_test.sh` or `./run_test.sh tests/test_base.py` (if you want to run the particular file/test).
The first run may take about a minute because it prepares the db and devbox.


If you have updated some requirements, you need to re-run `docker-compose -f docker-compose.tests.yaml build`
