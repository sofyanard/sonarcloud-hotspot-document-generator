import requests
import json
import math
from read_write_json import append_to_json
import aiohttp
import asyncio
import concurrent.futures
# from insert_into_doc import initialize_doc, insert_to_doc

def call_url(url, headers, params, json: bool = False):
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises a HTTPError if the HTTP request returned an unsuccessful status code
        
        if json == False:
            return response.text
        else:
            return response.json()
            
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    return None

async def call_url_a(url, headers, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            return await response.json()

def convert_to_json(data):
    try:
        return json.loads(data)
    except Exception as e: print(e)
    
def check_if_list_has_data(url_list, headers, params_check):
    # params_check["impactSeverities"]= severity.upper()
    # params_check["ps"]= 1
    
    result_json= convert_to_json(call_url(url_list, headers, params_check))
    return result_json

def iterate_list(url_list, headers, params_iterate, num_of_iteration):
    result = []
    x=1
    
    for x in range(1,num_of_iteration+1):
        params_iterate["p"]= x
        result_json=convert_to_json(call_url(url_list, headers, params_iterate))
        result.append(result_json)
        ++x
    return result

async def iterate_list_a(url_list, headers, params_iterate, num_of_iteration):
    # tasks = []

    # for x in range(1, num_of_iteration + 1):
    #     params_iterate["p"] = x
    #     task = asyncio.create_task(call_url_a(url_list, headers, params_iterate))
    #     tasks.append(task)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        loop = asyncio.get_event_loop()
        tasks = []
        tasks.append(loop.run_in_executor(executor, call_url, url_list, headers, params_iterate, True))

    return await asyncio.gather(*tasks)

def get_detail(url_detail, headers, params):
    result_json=convert_to_json(call_url(url_detail, headers, params))
    return result_json

async def get_detail_a(url_detail, headers, params):
    result_json = asyncio.create_task(call_url(url_detail, headers, params))
    return result_json

def get_project_list(url: str, headers: dict[str, str], params: dict[str, str]) -> list:
    result_json: list = []
    for project in convert_to_json(call_url(url, headers, params))["components"]:
        result_json.append({"key":project["key"], "name":project["name"]})
    return result_json

def get_organization_list(url: str, headers: dict[str, str], params: dict[str, str] = {"member": "true"}) -> list:
    result_json: list = []
    x = convert_to_json(call_url(url, headers, params))
    if isinstance(x, dict):
        for organization in x["organizations"]:
            result_json.append({"key":organization["key"], "name":organization["name"]})
    else:
        result_json.append({"key":"default", "name":"default"})
    return result_json

def backup_iterate(url_list, headers, params, severity):
    params["impactSeverities"]= severity.upper()
    result_json= convert_to_json(call_url(url_list, headers, params))
    
    if result_json["total"] > 0:
        append_to_json(result_json, "all_issues_"+params["componentKeys"]+"_"+params["impactSoftwareQualities"]+"_"+params["impactSeverities"]+".json")
        print("total: " + str(result_json["total"]))
        
        num_of_iteration = math.ceil(result_json["total"]/params["ps"])
        print("num_of_iteration"+str(num_of_iteration))
        # print(params["p"])
        
        for x in range(2,num_of_iteration+1):
            ++x
            # print("num of param: " + str(params["p"]))
            params["p"]= x
            print(params["p"])
            result_json=convert_to_json(call_url(url_list, headers, params))
            append_to_json(result_json, "all_issues_"+params["componentKeys"]+"_"+params["impactSoftwareQualities"]+"_"+params["impactSeverities"]+".json")
            
    else:
        print('Failed to retrieve data')
