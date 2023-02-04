#!/usr/bin/env python
#-*- coding: UTF-8 -*-
# you should create own connects.py with connection to DB

import os, time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import random
from connects import DB
from datetime import datetime,timedelta
from bs4 import BeautifulSoup
import pymysql
import json
import dateparser
import requests
from mimesis import Person
from mimesis.enums import Gender


db = DB()
apikey='apikey'


class Queries():

    def get_fb_work_acc(self):
        return db.q_new('select', """ """)

    def getToken(self):
        return db.q_new('select', """ """)[0][0]


    def get_inst_session_id(self):
        return db.q_new('select', """ """)


    def get_facebook_acc(self, id_):
        return db.q_new('select', """ """.format(id_))


    def add_new_acc(self, data):
        db.q_new('update', """ """)

    def get_reg_acc(self):
        return db.q_new('select', """ """)


    def update_session_id(self, t_id, sessionid):
        db.q_new('update', """ """)


    def update_session_id_error(self, t_id):
        db.q_new('update', """ """)



class NewAcc():

    def auth(self, data, driver):
        try:
            driver.get("https://www.facebook.com/me")
            time.sleep(5)

            for reg in data:
                id = reg[0]
                login = reg[3]
                password = reg[4]

            print("id: ", id)
            print("login: ", login)
            print("password: ", password)

            regemail_elem = driver.find_element_by_name("email")
            pwd_elem = driver.find_element_by_name("pass")

            for character in login:
                regemail_elem.send_keys(character)
                time.sleep(random.uniform(0.1, 0.3))
            time.sleep(random.randint(3,5))

            for character in password:
                pwd_elem.send_keys(character)
                time.sleep(random.uniform(0.1, 0.3))

            time.sleep(random.randint(3,5))

            driver.find_element_by_xpath("//button[@name='login']").click()
            time.sleep(random.randint(10,15))


            driver.save_screenshot("logged_in.png")


        except Exception as e:
            print("Auth: ", e)


    def register(self, data, driver):
        sessionid = ''

        for reg in data:
            id = reg[0]
            type = reg[1]
            name  = reg[2]
            login = reg[3]
            password = reg[4]
            bdate = reg[5]

            firstname, lastname = name.split(" ")

            print("id: ", id)
            print("type: ", type)
            print("firstname : ", firstname )
            print("lastname : ", lastname )
            print("login: ", login)
            print("password: ", password)
            print("bdate: ", bdate)


        try:

            firstname_elem = driver.find_element_by_name("firstname")
            lastname_elem = driver.find_element_by_name("lastname")
            regemail_elem = driver.find_element_by_name("reg_email__")
            pwd_elem = driver.find_element_by_name("reg_passwd__")

            l = "abcdefghijklmnopqrstuvwxyz"
            loglen = random.randint(10, 15)

            print("phone number ...")
            get_num = requests.get("https://onlinesim.ru/api/getNum.php?apikey={0}&action=getNumber&service=facebook&country=77".format(apikey))
            
            print("Get a phone number: ",get_num)
            time.sleep(2)

            try:

                numbers=requests.get("https://onlinesim.ru/api/getState.php?apikey={0}".format(apikey)).json()
                
                print("numbers", numbers)
                phone=numbers[0]['number']
                tzid = numbers[0]['tzid']

                print("tzid: ", tzid)
                print("phone: ", phone)

            except Exception as e:
                print("number: ", e)

            driver.save_screenshot("fb_data.png")

            for character in phone:
                regemail_elem.send_keys(character)
                time.sleep(random.uniform(0.1, 0.3))
            time.sleep(random.randint(3,5))

            for character in firstname:
                firstname_elem.send_keys(character)
                time.sleep(random.uniform(0.1, 0.3))
            time.sleep(random.randint(3,5))

            for character in lastname:
                lastname_elem.send_keys(character)
                time.sleep(random.uniform(0.1, 0.3))
            time.sleep(random.randint(3,5))

            for character in password:
                pwd_elem.send_keys(character)
                time.sleep(random.uniform(0.1, 0.3))

            time.sleep(random.randint(3,5))

            driver.save_screenshot("entered_data.png")

            time.sleep(random.randint(3,5))

            year = str(str(bdate).split('-')[0])
            month = str(int(str(bdate).split('-')[1]))
            day = str(int(str(bdate).split('-')[2]))

            driver.save_screenshot("birthday_data.png")

            time.sleep(random.randint(3,5))

            time.sleep(random.uniform(0.5, 1.5))
            driver.find_element_by_xpath("//select[@name='birthday_day']/option[@value='%s']"%(day)).click()
            time.sleep(random.uniform(0.5, 1.5))
            driver.find_element_by_xpath("//select[@name='birthday_month']/option[@value='%s']"%(month)).click()
            time.sleep(random.uniform(0.5, 1.5))
            driver.find_element_by_xpath("//select[@name='birthday_year']/option[@value='%s']"%(year)).click()
            time.sleep(random.uniform(0.5, 1.5))

            driver.find_element_by_xpath("//input[@name='sex'][@value='1']").click();
            time.sleep(random.uniform(0.5, 1.5))

            driver.save_screenshot("birthday_data_entered.png")

            driver.find_element_by_xpath("//button[@name='websubmit']").click();

            time.sleep(random.randint(20,25))

            driver.save_screenshot("enter_the_code.png")

            try:

                print("Enter the code ...")

                code_elem = driver.find_element_by_id("code_in_cliff")

                for character in send_code:
                    code_elem.send_keys(character)
                    time.sleep(random.uniform(0.1, 0.3))

                driver.find_element_by_xpath("//button[@name='confirm']").click()
                
                time.sleep(random.randint(15,25))

                try:
                    driver.find_element_by_xpath("//a[text()='ОК").click()
                except Exception as e:
                    try:
                        driver.find_element_by_xpath("//*[text()='ОК").click()
                    except:
                        try:
                            driver.get("https://www.facebook.com/me")
                            time.sleep(2)
                        except Exception as e:
                            print("ClickError", e)
                
                time.sleep(random.randint(15,25))

                driver.save_screenshot("entered_the_code.png")

                sessionid = driver.get_cookies()

                print(sessionid)
                
                try:
                    numbers=requests.get("https://onlinesim.ru/api/setOperationOk.php?apikey={0}&tzid={1}".format(apikey,tzid))
                except Exception as e:
                    print("number_ok", e)


            except Exception as e:
                time.sleep(30)

                # BAN
                try:
                    numbers=requests.get("https://onlinesim.ru/api/setOperationOk.php?apikey={0}&tzid={1}&ban=1".format(apikey,tzid))
                except Exception as e:
                    print("number_error", e)

        except Exception as e:
            print("register_error", e)
            return sessionid

        return sessionid


    def transliterate(self,name):
        # Dictionary
        slovar = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'i','к':'k','л':'l','м':'m','н':'n',
                'о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'cz','ш':'sh','щ':'scz','ъ':'','ы':'y','ь':'','э':'e',
                'ю':'u','я':'ja', 'А':'a','Б':'b','В':'v','Г':'g','Д':'d','Е':'e','Ё':'e','Ж':'zh','З':'z','И':'i','Й':'i','К':'k','Л':'l','М':'m','Н':'n',
                'О':'o','П':'p','Р':'r','С':'s','Т':'t','У':'u','Ф':'F','х':'h','Ц':'c','Ч':'cz','Ш':'sh','Щ':'scz','Ъ':'','Ы':'y','Ь':'','Э':'e',
                'Ю':'u','Я':'ja',',':'','?':'',' ':'_','~':'','!':'','@':'','#':'', '$':'','%':'','^':'','&':'','*':'','(':'',')':'','-':'','=':'','+':'',
                ':':'',';':'','<':'','>':'','\'':'','"':'','\\':'','/':'','№':'', '[':'',']':'','{':'','}':'','ґ':'','ї':'', 'є':'','Ґ':'g','Ї':'i', 'Є':'e'}
        # Replace all letter in string
        for key in slovar:
            name = name.replace(key, slovar[key])
        return name

    def create_profile(self):

        try:
            person = Person('ru')
            s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
            l = "abcdefghijklmnopqrstuvwxyz"
            firstname=person.name(gender=Gender.FEMALE)
            lastname=person.surname(gender=Gender.FEMALE)
            passlen = random.randint(6, 12)
            pwd =  "".join(random.sample(s,passlen ))
            loglen = random.randint(10, 15)

            log_name = self.transliterate(firstname)

            login= str(log_name) +"_"+"".join(random.sample(l,loglen ))

            birthday_day=random.randint(1, 28)
            if len(str(birthday_day)) ==1:
                birthday_days='0'+str(birthday_day)
            else:
                birthday_days=birthday_day

            birthday_month=random.randint(1, 12)
            if len(str(birthday_month)) ==1:
                birthday_months='0'+str(birthday_month)
            else:
                birthday_months=birthday_month

            birthday_year=random.randint(1990, 2000)
            birthday_date=str(birthday_year)+'-'+str(birthday_months)+'-'+str(birthday_days)
            fullname = str(firstname)+' '+str(lastname)


        except Exception as e:
            print(e)

        return {'login' : login, 
               'reg_passwd__' : pwd,
               'birthday_day':birthday_day,
               'birthday_month':birthday_month,
               'birthday_year':birthday_year,
               'birthday_date' : birthday_date,
               'fullname':fullname}