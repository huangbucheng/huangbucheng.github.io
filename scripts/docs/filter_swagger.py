import json

def filter_swagger_by_tag(swagger_file):
    with open(swagger_file, 'r') as f:
        swagger = json.load(f)

    filtered_paths = {}
    used_definitions = set()
    used_responses = set()

    # 收集所有被使用的定义和响应
    for path, methods in swagger['paths'].items():
        for method, details in methods.items():
            filtered_paths[path] = methods
            
            # 收集参数中使用的定义
            if 'parameters' in details:
                for param in details['parameters']:
                    if 'schema' in param:
                        collect_definitions(param['schema'], used_definitions, swagger['definitions'])
            
            # 收集响应中使用的定义
            if 'responses' in details:
                for response_code, response in details['responses'].items():
                    # 处理直接schema
                    if 'schema' in response:
                        collect_definitions(response['schema'], used_definitions, swagger['definitions'])
                    # 处理响应引用
                    elif '$ref' in response:
                        ref = response['$ref'].split('/')[-1]
                        used_responses.add(ref)
                        # 收集引用响应中的schema定义
                        if 'responses' in swagger and ref in swagger['responses']:
                            ref_response = swagger['responses'][ref]
                            if 'schema' in ref_response:
                                collect_definitions(ref_response['schema'], used_definitions, swagger['definitions'])

    # 过滤定义 - 只保留被使用的定义
    filtered_definitions = {k: v for k, v in swagger.get('definitions', {}).items() if k in used_definitions}
    
    # 过滤响应
    filtered_responses = {}
    if 'responses' in swagger:
        filtered_responses = {k: v for k, v in swagger['responses'].items() if k in used_responses}

    swagger['paths'] = filtered_paths
    swagger['definitions'] = filtered_definitions
    if 'responses' in swagger:
        swagger['responses'] = filtered_responses

    with open(f'filtered_{swagger_file}', 'w') as f:
        json.dump(swagger, f, indent=2, ensure_ascii=False)

def collect_definitions(schema, used_definitions, all_definitions):
    if '$ref' in schema:
        ref = schema['$ref'].split('/')[-1]
        if ref not in used_definitions:
            used_definitions.add(ref)
            if ref in all_definitions:
                collect_definitions(all_definitions[ref], used_definitions, all_definitions)
    elif 'items' in schema:
        collect_definitions(schema['items'], used_definitions, all_definitions)
    elif 'properties' in schema:
        for prop in schema['properties'].values():
            collect_definitions(prop, used_definitions, all_definitions)

if __name__ == '__main__':
    filter_swagger_by_tag('swagger_openapi.json')
