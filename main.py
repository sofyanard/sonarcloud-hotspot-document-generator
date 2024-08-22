from api_call import check_if_list_has_data, iterate_list, get_detail, get_project_list, get_organization_list, iterate_list_a, get_detail_a
from read_write_json import read_json_file, write_json_file
from read_write_docx import initialize_doc, insert_to_doc, add_header, load_doc, merge_and_save_docx, replace_text_in_docx
import math
import asyncio
import concurrent.futures
import time

def get_token() -> str:
    ret = ""
    try:
        with open("token", 'r') as file:
            ret = file.read().strip()
    except Exception as err:
        print(f'Error get token: {err}')
    finally:
        return ret

def console_input(data, type: str):
    print()
    lenn=len(data)
    ret: list = []
    _input_text: str = ""
    load_from_file = False
    if lenn > 1:
        if type == "organization":
            print("Available Organization to Select: ")
            _input_text = "Select organization "
        elif type == "project":
            print("Available Project to Select: ")
            _input_text = "Select project "
        elif type == "load_from_file":
            print("Available Option to Select: ")
            _input_text = "Select load data "
            lenn-=1
            load_from_file = True

        for key, val in enumerate(data):
            print(f'{key}: {val["name"]}')
            
        if not load_from_file:    
            print(f"{lenn}: All")

        try:
            _input: int = int(input(_input_text + f'[0-{lenn}]: '))
            
            if _input == lenn and not load_from_file:
                ret = data
            elif load_from_file and _input == 0:
                return False
            elif load_from_file and _input == 1:
                return True
            elif data[int(_input)] in data:
                ret.append(data[_input])

        except ValueError:
            print("Input must be an integer")
            return console_input(data, type)
        except IndexError:
            print(f"Input must start from 0 to {lenn}")
            return console_input(data, type)
    else:
        ret = data
    return ret

def main():
    headers = {
        "accept":"application/json",
        "Authorization": f'Bearer {get_token()}',
    }
    
    base_data_dir = './data/'
    raw_data_dir = base_data_dir + 'raw_response/'
    base_domain = 'http://103.59.160.119/api/'
    
    url_organization_list = base_domain + 'organizations/search'
    organization_list: dict = console_input(get_organization_list(url_organization_list, headers), "organization")
    
    url_project_list: str = base_domain + 'components/search_projects'
    url_list = base_domain+'hotspots/search'
    
    project_list: list = []

    impact_software_quality_list=[
        "SECURITY",
        "RELIABILITY",
        "MAINTAINABILITY",
    ]
    
    severity_list=[
        "HIGH",
        "MEDIUM",
        "LOW"
    ]

    params: dict = {
        "ps":500,
        "p":1,
    }

    load_from_file=True
    data = {}
    rules = []
    hotspots = []
    
    for organization in organization_list:
        params["organization"] = organization["key"]
        print("Getting project list in " + organization["key"])
        project_list += console_input(get_project_list(url_project_list, headers, {"organization": organization["key"] }), "project")
        load_from_file=console_input([{"name":"Load From Internet"}, {"name":"Load From File"}], "load_from_file")
        start = time.time()

        for project in project_list:
            if load_from_file:
                data= read_json_file(raw_data_dir +"All Hotspot "+project["name"]+".json")
                if data:
                    print("Getting data from "+ raw_data_dir +"All Hotspot "+project["name"]+".json")
            end = time.time()
            print("Elapsed time to get detail data from file: " + str(end-start))
            
            if data == {}:
                params["project"]= project["key"]
                
                print("Getting data from internet")
                print(f'Getting {project["key"]} hotspot')

                # *** hotspot: request page 1 ***
                page = 1
                params["p"] = page
                check = check_if_list_has_data(url_list, headers, params)
                total_hotspots = check["paging"]["total"]
                print(f'Total hotspots: {total_hotspots}')

                hotspots = check["hotspots"]
                
                # *** hotspot: loop if results are more than 1 page ***
                while (len(hotspots) < total_hotspots):
                    page = page + 1
                    params["p"] = page
                    check = check_if_list_has_data(url_list, headers, params)
                    hotspots += check["hotspots"]
                
                # *** hotspot: construct json data ***
                for hotspot in hotspots:
                    # print(f'{hotspots.index(hotspot) + 1} : {hotspot["securityCategory"]}')
                    type = hotspot["securityCategory"]
                    if (type not in data):
                        data[type] = []
                    data[type].append(hotspot)

            end = time.time()
            print("Elapsed time before get detail: " + str(end-start))
            get_hotspot_detail(headers, params, project["name"], data, base_domain, base_data_dir, load_from_file)
    
    end = time.time()
    print("Elapsed time: " + str(end-start))

def get_hotspot_detail(headers: dict, params: dict, project, data, base_domain: str, base_data_dir: str, load_from_file: bool):
    # set data dir
    master_data_dir = base_data_dir + 'master/'
    failed_data_dir = base_data_dir + 'failed/'
    raw_data_dir = base_data_dir + 'raw_response/'
    report_dir = base_data_dir + 'generated_report/'
    
    url_detail = base_domain + 'rules/show' 
    header1={}
    failed: list=[]
    detail_data=None

    master_hotspot= read_json_file(master_data_dir+"master hotspot.json")
    i=1
    
    # init doc
    # doc_name = report_dir + "All Issue "+project+".docx"
    # doc= initialize_doc(doc_name)
    
    doc_template_open_name = "./data/doc_template/Reporting-SAKTI-opening-template.docx"
    doc1= load_doc(doc_template_open_name)
    
    doc_template_close_name = "./data/doc_template/Reporting-SAKTI-closing-template.docx"
    doc2= load_doc(doc_template_close_name)
    
    replace_text_in_docx(doc1, "@%APP%@", project)
    
    # adding header
    # add_header("Latar Belakang", doc,1)
    # add_header("Tujuan", doc,1)
    # add_header("Metodologi", doc,1)
    # doc.add_page_break() 
    # add_header("Temuan", doc,1)
    
    for key, value in data.items():

        print(f'key: {key}')
        print("==========")
        
        paragraph = doc1.add_paragraph()
        paragraph.add_run("\n")
        if key not in header1:
            add_header(key, doc1,2)
            header1[key] = True
        
        # processing each hotspot
        for hotspot in value:
            print(f'hotspot: {hotspot["key"]}')
            print("==========")

            if load_from_file == False:
                if hotspot["ruleKey"] not in master_hotspot:
                    params_details={
                        "key":hotspot["ruleKey"],
                        "organization":params["organization"],
                    }
                    
                    detail_data = get_detail(url_detail, headers, params_details)

                    print(f'detail_data: {detail_data["key"]}')
                    print("==========")

                    master_hotspot[hotspot["ruleKey"]] = detail_data

                    print(f'master_hotspot: {detail_data["key"]}')
                    print("==========")

                    hotspot["rule"]= detail_data["rule"]
                else:
                    hotspot["rule"]= master_hotspot[hotspot["ruleKey"]]

                if insert_to_doc(hotspot, doc1, i, project) == False:
                    failed.append(hotspot)
                
                # print(f'hotspot: {hotspot}')
                # print("==========")
        
    # input("Press Enter to continue...")

    # doc.save(report_dir + "All Issue "+project+".docx")
    doc1.add_page_break()
    merge_and_save_docx(doc1, doc2, report_dir + "All Issue "+project+".docx")
    if not load_from_file :
        write_json_file(data, raw_data_dir + "All Hotspot "+project+".json")
        write_json_file(master_hotspot, master_data_dir + "Master Hotspot.json")
    write_json_file(failed, failed_data_dir + "Failed Append "+project+".json")

def process(load_from_file, hotspot, master_hotspot, params, url_detail, headers, doc1, i, project, failed):
    if load_from_file == False:
        if hotspot["ruleKey"] not in master_hotspot:
            params_details={
                "key":hotspot["ruleKey"],
                "organization":params["organization"],
            }
            
            detail_data= get_detail(url_detail, headers, params_details)
            master_hotspot[detail_data["ruleKey"]] = detail_data["rule"]
            hotspot["rule"]= detail_data["rule"]
        else:
            hotspot["rule"]= master_hotspot[hotspot["ruleKey"]]
    
    if insert_to_doc(hotspot, doc1, i, project) == False:
        failed.append(hotspot)

if __name__ == '__main__':
    main()