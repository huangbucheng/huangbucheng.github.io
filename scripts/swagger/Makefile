swagger:
	swagger generate spec --include-tag=openapi -o ./docs/swagger_openapi.json
	cd docs && python3 filter_swagger.py && cd -
	redoc-cli bundle -o docs/openapi.html docs/filtered_swagger_openapi.json
