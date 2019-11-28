# Author: Edvinas Dulskas
# Number of requests made: 7
# How to reduce requests: Maybe reduce code redundancy?
#
#  Note: sometimes page loads airports suggestions very slowly and if you get an error in console (there is no such an attribute @id['ARN/LHR']) 
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
                rl = data[i+1].find_all('tr', attrs={'class':'flight'})
                route = rl[1].find_all('span', attrs={'class':'location'})
                temp_dict['arrival_airport'].append(route[1].text)
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
def printResult(data1, data2, data3):
    # check if .xlsx file exists, if yes - delete
    if os.path.exists(file_xlsx):
        os.remove(file_xlsx)

    df1 = pd.DataFrame(data1, columns=['date', 'departure_airport', 'arrival_airport', 'connection_airport', 'departure_time', 'arrival_time', 'price'])
    df2 = pd.DataFrame(data2, columns=['date', 'departure_airport', 'arrival_airport', 'connection_airport', 'departure_time', 'arrival_time', 'price'])
    df3 = pd.DataFrame(data3, columns=['date', 'departure_airport', 'arrival_airport', 'connection_airport', 'departure_time', 'arrival_time',
    'price', 'date_back', 'departure_airport_back', 'arrival_airport_back', 'connection_airport_back', 'departure_time_back', 'arrival_time_back',
    'price_back', 'total_price'])

    writer = pd.ExcelWriter(file_xlsx, engine='xlsxwriter')
    
    # Position the dataframes in the worksheet.
    df1.to_excel(writer, sheet_name='Sheet1')  # Default position, cell A1.
    df2.to_excel(writer, sheet_name='Sheet1', startrow=len(data1['date'])+2)
    df3.to_excel(writer, sheet_name='Sheet1', startrow=(len(data1['date'])+2+len(data2['date'])+2))

    writer.save()

# open datepicker and choose date for departure/arrival
def pickTheDate(xpath, date):
    # Open datePicker for depart date
    driver.find_element_by_xpath(xpath).click()

    # Find the correct month and day (2020-05 [MAY]) for departure/arrival 
    if(driver.find_element_by_xpath('/html/body/div[3]/div/div/span[1]').text + ' 2020' != date[:8]):
        for i in range(12):
            time.sleep(0.5)
            driver.find_element_by_xpath('/html/body/div[3]/div/a[2]/span').click()
            if(driver.find_element_by_xpath('/html/body/div[3]/div/div/span[1]').text + ' 2020' == 'MAY 2020'): # break if found
                days = driver.find_elements_by_class_name('ui-state-default')
                idx = 0
                for d in days:
                    if(int(d.text) == int(date[9:])):
                       break
                    idx += 1
                time.sleep(0.5)
                days[idx].click()
                break
    else:
        time.sleep(0.5)
        days = driver.find_elements_by_class_name('ui-state-default')
        idx = 0
        for d in days:
            if(int(d.text) == int(date[9:])):
                break
            idx += 1
        days[idx].click()

# make cheapest combinations
def flightCombinations(data_dep, data_arr):
    temp_dict = {
    'date' : [],
    'departure_airport' : [],
    'arrival_airport' : [],
    'connection_airport' : [],
    'departure_time' : [],
    'arrival_time' : [],
    'price' : [],
    'date_back' : [],
    'departure_airport_back' : [],
    'arrival_airport_back' : [],
    'connection_airport_back' : [],
    'departure_time_back' : [],
    'arrival_time_back' : [],
    'price_back' : [],
    'total_price' : []
    }

    for i in range(len(data_dep['date'])):
        cheapest = float(data_dep['price'][i]) + float(data_arr['price'][0])      # sum up prices with the first arrival flight
        idx = 0         # index for arrival flight
        for j in range(len(data_arr)):
            temp_price = float(data_dep['price'][i]) + float(data_arr['price'][j])    # calculate combinations prices
            if(temp_price < cheapest):      #if cheapest price found set it and set the cheapest combo arrival flight index      
                cheapest = temp_price 
                idx = j
        temp_dict['date'].append(data_dep['date'][i])
        temp_dict['departure_airport'].append(data_dep['departure_airport'][i])
        temp_dict['arrival_airport'].append(data_dep['arrival_airport'][i])
        temp_dict['connection_airport'].append(data_dep['connection_airport'][i])
        temp_dict['departure_time'].append(data_dep['departure_time'][i])
        temp_dict['arrival_time'].append(data_dep['arrival_time'][i])
        temp_dict['price'].append(data_dep['price'][i])
        temp_dict['date_back'].append(data_arr['date'][idx])
        temp_dict['departure_airport_back'].append(data_arr['departure_airport'][idx])
        temp_dict['arrival_airport_back'].append(data_arr['arrival_airport'][idx])
        temp_dict['connection_airport_back'].append(data_arr['connection_airport'][idx])
        temp_dict['departure_time_back'].append(data_arr['departure_time'][idx])
        temp_dict['arrival_time_back'].append(data_arr['arrival_time'][idx])
        temp_dict['price_back'].append(data_arr['price'][idx])
        temp_dict['total_price'].append(cheapest)

    return temp_dict

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
pickTheDate('/html/body/div[1]/form/div[4]/div[2]/div[4]/div[2]/div[1]/div[1]/div[2]/div[5]/div[1]/div[2]', 'MAY 2020 08')

time.sleep(0.5)

# Open datePicker for arrival date
pickTheDate('/html/body/div[1]/form/div[4]/div[2]/div[4]/div[2]/div[1]/div[1]/div[2]/div[6]/div[2]/div[2]', 'MAY 2020 15')

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
combo_dict = flightCombinations(dep_dict, arr_dict)     # cheapest combinations

# print results to excel file
printResult(dep_dict, arr_dict, combo_dict)

# close driver
driver.close()