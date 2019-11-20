# Author: Edvinas Dulskas
# Note: sometimes page loads airports suggestions very slowly and if you get an error in console (there is no such an attribute @id['ARN/LHR']) 
#       just run the program again.. Also, sometimes, if you make too many attempts web requests you to do the captcha or it keeps reloading 
#       constantly. If the page keeps reloading - open new tab and go to https://classic.flysas.com/en/de, click on search and then back to the 
#       original tab, page starts to load the content...
import pandas as pd
import time
import os
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from pprint import pprint

# ---- Constants ---
URL = 'https://classic.flysas.com/en/de'
file_csv = 'task_2_results.csv'
file_xlsx = 'task_2_results.xlsx'

# ---- Functions ----
# Get tbody of both tables 
def getBody(soup, id):
    return soup.find('table', attrs={'id':''+ id +''}).find('tbody')

# Get main data from tables
def getData(data):
    return data.find_all('tr', attrs={'class':['segmented', 'segments']})

# Extracting all the data and puting into the dictionary
def extractData(data, city, date):
    temp_dict = {
    'date' : [],
    'departure_airport' : [],
    'arrival_airport' : [],
    'connection_airport' : [],
    'departure_time' : [],
    'arrival_time' : [],
    'price' : []
    }

    for i in range(0, len(data), 2):
        dp = data[i+1].find('tr', attrs={'class':'flight'}).find_all('span', attrs={'class':'location'})
        if(dp[1].text == 'Oslo' or dp[1].text[:len(city)] == ''+ city +''): # if direct to London or has a stop in Oslo     
            temp_dict['departure_airport'].append(dp[0].text)   # get departure airport
            if(dp[1].text == 'Oslo'):           # if it's connecting flight then add connecting_airport and arrival_airport
                temp_dict['connection_airport'].append(dp[1].text)
                temp_dict['arrival_airport'].append(''+ city +'')
            else:                                  # if it's direct flight, add only arrival_airport
                temp_dict['arrival_airport'].append(dp[1].text) 
                temp_dict['connection_airport'].append('--')  
            temp_dict['date'].append(''+ date +'')  # fill in the date
            price = data[i].find_all('span', attrs={'class':'number'})      # get all prices
            p_temp = []
            for p in price:
                p_temp.append(p.text.replace(',', '.'))     # change every , to . because otherwise it throus conversation error (can't convert string to float)
            temp_dict['price'].append(min(p_temp, key=float))     # take only lowest price (cheapest one)
            times = data[i].find('td', attrs={'class':'time'}).find_all('span', attrs={'class':'time'})
            temp_dict['departure_time'].append(times[0].text)   # add departure time
            temp_dict['arrival_time'].append(times[1].text)     # add arrival time
        else:
            continue        # jump to next line

    return temp_dict

# Print data to .csv file
def printResult(result, type):
    # if we're printing the first time
    if(type == 0):
        # check if .csv file exists, if yes - delete
        if os.path.exists(file_csv):
            os.remove(file_csv)
        # check if .xlsx file exists, if yes - delete
        if os.path.exists(file_xlsx):
            os.remove(file_xlsx)

        df = pd.DataFrame(result, columns=['date', 'departure_airport', 'arrival_airport', 'connection_airport', 'departure_time', 'arrival_time', 'price'])
        df.to_csv(file_csv, index=False, encoding='utf-8')

    else:
        df = pd.DataFrame(result, columns=['date', 'departure_airport', 'arrival_airport', 'connection_airport', 'departure_time', 'arrival_time', 'price'])
        df.to_csv(file_csv, mode='a', index = False, encoding='utf-8')
        convertCsvToXlsx()

# Export data from .csv to .xlsx and delete .csv file
def convertCsvToXlsx():
    read_file = pd.read_csv(file_csv)
    read_file.to_excel (file_xlsx, index = None, header=True)
    # delete .csv file
    if os.path.exists(file_csv):
            os.remove(file_csv)

# ---- Main code -----
# loading webDriver
driver = Chrome('C:\webdrivers\chromedriver.exe')
driver.get(URL)

# getting input elements (departure and destination)
dep_input = driver.find_element_by_id('ctl00_FullRegion_MainRegion_ContentRegion_ContentFullRegion_ContentLeftRegion_CEPGroup1_CEPActive_cepNDPRevBookingArea_predictiveSearch_txtFrom')
arr_input = driver.find_element_by_id('ctl00_FullRegion_MainRegion_ContentRegion_ContentFullRegion_ContentLeftRegion_CEPGroup1_CEPActive_cepNDPRevBookingArea_predictiveSearch_txtTo')

# giving text to the inputs and selecting coresponding airports
dep_input.send_keys('ARN')
time.sleep(4)
driver.find_element_by_xpath('//*[@id="ARN"]').click()
arr_input.send_keys('LHR')
time.sleep(4)
driver.find_element_by_xpath('//*[@id="LHR"]').click()

# Open datePicker for depart date
driver.find_element_by_xpath('/html/body/div[1]/form/div[4]/div[2]/div[4]/div[2]/div[1]/div[1]/div[2]/div[5]/div[1]/div[2]').click()

# Find the correct month and day (2020-05 [MAY]) for departure 
if(driver.find_element_by_xpath('/html/body/div[3]/div/div/span[1]').text + ' 2020' != 'MAY 2020'):
    for i in range(12):
        driver.find_element_by_xpath('/html/body/div[3]/div/a[2]/span').click()
        if(driver.find_element_by_xpath('/html/body/div[3]/div/div/span[1]').text + ' 2020' == 'MAY 2020'): # break if found
            time.sleep(0.5)
            driver.find_element_by_xpath('/html/body/div[3]/table/tbody/tr[2]/td[5]/a').click() # choose 8th day and click
            break
        time.sleep(0.5)
else:
    time.sleep(0.5)
    driver.find_element_by_xpath('/html/body/div[3]/table/tbody/tr[2]/td[5]/a').click() # choose 8th day and click

time.sleep(0.5)

# Open datePicker for arrival date
driver.find_element_by_xpath('/html/body/div[1]/form/div[4]/div[2]/div[4]/div[2]/div[1]/div[1]/div[2]/div[6]/div[2]/div[2]').click()

# Find the correct month and day (2020-05 [MAY]) for arrival
if(driver.find_element_by_xpath('/html/body/div[3]/div/div/span[1]').text + ' 2020' != 'MAY 2020'):
    for i in range(12):
        driver.find_element_by_xpath('/html/body/div[3]/div/a[2]/span').click()
        if(driver.find_element_by_xpath('/html/body/div[3]/div/div/span[1]').text + ' 2020' == 'MAY 2020'): # break if found
            time.sleep(0.5)
            driver.find_element_by_xpath('/html/body/div[3]/table/tbody/tr[3]/td[5]/a').click() # choose 15th day and click
            break
        time.sleep(0.5)
else:
    time.sleep(0.5)
    driver.find_element_by_xpath('/html/body/div[3]/table/tbody/tr[3]/td[5]/a').click() # choose 15th day and click

time.sleep(0.5)

# Pressing 'Search' button
button = driver.find_element_by_xpath('//*[@id="ctl00_FullRegion_MainRegion_ContentRegion_ContentFullRegion_ContentLeftRegion_CEPGroup1_CEPActive_cepNDPRevBookingArea_Searchbtn_ButtonLink"]/span[2]')
driver.execute_script("arguments[0].click();", button)

# switch driver to new window and take main content (tbody from table [id='WDSEffect_table_0'])
element = WebDriverWait(driver, 60).until(lambda x: x.find_element_by_id('panel_0'))
soup = BeautifulSoup(driver.page_source, 'html.parser')

# get content from both tables
tbody_dep = getBody(soup, 'WDSEffect_table_0')
tbody_arr = getBody(soup, 'WDSEffect_table_1')

# data from tables (all the nessesary rows)
data_dep = getData(tbody_dep)
data_arr = getData(tbody_arr)

# final data extracted and put into dictionaries
dep_dict = extractData(data_dep, 'London', '2020-05-08')
arr_dict = extractData(data_arr, 'Stockholm', '2020-05-15')

# close driver
driver.close()

# print results to file
printResult(dep_dict, 0)    # printing for the first time
printResult(arr_dict, 1)