# Author: Edvinas Dulskas
# Number of requests made: 30
# How to reduce requests: I don't really know...
import requests
import pandas as pd
import time
import os
from selenium.webdriver import Chrome
from bs4 import BeautifulSoup
from pprint import pprint

file_csv = 'task_1_results.csv'
file_xlsx = 'task_1_results.xlsx'
URL = 'https://www.norwegian.com/en/'

# Go to the page by URL
def Connect(URL):
    page = requests.get(URL)
    return BeautifulSoup(page.content, 'html.parser')

# get main content
def GetMainData(soup):
    # Check if there are any flights on that day
    if(soup.find('table', attrs={'class':'avadaytable'})):
        return soup.find('table', attrs={'class':'avadaytable'}).find('tbody').find_all('tr', attrs={'class':['rowinfo1', 'rowinfo2']})
    else:
        return 0

# Extract needed data
def ExtractData(data, day):
    temp_dict = {}
    temp_dict.setdefault('date', [])
    temp_dict.setdefault('departure_airport', [])      
    temp_dict.setdefault('arrival_airport', [])
    temp_dict.setdefault('departure_time', [])
    temp_dict.setdefault('arrival_time', [])
    temp_dict.setdefault('price', [])
    # increment i by 2
    for i in range(0, len(data), 2):
        if(data[i].find('td', attrs={'class':'duration'}).text == 'Direct'):
            temp_dict['date'].append('2020-05-'+ day)
            temp_dict['departure_airport'].append(data[i+1].find('td', attrs={'class':'depdest'}).text)     # appends departure airport
            temp_dict['arrival_airport'].append(data[i+1].find('td', attrs={'class':'arrdest'}).text)       # appends arrival airport
            temp_dict['departure_time'].append(data[i].find('td', attrs={'class':'depdest'}).text)          # appends departure time
            temp_dict['arrival_time'].append(data[i].find('td', attrs={'class':'arrdest'}).text)            # appebds arrival time
            temp = data[i].find_all('label', attrs={'class':'label seatsokfare'})                           # extract prices
            temp_p = []
            for p in temp:
                temp_p.append(p.text)
            temp_dict['price'].append(min(temp_p, key=float))       # take minimum price for each flight [min(LowFare, LowFare+, Flex)]

    return temp_dict

# Print data to .csv file
def PrintResult(result, type):
    # if we're printing the first time
    if(type == 0):
        # check if .csv file exists, if yes - delete
        if os.path.exists(file_csv):
            os.remove(file_csv)
        # check if .xlsx file exists, if yes - delete
        if os.path.exists(file_xlsx):
            os.remove(file_xlsx)

        df = pd.DataFrame(result, columns=['date', 'departure_airport', 'arrival_airport', 'departure_time', 'arrival_time', 'price'])
        df.to_csv(file_csv, index=False, encoding='utf-8')

    else:
        df = pd.DataFrame(result, columns=['date', 'departure_airport', 'arrival_airport', 'departure_time', 'arrival_time', 'price'])
        df.to_csv(file_csv, mode='a', index = False, header=None)

# Export data from .csv to .xlsx and delete .csv file
def ConvertCsvToXlsx():
    read_file = pd.read_csv (file_csv)
    read_file.to_excel (file_xlsx, index = None, header=True)
    # delete .csv file
    if os.path.exists(file_csv):
            os.remove(file_csv)

# returns available dates
def pickDays(xpath, date):
    # Open datePicker for depart date
    driver.find_element_by_xpath(xpath).click()
    temp = []

    # Find the correct month (2020-05 [MAY]) for departure
    if(driver.find_element_by_xpath('/html/body/main/div[4]/div/div/div[2]/div[2]/div/div/form/div/div/div/fieldset[2]/div/section[1]/div/div/div[1]/div/div[1]/div/div/button[2]').text != date):
        for i in range(12):
            time.sleep(0.5)
            driver.find_element_by_xpath('//*[@id="outboundDate"]/div/div/div[1]/div/div[1]/div/div/button[3]').click()
            if(driver.find_element_by_xpath('/html/body/main/div[4]/div/div/div[2]/div[2]/div/div/form/div/div/div/fieldset[2]/div/section[1]/div/div/div[1]/div/div[1]/div/div/button[2]').text == date): # break if found 
                time.sleep(3)
                tt = driver.find_element_by_xpath('//*[@id="outboundDate"]/div/div/div[1]/div/div[1]/div/table/tbody').find_elements_by_css_selector('button[aria-disabled=false]')
                for t in tt:
                    temp.append(t.text)
                break
    else:
        time.sleep(3)
        tt = driver.find_element_by_xpath('//*[@id="outboundDate"]/div/div/div[1]/div/div[1]/div/table/tbody').find_elements_by_css_selector('button[aria-disabled=false]')
        for t in tt:
            temp.append(t.text)

    return temp

# ---------- Main code --------------

# loading webDriver
driver = Chrome('C:\webdrivers\chromedriver.exe')
driver.get(URL) 

time.sleep(2)

dep_input = driver.find_element_by_id('airport-select-origin')
arr_input = driver.find_element_by_id('airport-select-destination')

# giving text to the inputs and selecting coresponding airports
dep_input.clear()
dep_input.send_keys('OSL')
time.sleep(1)
driver.find_element_by_xpath('//*[@id="OSL"]').click()
arr_input.clear()
arr_input.send_keys('RIX')
time.sleep(1)
driver.find_element_by_xpath('//*[@id="RIX"]').click()

days = pickDays('//*[@id="outboundDate"]/div/div/label/input', 'May 2020')

driver.close()

# go throught all 31 days
print('processing...')

for i in range(len(days)):
    URL = ('https://www.norwegian.com/en/ipc/availability/avaday?D_City=OSLALL&A_City=RIX&TripType=1&'
        'D_Day={day_variable}&D_Month=202005&D_SelectedDay={day_variable}&R_Day={day_variable}&R_Month=202005&'
        'R_SelectedDay={day_variable}&AgreementCodeFK=-1&CurrencyCode=EUR').format(day_variable = days[i])
    soup = Connect(URL)         # get content
    data = GetMainData(soup)    # get main data
    if(data == 0):              # if there is no flights that day, go to next day
        continue
    result = ExtractData(data, days[i])  # extract needed data
    PrintResult(result, i)      # write data to file

# convert csv to xlsx
ConvertCsvToXlsx()