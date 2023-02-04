import json
import time
import os
import stat
import sys
import shutil
import requests
import zipfile
import subprocess
import pathlib
import tempfile
import math

from extensionsManager import *
from connects import DB

db = DB()

getProxy = db.q_new('select', """ """)[0]

USERNAME= getProxy[0]
PASSWORD= getProxy[1]
HOST= getProxy[2]
PORT= getProxy[3]

print("USERNAME",USERNAME)
print("PASSWORD",PASSWORD)
print("HOST",HOST)
print("PORT",PORT)

API_URL = 'https://api.gologin.com'


class GoLogin(object):
    def __init__(self, options):
        self.access_token = options.get('token')

        self.tmpdir = options.get('tmpdir', tempfile.gettempdir())
        self.address = options.get('address', '127.0.0.1')
        self.extra_params = options.get('extra_params', [])
        self.port  = options.get('port', 3500)
        self.local = options.get('local', False)
        self.spawn_browser = options.get('spawn_browser', True)
        self.credentials_enable_service = options.get('credentials_enable_service')

        home = str(pathlib.Path.home())
        self.executablePath = options.get('executablePath', os.path.join(home, '.gologin/browser/orbita-browser/chrome'))
        if not os.path.exists(self.executablePath) and sys.platform=="darwin":
            self.executablePath = os.path.join(home, '.gologin/browser/Orbita-Browser.app/Contents/MacOS/Orbita')
        print('executablePath', self.executablePath)
        if self.extra_params:
            print('extra_params', self.extra_params)
        self.setProfileId(options.get('profile_id')) 


    def setProfileId(self, profile_id):
        self.profile_id = profile_id
        if self.profile_id==None:
            return
        self.profile_path = os.path.join(self.tmpdir, 'gologin_'+self.profile_id)
        self.profile_zip_path = os.path.join(self.tmpdir, 'gologin_'+self.profile_id+'.zip')
        self.profile_zip_path_upload = os.path.join(self.tmpdir, 'gologin_'+self.profile_id+'_upload.zip')


    def loadExtensions(self):
        profile = self.profile
        chromeExtensions = profile.get('chromeExtensions')
        extensionsManagerInst = ExtensionsManager()
        pathToExt = ''
        for ext in chromeExtensions:
            ver = extensionsManagerInst.downloadExt(ext)
            pathToExt += os.path.join(pathlib.Path.home(), '.gologin', 'extensions', 'chrome-extensions', ext + '@' + ver + '\n')

        return pathToExt


    def spawnBrowser(self):
        proxy = self.proxy
        proxy_host = ''
        if proxy:
            if proxy.get('mode')==None or proxy.get('mode')=='geolocation':
                proxy['mode'] = 'http'
            proxy_host = proxy.get('host')            
            proxy = self.formatProxyUrl(proxy)
        
        tz = self.tz.get('timezone')
        chromeExtensions = self.profile.get('chromeExtensions')
        if chromeExtensions and len(chromeExtensions)>0:
            paths = self.loadExtensions()
            split_paths = paths.split('\n')
            while '' in set(split_paths):
                split_paths.remove('')

        params = [
        self.executablePath,
        '--remote-debugging-port='+str(self.port),
        '--user-data-dir='+self.profile_path, 
        '--password-store=basic', 
        '--tz='+tz, 
        '--gologin-profile='+self.profile_name, 
        '--lang=en', 
        '--no-sandbox',
        ]
        load_ext = '--load-extension='
        if chromeExtensions and len(chromeExtensions)>0:
            for path in split_paths:
                load_ext += path
                load_ext += ','
            params.append(load_ext)

        if proxy:
            hr_rules = '"MAP * 0.0.0.0 , EXCLUDE %s"'%(proxy_host)
            params.append('--proxy-server='+proxy)
            params.append('--host-resolver-rules='+hr_rules)

        for param in self.extra_params:
            params.append(param)

        if sys.platform == "darwin":
            subprocess.Popen(params)
        else:
            subprocess.Popen(params, start_new_session=True)

        try_count = 1
        url = str(self.address) + ':' + str(self.port)
        while try_count<100:
            try:
                data = requests.get('http://'+url+'/json').content
                break
            except:
                try_count += 1
                time.sleep(1)
        return url

    def start(self):
        profile_path = self.createStartup()
        if self.spawn_browser == True:
            return self.spawnBrowser()
        return profile_path

    def zipdir(self, path, ziph):
        for root, dirs, files in os.walk(path):
            for file in files:
                path = os.path.join(root, file)
                if not os.path.exists(path):
                    continue
                if stat.S_ISSOCK(os.stat(path).st_mode):
                    continue
                try:
                    ziph.write(path, path.replace(self.profile_path, ''))
                except:
                    continue

    def stop(self):
        self.sanitizeProfile()
        if self.local==False:
            self.commitProfile()
            os.remove(self.profile_zip_path_upload)
            shutil.rmtree(self.profile_path)

    def commitProfile(self):
        zipf = zipfile.ZipFile(self.profile_zip_path_upload, 'w', zipfile.ZIP_DEFLATED)
        self.zipdir(self.profile_path, zipf)
        zipf.close()
        
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'User-Agent': 'Selenium-API'
        }

        signedUrl = requests.get(API_URL + '/browser/' + self.profile_id + '/storage-signature', headers=headers).content.decode('utf-8')

        requests.put(signedUrl, data=open(self.profile_zip_path_upload, 'rb'))

    def sanitizeProfile(self):
        remove_dirs = [
          'Default/Cache',
          'Default/Service Worker/CacheStorage',
          'Default/Code Cache',
          'Default/GPUCache',
          'GrShaderCache',
          'ShaderCache',
          'biahpgbdmdkfgndcmfiipgcebobojjkp',
          'afalakplffnnnlkncjhbmahjfjhmlkal',
          'cffkpbalmllkdoenhmdmpbkajipdjfam',
          'Dictionaries',
          'enkheaiicpeffbfgjiklngbpkilnbkoi',
          'oofiananboodjbbmdelgdommihjbkfag',
          'SafetyTips',
          'fonts',
        ];

        for d in remove_dirs:
            fpath = os.path.join(self.profile_path, d)
            if os.path.exists(fpath):
                try:
                    shutil.rmtree(fpath)
                except:
                    continue
    
    def formatProxyUrl(self, proxy):
        return proxy.get('mode', 'http')+'://'+proxy.get('host','')+':'+str(proxy.get('port',80))

    def formatProxyUrlPassword(self, proxy):
        if proxy.get('username', '')=='':
            return proxy.get('mode', 'http')+'://'+proxy.get('host','')+':'+str(proxy.get('port',80))
        else:
            return proxy.get('mode', 'http')+'://'+proxy.get('username','')+':'+proxy.get('password')+'@'+proxy.get('host','')+':'+str(proxy.get('port',80))


    def getTimeZone(self):
        proxy = self.proxy
        if proxy:            
            proxies = {proxy.get('mode'): self.formatProxyUrlPassword(proxy)}
            data = requests.get('https://time.gologin.com', proxies=proxies)
        else:
            data = requests.get('https://time.gologin.com')
        return json.loads(data.content.decode('utf-8'))


    def getProfile(self, profile_id=None):
        profile = self.profile_id if profile_id==None else profile_id
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'User-Agent': 'Selenium-API'
        }
        data = json.loads(requests.get(API_URL + '/browser/' + profile, headers=headers).content.decode('utf-8'))
        if data.get("statusCode")==404:
            raise Exception(data.get("error")+ ": " +data.get("message"))            
        return data

    def downloadProfileZip(self):
        s3path = self.profile.get('s3Path', '')
        data = ''
        if s3path=='':
            # print('downloading profile direct')
            headers = {
                'Authorization': 'Bearer ' + self.access_token,
                'User-Agent': 'Selenium-API'
            }
            data = requests.get(API_URL + '/browser/'+self.profile_id, headers=headers).content
        else:
            # print('downloading profile s3')
            s3url = 'https://gprofiles.gologin.com/' + s3path.replace(' ', '+')
            data = requests.get(s3url).content

        if len(data)==0:
            self.createEmptyProfile()            
        else:
            with open(self.profile_zip_path, 'wb') as f:
                f.write(data)
        
        try:
            self.extractProfileZip()
        except:
            self.uploadEmptyProfile()
            self.createEmptyProfile()   
            self.extractProfileZip()

        if not os.path.exists(os.path.join(self.profile_path, 'Default', 'Preferences')):
            self.uploadEmptyProfile()
            self.createEmptyProfile()   
            self.extractProfileZip()

    def uploadEmptyProfile(self):
        print('uploadEmptyProfile')
        upload_profile = open(r'./gologin_zeroprofile.zip', 'wb')
        source = requests.get('https://gprofiles.gologin.com/zero_profile.zip')
        upload_profile.write(source.content)
        upload_profile.close

    def createEmptyProfile(self):
        print('createEmptyProfile')
        empty_profile = '../gologin_zeroprofile.zip'
        if not os.path.exists(empty_profile):
            empty_profile = 'gologin_zeroprofile.zip'
        shutil.copy(empty_profile, self.profile_zip_path)

    def extractProfileZip(self):
        with zipfile.ZipFile(self.profile_zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.profile_path)       
        os.remove(self.profile_zip_path)


    def getGeolocationParams(self, profileGeolocationParams, tzGeolocationParams):
        if profileGeolocationParams.get('fillBasedOnIp'):
          return {
            'mode': profileGeolocationParams['mode'],
            'latitude': float(tzGeolocationParams['latitude']),
            'longitude': float(tzGeolocationParams['longitude']),
            'accuracy': float(tzGeolocationParams['accuracy']),
          }
        
        return {
          'mode': profileGeolocationParams['mode'],
          'latitude': profileGeolocationParams['latitude'],
          'longitude': profileGeolocationParams['longitude'],
          'accuracy': profileGeolocationParams['accuracy'],
        }


    def convertPreferences(self, preferences):
        resolution = preferences.get('resolution', '1920x1080')
        preferences['screenWidth'] = int(resolution.split('x')[0])
        preferences['screenHeight'] = int(resolution.split('x')[1])
        
        self.tz = self.getTimeZone()
        # print('tz=', self.tz)
        tzGeoLocation = {
            'latitude': self.tz.get('ll', [0, 0])[0],
            'longitude': self.tz.get('ll', [0, 0])[1],
            'accuracy': self.tz.get('accuracy', 0),
        }

        preferences['geoLocation'] = self.getGeolocationParams(preferences['geolocation'], tzGeoLocation)

        preferences['webRtc'] = {
            'mode': 'public' if preferences.get('webRTC',{}).get('mode') == 'alerted' else preferences.get('webRTC',{}).get('mode'),
            'publicIP': self.tz['ip'] if preferences.get('webRTC',{}).get('fillBasedOnIp') else preferences.get('webRTC',{}).get('publicIp'),
            'localIps': preferences.get('webRTC',{}).get('localIps', [])
        }

        preferences['timezone'] = {
            'id': self.tz.get('timezone')
        }

        preferences['webgl_noise_value'] = preferences.get('webGL', {}).get('noise')
        preferences['get_client_rects_noise'] = preferences.get('webGL', {}).get('getClientRectsNoise')
        preferences['canvasMode'] = preferences.get('canvas', {}).get('mode')
        preferences['canvasNoise'] = preferences.get('canvas', {}).get('noise')
        preferences['audioContextMode'] = preferences.get('audioContext', {}).get('mode')
        preferences['audioContext'] = {
            'enable': preferences.get('audioContextMode')!= 'off',
            'noiseValue': preferences.get('audioContext').get('noise'),
        }

        preferences['webgl'] = {
            'metadata': {
              'vendor': preferences.get('webGLMetadata', {}).get('vendor'),
              'renderer': preferences.get('webGLMetadata', {}).get('renderer'),
              'mode': preferences.get('webGLMetadata', {}).get('mode') == 'mask',
            }
        }

        if preferences.get('navigator', {}).get('userAgent'):
            preferences['userAgent'] = preferences.get('navigator', {}).get('userAgent')

        if preferences.get('navigator', {}).get('doNotTrack'):
            preferences['doNotTrack'] = preferences.get('navigator', {}).get('doNotTrack')
        
        if preferences.get('navigator', {}).get('hardwareConcurrency'):
            preferences['hardwareConcurrency'] = preferences.get('navigator', {}).get('hardwareConcurrency')

        if preferences.get('navigator', {}).get('language'):
            preferences['language'] = preferences.get('navigator', {}).get('language')
        
        if preferences.get('isM1', False):
            preferences["is_m1"] = preferences.get('isM1', False)

        if preferences.get('os')=="android":
            devicePixelRatio = preferences.get("devicePixelRatio");
            deviceScaleFactorCeil = math.ceil(devicePixelRatio or 3.5);
            deviceScaleFactor = devicePixelRatio;
            if deviceScaleFactorCeil == devicePixelRatio:
                deviceScaleFactor += 0.00000001;

            preferences["mobile"] = {
                "enable": True,
                "width": preferences['screenWidth'],
                "height": preferences['screenHeight'],
                "device_scale_factor": deviceScaleFactor,
            }

        return preferences


    def updatePreferences(self):
        pref_file = os.path.join(self.profile_path, 'Default', 'Preferences')
        with open(pref_file, 'r', encoding="utf-8") as pfile:
            preferences = json.load(pfile)    
        profile = self.profile
        proxy = self.profile.get('proxy')
        # print('proxy=', proxy)
        if proxy and (proxy.get('mode')=='gologin' or proxy.get('mode')=='tor'):
            autoProxyServer = profile.get('autoProxyServer')
            splittedAutoProxyServer = autoProxyServer.split('://')
            splittedProxyAddress = splittedAutoProxyServer[1].split(':')
            port = splittedProxyAddress[1]

            proxy = {
              'mode': 'http',
              'host': splittedProxyAddress[0],
              'port': port,
              'username': profile.get('autoProxyUsername'),
              'password': profile.get('autoProxyPassword'),
              'timezone': profile.get('autoProxyTimezone', 'us'),
            }
            
            profile['proxy']['username'] = profile.get('autoProxyUsername')
            profile['proxy']['password'] = profile.get('autoProxyPassword')
        
        if not proxy or proxy.get('mode')=='none':
            print('no proxy')
            proxy = None
        
        if proxy and proxy.get('mode')==None:
            proxy['mode'] = 'http'

        self.proxy = proxy
        self.profile_name = profile.get('name')
        if self.profile_name==None:
            print('empty profile name')
            print('profile=', profile)
            exit()
            
        gologin = self.convertPreferences(profile)        
        if self.credentials_enable_service!=None:
            preferences['credentials_enable_service'] = self.credentials_enable_service
        preferences['gologin'] = gologin
        pfile = open(pref_file, 'w')
        json.dump(preferences, pfile)

    def createStartup(self):
        if self.local==False and os.path.exists(self.profile_path):
            shutil.rmtree(self.profile_path)
        self.profile = self.getProfile()
        if self.local==False:
            self.downloadProfileZip()
        self.updatePreferences()
        
        return self.profile_path


    def headers(self):
        return {
            'Authorization': 'Bearer ' + self.access_token,
            'User-Agent': 'Selenium-API'
        }


    def getRandomFingerprint(self, options):
        os_type = options.get('os', 'lin')
        return json.loads(requests.get(API_URL + '/browser/fingerprint?os=' + os_type, headers=self.headers()).content.decode('utf-8'))

    def profiles(self):
        return json.loads(requests.get(API_URL + '/browser/', headers=self.headers()).content.decode('utf-8'))

    def create(self, options={}):
        profile_options = self.getRandomFingerprint(options)
        navigator = options.get('navigator')
        if options.get('navigator'):
            resolution = navigator.get('resolution')
            userAgent = navigator.get('userAgent')
            language = navigator.get('language')

            if resolution == 'random' or userAgent == 'random':
                options.pop('navigator')
            if resolution != 'random' and userAgent != 'random':
                options.pop('navigator')            
            if resolution == 'random' and userAgent != 'random':
                profile_options['navigator']['userAgent'] = userAgent
            if userAgent == 'random' and resolution != 'random':
                profile_options['navigator']['resolution'] = resolution
            if resolution != 'random' and userAgent != 'random':
                profile_options['navigator']['userAgent'] = userAgent
                profile_options['navigator']['resolution'] = resolution
                       
            profile_options['navigator']['language'] = language

        profile = {
          "name": "default_name",
          "notes": "auto generated",
          "browserType": "chrome",
          "os": "lin",
          "googleServicesEnabled": True,
          "lockEnabled": False,
          "audioContext": {
            "mode": "noise"
          },
          "canvas": {
            "mode": "noise"
          },
          "webRTC": {
            "mode": "disabled",
            "enabled": False,
            "customize": True,
            "fillBasedOnIp": True
          },
          "fonts": {
            "families": profile_options.get('fonts')
          },
          "navigator": profile_options.get('navigator', {}),
          # "screenHeight": 768,
          # "screenWidth": 1024,
          "profile": json.dumps(profile_options),
        }
    
        # if profile.get('navigator'):
        #   profile['navigator']['resolution'] = "1024x768"
        # else:
        #   profile['navigator'] = {'resolution': "1024x768"}
        
        for k,v in options.items():
            profile[k] = v

        response = json.loads(requests.post(API_URL + '/browser/', headers=self.headers(), json=profile).content.decode('utf-8'))
        return response.get('id')


    def delete(self, profile_id=None):
        profile = self.profile_id if profile_id==None else profile_id
        requests.delete(API_URL + '/browser/' + profile, headers=self.headers())


    def update(self, options):
        self.profile_id = options.get('id')
        profile = self.getProfile()
        #print("profile", profile)
        for k,v in options.items():
            profile[k] = v
        resp = requests.put(API_URL + '/browser/' + self.profile_id, headers=self.headers(), json=profile).content.decode('utf-8')
        #print("update", resp)
        #return json.loads(resp)

    def waitDebuggingUrl(self, delay_s, try_count=3):
        url = 'https://' + self.profile_id + '.orbita.gologin.com/json/version'
        wsUrl = ''
        try_number = 1
        while wsUrl=='':
            time.sleep(delay_s)
            try:
                response = json.loads(requests.get(url).content)
                wsUrl = response.get('webSocketDebuggerUrl', '')
            except:
                pass
            if try_number >= try_count:
                return {'status': 'failure', 'wsUrl': wsUrl}
            try_number += 1

        wsUrl = wsUrl.replace('ws://', 'wss://').replace('127.0.0.1', self.profile_id + '.orbita.gologin.com')
        return {'status': 'success', 'wsUrl': wsUrl}

    def startRemote(self, delay_s=3):
        profileResponse = requests.post(API_URL + '/browser/' + self.profile_id + '/web', headers=self.headers()).content.decode('utf-8')
        print('profileResponse', profileResponse)
        if profileResponse == 'ok':
            return self.waitDebuggingUrl(delay_s)
        return {'status': 'failure'}

    def stopRemote(self):
        requests.delete(API_URL + '/browser/' + self.profile_id + '/web', headers=self.headers())