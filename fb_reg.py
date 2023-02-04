#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from datetime import datetime
from threading import Thread
from fb_methods import Queries, NewAcc
import pymysql
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display
import json
import random
from sys import platform

from gologin import GoLogin
import requests as r
import time

q = Queries()
n = NewAcc()
token =q.getToken()


display = Display(visible=0, size=(1600, 900))
display.start()


# Get last account
last_stream = 0
accounts  = q.get_fb_work_acc()
for acc in accounts:
	last_stream = int(acc[1].split("PARSER_")[1])


# Next account
new_stream_id = last_stream+1
type_ = "FB_PARSER_"+str(new_stream_id)
print("\n")
print("new_stream", type_)


# Create GoLogin profile
profile_id=''
while len(profile_id)<3:

	try:
		prof_ID = "simple_profile"
		gl = GoLogin({'token':token, 'profile_id': prof_ID})
		data = {'name': type_}
		profile_id = gl.create(data)['name']
		print("Profile ID: ", profile_id)

	except Exception as e:
		print("Profile ID: ", e)



# Create an account
data = []
acc_data = n.create_profile()
login = acc_data['login']
password = acc_data['reg_passwd__']
birthday_day= acc_data['birthday_day']
birthday_month= acc_data['birthday_month']
birthday_year= acc_data['birthday_year']
birthday_date = acc_data['birthday_date']
fullname= acc_data['fullname']
work=0
soc_type=2
work_hour = 'mobile'


# Adding account to Database
data.append((soc_type,type_, work, fullname, login, password, birthday_date, profile_id, work_hour))
print(data)
q.add_new_acc(data)


# Choose unregistered account
no_reg_acc = q.get_reg_acc()
free_profile_id = no_reg_acc[0][6]

print("token", token)
print("free_profile_id",free_profile_id)
gl = GoLogin({
		'token': token,
		'profile_id': free_profile_id,
		'port':2051
		})

chrome_driver_path = 'chromedriver'
debugger_address = gl.start()
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", debugger_address)
driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

driver.get("https://www.facebook.com/reg")
time.sleep(2)

# Get unregistered account
t_id = no_reg_acc[0][0]
print("reg_acc", no_reg_acc, t_id)

# Registration
cookies = n.register(no_reg_acc, driver)
print("cookies", cookies)

data = str(cookies).replace("'","\"").replace("True", "true").replace("False", "false")

if "c_user=1000" not in str(data):
	try:
		n.auth(no_reg_acc, driver)
		driver.get("https://www.facebook.com/me")
		time.sleep(15)
		cookies=driver.get_cookies()
		data = str(cookies).replace("'","\"").replace("True", "true").replace("False", "false")
	except Exception as e:
		print(e)



print("data", data)

if "value\": \"1000" in str(data):
	# Updating a Session_ID
	q.update_session_id(t_id, str(data))
else:
	q.update_session_id_error(t_id)


driver.quit()
gl.stop()
display.stop()