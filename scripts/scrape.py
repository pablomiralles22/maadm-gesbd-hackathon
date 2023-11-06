import os
import sys
import requests
import datetime
import asyncio
import httpx
import re
from xml.etree.ElementTree import fromstring as element_tree_from_string, ElementTree

# Usage: python3 scrape.py start_date end_date target_path
assert len(sys.argv) >= 4, 'ERROR: You must specify at start date, end date and target path'
start_date, end_date, target_path = sys.argv[1], sys.argv[2], sys.argv[3]

start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

# CONSTANTS
MAX_CONCURRENT_REQUESTS = 10
BOE_URL = 'https://boe.es'
BOE_API = f'{BOE_URL}/diario_boe/xml.php?id='

get_api_url_for_id = lambda id: f'{BOE_API}{id}'
get_summary_api_url_for_date = lambda date: f'{BOE_API}BOE-S-{date.strftime("%Y%m%d")}'

get_id_regex_for_year = lambda year: rf'BOE-[^sS]-{year}-\d+'

async def parse_boe_for_id(boe_id, target_dir, async_client):
    print(f'Parsing BOE for id {boe_id}')
    filepath = os.path.join(target_dir, f'{boe_id}.xml')
    if os.path.exists(filepath):
        return

    try:
        response = await async_client.get(get_api_url_for_id(boe_id))
        assert response.status_code == 200, f"ERROR: Could not fetch the XML for id {boe_id}. Received status code {response.status_code}"
        xml_content = response.text
        xml = ElementTree(element_tree_from_string(xml_content))
        assert xml.getroot().tag != 'error', f'ERROR: Could not fetch the XML for id {boe_id}. Received error {xml_content}'
    except Exception as e:
        print(f'ERROR: Could not fetch the XML for id {boe_id}. Received error {e}.')
        return
    with open(filepath, 'w') as file:
        file.write(xml_content)

async def parse_boe_for_date(date, async_client):
    date_str = date.strftime('%Y-%m-%d')
    print(f'Parsing BOE for date {date_str}')
    
    # create directory
    date_directory = os.path.join(target_path, date.strftime('%Y/%m/%d'))
    os.makedirs(date_directory, exist_ok=True)
    
    # get and store xml summary file, linking to all entrances
    summary_xml_filename = os.path.join(date_directory, 'index.xml')
    
    if os.path.exists(summary_xml_filename):  # Read from disk
        with open(summary_xml_filename, 'r') as file:
            summary_xml_content = file.read()
    else: # Otherwise, fetch it
        try:
            response = requests.get(get_summary_api_url_for_date(date))
            assert response.status_code == 200, f"ERROR: Could not fetch the summary XML for date {date_str}. Received status code {response.status_code}."
            summary_xml_content = response.text
            summary_xml = ElementTree(element_tree_from_string(summary_xml_content))
            assert summary_xml.getroot().tag != 'error', f'ERROR: Could not fetch the summary XML for date {date_str}. Received error {summary_xml_content}.'
    
        except Exception as e:
            print(f'ERROR: Could not fetch the summary XML for date {date_str}. Got error {e}.')
            os.rmdir(date_directory)
            return

        with open(summary_xml_filename, 'w') as file:
            file.write(summary_xml_content)

    boe_ids = set(re.findall(get_id_regex_for_year(date.year), summary_xml_content))
    tasks = []
    for boe_id in boe_ids:
        tasks.append(
            asyncio.create_task(parse_boe_for_id(boe_id, date_directory, async_client))
        )
    await asyncio.gather(*tasks)


async def main():
    tasks = []
    limits = httpx.Limits(max_connections=MAX_CONCURRENT_REQUESTS)
    async with httpx.AsyncClient(limits=limits) as async_client:
        date = start_date
        while date <= end_date:
            tasks.append(asyncio.create_task(parse_boe_for_date(date, async_client)))
            date += datetime.timedelta(days=1)
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())